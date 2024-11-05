# Single Copier

Este script permite copiar uma página web para uma pasta local, incluindo todos os recursos referenciados, como imagens, CSS, JavaScript, fontes e vídeos. É especialmente útil para salvar páginas para visualização offline ou para arquivamento.

## Recursos

- **Copia páginas web inteiras**, incluindo recursos estáticos.
- **Processa arquivos CSS**, baixando recursos referenciados e arquivos importados via `@import`.
- **Lida com conteúdo dinâmico**, permitindo interação manual com a página antes da captura (opcional).
- **Preserva a estrutura de diretórios**, organizando recursos em pastas como `css`, `js`, `img`, `fonts`, etc.

## Pré-requisitos

- Python 3.x instalado no sistema.
- Módulos Python adicionais:
  - `requests`
  - `beautifulsoup4`
  - `lxml`
  - `selenium` (opcional, para interação manual)
  - `webdriver-manager` (opcional, para interação manual)

Você pode instalar os módulos necessários usando o `pip`:

```bash
pip install requests beautifulsoup4 lxml selenium webdriver-manager
```

## Instalação

1. **Clone ou faça download** deste repositório para o seu computador.

2. Certifique-se de que você tem o Python 3 instalado. Você pode verificar executando:

   ```bash
   python --version
   ```

   ou

   ```bash
   python3 --version
   ```

3. **Instale as dependências** listadas acima.

## Uso

```bash
python copier.py <URL_DA_PÁGINA> <PASTA_DE_SAÍDA> [opções]
```

### Parâmetros:

- `<URL_DA_PÁGINA>`: A URL completa da página que você deseja copiar.
- `<PASTA_DE_SAÍDA>`: O nome da pasta onde os arquivos serão salvos.

### Opções:

- `-o`, `--open-browser`: Abre um navegador para interação manual antes de capturar a página. Útil para páginas que requerem login, resolução de CAPTCHA ou carregam conteúdo via JavaScript.

### Exemplos:

#### Copiar uma página sem interação manual:

```bash
python copier.py https://exemplo.com/pagina.html pagina_copiada
```

#### Copiar uma página com interação manual:

```bash
python copier.py https://exemplo.com/pagina_dinamica.html pagina_copiada -o
```

Ao usar a opção `-o`, o navegador será aberto e você terá **1 minuto** para interagir com a página. Após esse tempo, o navegador será fechado automaticamente e o script continuará o processamento usando o código-fonte da página naquele momento.

### Personalizar o Tempo de Espera (Opcional):

Se desejar alterar o tempo que o navegador fica aberto ao usar a opção `-o`, você pode modificar o valor de `timeout` no código do script, na função `copy_site`:

```python
timeout = 60  # Tempo em segundos
```

## Como Funciona

1. **Captura da Página**:

   - **Sem a opção `-o`**: O script faz uma requisição HTTP à URL fornecida e obtém o código-fonte da página.
   - **Com a opção `-o`**: O script abre um navegador usando o Selenium, permite interação manual por um tempo especificado, e então captura o código-fonte da página.

2. **Processamento do Código-Fonte**:

   - O script analisa o código-fonte usando o BeautifulSoup.
   - Identifica todos os recursos referenciados (imagens, CSS, JS, fontes, vídeos, etc.).

3. **Download de Recursos**:

   - Baixa todos os recursos referenciados, organizando-os em pastas apropriadas.
   - Processa arquivos CSS, baixando recursos referenciados em `url()` e arquivos importados via `@import`.

4. **Atualização de Referências**:

   - Atualiza as referências nos arquivos HTML e CSS para apontar para os recursos locais baixados.

5. **Salvamento**:

   - Salva o código-fonte atualizado na pasta de saída como `index.html`.

## Estrutura de Pastas

Após a execução, a pasta de saída terá a seguinte estrutura:

```
<PASTA_DE_SAÍDA>/
├── index.html
├── css/
├── js/
├── img/
├── fonts/
├── videos/
└── other/
```

## Considerações Importantes

- **Respeito aos Termos de Uso**: Certifique-se de ter permissão para baixar e armazenar o conteúdo das páginas que você está copiando. Respeite os termos de uso dos sites e evite violar direitos autorais ou políticas de acesso.

- **Limitações**:

  - O script não pode baixar recursos que não existem no servidor ou que estão protegidos por mecanismos de segurança.
  - Alguns sites podem bloquear requisições automatizadas. Se você enfrentar problemas, tente usar a opção `-o` para interação manual.

- **Recursos Carregados via JavaScript**:

  - Para páginas que carregam conteúdo dinamicamente via JavaScript, é recomendado usar a opção `-o` para permitir que o conteúdo seja carregado antes da captura.

- **Dependências do Selenium**:

  - Se utilizar a opção `-o`, certifique-se de ter o Google Chrome instalado e que o ChromeDriver está configurado corretamente. O `webdriver-manager` ajuda a gerenciar o ChromeDriver automaticamente.

## Dicas de Depuração

- **Logs Detalhados**:

  - O script utiliza o módulo `logging` para fornecer informações sobre o processo. Por padrão, o nível de log é `INFO`. Para obter logs mais detalhados (por exemplo, para depuração), você pode alterar o nível de log para `DEBUG` no código:

    ```python
    logging.basicConfig(level=logging.DEBUG)
    ```

- **Verificação Manual**:

  - Se alguns recursos não foram baixados ou a página não está sendo exibida corretamente, verifique manualmente os arquivos HTML e CSS para identificar possíveis problemas nas referências.

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests com melhorias, correções de bugs ou novos recursos.

## Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
