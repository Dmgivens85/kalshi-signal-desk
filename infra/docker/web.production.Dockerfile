FROM node:20-bookworm-slim AS deps

WORKDIR /workspace

RUN corepack enable

COPY package.json pnpm-workspace.yaml turbo.json tsconfig.base.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/design-system/package.json packages/design-system/package.json
COPY packages/shared-ts/package.json packages/shared-ts/package.json
COPY packages/strategy-sdk/package.json packages/strategy-sdk/package.json

RUN pnpm install --filter web... --frozen-lockfile=false

FROM node:20-bookworm-slim AS builder

WORKDIR /workspace

RUN corepack enable

COPY --from=deps /workspace ./
COPY . .

RUN pnpm --dir apps/web build

FROM node:20-bookworm-slim AS runtime

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app \
    && apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /workspace/apps/web/public ./public
COPY --from=builder /workspace/apps/web/.next/standalone ./
COPY --from=builder /workspace/apps/web/.next/static ./apps/web/.next/static

USER app

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:3000/api/health').then((res) => process.exit(res.ok ? 0 : 1)).catch(() => process.exit(1))"

CMD ["node", "apps/web/server.js"]
