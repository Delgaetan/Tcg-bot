"""
Gère la lecture du fichier data/cards.json.
Pour ajouter/modifier une carte : édite ce fichier JSON, puis tape
/reloadcards dans Discord (pas besoin de redémarrer le bot).
"""
import json
import os
import random

CARDS_PATH = os.path.join(os.path.dirname(__file__), "data", "cards.json")

_cache = {"cards": {}, "rarity_weights": {}, "pack_cost": 100}


def load_cards():
    with open(CARDS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    _cache["cards"] = {c["id"]: c for c in data["cards"]}
    _cache["rarity_weights"] = data.get("rarity_weights", {})
    _cache["pack_cost"] = data.get("pack_cost", 100)
    return _cache


def get_card(card_id: str):
    return _cache["cards"].get(card_id)


def all_cards():
    return _cache["cards"]


def pack_cost():
    return _cache["pack_cost"]


def draw_random_card():
    """Tire une carte au hasard en respectant les probabilités de rareté définies dans cards.json"""
    rarities = list(_cache["rarity_weights"].keys())
    weights = list(_cache["rarity_weights"].values())
    chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]

    candidates = [c for c in _cache["cards"].values() if c["rarity"] == chosen_rarity]
    if not candidates:
        # fallback si aucune carte de cette rareté n'existe
        candidates = list(_cache["cards"].values())
    return random.choice(candidates)


# Charge les cartes au démarrage du module
load_cards()
