from db import add_signal
import time

def check_join(member):
    account_age_days = (time.time() - member.created_at.timestamp()) / 86400
    if account_age_days < 7:
        add_signal(member.guild.id, member.id, "new_account")
