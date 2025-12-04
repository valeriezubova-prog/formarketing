import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_BASE_URL = (os.getenv("WEBHOOK_BASE_URL") or "").rstrip("/")
WEBHOOK_PATH = "/webhook"  # путь, куда телега будет слать апдейты

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(F.text)
async def handle_text(message: Message):
    text = (message.text or "").strip().lower()
    if text == "да":
        await message.reply("в кране черная вода!")
    elif text == "нет":
        await message.reply("с-маркетинга ответ!")
    elif text == "не знаю":
        await message.reply("а кто знает?!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Старт приложения: ставим webhook
    if not WEBHOOK_BASE_URL:
        logger.warning("WEBHOOK_BASE_URL is not set, webhook will not be configured")
        yield
        return

    webhook_url = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"
    logger.info(f"Setting Telegram webhook to {webhook_url}")
    await bot.set_webhook(webhook_url)

    try:
        yield
    finally:
        # Остановка приложения: убираем webhook
        logger.info("Deleting Telegram webhook")
        await bot.delete_webhook()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def healthcheck():
    # Render ходит по /, важно возвращать 200
    return PlainTextResponse("OK")


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data)
    # Передаём апдейт aiogram'у
    await dp.feed_update(bot, update)
    return PlainTextResponse("OK")
