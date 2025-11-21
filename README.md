# OptiPix

Otimização segura e rápida de lotes de fotos com relatórios e UI web simples.

## Visão Geral
- Processa pastas inteiras com barra de progresso e relatório JSON detalhado.
- Conversão opcional para WebP, controle de qualidade, resize com limites de largura/altura e opção de manter/strip EXIF.
- Execução paralela utilizando processos, preservando timestamps originais.
- UI web single-page para upload de múltiplos arquivos e download de ZIP com os resultados.
- Suporte a JPG/JPEG, PNG, GIF (primeiro frame), WEBP e HEIC/HEIF/AVIF quando `pillow-heif` estiver disponível.

## Requisitos do Sistema
- Python `>= 3.11`
- Windows, macOS ou Linux
- Opcional para HEIF/AVIF: `libheif` instalado no sistema
- Docker (opcional) para execução containerizada

## Dependências
Versões pinadas em `pyproject.toml`:
- `Pillow==10.4.0`
- `Flask==3.0.0`
- `tqdm==4.66.5`
- `PyYAML==6.0.2`
- `pytest==8.3.3`

Suporte HEIF opcional (não instalado por padrão):
- `pillow-heif` (requer `libheif`)

## Instalação e Configuração
Instalação local:
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
pip install .
```

Executar servidor local:
```bash
python -m server
# Abra http://localhost:8000/
```

Sem instalar o pacote (execução direta):
```bash
python -m src.server
```

HEIF/AVIF (opcional):
- Debian/Ubuntu: `sudo apt-get install libheif1 libheif-dev && pip install pillow-heif`
- macOS: `brew install libheif && pip install pillow-heif`
- Windows: instale wheels compatíveis do `pillow-heif` ou mantenha HEIF desabilitado (arquivos HEIC serão `unsupported`).

## Configuração (config.yml)
Exemplo em `config.yml.example`:
```yaml
quality: 85
webp: true
max_width: 1920
max_height: 1080
keep_exif: false
workers: cpu_count - 1
```
Use `--config` na CLI para carregar um arquivo YAML e sobrepor com flags.

## Guia de Uso
### CLI
O comando permanece disponível como `photo-slimmer` e também como `optipix`.
Processar pasta:
```bash
optipix process "C:\\Fotos" \
  --quality 85 --webp --max-width 1920 --max-height 1080 \
  --strip-exif --recursive --workers 8 --output report.json
```
- In-place somente com `--confirm`. Sem `--confirm`, escreve em `optimized/`.
- `--dry-run` estima sem salvar.

Preview de arquivo:
```bash
optipix preview "C:\\Fotos\\IMG_0001.JPG" --quality 85 --webp
```

Lote grande (10.000 fotos, 8 workers):
```bash
optipix process D:\\Photos --recursive --workers 8 --webp --quality 85 \
  --max-width 1920 --max-height 1080 --strip-exif --output report.json
```

### UI Web
```bash
python -m server
# Abra http://localhost:8000/
```
Arraste arquivos/pastas, ajuste configurações e clique em Otimizar para baixar `optimized.zip` com as imagens e `report.json`.
Consulte o <a href="/web/styleguide.html" target="_blank" rel="noopener">Guia de Estilo</a> para tokens e componentes.

### Docker
```bash
docker build -t photo-slimmer ./photo-slimmer
docker run --rm -p 8000:8000 photo-slimmer
```
CLI via Docker:
```bash
docker run --rm -v C:/Fotos:/data photo-slimmer \
  photo-slimmer process /data --webp --quality 85 --recursive --workers 8 --output /data/report.json
```

## Arquitetura
```
photo-slimmer/
  src/
    cli.py        # CLI: subcomandos process/preview e flags
    server.py     # Flask: / (UI), /web/*, /api/preview, /api/optimize
    processor.py  # Orquestra pipeline, multiprocessos, barra de progresso, report.json
    utils.py      # Detecção formatos, resize, conversão/salvamento, preserva timestamps
    config.py     # Carrega e mescla config.yml com overrides
  web/
    index.html, app.js, styles.css  # UI simples
  tests/
    test_processor.py  # Preview, dry-run, relatório e HEIF unsupported
```
Fluxo principal:
1. `cli.py` chama `processor.process_directory` com configurações.
2. `processor.py` distribui arquivos com `ProcessPoolExecutor`, coleta resultados e gera sumário.
3. `utils.py` realiza resize e conversão (opcional WebP), aplica qualidade e EXIF, preserva timestamps.
4. `server.py` aceita uploads, processa e retorna um ZIP com otimizações e `report.json`.

## API (Web)
- `GET /` → `index.html`
- `GET /web/<path>` → estáticos
- `POST /api/preview` → `multipart/form-data` com `file`; retorna estimativa
- `POST /api/optimize` → `multipart/form-data` com `files[]`; retorna `optimized.zip` contendo `report.json`

## Relatórios e Logs
- `report.json` inclui por arquivo: `original_size`, `new_size`, `bytes_saved`, `percent_saved`, `status`, `actions`.
- Log em `photo-slimmer.log` (níveis INFO/WARN/ERROR).

## Testes
```bash
pytest -q
```
Status atual: `3 passed`. Cobrem preview, dry-run e geração de relatório.

## Status e Roadmap
- Versão: `0.1.0`
- Roadmap:
  - Progresso em tempo real na UI (SSE)
  - Modo in-place seguro no servidor (backup/lock)
  - Suporte opcional `pyvips` para alto desempenho
  - Mais testes de integração e perfis de memória

## Diretrizes de Contribuição
- Fork e PR com descrição clara.
- Rodar `pytest` e manter cobertura nos módulos afetados.
- Seguir estilo atual (Python 3.11+, modular, funções pequenas e testáveis).
- Evitar dependências não essenciais; preferir padrões do projeto.

## Licença e Créditos
- Licença: MIT (ver `LICENSE`).
- Créditos: contribuidores do projeto `photo-slimmer`.

## Boas Práticas e Recomendações
- Qualidade vs tamanho: `quality 80–90` em WebP costuma equilibrar artefatos e redução.
- Para lotes grandes, usar `workers = cpu_count - 1` e limitar `max_width/max_height` para conter memória.

- Manter EXIF aumenta tamanho; para lotes massivos, prefira `--strip-exif` quando metadados não forem críticos.
