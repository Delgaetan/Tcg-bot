import discord
from discord import app_commands
from discord.ext import commands

import database as db
import cards_manager as cm

RARITY_EMOJI = {
    "commune": "⚪",
    "rare": "🔵",
    "légendaire": "🟡",
}


class Packs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="openpack", description="Ouvre un pack de cartes")
    async def openpack(self, interaction: discord.Interaction):
        cost = cm.pack_cost()
        player = await db.get_player(interaction.user.id)

        if player["coins"] < cost:
            await interaction.response.send_message(
                f"❌ Il te faut **{cost}** pièces pour ouvrir un pack (tu as {player['coins']}).",
                ephemeral=True
            )
            return

        card = cm.draw_random_card()
        await db.update_coins(interaction.user.id, -cost)
        await db.add_card_to_inventory(interaction.user.id, card["id"], 1)

        emoji = RARITY_EMOJI.get(card["rarity"], "▫️")
        embed = discord.Embed(
            title="🎴 Nouveau pack ouvert !",
            description=f"{emoji} **{card['name']}** ({card['rarity']})",
            color=discord.Color.gold()
        )
        embed.add_field(name="PV", value=str(card["hp"]), inline=True)
        embed.add_field(name="ATK", value=str(card["atk"]), inline=True)
        embed.add_field(name="DEF", value=str(card["def"]), inline=True)
        if card.get("description"):
            embed.add_field(name="Description", value=card["description"], inline=False)
        if card.get("image_url"):
            embed.set_image(url=card["image_url"])

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Packs(bot))
