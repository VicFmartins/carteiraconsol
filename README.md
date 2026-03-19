# CarteiraConsol

CarteiraConsol is a production-minded portfolio consolidation and analysis platform built to ingest imperfect real-world investment files, normalize them into a consistent portfolio model, and expose both operational and executive layers on top of the processed data. It combines a FastAPI backend, a React workspace, a smart ETL pipeline, review-driven ingestion controls, PDF reporting, and AWS-ready deployment patterns into a system designed for real financial operations rather than toy datasets.

## Key Features

- Smart CSV/XLSX ingestion with schema detection and file-structure recovery
- Fuzzy column mapping with Portuguese and English aliases
- Soft validation and fallback behavior, including broker inference and configurable defaults
- Durable ingestion audit trail with persisted ingestion reports
- Review Queue for low-confidence or operator-attention runs
- Approve & Reprocess workflow that updates the same ingestion report in place
- Executive dashboard with live portfolio KPIs, allocation views, and positions table
- Executive PDF report generation using server-side ReportLab
- JWT authentication with protected API routes and hashed passwords
- Operational alerting foundation with SNS-ready provider support
- S3 to Lambda to ETL ingestion foundation with SQS-ready event parsing
- Docker Compose local stack with PostgreSQL and MinIO
- GitHub Actions CI for backend tests and frontend build
- AWS deployment baseline validated with a real temporary ECS Fargate + S3 test

## System Architecture

### Backend

The backend is built around FastAPI and a service-oriented application layer. HTTP routes stay thin and delegate work to services responsible for ETL orchestration, report persistence, authentication, alerting, storage, and reporting.

Core backend responsibilities:

- authentication and protected API access
- upload intake and ETL orchestration
- ingestion report lifecycle tracking
- portfolio query endpoints for dashboard and report consumers
- executive PDF generation
- S3/Lambda-compatible ingestion entrypoints

### ETL Pipeline

The ETL flow follows a clear pipeline:

```text
extract -> normalize -> transform -> enrich -> persist
```

Key properties of the pipeline:

- accepts local uploads and S3-backed ingestion
- supports generic CSV/XLSX plus broker-specific parsing paths
- normalizes noisy real-world tabular data into a consistent portfolio model
- produces ingestion metadata that feeds the review system and audit trail

### Frontend

The frontend is a React + Vite workspace with three operational modes:

- `Report Builder`
- `Review Queue`
- `Dashboard`

The product is intentionally split into:

- an operational layer for ingestion, triage, and correction
- an executive layer for portfolio visibility and PDF output

### Data Layer

The primary relational data store is PostgreSQL, managed with Alembic migrations.

Core persistence areas:

- portfolio domain tables
- `ingestion_reports`
- `accepted_column_mappings`
- user/auth data

For a temporary AWS validation run, the backend was also tested with SQLite in an ephemeral ECS task to minimize cost while still exercising the real application runtime.

## ETL Pipeline Deep Dive

The ETL pipeline was built around the reality that investment data is rarely clean.

### Schema Detection

The smart ingestion layer inspects incoming CSV and XLSX files to infer:

- delimiter
- header row
- relevant worksheet for Excel files
- noisy or ignorable preamble rows

This allows the system to handle files where headers are not on the first row or where the exported structure is inconsistent across institutions.

### Alias Resolution and Fuzzy Mapping

Canonical portfolio fields such as client, broker, ticker, quantity, average price, total value, and reference date are mapped from messy source columns using:

- explicit aliases
- normalized label comparison
- RapidFuzz-based fuzzy matching

This supports Portuguese and English variants as well as broker-specific naming differences.

### Fallback Logic

A strict financial schema is still important, but hard-failing too early creates false operational errors. The pipeline therefore supports smart fallback behavior.

Example:

- if `broker` is missing, the system can infer it from:
  - `custodian`
  - `institution`
  - `corretora`
  - `advisorcode`
  - source filename hints such as `XP` or `BTG`
- if broker still cannot be inferred, it can fall back to `UNKNOWN` when soft validation mode is enabled

### Soft Validation Mode

The pipeline distinguishes between:

- unrecoverable technical/data failures
- recoverable but low-confidence ingestions

If the data is usable but confidence is not high enough, the run is not blocked. Instead, it continues with:

- `review_required = true`
- structured review reasons
- ingestion report persistence for operator follow-up

### Ingestion Report Lifecycle

Every real ingestion run creates or updates an ingestion report that records:

- filename
- detected type
- parser name
- raw file reference
- processed file reference
- detected columns
- applied mappings
- confidence level
- review status and reasons
- rows processed and skipped
- timestamps
- reprocessing metadata

This makes the ETL flow auditable and supports the review loop without coupling the entire product to manual approval.

## Review System

The review system is the control layer that prevents low-confidence ingestion from being treated as either a silent success or a hard technical failure.

### Status Semantics

CarteiraConsol distinguishes clearly between:

- `success`
  - data processed successfully with no additional human action required
- `review_required`
  - data processed successfully enough to persist, but requires operator review
- `technical error`
  - the file could not be processed safely and the run failed

This distinction matters operationally because review-worthy files should remain actionable, while technical failures should remain clearly visible as failures.

### Review Queue

The Review Queue surfaces ingestion reports requiring attention. Operators can inspect:

- file metadata
- detected structure
- column mappings
- confidence score
- review reasons
- parser used
- processing outcomes

### Approve & Reprocess

The review workflow supports:

1. approving a report
2. reprocessing the original source
3. updating the same ingestion report in place
4. incrementing reprocessing metadata for auditability

This closes the operational learning loop while preserving traceability.

### Accepted Mapping Learning

Approved mappings are persisted in `accepted_column_mappings` so future ingestions can reuse known layouts before falling back to fuzzy matching. This creates incremental operational learning without introducing a full ML subsystem.

## Dashboard and Reporting

The executive layer turns processed holdings into something presentable to clients, leadership, and analysts.

### Dashboard

The live dashboard is powered by backend portfolio APIs and shows:

- total portfolio value
- total clients
- total assets
- total accounts
- allocation by asset class
- allocation by client
- top assets by total value
- portfolio evolution over time
- top positions table

The UI was intentionally polished to feel like a premium fintech interface rather than an internal admin screen.

### Executive PDF

CarteiraConsol includes server-side PDF generation for client-facing portfolio reports.

The first version includes:

- executive header and generation timestamp
- core KPI summary
- asset-class allocation
- top assets by value
- portfolio evolution
- top positions table
- operational notes when relevant

This is generated from live processed data rather than exporting a browser view.

## Authentication and Security

The platform includes a first secure authentication layer designed for non-local use.

Security choices:

- JWT authentication for API access
- password hashing via Passlib with bcrypt
- protected business routes
- public health check and login endpoints only
- frontend session restoration via `/auth/me`
- automatic bearer token inclusion in API requests
- logout and broken-session cleanup in the frontend

Protected capabilities include:

- upload
- ingestion reports
- portfolio data endpoints
- dashboard data access
- PDF generation

## Alerts System

The alerting layer was implemented as an operational concern, not embedded into ETL core logic.

### What Triggers Alerts

Current alert triggers:

- technical ingestion failures
- ingestions that complete with `review_required = true`

### Design Principles

- alerting is non-blocking
- ETL success or failure is never determined by alert delivery
- providers are configurable
- SNS-ready path exists for AWS deployment
- local development works with alerts disabled

This keeps the system reliable while making it operations-friendly.

## AWS Architecture and Validation

CarteiraConsol was designed to support a real cloud ingestion model while keeping the authenticated product runtime separate from event-driven processing.

### Recommended Architecture

```text
Frontend (static hosting)
    ->
FastAPI backend (ECS Fargate)
    ->
PostgreSQL (RDS in production)

Raw files
    ->
S3
    ->
SQS
    ->
Lambda ingestion handler
    ->
ETL pipeline
    ->
PostgreSQL + ingestion reports
```

### Why This Shape Was Chosen

- Lambda is a good fit for event-driven ingestion
- SQS provides buffering, retry control, and future DLQ support
- FastAPI remains a better fit for authenticated APIs, uploads, dashboard access, and PDF/report endpoints
- the API runtime is therefore kept separate from Lambda-based ingestion

### Real AWS Validation

The repository was validated with a real temporary AWS deployment.

Used for the verification run:

- ECS Fargate for the FastAPI backend
- S3 for raw file storage
- IAM roles for ECS execution and S3 access
- CloudWatch logs for runtime visibility

Cost-minimizing choice for the test:

- SQLite was used inside the temporary ECS task instead of provisioning RDS, because the goal was a short-lived runtime verification rather than a full durable production rollout

What was validated successfully:

- backend reachability
- auth login
- protected API access
- upload processing
- S3 raw file persistence
- portfolio data retrieval
- PDF generation

Important:

- this was a real deployment test, not only a design exercise
- the environment was destroyed after validation to avoid ongoing cost

For the AWS deployment baseline and artifacts, see:

- [docs/aws-deployment.md](C:/Users/vitor/OneDrive/Documentos/Playground/docs/aws-deployment.md)
- [template.yaml](C:/Users/vitor/OneDrive/Documentos/Playground/template.yaml)
- [deploy/ecs-task-definition.sample.json](C:/Users/vitor/OneDrive/Documentos/Playground/deploy/ecs-task-definition.sample.json)
- [.env.aws.example](C:/Users/vitor/OneDrive/Documentos/Playground/.env.aws.example)

## Local Development

### Prerequisites

- Python 3.13
- Node.js 20+
- Docker Desktop

### Backend Environment

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Install backend dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run migrations:

```powershell
alembic upgrade head
```

Create the first admin:

```powershell
python scripts/create_admin.py --email admin@carteira.local --full-name "Admin Local"
```

Run the backend:

```powershell
uvicorn app.main:app --reload
```

### Docker Compose Stack

The repository also includes a cloud-like local stack with PostgreSQL and MinIO:

```powershell
docker compose --env-file .env.docker up --build -d
docker compose --env-file .env.docker ps
```

This stack validates:

- FastAPI in containers
- PostgreSQL connectivity
- S3-compatible raw storage through MinIO
- bucket bootstrap
- upload and ETL behavior in a containerized environment

To stop and remove volumes:

```powershell
docker compose --env-file .env.docker down -v
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs at:

- `http://127.0.0.1:5173`

## Testing

The project includes a broad automated test surface.

Coverage areas include:

- ETL normalization and schema recovery
- smart ingestion and fuzzy mapping
- API behavior
- auth flows
- ingestion reports and review logic
- PDF generation endpoint
- Lambda event parsing and invocation path
- alerting behavior

Run the backend suite:

```powershell
python -m pytest
```

Run the frontend production build:

```powershell
cd frontend
npm run build
```

CI is configured in GitHub Actions to run backend tests and frontend build on push and pull request.

## Key Technical Decisions

### ReportLab Instead of HTML-to-PDF

The first PDF version uses ReportLab instead of a browser-style HTML renderer because:

- it avoids OS-level rendering dependencies
- it is easier to run consistently in Docker and ECS
- it keeps the server-side reporting path predictable for an infrastructure-light deployment

### Soft Validation Instead of Pure Hard Validation

Real investment files are often incomplete but still usable. Soft validation reduces false failures, preserves useful data, and routes ambiguous runs into a controlled review workflow instead of blocking the product entirely.

### Review Queue Instead of Blocking Ingestion

A review queue creates operational leverage. It allows the system to keep moving while preserving visibility into uncertainty. That is a better fit for real data operations than forcing all ambiguity to become a fatal error.

### SQLite for the Temporary AWS Test

The real AWS validation prioritized proof of runtime correctness while minimizing spend. SQLite inside an ephemeral ECS task was sufficient to validate:

- auth
- migrations
- upload
- ETL
- S3 raw storage
- protected API behavior
- PDF generation

without leaving an RDS instance running.

### Separation of ETL and Event Parsing

Lambda event parsing is kept separate from ETL execution so the ingestion service can support:

- direct API uploads
- direct S3 processing
- Lambda-triggered S3 events
- SQS-wrapped S3 events

This keeps the ingestion architecture adaptable without duplicating ETL logic.

## Lessons Learned and Engineering Insights

- Real-world financial ingestion is mostly a data-quality problem, not a file-upload problem.
- Overly strict validation creates false failures and destroys trust; soft validation with explicit review semantics is a better operational design.
- State consistency matters as much as raw processing correctness. The product only feels reliable when backend outcomes, persisted reports, API responses, and frontend UI states all align.
- Operational review states and technical error states must remain separate. Treating them as the same causes confusion, bad UX, and wrong operator actions.
- Frontend resilience matters in data products. Partial payloads, delayed snapshot refreshes, and non-fatal ETL outcomes must not blank the UI.
- Local and cloud parity should be designed intentionally. Docker + MinIO provided a useful bridge before validating a real AWS deployment.
- Deployment readiness is not only code readiness. It also includes secrets strategy, startup order, migrations, bootstrap flows, observability, and teardown discipline.

## Future Improvements

- Full production AWS IaC with CDK or a more complete SAM stack
- RDS PostgreSQL as the standard production backing store
- Full activation of the S3 to SQS to Lambda ingestion path in deployed environments
- DLQ strategy and richer operational observability
- Additional alert channels such as WhatsApp or Slack
- Richer human review tooling with field-level correction UX
- Multi-tenant support with stronger authorization boundaries
- Deeper broker-specific parsing coverage
- Historical portfolio analytics optimization for larger datasets

## Repository Highlights

- Backend API and ETL: [app](C:/Users/vitor/OneDrive/Documentos/Playground/app)
- Frontend workspace: [frontend](C:/Users/vitor/OneDrive/Documentos/Playground/frontend)
- Database migrations: [alembic](C:/Users/vitor/OneDrive/Documentos/Playground/alembic)
- AWS deployment guide: [docs/aws-deployment.md](C:/Users/vitor/OneDrive/Documentos/Playground/docs/aws-deployment.md)
- AWS ingestion baseline: [template.yaml](C:/Users/vitor/OneDrive/Documentos/Playground/template.yaml)
- ECS deployment sample: [deploy/ecs-task-definition.sample.json](C:/Users/vitor/OneDrive/Documentos/Playground/deploy/ecs-task-definition.sample.json)

## Author

Built by Vitória Martins as a product-grade engineering portfolio project focused on backend architecture, ETL reliability, operational workflow design, and executive data delivery.
