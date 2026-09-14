# ClaimBack

ClaimBack is an AI-assisted claims and reimbursement workspace that helps users ingest bills, receipts, policies, and coverage documents, then discover claim opportunities across subscriptions, warranties, and office reimbursements.

The project combines a Python/FastAPI backend with a React + Vite frontend to create a working demo for agentic document processing and claim workflows.

## Product concept

The application is designed around a simple but powerful idea:

- A user uploads documents or raw text
- The backend normalizes them into structured claim facts
- Matching logic looks for opportunities based on policy, ledger, and coverage data
- The system builds evidence plans and draft actions for review
- A human approves or dismisses claims before submission

This keeps the experience practical: document ingestion and AI reasoning are paired with a clear approval workflow rather than an opaque “black box” automation flow.

## Architecture

```text
frontend (React + Vite)
    |
    v
FastAPI backend
    |
    +--> Document ingestion and normalization
    +--> Policy and opportunity matching
    +--> Evidence / draft generation
    +--> AWS integrations (S3, DynamoDB, SES, optional OCR)
    +--> Repository-backed workflow state
```

## Stack

### Frontend

- React 19
- TypeScript
- Vite
- React Router
- Tailwind CSS
- Framer Motion
- Radix UI primitives

### Backend

- Python 3.11+
- FastAPI
- Pydantic
- AWS SDK for Python (boto3)
- Strands Agents
- OpenAI-compatible model access or native Bedrock routing
- DynamoDB single-table storage by default

## Repository layout

```text
claim_github/
├── backend/
│   ├── agents/
│   ├── database/
│   ├── prompts/
│   ├── services/
│   ├── tests/
│   ├── tools/
│   ├── workflow/
│   ├── .env.example
│   ├── Dockerfile
│   ├── config.py
│   ├── main.py
│   ├── pyproject.toml
│   ├── README.md
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   ├── .env.example
│   ├── package.json
│   ├── README.md
│   ├── tsconfig.json
│   └── vite.config.ts
├── .gitignore
├── README.md
└── ...
```

## Quick start

### 1) Install backend dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Then update `.env` with your AWS and model values.

### 2) Install frontend dependencies

```bash
cd frontend
npm install
cp .env.example .env.local
```

### 3) Run the backend

```bash
cd backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4) Run the frontend

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

The UI is typically available at:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000

## Environment configuration

This repo intentionally keeps secrets out of source control.

- Backend template: `backend/.env.example`
- Frontend template: `frontend/.env.example`
- Global ignore rules: `.gitignore`

### Required backend settings

Typical values include:

- `AWS_REGION`
- `AWS_PROFILE` or explicit AWS credentials
- `DYNAMODB_TABLE_NAME`
- `CLAIMBACK_RAW_DOCUMENTS_BUCKET`
- `CLAIMBACK_GENERATED_ARTIFACTS_BUCKET`
- `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL_ID` or `BEDROCK_MODEL_ID`

### Required frontend settings

- `VITE_API_BASE_URL`
- `VITE_CLAIMBACK_USER_ID`

## Development workflow

The project is set up so you can iterate locally without needing a production deployment:

1. Start the backend API.
2. Run the frontend dev server.
3. Upload sample documents or use the built-in demo flow.
4. Review opportunities, drafts, and audit events in the app.
5. Approve or dismiss claims before submission.

## Public repo guidance

Before opening this project publicly:

- Remove real AWS account identifiers
- Remove personal email addresses or bucket names
- Keep only generic placeholders in the sample env files
- Ensure any credentials are stored in local `.env` files only
- Document setup clearly for anyone cloning the repo

## License

This repository does not currently include a license file. If you plan to publish it publicly, add a license before the first public release.

## Next steps

Potential improvements for a production-ready public version:

- add Docker Compose for full local orchestration
- add a root-level Makefile
- add a proper CI pipeline
- add a sample dataset and demo walkthrough
- add deployment docs for AWS and frontend hosting
