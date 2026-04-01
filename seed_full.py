import logging
import sqlite3
from database import get_connection, init_db, add_weapon, add_skin, add_sticker

logging.basicConfig(level=logging.INFO)

# === Список оружия и скинов (из твоего файла) ===
# Здесь я приведу только начало, чтобы база не была пустой.
# Позже мы добавим полный список, но для теста хватит основных.
weapons_skins = {
    "G22": ["PixelCamouflage", "Nest", "Pattern", "Inferno", "FrostWyrm", "Relic", "Starfall", "Monster", "WhiteCarbon", "Carbon", "YellowLine", "Scale", "Casual", "SteelGrip", "LionLord", "Haunt", "Flock", "Briar", "Impulse", "Twilight", "ReindeerSweater", "FlorDeMuertos"],
    "USP": ["Genesis", "2Years", "2YearsRed", "Fiend", "Pisces", "New1", "Geometric", "Line", "Yellow", "Chameleon", "Stickerbomb", "PurpleCamo", "DigitalBurst", "Hunter02", "Griffin", "MirageMenace", "Corrode", "Ghosts", "Suture", "Rainforest", "CelestialTiger", "Hologram", "Horror"],
    "Deagle": ["CaptainMorgan", "Blood", "Predator", "RedDragon", "Winner", "DragonGlass", "Thunder", "Ace", "Pro", "Orochi", "Mafia", "Piranha", "Glory", "Infection", "DustDevil", "Aureate", "FusionCore", "VioletFlame", "Eclipse", "Vermilion", "Gambit", "Blossom", "WildFlower", "JadeStone"],
    "AKR": ["TreasureHunter", "Tiger", "Sport", "Necromancer", "Carbon", "2Years", "Worm", "New2", "Scale", "Noname", "TagKing", "Scylla", "SteelGrip", "Evolution", "MirageMenace", "Icewing", "Vermilion", "Orchid", "LaReina", "Sketch", "Genesis"],
    "M4": ["Lizard", "Samurai", "Predator", "Necromancer", "Tiger", "Pro", "GrandPrix", "New2", "Demon", "Noname", "Minotaur", "Sunset", "Powergame", "Paladin", "NKai", "Flock", "Ironclad", "Kachi", "BulletsAndRoses", "RetroFilm", "Flex"],
    "M4A1": ["Bubblegum", "Kitsune", "KINGv703", "YearOfTheTiger", "Sour", "Mermaid", "Serpent", "Ferocity", "Stainless", "SparklingGaze", "Overdrive", "Impact", "Tempest", "PawPaw", "PixelFlakes", "TreasureHunter", "JadeStone"],
    "AWM": ["Sport", "Phoenix", "Gear", "Scratch", "SportV2", "Genesis", "2YearsRed", "TreasureHunter", "Dragon", "BOOM", "Elevation", "Stickerbomb", "Poseidon", "ColdBlooded", "Kings", "Xenoguard", "Nebula", "FestalWrap", "HoheiTaisho", "Spectral", "Sylvan", "Ravage", "Moonstone", "Vampire", "JadeStone"],
    "MP7": ["Offroad", "Arcade", "2Years", "2YearsRed", "New1", "Revival", "Graffity", "Monkey", "Blizzard", "Empire", "Stickerbomb", "Dawn", "SpaceBlaster", "Precision", "FestalWrap", "Fright", "Ridge", "R1NA", "MagmaTrail", "Rebellion"],
    "P90": ["Radiation", "Ghoul", "Fury", "Pilot", "Jungle", "Samurai", "IronWill", "RONINmk9", "Z50FUJIN", "Oops", "DragonFlame", "Nebula", "Revenant", "FusionCore", "ColdLead", "Unstoppable", "Noir", "Oracle", "Foxfire", "Hologram", "Horizon"],
    "UMP45": ["Cyberpunk", "Pixel", "Shark", "Winged", "Beast", "Iron", "Cerberus", "Gas", "WhiteCarbon", "Geometric", "Spirit", "4Years", "PeacefulDream", "Warchief", "Arid", "Industrial", "Heatwave", "Smelter", "Leviathan"]
}

def seed_full():
    init_db()
    
    # Добавляем оружие и скины
    for weapon, skins in weapons_skins.items():
        add_weapon(weapon)
        for skin in skins:
            add_skin(weapon, skin)
            logging.info(f"Added: {weapon} - {skin}")
    
    # Добавляем основные наклейки из твоего списка (первые 50 для теста)
    stickers_list = [
        "Sticker_GoldSkull", "Sticker_Punisher", "Sticker_MadBat", "Sticker_InfernalSkull",
        "Sticker_Ghoul", "Sticker_Batrider", "Sticker_GangstaPumpkin", "Sticker_Snot",
        "Sticker_Devilish", "Sticker_HurryGhost", "Sticker_Feed", "Sticker_Anticamper",
        "Sticker_Boom", "Sticker_BloodyClown", "Sticker_Ghosty", "Sticker_Mummy",
        "Sticker_Rush", "Sticker_EvilPumpkin", "Sticker_Zombie", "Sticker_Dracula"
    ]
    for sticker in stickers_list:
        add_sticker(sticker, "Стандартная")
    
    logging.info("✅ Seed data completed!")

if __name__ == "__main__":
    seed_full()
