import discord
from discord.ext import commands
from detectors.reaction_patterns import check_reaction
from detectors.join_leave import check_join
from detectors.spam_language import check_message
from db import get_recent_signals

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

OWNER_ID = 1382858887786528803


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.event
async def on_member_join(member):
    check_join(member)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    check_message(message)
    await bot.process_commands(message)


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    reaction_time_ms = 100  # later you measure this properly
    await check_reaction(reaction, user, reaction_time_ms)

    signals = get_recent_signals(reaction.message.guild.id, user.id)

    if len(signals) >= 5:
        owner = await bot.fetch_user(OWNER_ID)
        await owner.send(
            f"⚠️ Possible automation detected\n"
            f"User: {user}\n"
            f"Server: {reaction.message.guild.name}\n"
            f"Signals: {signals}"
        )
