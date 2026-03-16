# Hosting OpenClaw in Docker

Run the OpenClaw gateway and CLI in Docker from this workspace.

## Quick start (recommended)

From the **workspace root**:

```bash
./docker-host.sh
```

Or from the **openclaw repo directory**:

```bash
cd openclaw && ./docker-setup.sh
```

This will:

1. Build the Docker image (or pull a pre-built image if `OPENCLAW_IMAGE` is set).
2. Run the onboarding wizard (model provider, etc.).
3. Start the gateway and write a token to `openclaw/.env`.
4. Expose the gateway at **http://127.0.0.1:18789**.

After setup, open http://127.0.0.1:18789/ in your browser and paste the token (Settings → token).

## Manual run (no wizard)

If you already have config and just want to start the stack:

```bash
cd openclaw
docker build -t openclaw:local -f Dockerfile .
# Ensure .env exists with OPENCLAW_CONFIG_DIR, OPENCLAW_WORKSPACE_DIR, OPENCLAW_GATEWAY_TOKEN
docker compose up -d openclaw-gateway
```

Default env (used by `docker-setup.sh`):

- `OPENCLAW_CONFIG_DIR` — host path for config (default: `$HOME/.openclaw`)
- `OPENCLAW_WORKSPACE_DIR` — host path for workspace (default: `$HOME/.openclaw/workspace`)
- `OPENCLAW_GATEWAY_PORT` — host port (default: `18789`)
- `OPENCLAW_GATEWAY_BIND` — `lan` (reachable from host) or `loopback`

## Useful commands

- **Logs:** `cd openclaw && docker compose logs -f openclaw-gateway`
- **Dashboard URL / token:** `cd openclaw && docker compose run --rm openclaw-cli dashboard --no-open`
- **Stop:** `cd openclaw && docker compose down`

Full Docker docs: [openclaw/docs/install/docker.md](openclaw/docs/install/docker.md)
