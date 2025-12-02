# detectors/spam_language.py
from db import add_alert

BANNED_WORDS = {
    "nigger",
    "nigga",
    "onlyfans",
}


def check_message(message):
    guild = message.guild
    if guild is None:
        return

    lower = message.content.lower()

    for word in BANNED_WORDS:
        if word in lower:
            details = (
                f"Message from {message.author} triggered banned language filter.\n"
                f"Content: {message.content[:200]}"
            )
            add_alert(
                guild_id=guild.id,
                user_id=message.author.id,
                alert_type="banned_language",
                details=details,
            )
            break
