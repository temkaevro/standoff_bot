import logging
from database import add_weapon, add_skin, add_sticker, init_db

# Здесь мы будем заполнять справочники из твоего большого списка.
# Пока добавим только несколько примеров для теста.
# Позже я помогу тебе импортировать полный список.

def seed_weapons_and_skins():
    # Пример: оружие и скины
    weapons_skins = {
        "AKR": ["TreasureHunter", "Tiger", "Sport", "Necromancer", "Carbon"],
        "M4": ["Lizard", "Samurai", "Predator", "Necromancer", "Tiger", "Pro", "GrandPrix"],
        "Deagle": ["CaptainMorgan", "Blood", "Predator", "RedDragon", "Winner", "DragonGlass", "Thunder"],
        # Добавим ещё несколько из твоего списка позже
    }
    for weapon, skins in weapons_skins.items():
        add_weapon(weapon)
        for skin in skins:
            add_skin(weapon, skin)

def seed_stickers():
    # Пример наклеек
    stickers = [
        "Sticker_GoldSkull", "Sticker_Punisher", "Sticker_MadBat", "Sticker_InfernalSkull",
        "Sticker_Ghoul", "Sticker_Batrider", "Sticker_GangstaPumpkin", "Sticker_Snot"
    ]
    for sticker in stickers:
        add_sticker(sticker, "Стандартная")  # редкость можно потом уточнить

def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    seed_weapons_and_skins()
    seed_stickers()
    logging.info("Seed data completed.")

if __name__ == "__main__":
    main()
