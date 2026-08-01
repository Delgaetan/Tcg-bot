import discord
from discord import app_commands
from discord.ext import commands
import asyncio

import database as db
import cards_manager as cm

DECK_SIZE = 5


class ActiveCard:
    """Représente une carte en combat (avec ses PV actuels, distincts de ses PV de base)."""
    def __init__(self, card_data):
        self.id = card_data["id"]
        self.name = card_data["name"]
        self.atk = card_data["atk"]
        self.defense = card_data["def"]
        self.max_hp = card_data["hp"]
        self.hp = card_data["hp"]

    @property
    def is_alive(self):
        return self.hp > 0


class Fighter:
    def __init__(self, user: discord.User, deck_ids: list):
        self.user = user
        self.cards = [ActiveCard(cm.get_card(cid)) for cid in deck_ids]
        self.index = 0

    @property
    def active(self):
        return self.cards[self.index] if self.index < len(self.cards) else None

    def next_alive_index(self):
        for i in range(self.index, len(self.cards)):
            if self.cards[i].is_alive:
                return i
        return None

    @property
    def has_cards_left(self):
        return any(c.is_alive for c in self.cards)


class ChallengeView(discord.ui.View):
    """Vue affichée à l'adversaire pour accepter ou refuser un défi."""
    def __init__(self, challenger: discord.User, opponent: discord.User, cog):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.cog = cog
        self.result = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("Ce défi ne t'est pas destiné.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.success, emoji="⚔️")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.result = True
        self.stop()
        await interaction.response.edit_message(content="⚔️ Défi accepté ! Le combat commence...", view=None)

    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.danger, emoji="🚫")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.result = False
        self.stop()
        await interaction.response.edit_message(content="🚫 Défi refusé.", view=None)


class AttackView(discord.ui.View):
    """Vue affichée au joueur dont c'est le tour, avec le bouton Attaquer."""
    def __init__(self, attacker: discord.User, timeout=45):
        super().__init__(timeout=timeout)
        self.attacker = attacker
        self.attacked = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.attacker.id:
            await interaction.response.send_message("Ce n'est pas ton tour.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Attaquer !", style=discord.ButtonStyle.danger, emoji="💥")
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.attacked = True
        self.stop()
        await interaction.response.defer()


def hp_bar(current, maximum, length=10):
    filled = max(0, min(length, round(length * current / maximum)))
    return "🟩" * filled + "⬛" * (length - filled)


class Battle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_battles = set()

    @app_commands.command(name="battle", description="Défie un autre joueur en duel de cartes")
    @app_commands.describe(adversaire="Le joueur que tu veux défier")
    async def battle(self, interaction: discord.Interaction, adversaire: discord.User):
        challenger = interaction.user
        opponent = adversaire

        if opponent.bot or opponent.id == challenger.id:
            await interaction.response.send_message("❌ Choix d'adversaire invalide.", ephemeral=True)
            return

        if challenger.id in self.active_battles or opponent.id in self.active_battles:
            await interaction.response.send_message("❌ Un des deux joueurs est déjà en combat.", ephemeral=True)
            return

        deck1 = await db.get_deck(challenger.id)
        deck2 = await db.get_deck(opponent.id)

        if len(deck1) < DECK_SIZE:
            await interaction.response.send_message(
                f"❌ Ton deck n'est pas complet. Utilise `/deckset` ({DECK_SIZE} cartes).", ephemeral=True
            )
            return
        if len(deck2) < DECK_SIZE:
            await interaction.response.send_message(
                f"❌ Le deck de {opponent.display_name} n'est pas complet.", ephemeral=True
            )
            return

        view = ChallengeView(challenger, opponent, self)
        await interaction.response.send_message(
            f"⚔️ {opponent.mention}, {challenger.mention} te défie en duel ! Acceptes-tu ?",
            view=view
        )
        await view.wait()

        if view.result is not True:
            return

        self.active_battles.add(challenger.id)
        self.active_battles.add(opponent.id)
        try:
            await self.run_battle(interaction, Fighter(challenger, deck1), Fighter(opponent, deck2))
        finally:
            self.active_battles.discard(challenger.id)
            self.active_battles.discard(opponent.id)

    async def run_battle(self, interaction: discord.Interaction, f1: Fighter, f2: Fighter):
        channel = interaction.channel
        turn_fighter, other_fighter = f1, f2

        while f1.has_cards_left and f2.has_cards_left:
            idx1 = f1.next_alive_index()
            idx2 = f2.next_alive_index()
            if idx1 is None or idx2 is None:
                break
            f1.index, f2.index = idx1, idx2

            status = (
                f"**{f1.user.display_name}** — {f1.active.name}\n"
                f"{hp_bar(f1.active.hp, f1.active.max_hp)} {f1.active.hp}/{f1.active.max_hp} PV\n\n"
                f"**{f2.user.display_name}** — {f2.active.name}\n"
                f"{hp_bar(f2.active.hp, f2.active.max_hp)} {f2.active.hp}/{f2.active.max_hp} PV\n\n"
                f"C'est au tour de **{turn_fighter.user.display_name}** ({turn_fighter.active.name}) !"
            )
            view = AttackView(turn_fighter.user)
            msg = await channel.send(status, view=view)
            await view.wait()

            if not view.attacked:
                await channel.send(f"⌛ {turn_fighter.user.display_name} n'a pas réagi à temps. Combat annulé.")
                return

            attacker_card = turn_fighter.active
            defender_card = other_fighter.active
            damage = max(1, attacker_card.atk - defender_card.defense)
            defender_card.hp -= damage

            result_text = f"💥 **{attacker_card.name}** inflige **{damage}** dégâts à **{defender_card.name}** !"
            if not defender_card.is_alive:
                defender_card.hp = 0
                result_text += f"\n☠️ **{defender_card.name}** est K.O. !"
            await channel.send(result_text)

            turn_fighter, other_fighter = other_fighter, turn_fighter
            await asyncio.sleep(1)

        winner = f1 if f1.has_cards_left else f2
        loser = f2 if f1.has_cards_left else f1

        reward = 50
        await db.update_coins(winner.user.id, reward)
        await channel.send(
            f"🏆 **{winner.user.display_name}** remporte le duel face à **{loser.user.display_name}** "
            f"et gagne **{reward}** pièces !"
        )


async def setup(bot):
    await bot.add_cog(Battle(bot))
