import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL")  # например, https://your-service.onrender.com
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = (WEBHOOK_BASE_URL or "").rstrip("/") + WEBHOOK_PATH

if not BOT_TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не задана")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(F.text)
async def handle_text(message: Message) -> None:
    """
    Обработчик всех текстовых сообщений.
    Реагирует строго на:
    - 'да' -> 'в кране черная вода!'
    - 'нет' -> 'с-маркетинга ответ!'
    - 'не знаю' -> 'а кто знает?!'
    Во всех остальных случаях молчит.
    """
    text = (message.text or "").strip().lower()

    if text == "да":
        await message.reply("в кране черная вода!")
    elif text == "нет":
        await message.reply("с-маркетинга ответ!")
    elif text == "не знаю":
        await message.reply("а кто знает?!")
    else:
        # Ничего не отвечаем, чтобы не флудить
        return


async def on_startup(app: web.Application):
    """
    Хук старта приложения: устанавливаем вебхук для Telegram,
    если задан WEBHOOK_BASE_URL. Если не задан, запускаем бот без вебхука.
    """
    if WEBHOOK_BASE_URL:
        await bot.set_webhook(url=WEBHOOK_URL)
        logger.info("Webhook set to %s", WEBHOOK_URL)
    else:
        logger.warning(
            "WEBHOOK_BASE_URL не задан, вебхук не будет установлен. "
            "Локальный запуск возможен только с polling (не используется на Render)."
        )


async def on_shutdown(app: web.Application):
    """
    Хук остановки приложения: удаляем вебхук и закрываем сессию бота.
    """
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()
    logger.info("Webhook удалён, сессия бота закрыта")


def create_app() -> web.Application:
    """
    Создаёт и настраивает aiohttp-приложение для работы через вебхук.
    """
    app = web.Application()

    # Обработчик Telegram вебхуков
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=WEBHOOK_PATH)

    # Хуки старта и остановки приложения
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Дополнительный health-check endpoint
    async def healthcheck(request: web.Request) -> web.Response:
        return web.Response(text="Bot is running")

    app.router.add_get("/", healthcheck)

    setup_application(app, dp, bot=bot)
    return app


app = create_app()

if __name__ == "__main__":
    # Локальный запуск через uvicorn:
    # WEBHOOK_BASE_URL можно не задавать, вебхук не будет установлен,
    # но HTTP-сервер всё равно поднимется.
    web.run_app(app, host="0.0.0.0", port=10000)
