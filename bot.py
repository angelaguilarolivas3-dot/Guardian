# bot.py — Guardian Safety / commuity health Bot

import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands

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

# ---------- CONFIG ----------
OWNER_ID = 1382858887786528803  # so the owner can do owner commands

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True


class GuardianBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",  # not really used, but it works
            intents=intents,
        )

    async def setup_hook(self):
        # Global sync for all servers the bot is in
        await self.tree.sync()
        print("✅ Slash commands synced globally.")


bot = GuardianBot()


# ---------- EVENTS ----------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_member_join(member: discord.Member):
    # Run join detector
    check_join(member)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Run spam / language detector
    check_message(message)

    # Must call this or slash commands won’t work with message events
    await bot.process_commands(message)


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return

    # TODO: measure actual reaction time; for now, use a dummy value
    reaction_time_ms = 100.0
    await check_reaction(reaction, user, reaction_time_ms)


# ---------- MODERATION SLASH COMMANDS ----------

def admin_only():
    """Reusable admin permission check decorator."""
    return app_commands.checks.has_permissions(administrator=True)


@bot.tree.command(name="warn", description="Warn a member")
@admin_only()
@app_commands.describe(
    member="Member to warn",
    reason="Reason for the warning (optional)"
)
async def warn(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided."
):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return

    add_warning(
        guild_id=guild.id,
        user_id=member.id,
        mod_id=interaction.user.id,
        reason=reason,
    )

    count = get_warning_count(guild.id, member.id)

    embed = discord.Embed(
        title="⚠️ Member Warned",
        color=discord.Color.orange()
    )
    embed.add_field(name="Member", value=member.mention, inline=True)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(text=f"This user now has {count} warning(s).")

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="warnings", description="See how many warnings a member has")
@admin_only()
@app_commands.describe(member="Member to check")
async def warnings(interaction: discord.Interaction, member: discord.Member):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return

    count = get_warning_count(guild.id, member.id)
    rows = get_warnings_for_user(guild.id, member.id)

    if count == 0:
        await interaction.response.send_message(
            f"✅ {member.mention} has no warnings.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=f"⚠️ Warnings for {member}",
        color=discord.Color.orange()
    )
    embed.add_field(name="Total Warnings", value=str(count), inline=False)

    for idx, (mod_id, reason, ts) in enumerate(rows, start=1):
        embed.add_field(
            name=f"#{idx} — by <@{mod_id}>",
            value=reason or "No reason provided.",
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="resetwarns", description="Reset warnings (member or entire server)")
@admin_only()
@app_commands.describe(
    member="Member whose warnings to reset (leave empty to reset entire server)"
)
async def resetwarns(interaction: discord.Interaction, member: discord.Member | None = None):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return

    if member is not None:
        clear_warnings_for_user(guild.id, member.id)
        await interaction.response.send_message(
            f"✅ Cleared warnings for {member.mention}.",
            ephemeral=True
        )
    else:
        clear_warnings_for_guild(guild.id)
        await interaction.response.send_message(
            "✅ Cleared **all warnings** for this server.",
            ephemeral=True
        )


@bot.tree.command(name="kick", description="Kick a member")
@admin_only()
@app_commands.describe(
    member="Member to kick",
    reason="Reason for kick"
)
async def kick(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided."
):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return

    try:
        await member.kick(reason=reason)
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to kick that member.", ephemeral=True)
        return

    await interaction.response.send_message(
        f"👢 {member.mention} was kicked.\n**Reason:** {reason}"
    )


@bot.tree.command(name="ban", description="Ban a member")
@admin_only()
@app_commands.describe(
    member="Member to ban",
    reason="Reason for ban"
)
async def ban(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided."
):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return

    try:
        await member.ban(reason=reason)
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to ban that member.", ephemeral=True)
        return

    await interaction.response.send_message(
        f"🔨 {member.mention} was banned.\n**Reason:** {reason}"
    )


# ---------- ALERTS COMMAND ----------

@bot.tree.command(name="alerts", description="View recent safety alerts")
@admin_only()
async def alerts(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return

    rows = get_recent_alerts_for_guild(guild.id, limit=15)

    if not rows:
        await interaction.response.send_message(
            "✅ No recent alerts for this server.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=f"🛡 Safety Alerts — {guild.name}",
        description="Recent signals from Guardian's detectors.",
        color=discord.Color.blurple()
    )

    for user_id, alert_type, details, ts in rows:
        user_mention = f"<@{user_id}>"
        short_details = (details[:150] + "…") if details and len(details) > 150 else (details or "No extra details.")
        embed.add_field(
            name=f"{alert_type} — {user_mention}",
            value=short_details,
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------- ERROR HANDLER FOR APP COMMANDS ----------

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.",
            ephemeral=True
        )
    else:
        # Log and show generic error
        print(f"[AppCommandError] {error}")
        try:
            await interaction.response.send_message(
                "❌ Something went wrong while executing that command.",
                ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "❌ Something went wrong while executing that command.",
                ephemeral=True
            )


# ---------- RUN BOT ----------

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set!")

bot.run(TOKEN)
