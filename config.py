import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

CBU_RATE_URL = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/{currency}/"
