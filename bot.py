# bot.py — Guardian Safety / commuity health Bot

# ===================== IMPORTS =====================
import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
from flask import Flask
from threading import Thread
import datetime

# ===================== CONFIG =====================
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 1382858887786528803

SUPPORT_SERVER = "https://discord.gg/DSpz2pkZYN"
TOS_LINK = "https://github.com/angelaguilarolivas3-dot/Guardian/blob/main/docs/tos.md"
PRIVACY_LINK = "https://github.com/angelaguilarolivas3-dot/Guardian/blob/main/docs/privacy.md"

# ===================== FLASK (RENDER UPTIME) =====================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()

# ===================== DATABASE =====================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS warns (
    guild_id INTEGER,
    user_id INTEGER,
    count INTEGER DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS log_channels (
    guild_id INTEGER PRIMARY KEY,
    channel_id INTEGER
)
""")

conn.commit()

# ===================== BOT SETUP =====================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ===================== LOGGING HELPER =====================
async def send_log(guild: discord.Guild, embed: discord.Embed):
    cursor.execute(
        "SELECT channel_id FROM log_channels WHERE guild_id = ?",
        (guild.id,)
    )
    row = cursor.fetchone()
    if not row:
        return

    channel = guild.get_channel(row[0])
    if not channel:
        return

    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        print("❌ Missing permissions to send logs")

# ===================== EVENTS =====================
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ===================== /HELP =====================
@tree.command(name="help", description="Show command list")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛡 Guardian Bot — Help",
        description="Moderation & community safety bot",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="🧑‍⚖️ Moderation",
        value="""
`/warn <user> <reason>`
`/warnings <user>`
`/kick <user> <reason>`
`/ban <user> <reason>`
`/timeout <user> <minutes>`
""",
        inline=False
    )

    embed.add_field(
        name="⚙️ Setup",
        value="`/setlogchannel <channel>`",
        inline=False
    )

    embed.add_field(
        name="📜 Legal",
        value=f"[Terms of Service]({TOS_LINK})\n[Privacy Policy]({PRIVACY_LINK})",
        inline=False
    )

    embed.add_field(
        name="🛠 Support",
        value=f"[Join Support Server]({SUPPORT_SERVER})",
        inline=False
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ===================== /SETLOGCHANNEL =====================
@tree.command(name="setlogchannel", description="Set moderation log channel")
@app_commands.checks.has_permissions(administrator=True)
async def setlogchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    cursor.execute(
        "INSERT OR REPLACE INTO log_channels VALUES (?, ?)",
        (interaction.guild.id, channel.id)
    )
    conn.commit()

    await interaction.response.send_message(
        f"✅ Log channel set to {channel.mention}",
        ephemeral=True
    )

# ===================== /WARN =====================
@tree.command(name="warn", description="Warn a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    cursor.execute(
        "SELECT count FROM warns WHERE guild_id = ? AND user_id = ?",
        (interaction.guild.id, member.id)
    )
    row = cursor.fetchone()
    count = (row[0] if row else 0) + 1

    cursor.execute(
        "INSERT OR REPLACE INTO warns VALUES (?, ?, ?)",
        (interaction.guild.id, member.id, count)
    )
    conn.commit()

    embed = discord.Embed(
        title="⚠️ Member Warned",
        color=discord.Color.orange(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="Moderator", value=interaction.user.mention)
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Total Warns", value=str(count))

    await interaction.response.send_message(embed=embed, ephemeral=True)
    await send_log(interaction.guild, embed)

# ===================== /WARNINGS =====================
@tree.command(name="warnings", description="View warnings")
@app_commands.checks.has_permissions(moderate_members=True)
async def warnings(interaction: discord.Interaction, member: discord.Member):
    cursor.execute(
        "SELECT count FROM warns WHERE guild_id = ? AND user_id = ?",
        (interaction.guild.id, member.id)
    )
    row = cursor.fetchone()
    count = row[0] if row else 0

    embed = discord.Embed(
        title="📋 Warning Count",
        description=f"{member.mention} has **{count} warnings**.",
        color=discord.Color.yellow()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ===================== /KICK =====================
@tree.command(name="kick", description="Kick a member")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str):
    await member.kick(reason=reason)

    embed = discord.Embed(
        title="👢 Member Kicked",
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="User", value=member)
    embed.add_field(name="Moderator", value=interaction.user)
    embed.add_field(name="Reason", value=reason)

    await interaction.response.send_message(embed=embed, ephemeral=True)
    await send_log(interaction.guild, embed)

# ===================== /BAN =====================
@tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str):
    await member.ban(reason=reason)

    embed = discord.Embed(
        title="🔨 Member Banned",
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="User", value=member)
    embed.add_field(name="Moderator", value=interaction.user)
    embed.add_field(name="Reason", value=reason)

    await interaction.response.send_message(embed=embed, ephemeral=True)
    await send_log(interaction.guild, embed)

# ===================== /TIMEOUT =====================
@tree.command(name="timeout", description="Timeout a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str):
    until = datetime.timedelta(minutes=minutes)
    await member.timeout(until, reason=reason)

    embed = discord.Embed(
        title="⏳ Member Timed Out",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="User", value=member)
    embed.add_field(name="Moderator", value=interaction.user)
    embed.add_field(name="Duration", value=f"{minutes} minutes")
    embed.add_field(name="Reason", value=reason)

    await interaction.response.send_message(embed=embed, ephemeral=True)
    await send_log(interaction.guild, embed)

# ===================== RUN =====================
if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN missing")

bot.run(TOKEN)
