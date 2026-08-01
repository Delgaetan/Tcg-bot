import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone

import database as db

DAILY_AMOUNT = 100
DAILY_COOLDOWN_HOURS = 20


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="solde", description="Voir ton nombre de pièces")
    async def solde(self, interaction: discord.Interaction):
        player = await db.get_player(interaction.user.id)
        await interaction.response.send_message(
            f"💰 Tu as **{player['coins']}** pièces."
        )

    @app_commands.command(name="daily", description="Récupère ta récompense quotidienne")
    async def daily(self, interaction: discord.Interaction):
        player = await db.get_player(interaction.user.id)
        now = datetime.now(timezone.utc)

        if player["last_daily"]:
            last = datetime.fromisoformat(player["last_daily"])
            elapsed = now - last
            if elapsed < timedelta(hours=DAILY_COOLDOWN_HOURS):
                remaining = timedelta(hours=DAILY_COOLDOWN_HOURS) - elapsed
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes = remainder // 60
                await interaction.response.send_message(
                    f"⏳ Tu as déjà récupéré ta récompense. Reviens dans **{hours}h{minutes:02d}**.",
                    ephemeral=True
                )
                return

        await db.update_coins(interaction.user.id, DAILY_AMOUNT)
        await db.set_last_daily(interaction.user.id, now.isoformat())
        await interaction.response.send_message(
            f"🎁 Tu as reçu **{DAILY_AMOUNT}** pièces ! Reviens dans {DAILY_COOLDOWN_HOURS}h."
        )


async def setup(bot):
    await bot.add_cog(Economy(bot))
