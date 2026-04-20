# Local Development

## Prerequisites

- Docker Desktop or compatible Docker engine
- Node.js 20+ with `pnpm`
- Python 3.11 if you want to run services outside containers

## First Run

1. Copy `.env.example` to `.env`.
2. Run `pnpm install`.
3. Start the stack with `docker compose up --build`.
4. Open `http://localhost:3000` for the frontend and `http://localhost:8000/docs` for the API.
5. Apply the API schema with `alembic -c services/api/alembic.ini upgrade head` if you want the migration-driven path instead of startup `create_all`.

## Notes

- The current scaffold uses mock signal data so teams can wire UI and API flows before connecting live Kalshi ingestion.
- Worker heartbeats publish into Redis on `platform.heartbeat`, which is a good place to hang dev observability first.
- Use `Authorization: Bearer local-dev-token` for protected API routes in local development unless you replace the auth scaffold with real JWT issuance.
