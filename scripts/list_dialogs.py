"""List Telegram dialogs — use to find the correct TELEGRAM_CHANNEL value."""

import asyncio
import logging

from telethon import TelegramClient

from app.config import settings

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    client = TelegramClient(
        str(settings.telegram_session_path),
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )
    await client.start()
    me = await client.get_me()
    print(f"Logged in as: {me.first_name} (@{me.username}) id={me.id}\n")
    print(f"{'ID':<20} {'Type':<12} Name")
    print("-" * 60)
    async for dialog in client.iter_dialogs():
        kind = "channel" if dialog.is_channel else "group" if dialog.is_group else "user"
        name = (dialog.name or "").encode("ascii", "replace").decode("ascii")
        print(f"{dialog.id:<20} {kind:<12} {name}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
