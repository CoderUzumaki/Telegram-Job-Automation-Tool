"""Resolve TELEGRAM_CHANNEL to a Telethon entity."""

from __future__ import annotations

import logging
import re

from telethon import TelegramClient

logger = logging.getLogger(__name__)


async def resolve_chat_entity(client: TelegramClient, target: str):
    """
    Resolve a chat/group/channel from .env.

    Accepts @username, numeric id (-100...), or display name substring match
    after scanning dialogs.
    """
    target = target.strip()
    if not target:
        raise ValueError("TELEGRAM_CHANNEL is empty")

    if target.startswith("@"):
        entity = await client.get_entity(target)
        logger.info("Resolved chat via username: %s -> id %s", target, entity.id)
        return entity

    # Numeric ids must be int for Telethon; string "-100..." often fails without cache.
    if re.fullmatch(r"-?\d+", target):
        wanted_id = int(target)
        async for dialog in client.iter_dialogs():
            if dialog.id == wanted_id:
                logger.info("Resolved chat via dialogs: %s (%s)", dialog.name, dialog.id)
                return dialog.entity
        try:
            entity = await client.get_entity(wanted_id)
            logger.info("Resolved chat via get_entity: %s", wanted_id)
            return entity
        except ValueError as exc:
            raise ValueError(
                f"Cannot find chat id {wanted_id}. "
                "Open the group in Telegram with this account, then retry. "
                "Or set TELEGRAM_CHANNEL to @username if the group has one."
            ) from exc

    # Substring match on dialog title (e.g. "SDE Premium Referrals")
    needle = target.lower()
    matches = []
    async for dialog in client.iter_dialogs():
        if needle in (dialog.name or "").lower():
            matches.append(dialog)
    if len(matches) == 1:
        logger.info("Resolved chat via name match: %s -> %s", target, matches[0].id)
        return matches[0].entity
    if len(matches) > 1:
        names = ", ".join(f"{d.name} ({d.id})" for d in matches)
        raise ValueError(f"Multiple chats match '{target}': {names}. Use numeric id or @username.")

    raise ValueError(
        f"Cannot find any chat matching '{target}'. "
        "Run: python scripts/list_dialogs.py"
    )


def peer_storage_id(peer_id, fallback: str) -> str:
    """Stable dedup key from message peer."""
    if hasattr(peer_id, "channel_id"):
        return str(peer_id.channel_id)
    if hasattr(peer_id, "chat_id"):
        return str(peer_id.chat_id)
    return fallback
