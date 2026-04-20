FROM node:20-bookworm-slim

WORKDIR /workspace

RUN corepack enable

COPY package.json pnpm-workspace.yaml turbo.json tsconfig.base.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/design-system/package.json packages/design-system/package.json
COPY packages/shared-ts/package.json packages/shared-ts/package.json
COPY packages/strategy-sdk/package.json packages/strategy-sdk/package.json

RUN pnpm install --filter web...

COPY . .

EXPOSE 3000
