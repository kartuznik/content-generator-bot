# Content Generator Bot — Runbook

Операционное руководство для self-hosted деплоя. Секреты, hostname и публичные IP сюда не пишем — используйте `.env` и Compose-проект окружения.

## Deploy

1. Клонируйте репозиторий и создайте `.env` из `.env.example`.
2. Обязательно: `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `YOKASSA_SHOP_ID`, `YOKASSA_SECRET_KEY`, `YOOKASSA_RETURN_URL`, `ADMIN_WEB_PASSWORD`, `FLASK_SECRET_KEY`.
3. Опционально: `OPENAI_MODEL`, `DB_PATH`, `LOG_LEVEL`.
4. Запуск:

```bash
docker compose up -d --build
docker compose ps
```

5. Проверка:
   - Логи polling бота здоровы (`docker compose logs --tail=100 bot`).
   - Admin panel отвечает на mapped host-порту **`:8005`** (пароль из `ADMIN_WEB_PASSWORD`).

После docs-only изменений пересборка не нужна. После изменений кода, влияющих на runtime, пересоберите затронутые сервисы:

```bash
docker compose up -d --build bot web
```

## Backup и restore

### SQLite

- Каталог данных по умолчанию: `./data` (в контейнере: `/app/data`).
- Файл БД: путь из `DB_PATH` или дефолт проекта в `data/`.

Холодный backup:

```bash
docker compose stop bot web
mkdir -p ./backups
cp -a ./data ./backups/data-$(date +%Y%m%d)
docker compose start bot web
```

Restore: остановить сервисы → заменить `./data` из backup → запустить сервисы → smoke `/start` в Telegram и вход в админку.

### Конфигурация

- `.env` храните вне git (secrets manager / шифрованное хранилище). Никогда не коммитьте.
- Compose и код приложения в git; восстановление — checkout известной ревизии и recreate контейнеров.

## Ротация API-ключей и секретов

Ротируйте один секрет за раз; после каждого recreate — smoke.

| Секрет | Шаги |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Новый токен в BotFather → обновить `.env` → `docker compose up -d --force-recreate bot` |
| `OPENAI_API_KEY` | Новый ключ → обновить `.env` → recreate `bot` → отозвать старый ключ после smoke |
| `YOKASSA_*` / `YOOKASSA_RETURN_URL` | Обновить credentials магазина / return URL → recreate `bot` |
| `ADMIN_WEB_PASSWORD` | Обновить `.env` → recreate `web` |
| `FLASK_SECRET_KEY` | Обновить `.env` → recreate `web` (сессии сбросятся) |

После любой ручной правки `.env`: проверить каждую изменённую строку через `grep '^VAR=' .env` **до** recreate (см. `/opt/standards/RULES.md` §4a).

## Инциденты

### Ошибки OpenAI / пустые генерации

- Смотрите логи бота и статус/баланс провайдера.
- Пользователь уже получает честное сообщение об ошибке; счётчик успешных генераций при exception не увеличивается.
- Mitigation: починить ключ/модель, повторить позже; вторичного LLM fallback в этом продукте нет.

### Админка недоступна

- `docker compose ps` / `logs web`; проверьте mapping host-порта `:8005`.
- Убедитесь, что `ADMIN_WEB_PASSWORD` есть в env запущенного контейнера (не печатать значение в чат).

### Платежи / `/subscribe`

- Проверьте credentials YooKassa и return URL.
- Смотрите логи бота вокруг `/subscribe`; секреты в тикеты не вставлять.

## Rollback

```bash
git log --oneline -5
git checkout <known-good-sha>
docker compose up -d --build
```

Восстановите `./data` из backup, если плохая ревизия повредила БД.

## Разморозка

Если продукт переведён в `inactive` и runtime остановлен, разморозка выполняется так:

1. Пополнить баланс OpenAI.
2. Проверить конфигурацию модели в `.env` (включая модель для генерации изображений).
3. Запустить runtime:

```bash
docker compose up -d
```

4. Провести живой smoke в Telegram:
   - `/generate`
   - `/generate_image`
5. После успешного smoke перевести паспорт в `README.md` обратно в `active`.
