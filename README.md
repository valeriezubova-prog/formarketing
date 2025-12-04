# Telegram "да / нет / не знаю" бот для Render

Файлы в этом архиве:
- `main.py` — FastAPI + aiogram бот с вебхуками
- `requirements.txt` — зависимости
- `render.yaml` — конфиг для Render

## Шаги

1. Залить эти файлы в репозиторий на GitHub.
2. В Render создать новый Web Service из этого репо.
3. В Env Vars добавить:
   - `BOT_TOKEN` — токен бота от BotFather
   - `WEBHOOK_BASE_URL` — адрес сервиса вида `https://<имя-сервиса>.onrender.com`
4. Дождаться деплоя и написать боту в личку `да`, `нет` или `не знаю`.
