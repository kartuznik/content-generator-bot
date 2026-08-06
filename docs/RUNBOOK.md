# Content Generator Bot — Runbook

Operational guide for self-hosted deployments. No secrets, hostnames, or public IPs are documented here — use your environment’s `.env` and Compose project.

## Deploy

1. Clone the repository and create `.env` from `.env.example`.
2. Required: `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `YOKASSA_SHOP_ID`, `YOKASSA_SECRET_KEY`, `YOOKASSA_RETURN_URL`, `ADMIN_WEB_PASSWORD`, `FLASK_SECRET_KEY`.
3. Optional: `OPENAI_MODEL`, `DB_PATH`, `LOG_LEVEL`.
4. Start:

```bash
docker compose up -d --build
docker compose ps
```

5. Verify:
   - Bot polling logs are healthy (`docker compose logs --tail=100 bot`).
   - Admin panel answers on the mapped host port **`:8005`** (password from `ADMIN_WEB_PASSWORD`).

After documentation-only changes, no rebuild is required. After code changes that affect runtime, rebuild touched services:

```bash
docker compose up -d --build bot web
```

## Backup and restore

### SQLite

- Default data dir: `./data` (container: `/app/data`).
- Typical DB file: path from `DB_PATH` or project default under `data/`.

Cold backup:

```bash
docker compose stop bot web
mkdir -p ./backups
cp -a ./data ./backups/data-$(date +%Y%m%d)
docker compose start bot web
```

Restore: stop services → replace `./data` from backup → start services → smoke `/start` in Telegram and admin login.

### Configuration

- Back up `.env` out-of-band (secrets manager / encrypted store). Never commit it.
- Compose and app code are in git; restore by checking out the known revision and recreating containers.

## API key / secret rotation

Rotate one secret at a time; smoke after each recreate.

| Secret | Steps |
|---|---|
| `TELEGRAM_BOT_TOKEN` | New token in BotFather → update `.env` → `docker compose up -d --force-recreate bot` |
| `OPENAI_API_KEY` | New key → update `.env` → recreate `bot` → revoke old key after smoke |
| `YOKASSA_*` / `YOOKASSA_RETURN_URL` | Update shop credentials/return URL → recreate `bot` |
| `ADMIN_WEB_PASSWORD` | Update `.env` → recreate `web` |
| `FLASK_SECRET_KEY` | Update `.env` → recreate `web` (sessions reset) |

After any manual `.env` edit: verify each changed line with `grep '^VAR=' .env` **before** recreate (see `/opt/standards/RULES.md` §4a).

## Incident response

### OpenAI errors / empty generations

- Check bot logs and provider status/balance.
- User already gets an honest failure message; successful counter is not incremented on exception.
- Mitigate: fix key/model, retry later; no secondary LLM fallback in this product.

### Admin panel unreachable

- `docker compose ps` / `logs web`; confirm host port `:8005` mapping.
- Confirm `ADMIN_WEB_PASSWORD` in the running container env (without printing it to chat).

### Payment / subscribe issues

- Verify YooKassa credentials and return URL.
- Check bot logs around `/subscribe`; do not paste secrets into tickets.

## Rollback

```bash
git log --oneline -5
git checkout <known-good-sha>
docker compose up -d --build
```

Restore `./data` from backup if the bad revision corrupted the DB.
