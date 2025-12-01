import time
from db import add_signal

REACTION_THRESHOLD_MS = 250  # human reflex lower bound


async def check_reaction(reaction, user, reaction_time_ms):
    if reaction_time_ms < REACTION_THRESHOLD_MS:
        add_signal(
            reaction.message.guild.id,
            user.id,
            "fast_reaction"
        )
