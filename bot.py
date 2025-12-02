import os
import discord
from discord.ext import commands

from detectors.reaction_patterns import check_reaction
from detectors.join_leave import check_join
from detectors.spam_language import check_message
from db import get_recent_signals
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def home():
    return "Guardian is running"

def run_web():
    app.run(host="0.0.0.0", port=10000)

Thread(target=run_web, daemon=True).start()

# ---------------- CONFIG ----------------
OWNER_ID = 1382858887786528803

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- EVENTS ----------------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} | Connected to {len(bot.guilds)} servers")

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
    if user.bot or not reaction.message.guild:
        return

    # You’ll refine this later
    reaction_time_ms = 100

    await check_reaction(reaction, user, reaction_time_ms)

    signals = get_recent_signals(
        reaction.message.guild.id,
        user.id
    )

    # Threshold trigger
    if len(signals) >= 5:
        owner = await bot.fetch_user(OWNER_ID)
        await owner.send(
            "⚠️ **Possible Automation Detected**\n"
            f"User: **{user}** (`{user.id}`)\n"
            f"Server: **{reaction.message.guild.name}**\n"
            f"Signals (last hour): `{len(signals)}`"
        )

# ---------------- START BOT ----------------

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN not set!")

bot.run(TOKEN)
