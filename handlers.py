from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from cbu_api import get_rate

router = Router()

kb_list = [
    [KeyboardButton(text="🇺🇸 USD"), KeyboardButton(text="🇪🇺 EUR"), KeyboardButton(text="🇷🇺 RUB")],
    [KeyboardButton(text="🔄 Сменить режим"), KeyboardButton(text="📊 Обновить курсы")]
]
keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)

user_settings = {}

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    welcome_text = (
        f"👋 <b>Здравствуйте, {message.from_user.first_name}!</b>\n\n"
        f"🤖 Я - ваш персональный валютный ассистент.\n"
        f"📊 Все курсы валют обновляются в реальном времени напрямую с официального сайта <b>Центрального Банка Республики Узбекистан (ЦБ РУз)</b>.\n\n"
        f"📌 <b>Как мной пользоваться:</b>\n"
        f"1️⃣ Нажмите на кнопку нужной валюты ниже, чтобы узнать её актуальный курс.\n"
        f"2️⃣ Отправьте мне любую сумму (число), чтобы мгновенно конвертировать её.\n"
        f"3️⃣ Кнопка <b>«🔄 Сменить режим»</b> позволяет переключать направление обмена (например, переводить из сумов в доллары).\n\n"
        f"Выполните первый шаг — выберите интересующую вас валюту:"
    )
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")

@router.message(F.text == "🔄 Сменить режим")
async def change_direction(message: Message):
    chat_id = message.chat.id
    
    if chat_id not in user_settings:
        user_settings[chat_id] = {"currency": "USD", "direction": "DIRECT"}
        
    if user_settings[chat_id]["direction"] == "DIRECT":
        user_settings[chat_id]["direction"] = "REVERSE"
        currency = user_settings[chat_id]["currency"]
        
        text = (
            f"🔄 <b>Режим конвертации успешно изменен!</b>\n\n"
            f"📥 <b>Текущие настройки:</b>\n"
            f"----------------------------------\n"
            f" Направление: <b>UZS ➡️ {currency}</b>\n"
            f" Расчет: <code>[Ваша сумма в сумах] ÷ [Курс ЦБ]</code>\n"
            f"----------------------------------\n\n"
            f"✍️ Отправьте сумму в <b>UZS (сумах)</b> для перевода."
        )
    else:
        user_settings[chat_id]["direction"] = "DIRECT"
        currency = user_settings[chat_id]["currency"]
        
        text = (
            f"🔄 <b>Режим конвертации успешно изменен!</b>\n\n"
            f"📥 <b>Текущие настройки:</b>\n"
            f"----------------------------------\n"
            f" Направление: <b>{currency} ➡️ UZS</b>\n"
            f" Расчет: <code>[Ваша сумма] × [Курс ЦБ]</code>\n"
            f"----------------------------------\n\n"
            f"✍️ Отправьте сумму в <b>{currency}</b> для перевода."
        )
        
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📊 Обновить курсы")
async def show_all_rates(message: Message):
    status_message = await message.answer("⏳ Получаю актуальные данные от ЦБ...")

    usd_rate = await get_rate("USD")
    eur_rate = await get_rate("EUR")
    rub_rate = await get_rate("RUB")

    if usd_rate and eur_rate and rub_rate:
        summary_text = (
            f"📊 <b>Актуальные курсы ЦБ РУз:</b>\n"
            f"----------------------------------\n"
            f"🇺🇸 1 USD = <code>{usd_rate:,.2f} UZS</code>\n"
            f"🇪🇺 1 EUR = <code>{eur_rate:,.2f} UZS</code>\n"
            f"🇷🇺 1 RUB = <code>{rub_rate:,.2f} UZS</code>\n"
            f"----------------------------------\n"
            f"✨ Данные обновлены!"
        ).replace(',', ' ')

        await status_message.delete()
        await message.answer(summary_text, parse_mode='HTML')
    else:
        await status_message.delete()
        await message.answer('❌ Не удалось обновить курсы. Попробуйте позже.')



@router.message(F.text.in_({"🇺🇸 USD", "🇪🇺 EUR", "🇷🇺 RUB"}))
async def save_currency(message: Message):
    currency_code = message.text.split()[-1] 
    chat_id = message.chat.id
    
    user_settings[chat_id] = {"currency": currency_code, "direction": "DIRECT"}
    
    rate = await get_rate(currency_code)
    if rate:

        text = (
            f"✅ <b>Валюта успешно выбрана!</b>\n\n"
            f"📊 Текущий курс ЦБ: <code>1 {currency_code} = {rate:,.2f} UZS</code>\n"
            f"🔄 Направление: <b>{currency_code} ➡️ UZS</b>\n\n"
            f"✍️ Отправьте сумму, которую хотите сконвертировать."
        )
        await message.answer(text, parse_mode="HTML")
    else:
        await message.answer("❌ Не удалось получить данные от Центробанка.")


@router.message()
async def convert_money(message: Message):
    chat_id = message.chat.id
    if chat_id not in user_settings:
        await message.answer("⚠️ Сначала выберите валюту с помощью кнопок!")
        return

    if not message.text:
        await message.answer("⚠️ Пожалуйста, отправьте корректное число (сумму).")
        return

    text = message.text.replace(",", ".").strip()
    try:
        amount = float(text)
    except ValueError:
        await message.answer("⚠️ Пожалуйста, отправьте корректное число (сумму).")
        return

    currency = user_settings[chat_id]["currency"]
    direction = user_settings[chat_id]["direction"]
    
    rate = await get_rate(currency)

    
    if rate:
        if direction == "DIRECT":
            result = amount * rate

            text_result = (
                f"🧮 <b>Результат конвертации:</b>\n"
                f"----------------------------------\n"
                f"💵 Отдаёте: <code>{amount:,.2f} {currency}</code>\n"
                f"🇺🇿 Получаете: <b><code>{result:,.2f} UZS</code></b>\n"
                f"----------------------------------\n"
                f"📈 Курс расчета: <code>1 {currency} = {rate:,.2f} UZS</code>"
            ).replace(",", " ")
        else:
            result = amount / rate
            
            text_result = (
                f"🧮 <b>Результат конвертации:</b>\n"
                f"----------------------------------\n"
                f"🇺🇿 Отдаёте: <code>{amount:,.2f} UZS</code>\n"
                f"💵 Получаете: <b><code>{result:,.2f} {currency}</code></b>\n"
                f"----------------------------------\n"
                f"📈 Курс расчета: <code>1 {currency} = {rate:,.2f} UZS</code>"
            ).replace(",", " ")

        await message.answer(text_result, parse_mode="HTML")
    else:
        await message.answer("❌ Ошибка при обращении к ЦБ. Попробуйте позже.")
