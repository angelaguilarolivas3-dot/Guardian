from db import add_signal

SUSPICIOUS_PHRASES = [
    "dm me",
    "free nitro",
    "trust me",
    "verify here",
    "onlyfans",
    "pornhuh"
]

def check_message(message):
    content = message.content.lower()
    for phrase in SUSPICIOUS_PHRASES:
        if phrase in content:
            add_signal(
                message.guild.id,
                message.author.id,
                "suspicious_phrase"
            )
