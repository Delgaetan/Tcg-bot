import discord
from discord import app_commands
from discord.ext import commands

import database as db
import cards_manager as cm


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reloadcards", description="[Admin] Recharge cards.json sans redémarrer le bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def reloadcards(self, interaction: discord.Interaction):
        try:
            cm.load_cards()
            await interaction.response.send_message(
                f"✅ Cartes rechargées : {len(cm.all_cards())} cartes chargées.", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

    @app_commands.command(name="givecard", description="[Admin] Donne une carte à un joueur")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(joueur="Le joueur", nom="Nom de la carte", quantite="Quantité (défaut 1)")
    async def givecard(self, interaction: discord.Interaction, joueur: discord.User, nom: str, quantite: int = 1):
        match = None
        for card in cm.all_cards().values():
            if card["name"].lower() == nom.lower():
                match = card
                break
        if not match:
            await interaction.response.send_message(f"❌ Carte inconnue : {nom}", ephemeral=True)
            return

        await db.add_card_to_inventory(joueur.id, match["id"], quantite)
        await interaction.response.send_message(
            f"✅ {quantite}x **{match['name']}** donné(e) à {joueur.display_name}."
        )

    @app_commands.command(name="givecoins", description="[Admin] Donne des pièces à un joueur")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(joueur="Le joueur", montant="Nombre de pièces")
    async def givecoins(self, interaction: discord.Interaction, joueur: discord.User, montant: int):
        await db.update_coins(joueur.id, montant)
        await interaction.response.send_message(f"✅ {montant} pièces données à {joueur.display_name}.")

    @givecard.error
    @givecoins.error
    @reloadcards.error
    async def admin_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("❌ Réservé aux administrateurs.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Erreur : {error}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Admin(bot))
