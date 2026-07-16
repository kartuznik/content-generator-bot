# Content Generator Bot

Production-ready Telegram-бот для генерации контента:
- текст — через **YandexGPT** (Yandex Cloud API),
- изображения — через **OpenAI DALL-E 3**,
- подписка/оплата — через **YooKassa**,
- админка — **Flask**.

## Стек

- `aiogram 3` (polling)
- `SQLite` (aiosqlite)
- `Flask` (simple admin panel)
- `YandexGPT` для текста
- `OpenAI DALL-E 3` для изображений
- `YooKassa` для подписки

## Quick Start

1. Клонировать репозиторий:
   ```bash
   git clone git@github.com:kartuznik/content-generator-bot.git
   cd content-generator-bot
   ```
2. Подготовить переменные окружения:
   ```bash
   cp .env.example .env
   ```
3. Запустить сервисы:
   ```bash
   docker compose up --build -d
   ```
4. Проверить:
   - Flask admin: `http://localhost:5000`
   - bot: polling в контейнере `bot`

## Переменные окружения

| Переменная | Назначение |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота от [@BotFather](https://t.me/BotFather). |
| `YANDEX_IAM_TOKEN` | IAM-токен Yandex Cloud для доступа к YandexGPT. Получить можно через CLI (`yc iam create-token`) или сервисный аккаунт. |
| `YANDEX_FOLDER_ID` | Folder ID вашего облачного каталога Yandex Cloud, где подключён Foundation Models API. |
| `OPENAI_API_KEY` | API-ключ OpenAI, используется только для DALL-E 3. |
| `YOKASSA_SHOP_ID` | ID магазина YooKassa. |
| `YOKASSA_SECRET_KEY` | Секретный ключ YooKassa. |
| `YOOKASSA_RETURN_URL` | URL возврата пользователя после оплаты. |
| `ADMIN_WEB_PASSWORD` | Пароль для HTTP Basic Auth в админке (`admin:<password>`). |
| `DB_PATH` | Путь к SQLite базе (по умолчанию `data/content_generator.db`). |

## Команды бота

- `/start`
- `/generate <текст>`
- `/generate_image <описание>`
- `/subscribe`
- `/help`

## Структура проекта

```text
content-generator-bot/
├── bot/
├── web/
├── data/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
└── README.md
```

## Web Admin

- HTTP Basic Auth:
  - login: `admin`
  - password: значение `ADMIN_WEB_PASSWORD`
- Dashboard:
  - число пользователей,
  - активные подписки,
  - общее число генераций,
  - доход (успешные платежи).
- Users:
  - просмотр лимитов и подписок,
  - ручное добавление бесплатных генераций,
  - продление подписки по дням.
