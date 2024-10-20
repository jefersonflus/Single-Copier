# Single Copier

O **Single Copier** é um script em Python que permite copiar uma única página de um site para uma pasta local. Ele baixa a página HTML fornecida e todos os recursos associados, como imagens, arquivos CSS, JavaScript, fontes e vídeos referenciados nessa página específica. O script ajusta automaticamente os caminhos nos arquivos HTML e CSS para que os recursos locais sejam usados, permitindo que você visualize a página offline.

## Índice

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Uso](#uso)
- [Funcionamento](#funcionamento)
- [Limitações e Notas](#limitações-e-notas)
- [Contribuição](#contribuição)
- [Licença](#licença)

## Características

- **Download de Página Única**: Baixa a página HTML especificada e todos os recursos referenciados nela.
- **Atualização de Caminhos**: Ajusta os caminhos nos arquivos HTML e CSS para apontar para os recursos locais.
- **Paralelismo**: Utiliza threads para baixar múltiplos recursos simultaneamente, acelerando o processo.
- **Respeito ao Domínio**: Limita o download apenas aos recursos hospedados no mesmo domínio da página fornecida.
- **Tratamento de Erros**: Fornece logs detalhados para ajudar na identificação de problemas durante o download.
- **Configuração via Linha de Comando**: Permite especificar a URL da página e o diretório de saída através de argumentos na linha de comando.

## Requisitos

- Python 3.6 ou superior
- Bibliotecas Python:

  - `requests`
  - `beautifulsoup4`
  - `lxml` (opcional, mas recomendado para melhor desempenho)

- **Nota**: As bibliotecas podem ser instaladas usando o `pip`.

## Instalação

1. **Clone o repositório ou copie o script para o seu ambiente local**.

2. **Instale as bibliotecas necessárias**:

   Abra o terminal ou prompt de comando e execute:

   ```bash
   pip install requests beautifulsoup4 lxml
   ```

## Uso

Execute o script via linha de comando, especificando a URL da página que deseja copiar e o nome da pasta de saída.

```bash
python single_copier.py <URL_DA_PÁGINA> <PASTA_DE_SAÍDA>
```

**Exemplo**:

```bash
python single_copier.py https://exemplo.com/pagina.html pagina_copiada
```

Isso irá:

- Baixar o conteúdo de `https://exemplo.com/pagina.html`.
- Criar uma pasta chamada `pagina_copiada` no diretório atual.
- Salvar todos os arquivos baixados dentro da pasta `pagina_copiada`, organizados em subpastas (`img`, `css`, `js`, etc.).
- Gerar um arquivo `index.html` na pasta de saída, com os caminhos atualizados para os recursos locais.

## Funcionamento

1. **Configuração Inicial**:

   - O script inicia criando a estrutura de pastas necessária dentro do diretório de saída (por padrão: `img`, `css`, `js`, `videos`, `fonts`, `other`).
   - Configura uma sessão HTTP usando `requests.Session()` para reutilizar conexões e definir cabeçalhos padrão, simulando um navegador real.

2. **Download da Página Especificada**:

   - Acessa a URL fornecida e faz o download do conteúdo HTML.
   - Utiliza o `BeautifulSoup` para analisar o HTML e encontrar todos os elementos que referenciam recursos externos presentes nessa página.

3. **Download dos Recursos**:

   - Identifica recursos como imagens, arquivos CSS, scripts, vídeos e fontes referenciados na página.
   - Utiliza um `ThreadPoolExecutor` para baixar múltiplos recursos em paralelo.
   - Limita o download apenas a recursos hospedados no mesmo domínio da página original.
   - Atualiza os atributos dos elementos no HTML para apontar para os arquivos locais baixados.

4. **Processamento de Arquivos CSS**:

   - Analisa os arquivos CSS referenciados na página para encontrar URLs de recursos (como imagens de fundo e fontes).
   - Baixa esses recursos e atualiza as URLs dentro dos arquivos CSS para apontar para os arquivos locais.

5. **Salvamento dos Arquivos**:

   - Salva todos os recursos baixados nas pastas correspondentes dentro do diretório de saída.
   - Gera um arquivo `index.html` com o conteúdo atualizado.

6. **Logs e Tratamento de Erros**:

   - Fornece logs informativos sobre o progresso do download.
   - Trata exceções e erros HTTP, registrando avisos ou erros conforme necessário.
   - Ignora recursos que não podem ser baixados devido a erros de autorização (códigos HTTP 401).

## Limitações e Notas

- **Apenas Página Fornecida**: O script baixa apenas a página HTML especificada e os recursos diretamente referenciados nela. Não segue links para outras páginas ou baixa o site inteiro.

- **Conteúdo Dinâmico**: O script não captura conteúdo carregado dinamicamente via JavaScript (por exemplo, dados carregados após a renderização inicial da página). Para páginas altamente dinâmicas, considere usar ferramentas como o Selenium ou Playwright.

- **Recursos Protegidos**: Alguns recursos podem estar protegidos e exigir autenticação ou tokens de acesso. O script ignora esses recursos e registra um aviso.

- **Respeito às Políticas do Site**:

  - Certifique-se de ter permissão para baixar e usar os recursos da página.
  - Respeite o arquivo `robots.txt` e os termos de uso do site.
  - Evite violar direitos autorais ou usar o script para atividades não éticas.

- **Escopo do Download**: O script baixa apenas recursos hospedados no mesmo domínio da página fornecida. Recursos externos (por exemplo, bibliotecas CDN) não são baixados.

- **Desempenho**: O uso de threads acelera o download, mas pode aumentar a carga na sua conexão de internet e no servidor de destino. Use com responsabilidade.

- **Compatibilidade de Sistemas Operacionais**: O script utiliza a biblioteca `pathlib` para garantir compatibilidade entre diferentes sistemas operacionais (Windows, macOS, Linux).

## Contribuição

Contribuições são bem-vindas! Se você deseja melhorar o **Single Copier**, sinta-se à vontade para:

- Abrir uma *issue* para relatar bugs ou sugerir melhorias.
- Enviar um *pull request* com correções ou novos recursos.

Antes de contribuir, por favor:

- Certifique-se de que seu código segue as boas práticas de codificação em Python.
- Teste suas alterações para garantir que não introduzam novos problemas.

## Licença

Este projeto é distribuído sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para obter mais detalhes.
