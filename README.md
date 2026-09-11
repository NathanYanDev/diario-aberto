# Diário Oficial de Jundiaí — coleta, extração e busca

Coletor, extrator e motor de busca (textual + semântica) sobre a Imprensa
Oficial do Município de Jundiaí (https://imprensaoficial.jundiai.sp.gov.br).

Projeto pessoal — aplica, numa escala bem menor, princípios que uso
profissionalmente automatizando coleta de dados públicos (scraping
resiliente, extração de PDF com fallback, testes construídos a partir de
falhas reais).

## Por que esse projeto existe

Não tem API pública pra Jundiaí (diferente de projetos como o [Querido
Diário](https://queridodiario.ok.org.br), que cobre outros ~350 municípios
brasileiros, mas não este) — então o dado só existe em HTML paginado +
PDF. Diferente do Querido Diário, este projeto segmenta cada edição em
atos administrativos individuais (Portarias, Decretos, Editais) em vez de
indexar a edição inteira, e busca combina full-text tradicional com busca
semântica via embeddings.

## Stack e por quê

| Camada          | Escolha                                              | Justificativa                                                                                                                    |
| --------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Scraping        | httpx + BeautifulSoup + tenacity                     | HTTP simples resolve (site não tem proteção anti-bot); tenacity dá retry/backoff declarativo sem reinventar                      |
| Extração de PDF | pdfplumber, com fallback pra pytesseract + pdf2image | Confirmado com PDF real (Edição 2917/2006): parte do conteúdo é imagem, não texto — ver achado abaixo                            |
| Banco           | Postgres + pgvector                                  | Uma tabela só, busca textual (`tsvector` nativo) e semântica (`pgvector`) lado a lado, sem precisar manter dois bancos separados |
| Schema          | SQL puro (`schema.sql`), sem Alembic                 | Escopo pessoal não justifica migração versionada agora; registrado aqui como melhoria futura, não como lacuna esquecida          |
| API             | FastAPI                                              | Padrão de mercado pra expor a busca via HTTP, tipagem via Pydantic                                                               |
| Testes          | pytest, com fixtures de PDF/HTML reais               | Mesmo padrão do Sentinel: teste construído a partir de caso real de falha, não hipotético                                        |

## Estrutura do projeto

```
src/diario_aberto/
├── config.py            # configuração via variáveis de ambiente - TODO
├── db/                  # modelos SQLAlchemy + sessão - Models feito / Sessão TODO
├── scraper/             # listagem paginada + parsing de cada edição — TODO
├── extraction/          # texto de PDF + segmentação em atos — TODO
├── embeddings/          # geração de embeddings - TODO
├── search/              # busca textual/semântica/híbrida — TODO
├── api/                 # FastAPI - TODO
└── cli.py               # orquestrador do backfill — TODO

tests/
├── fixtures/            # PDFs/HTMLs reais usados como casos de regressão
└── test_*.py
```
