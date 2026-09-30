# AI Security Copilot - dashboard

React + TypeScript + Vite + Tailwind v4 + shadcn/ui frontend for
[AI Security Copilot](../README.md). See the root README and
[`docs/local-development.md`](../docs/local-development.md) for how this fits into the rest of
the project, and [`docs/deployment.md`](../docs/deployment.md) for deploying the built output.

```bash
npm install
npm run dev      # http://localhost:5173, proxies /api to http://127.0.0.1:8000 (start the backend first)
npm run build    # → dist/, served as static files in production (see docs/deployment.md)
npm run lint     # oxlint
```

## Layout

```
src/api/          hand-written fetch client + types mirroring backend/app/schemas/*.py
src/auth/         token storage (localStorage) + the RequireAuth route guard
src/pages/        one component per route (login, analyze, analysis detail, history)
src/components/dashboard/   the analysis-report building blocks (risk summary, SHAP chart,
                             indicators, domain info, threat intel, AI explanation, feedback)
src/components/ui/          shadcn/ui components - generated, then owned and edited directly
```

The API client is intentionally hand-written rather than generated from the backend's OpenAPI
schema (`openapi-typescript` is a Should-tier addition the project plan calls out and defers), so
the frontend has no build-time dependency on a running backend.
