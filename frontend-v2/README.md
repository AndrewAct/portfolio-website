# Frontend v2 (Vue + TypeScript)

This is the Vue 3 + TypeScript rewrite of the portfolio frontend. Built with Vite, served by Nginx in Docker.

## Commands

- `npm run dev`: local development
- `npm run build`: production build to `dist/`
- `npm run preview`: local preview (`vite preview`, overlay disabled)

## Vite overlay

The error overlay is disabled in dev and preview via `vite.config.ts`:
- `server.hmr.overlay = false`
- `preview.hmr = false`

## Docker

Build and run locally:

```bash
cd frontend-v2
docker compose up --build -d
# open http://localhost:8080
```

## AWS Lightsail

1. Build image and push to your registry (e.g., Docker Hub):
```bash
docker build -t <your-dockerhub-username>/portfolio-frontend-v2:latest .
docker push <your-dockerhub-username>/portfolio-frontend-v2:latest
```
2. In Lightsail Container Service, create a new deployment using the image above.
3. Expose port 80 and set health check path `/`.

Alternatively, deploy on a Lightsail instance:
- Provision an instance
- Install Docker
- Pull and run the image exposing port 80

## Env vars

Use Vite-style variables in `.env` (prefix with `VITE_`). See `.env.example`.
