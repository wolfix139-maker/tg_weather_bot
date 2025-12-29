import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from telegram import ReplyKeyboardMarkup, KeyboardButton

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

def get_weather_by_coords(lat: float, lon: float) -> str:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "ru",
    }
    r = requests.get(url, params=params, timeout=10)

    if r.status_code != 200:
        return "Не смог получить погоду по геолокации 😅 Попробуй ещё раз."

    data = r.json()
    place = data.get("name", "вашем месте")
    temp = data["main"]["temp"]
    feels = data["main"]["feels_like"]
    desc = data["weather"][0]["description"]
    wind = data["wind"]["speed"]

    return (
        f"📍 Погода в {place}:\n"
        f"• {desc}\n"
        f"• {temp}°C (ощущается как {feels}°C)\n"
        f"• ветер {wind} м/с"
    )

def get_weather(city: str) -> str:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "ru",
    }
    r = requests.get(url, params=params, timeout=10)

    if r.status_code != 200:
        return "Не нашёл город 😅 Попробуй написать иначе (например: Warsaw, Gdansk)."

    data = r.json()
    temp = data["main"]["temp"]
    feels = data["main"]["feels_like"]
    desc = data["weather"][0]["description"]
    wind = data["wind"]["speed"]

    return (
        f"🌤 Погода в {city}:\n"
        f"• {desc}\n"
        f"• {temp}°C (ощущается как {feels}°C)\n"
        f"• ветер {wind} м/с"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команды:\n"
        "/start - старт\n"
        "/weather - запросить погоду\n"
        "/help - подсказка\n"
        "/location - Поделится своей локацией и узнать погоду за окном\n\n"
        "Или просто напиши город (например: Warsaw, Gdansk).")

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ок! Напиши город (например: Warsaw)")

async def location_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("📍 Отправить геолокацию", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "Нажми кнопку ниже, чтобы отправить геолокацию. Я покажу погоду рядом с тобой 🌦",
        reply_markup=reply_markup
    )
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not WEATHER_API_KEY:
        await update.message.reply_text("Я не вижу WEATHER_API_KEY. Добавь ключ погоды в Run Configuration.")
        return

    loc = update.message.location
    result = get_weather_by_coords(loc.latitude, loc.longitude)
    await update.message.reply_text(result)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()

    if not WEATHER_API_KEY:
        await update.message.reply_text("Я не вижу WEATHER_API_KEY. Добавь ключ погоды в Run Configuration.")
        return

    result = get_weather(city)
    await update.message.reply_text(result)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n"
        "/start - старт\n"
        "/weather - запросить погоду\n"
        "/help - подсказка\n"
        "/location - Поделится своей локацией и узнать погоду за окном\n\n"
        "Или просто напиши город (например: Warsaw, Gdansk)."
    )


def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Не найден TELEGRAM_TOKEN. Добавь переменную окружения.")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("location", location_cmd))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    PORT = int(os.getenv("PORT", "8000"))
    WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL")      # <-- берем из env
    WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "tg-webhook")

    print("✅ Bot started")

    if WEBHOOK_BASE_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=WEBHOOK_PATH,
            webhook_url=f"{WEBHOOK_BASE_URL.rstrip('/')}/{WEBHOOK_PATH}",
            drop_pending_updates=True,
        )
    else:
        app.run_polling()


if __name__ == "__main__":
    main()
