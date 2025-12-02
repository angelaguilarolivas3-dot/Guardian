# detectors/join_leave.py
import time
from db import add_alert


def check_join(member):
    guild = member.guild
    account_age_days = (time.time() - member.created_at.timestamp()) / 86400

    if account_age_days < 3:
        details = (
            f"New member {member} joined with a very new account "
            f"({account_age_days:.2f} days old)."
        )
        add_alert(
            guild_id=guild.id,
            user_id=member.id,
            alert_type="new_account_join",
            details=details,
        )
