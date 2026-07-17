# Content Generator Bot

Production-ready Telegram-бот для генерации контента:
- текст — через **OpenAI GPT-4o-mini** (можно переключить на GPT-4),
- изображения — через **OpenAI DALL-E 3**,
- подписка/оплата — через **YooKassa**,
- админка — **Flask**.

## Стек

- `aiogram 3` (polling)
- `SQLite` (aiosqlite)
- `Flask` (admin panel)
- `OpenAI GPT` для текста
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
   - Flask admin: `http://localhost:8005`
   - bot: polling в контейнере `content-generator-bot`

## Переменные окружения

| Переменная | Назначение |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота от [@BotFather](https://t.me/BotFather). |
| `OPENAI_API_KEY` | API-ключ OpenAI для текста и изображений. Получить: [platform.openai.com/api-keys](https://platform.openai.com/api-keys). |
| `OPENAI_MODEL` | Модель для текстовой генерации (`gpt-4o-mini` по умолчанию или `gpt-4`). |
| `YOKASSA_SHOP_ID` | ID магазина YooKassa. |
| `YOKASSA_SECRET_KEY` | Секретный ключ YooKassa. |
| `YOOKASSA_RETURN_URL` | URL возврата пользователя после оплаты. |
| `ADMIN_WEB_PASSWORD` | Пароль входа в веб-админку. |
| `FLASK_SECRET_KEY` | Секрет Flask-сессий для веб-панели. |
| `DB_PATH` | Путь к SQLite базе (по умолчанию `data/content_generator.db`). |
| `LOG_LEVEL` | Уровень логирования приложения. |

## Команды бота

- `/start`
- `/generate <текст>`
- `/generate_image <описание>`
- `/subscribe`
- `/help`

## Web Admin

- Вход: форма `/login` с паролем `ADMIN_WEB_PASSWORD`
- Dashboard:
  - число пользователей,
  - активные подписки,
  - успешные генерации
- Users:
  - просмотр лимитов и подписок,
  - ручное добавление `+5` бесплатных генераций
- Generations:
  - последние 50 генераций из `generated_posts`
