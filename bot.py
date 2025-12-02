# bot.py — Guardian Safety / commuity health Bot

import os
import time
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread

from detectors.reaction_patterns import check_reaction
from detectors.join_leave import check_join
from detectors.spam_language import check_message

from db import (
    add_warning,
    get_warning_count,
    get_warnings_for_user,
    clear_warnings_for_user,
    clear_warnings_for_guild,
    get_recent_alerts_for_guild,
)

# ===================== RENDER WEB KEEP-ALIVE =====================
app = Flask(__name__)

@app.route("/")
def home():
    return "Guardian bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web, daemon=True).start()

# ===================== BOT SETUP =====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

LOG_CHANNELS = {}  # guild_id -> channel_id


# ===================== READY =====================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Guardian online as {bot.user}")


# ===================== EVENTS =====================
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

    reaction_time_ms = 120  # placeholder
    await check_reaction(reaction, user, reaction_time_ms)

    guild_id = reaction.message.guild.id
    alerts = get_recent_alerts_for_guild(guild_id, 1)

    if alerts and guild_id in LOG_CHANNELS:
        channel = bot.get_channel(LOG_CHANNELS[guild_id])
        if channel:
            u, t, d, ts = alerts[0]
            await channel.send(
                f"⚠️ **Guardian Alert**\n"
                f"User: <@{u}>\n"
                f"Type: `{t}`\n"
                f"Details: {d}"
            )


# ===================== /HELP =====================
@bot.tree.command(name="help", description="Show Guardian commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛡 Guardian Bot Help",
        description="A community safety & moderation bot designed to keep servers healthy.",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="🛠 Moderation Commands",
        value=(
            "`/warn` – Warn a member\n"
            "`/warnings` – View member warnings\n"
            "`/resetwarns` – Clear warnings\n"
            "`/kick` – Kick a member\n"
            "`/ban` – Ban a member"
        ),
        inline=False
    )

    embed.add_field(
        name="🚨 Safety & Monitoring",
        value=(
            "`/alerts` – View recent safety alerts\n"
            "Guardian automatically detects suspicious behavior."
        ),
        inline=False
    )

    embed.add_field(
        name="⚙️ Configuration",
        value="`/setlogchannel` – Set where alerts are sent *(Admin only)*",
        inline=False
    )

    embed.add_field(
        name="📜 Legal",
        value=(
            "[📄 Terms of Service](https://github.com/angelaguilarolivas3-dot/Guardian/blob/main/docs/tos.md)\n"
            "[🔒 Privacy Policy](https://github.com/angelaguilarolivas3-dot/Guardian/blob/main/docs/privacy.md)"
        ),
        inline=False
    )

    embed.add_field(
        name="🆘 Support Server",
        value="[Join the Guardian Support Server](https://discord.gg/DSpz2pkZYN)",
        inline=False
    )

    embed.set_footer(text="Guardian • Safety first • Built for the Discord Buildathon")

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ===================== /SETLOGCHANNEL =====================
@bot.tree.command(name="setlogchannel", description="Set channel for Guardian alerts (admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def setlogchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    LOG_CHANNELS[interaction.guild.id] = channel.id
    await interaction.response.send_message(
        f"✅ Alerts will be logged in {channel.mention}",
        ephemeral=True
    )


# ===================== WARN =====================
@bot.tree.command(name="warn", description="Warn a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(interaction, member: discord.Member, reason: str = "No reason provided"):
    add_warning(interaction.guild.id, member.id, interaction.user.id, reason)
    count = get_warning_count(interaction.guild.id, member.id)

    await interaction.response.send_message(
        f"⚠️ {member.mention} warned.\n"
        f"Reason: {reason}\n"
        f"Total warns: **{count}**"
    )


# ===================== WARNINGS =====================
@bot.tree.command(name="warnings", description="View member warnings")
@app_commands.checks.has_permissions(moderate_members=True)
async def warnings(interaction, member: discord.Member):
    count = get_warning_count(interaction.guild.id, member.id)
    if count == 0:
        await interaction.response.send_message("✅ No warnings.", ephemeral=True)
        return

    rows = get_warnings_for_user(interaction.guild.id, member.id)

    embed = discord.Embed(
        title=f"Warnings for {member}",
        color=discord.Color.orange()
    )

    for mod_id, reason, ts in rows:
        embed.add_field(
            name=f"By <@{mod_id}>",
            value=reason,
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ===================== RESET WARNS =====================
@bot.tree.command(name="resetwarns", description="Reset warnings")
@app_commands.checks.has_permissions(moderate_members=True)
async def resetwarns(interaction, member: discord.Member | None = None):
    if member:
        clear_warnings_for_user(interaction.guild.id, member.id)
        await interaction.response.send_message(f"✅ Cleared warnings for {member.mention}")
    else:
        clear_warnings_for_guild(interaction.guild.id)
        await interaction.response.send_message("✅ Cleared all warnings in this server")


# ===================== KICK =====================
@bot.tree.command(name="kick", description="Kick a member")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction, member: discord.Member, reason: str = "No reason"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 {member.mention} kicked.")


# ===================== BAN =====================
@tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    await member.ban(reason=reason)

    await interaction.response.send_message(
        f"🔨 Banned {member.mention}",
        ephemeral=True
    )

    await send_log(
        interaction.guild,
        f"🔨 **Ban**\n"
        f"User: {member}\n"
        f"Moderator: {interaction.user}\n"
        f"Reason: {reason}"
    )

# ===================== ALERTS =====================
@bot.tree.command(name="alerts", description="View safety alerts")
@app_commands.checks.has_permissions(moderate_members=True)
async def alerts(interaction):
    rows = get_recent_alerts_for_guild(interaction.guild.id)

    if not rows:
        await interaction.response.send_message("✅ No recent alerts.", ephemeral=True)
        return

    embed = discord.Embed(title="🛡 Guardian Alerts", color=discord.Color.red())
    for u, t, d, ts in rows:
        embed.add_field(
            name=f"{t} — <@{u}>",
            value=d,
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ===================== RUN =====================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN missing!")

bot.run(TOKEN)
