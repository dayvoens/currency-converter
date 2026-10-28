import aiohttp

from config import CBU_RATE_URL


async def get_rate(currency):
    url = CBU_RATE_URL.format(currency=currency)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data[0]["Rate"])
                else:
                    print(f'Ошибка сервера ЦБ: {response.status}')
                    return None
    except Exception as e:
        print(f'Ошибка при получении данных от ЦБ: {e}')
        return None
