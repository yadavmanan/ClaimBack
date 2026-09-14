# ClaimBack Frontend

This is the React + Vite user interface for ClaimBack. It gives users a dashboard to review detected opportunities, inspect documents, check coverage, and approve or dismiss claim workflows.

## What the frontend does

- Shows claim opportunities with status, impact, and next steps
- Displays issued documents and uploaded evidence in the vault
- Lets users inspect a single opportunity and its audit trail
- Surfaces activity history for the current user
- Calls the FastAPI backend to ingest files and manage approvals

## Stack

- React 19
- TypeScript
- Vite
- React Router
- Tailwind CSS
- Framer Motion
- Radix UI primitives

## Project structure

- `src/App.tsx` – application routes
- `src/pages/` – dashboard, opportunity detail, vault, and activity screens
- `src/components/` – reusable UI and feature panels
- `src/api/client.ts` – requests to the backend
- `src/hooks/` – store hooks and state access
- `src/types/` – shared data models

## Local setup

1. Open a terminal in the `frontend` directory.
2. Install dependencies.

```bash
npm install
```

3. Copy the frontend example env file.

```bash
cp .env.example .env.local
```

4. Update the values if needed.

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_CLAIMBACK_USER_ID=usr_demo
```

## Run the app

```bash
npm run dev -- --host 0.0.0.0
```

Then open the local Vite URL, usually:

```text
http://localhost:5173
```

## Build for production

```bash
npm run build
```

To preview the production build:

```bash
npm run preview -- --host 0.0.0.0
```

## Notes

- The frontend expects the backend to be running on the value in `VITE_API_BASE_URL`.
- `VITE_CLAIMBACK_USER_ID` is useful for demo mode and local testing.
- This app is intentionally designed for a local demo and a small internal workflow, not a production-scale consumer app.

## Public repo guidance

- Keep `.env*` files local and never commit secrets
- Prefer generic values in `.env.example`
- When deploying publicly, ensure the API origin is configured correctly in the frontend environment
