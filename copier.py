import os
import re
import requests
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
from pathlib import Path
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor
import time
import mimetypes

# Importações adicionais para o Selenium (se usar a opção -o)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_folder_structure(base_path):
    folders = ["img", "css", "js", "videos", "fonts", "other"]
    for folder in folders:
        Path(base_path, folder).mkdir(parents=True, exist_ok=True)

def save_file(url, folder_path, base_path, session):
    if url.startswith("data:"):  # Ignorar data URIs
        return None

    url, _ = urldefrag(url)  # Remove fragmentos de URL

    try:
        # Remover query parameters para determinar o nome do arquivo
        url_without_query = url.split('?')[0]

        response = session.get(url, stream=True, timeout=10)
        response.raise_for_status()

        parsed_url = urlparse(url_without_query)
        file_name = os.path.basename(parsed_url.path)
        if not file_name or '.' not in file_name:
            # Tentar obter o tipo de conteúdo a partir do cabeçalho da resposta
            content_type = response.headers.get('Content-Type')
            if content_type:
                ext = mimetypes.guess_extension(content_type.split(';')[0].strip())
                if ext:
                    file_name = f"unknown_file{ext}"
                else:
                    file_name = "unknown_file"
            else:
                file_name = "unknown_file"

        logger.debug(f"Salvando arquivo de URL: {url} com nome: {file_name}")

        file_path = Path(folder_path) / file_name

        if file_path.exists():
            return file_path.relative_to(base_path).as_posix()

        folder_path.mkdir(parents=True, exist_ok=True)  # Garantir que o diretório existe

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return file_path.relative_to(base_path).as_posix()
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else 'N/A'
        if status_code == 401:
            logger.warning(f"Acesso não autorizado ao baixar {url}: {e}")
        elif status_code == 404:
            logger.info(f"Recurso não encontrado (404) ao baixar {url}")
        else:
            logger.error(f"Erro HTTP ao baixar {url} (Status {status_code}): {e}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erro de conexão ao baixar {url}: {e}")
    except Exception as e:
        logger.error(f"Ocorreu um erro ao baixar {url}: {e}")
    return None

def process_css_file(css_file_path, css_file_url, base_path, session, processed_files=None):
    if processed_files is None:
        processed_files = set()

    # Evitar processar o mesmo arquivo mais de uma vez
    css_file_real_path = css_file_path.resolve()
    if css_file_real_path in processed_files:
        return
    processed_files.add(css_file_real_path)

    url_pattern = re.compile(r'url\(\s*[\'"]?(.*?)[\'"]?\s*\)', re.IGNORECASE)
    import_pattern = re.compile(r'@import\s+(?:url\()?["\']?(.*?)["\']?\)?\s*;')

    with open(css_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Processar @import statements
    imports = import_pattern.findall(content)
    for import_url in imports:
        import_url = import_url.strip().strip('\'"')
        if import_url.startswith('data:'):
            continue
        full_import_url = urljoin(css_file_url, import_url)
        logger.debug(f"Processando @import no CSS: {import_url} -> {full_import_url}")
        folder_path = Path(base_path, 'css')
        saved_import_path = save_file(full_import_url, folder_path, base_path, session)
        if saved_import_path:
            # Caminho completo para o arquivo CSS importado salvo localmente
            import_css_file_path = base_path / saved_import_path

            # Calcular o caminho relativo entre o arquivo CSS atual e o CSS importado
            relative_import_path = os.path.relpath(import_css_file_path, start=css_file_path.parent)
            relative_import_path = relative_import_path.replace('\\', '/')  # Para compatibilidade com Windows

            # Atualizar a declaração @import no conteúdo do CSS
            # Substituir todas as ocorrências do @import original
            pattern = re.compile(r'@import\s+(?:url\()?[\'"]?' + re.escape(import_url) + r'[\'"]?\)?\s*;')
            content = pattern.sub(f'@import "{relative_import_path}";', content)

            # Processar o arquivo CSS importado
            process_css_file(import_css_file_path, full_import_url, base_path, session, processed_files)

    # Processar URLs dentro do CSS
    urls = url_pattern.findall(content)
    for url in urls:
        url = url.strip().strip('\'"')
        if url.startswith('data:'):
            continue
        full_url = urljoin(css_file_url, url)
        logger.debug(f"Processando URL no CSS: {url} -> {full_url}")
        folder = 'fonts' if any(ext in url.lower() for ext in ['.woff', '.woff2', '.ttf', '.otf', '.eot', '.svg']) else 'img'
        folder_path = Path(base_path, folder)
        saved_path = save_file(full_url, folder_path, base_path, session)
        if saved_path:
            # Caminho completo para o recurso salvo localmente
            resource_file_path = base_path / saved_path

            # Calcular o caminho relativo entre o arquivo CSS atual e o recurso
            relative_resource_path = os.path.relpath(resource_file_path, start=css_file_path.parent)
            relative_resource_path = relative_resource_path.replace('\\', '/')

            # Substituir a URL no conteúdo do CSS
            content = content.replace(url, relative_resource_path)

    with open(css_file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def download_assets(soup, base_url, page_url, base_path, session):
    tags = {
        "img": ["src", "srcset"],
        "link": ["href"],
        "script": ["src"],
        "video": ["src"],
        "source": ["src", "srcset"]
    }

    original_domain = urlparse(base_url).netloc

    def process_element(element, attribute, tag):
        url = element.get(attribute)
        if url:
            url = url.strip()
            full_url = urljoin(page_url, url)
            resource_domain = urlparse(full_url).netloc
            if resource_domain != original_domain:
                return
            folder = "other"
            if tag == "img":
                folder = "img"
            elif tag == "link" and "stylesheet" in element.get("rel", []):
                folder = "css"
            elif tag == "script":
                folder = "js"
            elif tag in ["video", "source"]:
                folder = "videos"
            elif any(ext in url.lower() for ext in ['.woff', '.woff2', '.ttf', '.otf', '.eot', '.svg']):
                folder = "fonts"

            folder_path = Path(base_path, folder)
            saved_path = save_file(full_url, folder_path, base_path, session)
            if saved_path:
                element[attribute] = saved_path

                # Se for um arquivo CSS, processá-lo imediatamente
                if tag == "link" and "stylesheet" in element.get("rel", []):
                    css_file_path = folder_path / Path(saved_path).name
                    css_file_url = full_url
                    process_css_file(css_file_path, css_file_url, base_path, session)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for tag, attributes in tags.items():
            elements = soup.find_all(tag)
            for element in elements:
                for attribute in attributes:
                    futures.append(executor.submit(process_element, element, attribute, tag))
        for future in futures:
            future.result()

def save_html(soup, path):
    with open(path, "w", encoding="utf-8") as file:
        file.write(soup.prettify())

def get_page_source_with_selenium(url, timeout):
    options = Options()
    # Remova o argumento headless para mostrar o navegador
    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.get(url)

    logger.info(f"O navegador será fechado automaticamente em {timeout} segundos.")

    # Espera pelo tempo especificado
    time.sleep(timeout)

    # Obtém o código-fonte da página
    page_source = driver.page_source

    # Obtém a URL atual após possíveis redirecionamentos ou navegações
    final_url = driver.current_url

    driver.quit()

    return page_source, final_url

def copy_site(url, output_folder, open_browser=False):
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    create_folder_structure(output_folder)

    session = requests.Session()

    try:
        if open_browser:
            # Usar o Selenium para obter o código-fonte após interação do usuário
            timeout = 30  # 1 minuto
            page_content, final_url = get_page_source_with_selenium(url, timeout)
        else:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            page_content = response.content
            final_url = response.url

        parsed_url = urlparse(final_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # Garantir que page_url termine com '/' se necessário
        path = parsed_url.path
        if not path.endswith('/') and not os.path.splitext(path)[1]:
            path += '/'
        page_url = parsed_url._replace(path=path).geturl()

        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, como Gecko) '
                          'Chrome/58.0.3029.110 Safari/537.3',
            'Referer': base_url
        })

        encoding = 'utf-8'  # Presumindo que o conteúdo está em UTF-8
        soup = BeautifulSoup(page_content, "html.parser", from_encoding=encoding)

        download_assets(soup, base_url, page_url, output_folder, session)

        html_path = output_folder / "index.html"
        save_html(soup, html_path)
        logger.info("Download concluído com sucesso.")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Erro HTTP ao acessar o site: {e}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erro de conexão ao acessar o site: {e}")
    except Exception as e:
        logger.error(f"Ocorreu um erro ao acessar o site: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Copiar uma página web para uma pasta local.')
    parser.add_argument('url', help='A URL da página que você deseja copiar.')
    parser.add_argument('output_folder', help='O nome da pasta de saída.')
    parser.add_argument('-o', '--open-browser', action='store_true', help='Abre um navegador para interação manual antes de capturar a página.')
    args = parser.parse_args()
    copy_site(args.url, args.output_folder, args.open_browser)
