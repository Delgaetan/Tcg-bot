# Mon Bot TCG Discord

Bot de trading card game 100% personnalisable : toi seul décides des cartes,
de leurs stats, des raretés et des probabilités de pack.

## Ce que le bot sait faire

- `/openpack` — ouvrir un pack de cartes aléatoire (coût en pièces)
- `/collection` — voir toutes ses cartes
- `/carte <nom>` — voir le détail d'une carte
- `/deckset` — composer son deck de combat (5 cartes)
- `/deck` — voir son deck actuel
- `/battle @joueur` — défier un joueur en duel tour par tour
- `/daily` — récupérer sa récompense quotidienne de pièces
- `/solde` — voir son nombre de pièces
- `/givecard`, `/givecoins`, `/reloadcards` — commandes admin

## Étape 1 — Créer l'application Discord

1. Va sur https://discord.com/developers/applications
2. Clique **New Application**, donne-lui un nom
3. Dans l'onglet **Bot**, clique **Reset Token** puis copie le token (garde-le secret !)
4. Toujours dans **Bot**, active **Message Content Intent**
5. Dans **OAuth2 → URL Generator** :
   - Coche `bot` et `applications.commands`
   - Permissions : `Send Messages`, `Embed Links`, `Use Slash Commands`
   - Copie l'URL générée en bas, ouvre-la dans ton navigateur pour inviter le bot sur ton serveur

## Étape 2 — Ajouter tes cartes (aucun code requis)

Ouvre `data/cards.json`. Chaque carte est un bloc comme celui-ci :

```json
{
  "id": "nouvelle-carte",
  "name": "Nom Affiché",
  "hp": 50,
  "atk": 10,
  "def": 5,
  "rarity": "rare",
  "image_url": "",
  "description": "Une description sympa."
}
```

- `id` : identifiant unique, sans espace ni majuscule (ex: `flamurex`)
- `rarity` : doit correspondre à une des clés dans `rarity_weights`
- `rarity_weights` : les probabilités relatives de tirage dans un pack
- `pack_cost` : prix d'un pack en pièces

Après modification, tape `/reloadcards` dans Discord (en tant qu'admin) —
pas besoin de redémarrer le bot.

## Étape 3 — Lancer le bot en local (pour tester)

```bash
pip install -r requirements.txt
cp .env.example .env
# Colle ton token dans le fichier .env
python bot.py
```

## Étape 4 — Héberger gratuitement sur Railway (24/7)

1. Crée un compte sur https://railway.app (gratuit, connexion via GitHub)
2. Mets ce dossier dans un dépôt GitHub (public ou privé)
3. Sur Railway : **New Project → Deploy from GitHub repo** → sélectionne ton dépôt
4. Dans l'onglet **Variables** du projet Railway, ajoute :
   - `DISCORD_TOKEN` = ton token (le même que dans `.env`)
5. Railway détecte le `Procfile` et lance `python bot.py` automatiquement
6. Le bot tourne en continu — pour ajouter des cartes plus tard, modifie
   `data/cards.json` sur GitHub, Railway redéploie tout seul

⚠️ Le tier gratuit de Railway offre un crédit mensuel limité (largement
suffisant pour un petit bot Discord). Si tu dépasses, tu peux passer sur
Oracle Cloud Free Tier (gratuit à vie, un peu plus technique à configurer).

## Prochaines étapes possibles

- Ajouter des effets spéciaux aux cartes (soin, poison, esquive...)
- Système de trading entre joueurs
- Classement (leaderboard) des meilleurs combattants
- Images personnalisées pour chaque carte (`image_url`)

Dis-moi quand tu veux ajouter une de ces fonctionnalités, je m'en occupe.
