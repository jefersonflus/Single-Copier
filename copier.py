import os
import re
import requests
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
from pathlib import Path
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_folder_structure(base_path):
    folders = ["img", "css", "js", "videos", "fonts", "other"]
    for folder in folders:
        os.makedirs(os.path.join(base_path, folder), exist_ok=True)

def save_file(url, folder_path, base_path, session):
    if url.startswith("data:"):  # Ignorar data URIs
        return None

    url, _ = urldefrag(url)  # Remove fragmentos de URL

    try:
        response = session.get(url, stream=True, timeout=10)
        response.raise_for_status()

        parsed_url = urlparse(url)
        file_name = os.path.basename(parsed_url.path)
        if not file_name:  # Evitar salvar arquivos sem nome
            file_name = "unknown_file"

        file_path = Path(folder_path) / file_name

        if file_path.exists():
            return file_path.relative_to(base_path).as_posix()

        os.makedirs(folder_path, exist_ok=True)  # Garantir que o diretório existe

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return file_path.relative_to(base_path).as_posix()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            logger.warning(f"Acesso não autorizado ao baixar {url}: {e}")
        else:
            logger.error(f"Erro HTTP ao baixar {url}: {e}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erro de conexão ao baixar {url}: {e}")
    except Exception as e:
        logger.error(f"Ocorreu um erro ao baixar {url}: {e}")
    return None

def download_assets(soup, base_url, base_path, session):
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
            full_url = urljoin(base_url, url)
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

            folder_path = os.path.join(base_path, folder)
            saved_path = save_file(full_url, folder_path, base_path, session)
            if saved_path:
                element[attribute] = saved_path

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for tag, attributes in tags.items():
            elements = soup.find_all(tag)
            for element in elements:
                for attribute in attributes:
                    futures.append(executor.submit(process_element, element, attribute, tag))
        for future in futures:
            future.result()

def process_css_files(css_folder, base_url, base_path, session):
    css_files = [os.path.join(css_folder, f) for f in os.listdir(css_folder) if f.endswith('.css')]
    url_pattern = re.compile(r'url\((.*?)\)')
    for css_file in css_files:
        with open(css_file, 'r', encoding='utf-8') as file:
            content = file.read()
        urls = url_pattern.findall(content)
        for url in urls:
            url = url.strip('\'"')
            if url.startswith('data:'):
                continue
            full_url = urljoin(base_url, url)
            folder = 'fonts' if any(ext in url for ext in ['.woff', '.woff2', '.ttf', '.otf', '.eot']) else 'img'
            folder_path = os.path.join(base_path, folder)
            saved_path = save_file(full_url, folder_path, base_path, session)
            if saved_path:
                relative_path = Path(saved_path).as_posix()
                content = content.replace(url, relative_path)
        with open(css_file, 'w', encoding='utf-8') as file:
            file.write(content)

def save_html(soup, path):
    with open(path, "w", encoding="utf-8") as file:
        file.write(soup.prettify())

def copy_site(url, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    create_folder_structure(output_folder)

    session = requests.Session()
    base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))

    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' \
                      'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                      'Chrome/58.0.3029.110 Safari/537.3',
        'Referer': base_url
    })

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        download_assets(soup, base_url, output_folder, session)
        process_css_files(os.path.join(output_folder, "css"), base_url, output_folder, session)

        html_path = os.path.join(output_folder, "index.html")
        save_html(soup, html_path)
        logger.info("Download concluído com sucesso.")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Erro HTTP ao acessar o site: {e}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erro de conexão ao acessar o site: {e}")
    except Exception as e:
        logger.error(f"Ocorreu um erro ao acessar o site: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Copiar um site para uma pasta local.')
    parser.add_argument('url', help='A URL do site que você deseja copiar.')
    parser.add_argument('output_folder', help='O nome da pasta de saída.')
    args = parser.parse_args()
    copy_site(args.url, args.output_folder)
