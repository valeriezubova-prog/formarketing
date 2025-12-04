import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL")  # например, https://telegram-da-net-ne-znayu-bot.onrender.com
WEBHOOK_PATH = "/webhook"


def get_webhook_url() -> str:
    base = (WEBHOOK_BASE_URL or "").rstrip("/")
    return base + WEBHOOK_PATH if base else ""


bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher()


@dp.message(F.text)
async def handle_text(message: Message) -> None:
    """
    Реагирует строго на:
    - 'да' -> 'в кране черная вода!'
    - 'нет' -> 'с-маркетинга ответ!'
    - 'не знаю' -> 'а кто знает?!'
    Остальные сообщения игнорируются.
    """
    text = (message.text or "").strip().lower()

    if text == "да":
        await message.reply("в кране черная вода!")
    elif text == "нет":
        await message.reply("с-маркетинга ответ!")
    elif text == "не знаю":
        await message.reply("а кто знает?!")
    else:
        return


async def on_startup(app: web.Application):
    """
    При старте сервиса выставляем вебхук, если есть PUBLIC URL.
    """
    if not bot:
        logger.error("BOT_TOKEN не задан, бот не будет работать")
        return

    webhook_url = get_webhook_url()
    if webhook_url:
        await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        logger.info("Webhook set to %s", webhook_url)
    else:
        logger.warning(
            "WEBHOOK_BASE_URL не задан, вебхук не установлен. "
            "На Render он ОБЯЗАТЕЛЬНО должен быть задан."
        )


async def on_shutdown(app: web.Application):
    """
    При остановке сервиса удаляем вебхук и закрываем сессию.
    """
    if not bot:
        return

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()
    logger.info("Webhook removed, bot session closed")


def create_app() -> web.Application:
    """
    Фабрика aiohttp-приложения для uvicorn (--factory).
    """
    if not BOT_TOKEN:
        raise RuntimeError("Переменная окружения BOT_TOKEN не задана")

    app = web.Application()

    # обработчик вебхука Telegram
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=WEBHOOK_PATH)

    # health-check по корню — Render дергает /
    async def healthcheck(request: web.Request) -> web.Response:
        return web.Response(text="Bot is running")

    app.router.add_get("/", healthcheck)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    setup_application(app, dp, bot=bot)
    return app


# локальный запуск (например, python bot.py)
if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=10000)
