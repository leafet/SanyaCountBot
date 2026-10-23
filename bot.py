import os
import asyncio
import datetime
import zoneinfo
import re  # Импортируем регулярные выражения для поиска цифры
import discord
from discord.ext import tasks
from dotenv import load_dotenv
from aiohttp import web

load_dotenv()

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Укажите ваш ID канала
CHANNEL_ID = 1563065598836084817

# НАСТРОЙКА ВРЕМЕНИ ОБНОВЛЕНИЯ (например, каждый день в 00:00 по Москве)
MY_TZ = zoneinfo.ZoneInfo("Europe/Moscow")
CRON_TIME = datetime.time(hour=0, minute=0, second=0, tzinfo=MY_TZ)


@tasks.loop(time=CRON_TIME)
async def update_channel_counter():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if channel:
        try:
            # 1. Считываем текущее название канала
            current_name = channel.name  # Например: "день-14" или "📅-день-5"

            # Находим все цифры в названии с помощью регулярного выражения
            numbers = re.findall(r'\d+', current_name)

            if numbers:
                # Если цифра найдена, берем её и увеличиваем на 1
                current_day = int(numbers[0])
                next_day = current_day + 1
            else:
                # Если цифры в названии вообще нет (например, канал называется "general"),
                # то начнем отсчет с 1
                next_day = 1

            # 2. Формируем новое название и обновляем канал
            new_name = f"день-{next_day}"
            await channel.edit(name=new_name)
            print(f"Канал обновлен с '{current_name}' на '{new_name}'")

            # 3. Отправляем сообщение
            await channel.send(f"📅 Наступил **день {next_day}**!")

        except discord.Forbidden:
            print("Ошибка: У бота нет прав на управление этим каналом.")
        except discord.HTTPException as e:
            print(f"Ошибка Discord (возможно, лимит 2 переименования в 10 минут): {e}")
    else:
        print("Ошибка: Канал не найден.")


@client.event
async def on_ready():
    print(f'Бот авторизован как {client.user}. Парсинг счетчика настроен напрямую из Discord!')

    if not update_channel_counter.is_running():
        update_channel_counter.start()


async def health(request):
    return web.json_response({"status": "ok"})


def create_http_app():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/healthz", health)
    return app


async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is required")

    port = int(os.environ.get("PORT", "10000"))
    runner = web.AppRunner(create_http_app())
    await runner.setup()
    try:
        await web.TCPSite(runner, host="0.0.0.0", port=port).start()
        print(f"HTTP server listening on port {port}")
        async with client:
            await client.start(token)
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    discord.utils.setup_logging()
    asyncio.run(main())
