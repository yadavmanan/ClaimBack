# ClaimBack Backend

The backend powers the ClaimBack agentic workflow: it ingests documents, normalizes claim data, matches them to policies and coverage, drafts reimbursement actions, and exposes the API consumed by the frontend.

## What this service does

- Accepts uploaded or raw documents from the web app
- Stores document metadata and claim state in a repository backend
- Detects opportunity types such as warranty claims, policy reimbursements, duplicate charges, and bill price hikes
- Normalizes incoming text into structured claim facts
- Builds evidence plans and action drafts for human approval
- Supports submission workflows for approved claims
- Exposes a FastAPI REST API for the frontend

## Tech stack

- Python 3.11+
- FastAPI
- Pydantic + Pydantic Settings
- boto3 for AWS services
- Strands agents + OpenAI-compatible model access
- DynamoDB single-table repository by default
- S3 storage and optional AWS OCR / SES integration

## Project structure

- `main.py` – FastAPI application and route definitions
- `config.py` – environment-driven settings
- `runtime.py` – repository bootstrap and tool wiring
- `aws_clients.py` – shared AWS session/client helpers
- `agents/` – document extraction, claim matching, and drafting logic
- `database/` – models and repository implementations
- `services/` – normalization, evidence, notification, OCR, and tracking logic
- `workflow/` – ingestion, approval, follow-up, and submission flows
- `tools/` – repository-backed tools used by the agent workflow
- `tests/` – lifecycle and parsing regression tests

## Local setup

1. Open a terminal in the repository root.
2. Create and activate a Python environment.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Copy the environment template and fill in your values.

```bash
cp .env.example .env
```

5. Review the required settings in `.env`.

At minimum, the app expects values for:

- `AWS_REGION`
- `AWS_PROFILE` or explicit AWS credentials
- `DYNAMODB_TABLE_NAME`
- `CLAIMBACK_RAW_DOCUMENTS_BUCKET`
- `CLAIMBACK_GENERATED_ARTIFACTS_BUCKET`
- model settings such as `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL_ID`, or `BEDROCK_MODEL_ID`

## Running the API

From the repository root:

```bash
cd backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Then verify health status:

```bash
curl http://localhost:8000/health
```

## Repository backends

By default, the app is set up to use a DynamoDB-backed single-table repository. If you are just exploring the project locally, the repository implementation can also run in-memory mode depending on the configuration.

## AWS integration notes

- `AWS_PROFILE` is recommended for local dev instead of hardcoding credentials
- Set `CLAIMBACK_RAW_DOCUMENTS_BUCKET` before uploading documents through the API
- `DYNAMODB_ENDPOINT_URL` may be used for local emulators or testing
- SES and Textract values are optional for the basic local lifecycle tests

## Testing

```bash
cd backend
python -m unittest backend.tests.test_backend_lifecycle
```

This suite exercises the document lifecycle, policy matching, and parsing behavior.

## Public release checklist

- Keep `.env` out of version control
- Never commit real credentials or production AWS account identifiers
- Use placeholders in sample configuration files
- Add public-facing documentation for setup, architecture, and environment variables

## API overview

Main endpoints include:

- `GET /health`
- `POST /api/documents/ingest`
- `POST /api/users/{user_id}/documents/upload`
- `GET /api/users/{user_id}/documents`
- `GET /api/users/{user_id}/opportunities`
- `GET /api/users/{user_id}/activity`
- `GET /api/opportunities/{opportunity_id}`

See the app routes in `backend/main.py` for the full request contract.
