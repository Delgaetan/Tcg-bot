import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

import database as db

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

COGS = [
    "cogs.economy",
    "cogs.packs",
    "cogs.cards",
    "cogs.battle",
    "cogs.admin",
]


@bot.event
async def on_ready():
    await db.init_db()
    for cog in COGS:
        try:
            await bot.load_extension(cog)
        except Exception as e:
            print(f"Erreur au chargement de {cog} : {e}")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} commandes slash synchronisées.")
    except Exception as e:
        print(f"Erreur de synchronisation : {e}")
    print(f"✅ Connecté en tant que {bot.user}")


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN manquant. Configure-le dans le fichier .env")
    bot.run(TOKEN)
