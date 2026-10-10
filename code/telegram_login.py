"""Renew the configured Telegram session interactively without printing credentials."""
import asyncio
import os
from project_paths import telegram_session_path
from telethon import TelegramClient
from download_telegram_posts import load_dotenv

async def main():
    load_dotenv()
    client = TelegramClient(telegram_session_path(), int(os.environ['TELEGRAM_API_ID']), os.environ['TELEGRAM_API_HASH'])
    await client.start()
    print('Telegram login complete.')
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
