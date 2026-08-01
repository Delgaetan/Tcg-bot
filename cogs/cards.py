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

DECK_SIZE = 5


class Cards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="collection", description="Voir toutes tes cartes")
    async def collection(self, interaction: discord.Interaction):
        inventory = await db.get_inventory(interaction.user.id)
        if not inventory:
            await interaction.response.send_message(
                "Tu n'as encore aucune carte. Essaie `/openpack` !", ephemeral=True
            )
            return

        lines = []
        for card_id, qty in inventory.items():
            card = cm.get_card(card_id)
            if not card:
                continue
            emoji = RARITY_EMOJI.get(card["rarity"], "▫️")
            lines.append(f"{emoji} **{card['name']}** x{qty} — PV {card['hp']} / ATK {card['atk']} / DEF {card['def']}")

        embed = discord.Embed(
            title=f"📚 Collection de {interaction.user.display_name}",
            description="\n".join(lines),
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="carte", description="Voir le détail d'une carte")
    @app_commands.describe(nom="Nom de la carte")
    async def carte(self, interaction: discord.Interaction, nom: str):
        found = None
        for card in cm.all_cards().values():
            if card["name"].lower() == nom.lower():
                found = card
                break
        if not found:
            await interaction.response.send_message("❌ Carte introuvable.", ephemeral=True)
            return

        emoji = RARITY_EMOJI.get(found["rarity"], "▫️")
        embed = discord.Embed(
            title=f"{emoji} {found['name']}",
            description=found.get("description", ""),
            color=discord.Color.purple()
        )
        embed.add_field(name="Rareté", value=found["rarity"], inline=True)
        embed.add_field(name="PV", value=str(found["hp"]), inline=True)
        embed.add_field(name="ATK", value=str(found["atk"]), inline=True)
        embed.add_field(name="DEF", value=str(found["def"]), inline=True)
        if found.get("image_url"):
            embed.set_image(url=found["image_url"])
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="deck", description="Voir ton deck actuel")
    async def deck(self, interaction: discord.Interaction):
        deck_ids = await db.get_deck(interaction.user.id)
        if not deck_ids:
            await interaction.response.send_message(
                "Ton deck est vide. Utilise `/deckset` pour le composer.", ephemeral=True
            )
            return
        lines = []
        for cid in deck_ids:
            card = cm.get_card(cid)
            if card:
                emoji = RARITY_EMOJI.get(card["rarity"], "▫️")
                lines.append(f"{emoji} **{card['name']}** — PV {card['hp']} / ATK {card['atk']} / DEF {card['def']}")
        embed = discord.Embed(
            title=f"⚔️ Deck de {interaction.user.display_name}",
            description="\n".join(lines),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="deckset", description=f"Compose ton deck ({DECK_SIZE} cartes que tu possèdes)")
    @app_commands.describe(
        carte1="Nom de la carte 1", carte2="Nom de la carte 2",
        carte3="Nom de la carte 3", carte4="Nom de la carte 4",
        carte5="Nom de la carte 5"
    )
    async def deckset(self, interaction: discord.Interaction, carte1: str, carte2: str,
                       carte3: str, carte4: str, carte5: str):
        noms = [carte1, carte2, carte3, carte4, carte5]
        inventory = await db.get_inventory(interaction.user.id)

        card_ids = []
        for nom in noms:
            match = None
            for card in cm.all_cards().values():
                if card["name"].lower() == nom.lower():
                    match = card
                    break
            if not match:
                await interaction.response.send_message(f"❌ Carte inconnue : **{nom}**", ephemeral=True)
                return
            if inventory.get(match["id"], 0) < 1:
                await interaction.response.send_message(f"❌ Tu ne possèdes pas **{match['name']}**.", ephemeral=True)
                return
            card_ids.append(match["id"])

        await db.set_deck(interaction.user.id, card_ids)
        await interaction.response.send_message(f"✅ Deck mis à jour avec : {', '.join(noms)}")


async def setup(bot):
    await bot.add_cog(Cards(bot))
