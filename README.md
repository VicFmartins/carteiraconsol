# CarteiraConsol

Plataforma full-stack para consolidação, processamento e análise de carteiras de investimento multi-instituição. O projeto foi construído para transformar arquivos heterogêneos de corretoras e bancos em uma base analítica consistente, pronta para consumo por APIs, interface web executiva e dashboards em BI.

Na prática, o CarteiraConsol conecta o fluxo operacional de ingestão de arquivos ao fluxo de entrega de informação: recebe planilhas reais, executa um ETL orientado a eventos, persiste snapshots consolidados no PostgreSQL e expõe os dados em uma experiência moderna de workspace para análise patrimonial.

## 🚀 Pitch Rápido

O CarteiraConsol resolve um problema comum em operações de investimento: dados de posição espalhados entre corretoras, extratos, formatos e nomenclaturas inconsistentes. Em vez de depender de tratamento manual, o sistema padroniza ativos, classifica posições, enriquece metadados, atualiza a base consolidada e entrega uma camada de consumo pronta para produto e analytics.

## 🎯 Visão Geral do Projeto

Carteiras de investimento reais costumam chegar em formatos diferentes:

- CSVs com cabeçalhos inconsistentes
- planilhas XLSX exportadas por plataformas distintas
- arquivos JSON com estruturas específicas de integradores
- snapshots de posição e arquivos de movimentação

O CarteiraConsol foi desenhado para resolver esse cenário com uma arquitetura modular:

- ingestão de arquivos locais ou via S3
- processamento ETL com regras reutilizáveis
- persistência relacional no PostgreSQL
- exposição via FastAPI
- consumo em frontend React
- exploração analítica via Metabase

## 🧭 Por Que Este Projeto Importa

Além de ser um backend ETL funcional, o projeto demonstra uma visão de produto:

- camada operacional de ingestão
- camada transacional e histórica
- camada de API
- camada de consumo analítico
- camada de apresentação para usuário final

Isso o torna relevante tanto como projeto de engenharia de dados quanto como foundation de um produto SaaS para wealth management, family office, consolidação patrimonial ou reporting de investimentos.

## 🏗️ Arquitetura

### Diagrama Simplificado

```text
Frontend React
    ↓
FastAPI (upload + consulta + ETL trigger)
    ↓
ETL Pipeline (extract → transform → enrich → load)
    ↓
PostgreSQL
    ↓
Analytics Views
    ↓
Metabase / Workspace Executivo
```

### Arquitetura em Camadas

```text
Usuário / Operador
    ↓
Frontend Workspace (React + TypeScript + Tailwind)
    ↓
API Layer (FastAPI routes)
    ↓
Service Layer (ETL service, query services, storage service)
    ↓
ETL Layer
    ├── Extract
    ├── Transform
    ├── Enrich
    └── Load
    ↓
Database Layer (SQLAlchemy + PostgreSQL)
    ↓
Analytics Layer (SQL views para Metabase)
```

## ✅ Funcionalidades Implementadas

- Upload real de arquivos para o backend via `POST /upload`
- Processamento ETL real com persistência em PostgreSQL
- Suporte a CSV, XLSX/XLS e JSON
- Suporte a ingestão local e via AWS S3
- Handler compatível com AWS Lambda
- Suporte dedicado a arquivos reais da XP em `data/real_inputs`
- Normalização de colunas inconsistentes
- Normalização de nomes de ativos
- Classificação de ativos em:
  - `fixed_income`
  - `equities`
  - `crypto`
  - `funds`
  - `others`
- Enriquecimento com metadados simulados
- Carga consolidada em tabelas normalizadas
- Endpoints REST para consulta de clientes, contas, ativos e posições
- Paginação e filtros simples nos endpoints de listagem
- Views analíticas prontas para dashboard
- Workspace executivo no frontend com:
  - upload de arquivo
  - estados de processamento
  - histórico recente de uploads
  - resumo do último processamento
  - preview executivo da carteira
- Integração com Metabase para dashboards
- Cobertura de testes automatizados com `pytest`

## 🧰 Tecnologias Utilizadas

### Backend

- Python 3.13
- FastAPI
- SQLAlchemy
- Pandas
- PostgreSQL
- python-dotenv
- boto3
- openpyxl
- Mangum

### Frontend

- React 18
- TypeScript
- Vite
- Tailwind CSS
- XLSX

### Analytics e Operação

- PostgreSQL Views
- Metabase
- Pytest
- Docker (uso local para PostgreSQL e Metabase)

## 📁 Estrutura do Projeto

```text
carteiraconsol/
├── app/
│   ├── api/                # Rotas FastAPI e router principal
│   ├── core/               # Configuração, logging e exceptions
│   ├── db/                 # Base SQLAlchemy, session e init do banco
│   ├── etl/                # Pipeline ETL modular
│   │   ├── extract/
│   │   ├── transform/
│   │   ├── enrich/
│   │   └── load/
│   ├── lambda_handlers/    # Handlers compatíveis com AWS Lambda
│   ├── models/             # Modelos ORM
│   ├── schemas/            # Schemas Pydantic
│   ├── services/           # Regras de aplicação e integração
│   └── utils/              # Utilitários auxiliares
├── alembic/                # Migrações versionadas do banco
├── data/
│   ├── processed/          # Saídas processadas do ETL
│   ├── raw/                # Arquivos brutos recebidos/localizados
│   ├── real_inputs/        # Arquivos reais de entrada, como XP
│   └── samples/            # Arquivos de exemplo para teste
├── docs/                   # Guias auxiliares, incluindo Metabase
├── frontend/               # Workspace web em React
├── scripts/                # Scripts operacionais e utilitários
├── sql/                    # Views analíticas e queries de dashboard
├── tests/                  # Testes automatizados
├── .env.example            # Variáveis de ambiente
├── requirements.txt        # Dependências backend
└── README.md               # Documentação principal
```

## ⚙️ Como Rodar Localmente

### 1. Pré-requisitos

- Python 3.13
- Node.js 20+ ou compatível
- PostgreSQL local
- Docker Desktop (opcional, para PostgreSQL e Metabase)

### 2. Banco de Dados

O projeto foi preparado para desenvolvimento local com PostgreSQL.

Exemplo de banco local:

- Host: `localhost`
- Porta: `5432`
- Database: `etl_db`
- Usuário: `postgres`
- Senha: `postgres`

### 3. Variáveis de Ambiente

Crie o `.env` a partir do arquivo `.env.example`:

```powershell
Copy-Item .env.example .env
```

Conteúdo base:

```env
PROJECT_NAME=CarteiraConsol
APP_ENV=development
APP_VERSION=0.1.0
LOG_LEVEL=INFO
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/etl_db
AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=carteiraconsol-vi-001
S3_BUCKET_PREFIX=incoming/
DEFAULT_RISK_PROFILE=moderado
RAW_STORAGE_MODE=local
AUTO_CREATE_TABLES=true
API_PREFIX=
JWT_SECRET_KEY=change-me-before-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
ALERTS_ENABLED=false
ALERT_PROVIDER=noop
ALERT_SNS_TOPIC_ARN=
```

`AUTO_CREATE_TABLES` existe como conveniência para desenvolvimento local. Em ambientes compartilhados ou de produção, prefira deixá-lo como `false` e aplicar mudanças de schema via migrações explícitas e revisadas.

O repositório agora inclui uma baseline Alembic para versionar o schema com segurança. Em produção, a evolução da base não deve depender de `create_all()`: use migrações revisadas e aplique-as com `alembic upgrade head`.

### 4. Instalar Dependências do Backend

```powershell
cd C:\Users\vitor\OneDrive\Documentos\Playground
python -m pip install -r requirements.txt
```

### 5. Inicializar o Banco

```powershell
python scripts/init_db.py
```

Se o banco `etl_db` ainda não existir:

```powershell
python scripts/ensure_postgres_db.py
python scripts/init_db.py
```

Se voce ja vinha usando a base local antes do Alembic e ela foi criada por `AUTO_CREATE_TABLES`, faca um alinhamento unico do historico antes de aplicar novas migrations:

```powershell
alembic stamp head
```

### 5.1. Aplicar migrações com Alembic

Para aplicar a baseline atual e futuras mudanças de schema:

```powershell
alembic upgrade head
```

Para criar uma nova revisão a partir dos modelos atuais:

```powershell
alembic revision --autogenerate -m "describe schema change"
```

Para consultar o estado das migrações:

```powershell
alembic current
alembic history
```

Uso recomendado:

- desenvolvimento local rápido: `AUTO_CREATE_TABLES=true` continua disponível
- ambientes compartilhados ou produção: `AUTO_CREATE_TABLES=false` e `alembic upgrade head`

### 6. Rodar o Backend

```powershell
uvicorn app.main:app --reload
```

Backend disponível em:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### 6.1. Criar o primeiro admin

Antes de usar o frontend autenticado, crie um usuario administrador local:

```powershell
python scripts/create_admin.py --email seu@email.com --full-name "Seu Nome"
```

Se preferir, omita `--password` para informar a senha de forma interativa.

### 7. Instalar e Rodar o Frontend

```powershell
cd C:\Users\vitor\OneDrive\Documentos\Playground\frontend
npm install
npm run dev
```

Frontend disponível em:

```text
http://127.0.0.1:5173
```

### 8. Rodar PostgreSQL e Metabase com Docker (opcional)

Se você usa containers locais:

```powershell
docker start carteiraconsol-postgres
docker start metabase-carteiraconsol
```

Metabase:

```text
http://localhost:3001
```

### 9. Rodar o stack local cloud-like com Docker Compose

O repositório inclui uma stack local para validar um fluxo próximo do alvo em nuvem:

- FastAPI em container
- PostgreSQL em container
- MinIO como storage S3-compatible
- bootstrap automático do bucket

Arquivos principais:

- `Dockerfile`
- `docker-compose.yml`
- `.env.docker`

Subir a stack:

```powershell
docker compose --env-file .env.docker up --build -d
```

Ver serviços:

```powershell
docker compose --env-file .env.docker ps
docker compose --env-file .env.docker logs backend
docker compose --env-file .env.docker logs minio_setup
```

Parar e remover volumes:

```powershell
docker compose --env-file .env.docker down -v
```

Endpoints úteis:

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- MinIO API: `http://127.0.0.1:9000`
- MinIO Console: `http://127.0.0.1:9001`

Nesse modo, use `RAW_STORAGE_MODE=s3` com `AWS_ENDPOINT_URL=http://minio:9000` e `AWS_S3_FORCE_PATH_STYLE=true`, como já configurado em `.env.docker`.

O `.env.docker` usa `PORT=8000` para expor a API localmente na mesma porta do ambiente padrão.

Fluxo validado localmente com essa stack:

- upload via `POST /upload` no host
- arquivo bruto persistido no bucket MinIO
- ETL persistindo clientes, contas, ativos e posições no PostgreSQL
- endpoints `/clients`, `/assets` e `/positions` respondendo com os dados processados

## 🔌 Uso da API

### Endpoints Principais

#### Health Check

```http
GET /health
```

#### Autenticacao

```http
POST /auth/login
GET /auth/me
```

#### Upload e Processamento

```http
POST /upload
POST /etl/run
POST /etl/run-from-s3
```

#### Consulta de Entidades

```http
GET /clients
GET /accounts
GET /assets
GET /positions
GET /ingestion-reports
GET /ingestion-reports/{id}
PATCH /ingestion-reports/{id}/review
GET /reports/portfolio/pdf
```

### Filtros e Paginação

Os endpoints de listagem já suportam paginação simples com parâmetros como:

- `limit`
- `offset`

E filtros por recurso, como por exemplo:

- cliente
- corretora
- classe de ativo
- data de referência

## 📤 Fluxo de Upload

O upload já está integrado ponta a ponta entre frontend e backend.

### Fluxo Atual

1. Usuário seleciona um arquivo no workspace React
2. O frontend envia o arquivo para `POST /upload`
3. O backend salva o arquivo em diretório temporário seguro
4. O ETL é executado usando o pipeline real
5. Os dados são normalizados, enriquecidos e persistidos
6. O backend retorna um resumo estruturado
7. O frontend recarrega o snapshot consolidado da API
8. A UI mostra:
   - estado de processamento
   - resumo do último processamento
   - histórico curto dos uploads recentes

### Exemplo de Request

```powershell
curl.exe -X POST "http://127.0.0.1:8000/upload" -F "file=@C:\Users\vitor\OneDrive\Documentos\Playground\data\samples\sample_portfolio.csv"
```

### Exemplo de Resposta

```json
{
  "status": "success",
  "data": {
    "filename": "sample_portfolio.csv",
    "detected_type": "csv",
    "rows_processed": 6,
    "rows_skipped": 0,
    "message": "Arquivo sample_portfolio.csv processado com sucesso.",
    "processed_at": "2026-03-18T19:30:00.000000+00:00",
    "raw_file": "C:\\...\\data\\raw\\20260318193000_sample_portfolio.csv",
    "processed_file": "C:\\...\\data\\processed\\normalized_positions_20260318193000.csv"
  }
}
```

## 📄 Relatório PDF Executivo

O backend agora gera um PDF executivo real a partir dos dados consolidados já persistidos na plataforma.

Escolha técnica desta primeira versão:

- geração server-side com `reportlab`

Motivo:

- mantém a implantação em ECS e ambientes locais mais simples do que depender de runtimes gráficos nativos
- produz um PDF real no backend, sem depender de export do navegador
- atende bem a primeira versão de um relatório premium com layout, métricas, tabelas e hierarquia visual

Endpoint:

```http
GET /reports/portfolio/pdf
```

Filtros opcionais:

- `client_name`
- `asset_class`
- `reference_date`

Exemplo:

```powershell
curl.exe -L "http://127.0.0.1:8000/reports/portfolio/pdf?reference_date=2026-03-17" ^
  -H "Authorization: Bearer SEU_TOKEN" ^
  --output carteira_executive_report.pdf
```

Conteúdo da versão atual:

- header executivo
- data de geração
- valor total consolidado
- total de clientes
- total de ativos
- total de contas
- alocação por classe de ativo
- top ativos por valor
- evolução por data de referência
- tabela das principais posições
- nota operacional quando existirem ingestões pendentes de revisão

## 🔄 ETL: Visão de Alto Nível

O pipeline segue a ordem:

```text
extract → transform → enrich → load
```

### 1. Extract

Leitura de:

- CSV
- XLSX / XLS
- JSON
- diretórios com arquivos reais da XP
- arquivos locais em `data/raw`, `data/samples` e `data/real_inputs`
- objetos no S3

### 2. Transform

Regras principais:

- normalização de colunas
- parsing numérico com formatos brasileiros e internacionais
- parsing robusto de datas
- limpeza de valores vazios
- tratamento de alias de corretoras e campos
- classificação de ativos

### 3. Enrich

Enriquecimento simples com metadados simulados, como:

- CNPJ
- vencimento
- nome normalizado

### 4. Load

Persistência nas tabelas de domínio:

- `clients`
- `accounts`
- `assets_master`
- `positions_history`

## 🗃️ Banco de Dados

### Tabelas Principais

#### `clients`

Armazena o investidor consolidado:

- `id`
- `name`
- `risk_profile`

#### `accounts`

Representa a conta/custódia por corretora:

- `id`
- `client_id`
- `broker`

#### `assets_master`

Catálogo consolidado de ativos:

- `id`
- `ticker`
- `original_name`
- `normalized_name`
- `asset_class`
- `cnpj`
- `maturity_date`

#### `positions_history`

Snapshot histórico por ativo/conta/data:

- `id`
- `account_id`
- `asset_id`
- `quantity`
- `avg_price`
- `total_value`
- `reference_date`

### Views Analíticas

As views em [analytics_views.sql](C:/Users/vitor/OneDrive/Documentos/Playground/carteiraconsol/sql/analytics_views.sql) já estão prontas para consumo por BI:

- `analytics_position_facts`
- `analytics_allocation_by_asset_class`
- `analytics_positions_by_broker`
- `analytics_positions_by_client`
- `analytics_portfolio_totals_by_reference_date`

Essas views suportam análises como:

- alocação por classe
- exposição por corretora
- exposição por cliente
- total consolidado por data de referência

## 🖥️ Frontend: Conceito de Workspace

O frontend não é apenas uma tela de upload. Ele foi desenhado como um workspace executivo de análise de portfólio.

### Conceitos da Interface

- sidebar escura com ações e contexto do cliente
- canvas claro com preview de relatório
- linguagem visual fintech/consultoria
- resumo do último processamento
- histórico curto de uploads
- leitura visual com KPIs, alocação, exposição e timeline

### Componentes Principais

- [App.tsx](C:/Users/vitor/OneDrive/Documentos/Playground/carteiraconsol/frontend/src/App.tsx)
- [Sidebar.tsx](C:/Users/vitor/OneDrive/Documentos/Playground/carteiraconsol/frontend/src/components/Sidebar.tsx)
- [ReportCanvas.tsx](C:/Users/vitor/OneDrive/Documentos/Playground/carteiraconsol/frontend/src/components/ReportCanvas.tsx)

### O que o usuário vê

- seleção de arquivo
- estados explícitos de upload:
  - `idle`
  - `uploading`
  - `processing`
  - `success`
  - `error`
- resumo da última execução
- histórico recente de uploads
- preview executivo dos dados consolidados

## 📊 BI / Metabase

O projeto já inclui a base necessária para dashboards locais com Metabase.

### Arquivos Relacionados

- [analytics_views.sql](C:/Users/vitor/OneDrive/Documentos/Playground/carteiraconsol/sql/analytics_views.sql)
- [metabase_dashboard_queries.sql](C:/Users/vitor/OneDrive/Documentos/Playground/carteiraconsol/sql/metabase_dashboard_queries.sql)
- [metabase_dashboard_guide.md](C:/Users/vitor/OneDrive/Documentos/Playground/carteiraconsol/docs/metabase_dashboard_guide.md)

### Como aplicar as views

```powershell
python scripts/create_analytics_views.py
```

### Como rodar o Metabase localmente

```powershell
docker run -d --name metabase-carteiraconsol -p 3001:3000 metabase/metabase:latest
```

Abra:

```text
http://localhost:3001
```

### Conexão sugerida no Metabase

- Host: `host.docker.internal`
- Port: `5432`
- Database: `etl_db`
- Username: `postgres`
- Password: `postgres`

## ☁️ S3 e Lambda

O projeto já está preparado para evolução cloud-native.

Para a trilha de implantação em AWS, consulte também [aws-deployment.md](C:/Users/vitor/OneDrive/Documentos/Playground/docs/aws-deployment.md), [.env.aws.example](C:/Users/vitor/OneDrive/Documentos/Playground/.env.aws.example), [template.yaml](C:/Users/vitor/OneDrive/Documentos/Playground/template.yaml) e [ecs-task-definition.sample.json](C:/Users/vitor/OneDrive/Documentos/Playground/deploy/ecs-task-definition.sample.json).

### S3

Suporte implementado para:

- upload de arquivos para bucket
- listagem por prefixo
- download local antes do processamento
- ETL acionado a partir do S3

Script auxiliar:

```powershell
python scripts/upload_to_s3.py --file "C:\...\sample_portfolio.csv" --key "incoming/sample_portfolio.csv"
```

### Lambda

Existe compatibilidade com execução serverless em:

- [etl_handler.py](C:/Users/vitor/OneDrive/Documentos/Playground/carteiraconsol/app/lambda_handlers/etl_handler.py)
- [api_handler.py](C:/Users/vitor/OneDrive/Documentos/Playground/carteiraconsol/app/lambda_handlers/api_handler.py)

O handler ETL aceita:

- payload direto com `s3_key`
- payload com `source_path`
- evento S3 com `Records[]`
- evento SQS contendo um evento S3 no `body`

Fluxo cloud-ready suportado:

```text
S3 object created
    ↓
AWS Lambda event (ou SQS contendo o evento S3)
    ↓
app.lambda_handlers.etl_handler.handler(...)
    ↓
ETLService.run_from_lambda_invocation(...)
    ↓
PortfolioETLPipeline
    ↓
PostgreSQL + ingestion_reports
```

Observabilidade mantida no fluxo Lambda:

- `source_type` indica `lambda_s3` quando a execução parte de um evento
- `source_file` e `raw_file` preservam a URI `s3://bucket/key` quando disponível
- `ingestion_reports` continuam registrando:
  - status
  - parser
  - review metadata
  - confidence
  - linhas processadas/puladas

Script local de simulação:

```powershell
python scripts/invoke_lambda_etl.py --s3-key "incoming/sample_portfolio.csv"
```

Simulando um evento S3 direto:

```powershell
python scripts/invoke_lambda_etl.py --s3-event-key "incoming/sample_portfolio.csv"
```

Simulando um evento SQS contendo um evento S3:

```powershell
python scripts/invoke_lambda_etl.py --sqs-event-key "incoming/sample_portfolio.csv"
```

Também é possível usar fixtures locais:

```powershell
python scripts/invoke_lambda_etl.py --payload-file "tests/fixtures/lambda_s3_event.json"
python scripts/invoke_lambda_etl.py --payload-file "tests/fixtures/lambda_sqs_s3_event.json"
```

### Alertas operacionais

O backend agora pode emitir alertas operacionais quando uma ingestão exige atenção humana.

Casos cobertos nesta primeira camada:

- falha técnica de ingestão
- ingestão concluída com `review_required=true`

Estratégia inicial:

- local/dev: `ALERTS_ENABLED=false` ou `ALERT_PROVIDER=noop`
- ambientes compartilhados: `ALERT_PROVIDER=log` para visibilidade imediata
- AWS/produção: `ALERT_PROVIDER=sns` com `ALERT_SNS_TOPIC_ARN`

Campos principais enviados no payload do alerta:

- `ingestion_report_id`
- `filename`
- `source_type`
- `status`
- `review_status`
- `review_reasons`
- `detection_confidence`
- `raw_file`
- `processed_at`

Falhas de envio de alerta não interrompem o ETL. O pipeline continua concluindo ou falhando de acordo com a regra original, enquanto o backend registra o problema de notificação em log.

O que ainda fica para a próxima etapa de AWS real:

- infraestrutura IaC (Terraform/CDK)
- permissões IAM e policies do bucket
- fila SQS real para retries e desacoplamento
- DLQ e observabilidade operacional em CloudWatch

## 📥 Suporte a Inputs Reais da XP

O projeto já contém suporte dedicado para arquivos reais da XP em `data/real_inputs`.

Parsers específicos:

- `xp_position_parser.py`
- `xp_movements_parser.py`
- `xp_json_parser.py`
- `xp_bundle_parser.py`

O bundle parser é capaz de:

- detectar arquivos de posição inicial
- detectar arquivos de movimentação
- detectar JSONs de posição
- priorizar snapshots sobre movimentos quando ambos existem

Execução:

```powershell
python scripts/run_etl.py --real-inputs
```

## 🔁 Fluxo End-to-End

```text
Planilha / JSON / S3 / XP real input
    ↓
Upload ou script operacional
    ↓
FastAPI / ETLService / PortfolioETLPipeline
    ↓
Normalização + enriquecimento + carga
    ↓
PostgreSQL
    ↓
Views analíticas
    ↓
API + Frontend + Metabase
```

### Passo a Passo

1. Um arquivo é disponibilizado localmente, via frontend ou via S3
2. O backend identifica o tipo e o parser aplicável
3. O ETL executa o fluxo de extração, transformação, enriquecimento e carga
4. A base PostgreSQL recebe o snapshot consolidado
5. As views analíticas ficam disponíveis para BI
6. O frontend recarrega o snapshot e monta o preview executivo
7. O Metabase pode consumir as views para dashboards

## 🧪 Exemplos de Uso

### Rodar ETL com arquivo sample

```powershell
python scripts/run_etl.py --sample
```

### Rodar ETL com inputs reais da XP

```powershell
python scripts/run_etl.py --real-inputs
```

### Rodar ETL a partir do S3

```powershell
python scripts/run_etl.py --source s3 --s3-key "incoming/sample_portfolio.csv"
```

### Verificar contagem de dados no banco

```powershell
python scripts/check_db.py
```

### Validar acesso ao S3

```powershell
python scripts/verify_s3_access.py
```

### Rodar testes

```powershell
python -m pytest
```

## 🔁 CI / GitHub Actions

O repositório inclui uma baseline de CI em [.github/workflows/ci.yml](C:/Users/vitor/OneDrive/Documentos/Playground/.github/workflows/ci.yml), executada em `push` e `pull_request`.

Ela valida:

- backend:
  - instalação via `requirements.txt`
  - execução de `python -m pytest`
- frontend:
  - instalação via `npm ci` em `frontend/`
  - build via `npm run build`

Essa baseline não depende de secrets e foi pensada para verificação pública e reprodutível do projeto.

## 🗺️ Roadmap / Melhorias Futuras

- persistência de histórico de uploads em banco
- autenticação e autorização por usuário/cliente
- filas e processamento assíncrono de ETL
- observabilidade com tracing e métricas operacionais
- exportação de PDF server-side
- background jobs para reconciliação incremental
- suporte a mais instituições além de XP
- materialized views para grandes volumes históricos
- multi-tenant / row-level security para uso compartilhado

## 👤 Autor

Desenvolvido por **Vitória** como projeto de engenharia de dados, backend, analytics e product delivery para consolidação e análise de carteiras de investimento.
