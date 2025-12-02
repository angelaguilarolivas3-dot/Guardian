# detectors/reaction_patterns.py
import time
from db import add_alert


async def check_reaction(reaction, user, reaction_time_ms: float):
    guild = reaction.message.guild
    if guild is None:
        return

    # Example threshold: under 150ms looks botty
    if reaction_time_ms < 150:
        details = (
            f"User reacted very quickly ({reaction_time_ms:.1f} ms) "
            f"to message ID {reaction.message.id} in #{reaction.message.channel}."
        )
        add_alert(
            guild_id=guild.id,
            user_id=user.id,
            alert_type="suspicious_reaction",
            details=details,
        ) 
