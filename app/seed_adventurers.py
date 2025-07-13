import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.append('.')
from app.models import Base, Adventurer, AdventurerClass

DATABASE_URL = "sqlite:///./data/db.sqlite"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

adventurer_pool = [
    {"name": "Elira Swiftblade", "adventurer_class": AdventurerClass.FIGHTER},
    {"name": "Borin Stonefist", "adventurer_class": AdventurerClass.DWARF},
    {"name": "Seraphine Dawnstar", "adventurer_class": AdventurerClass.CLERIC},
    {"name": "Milo Underbough", "adventurer_class": AdventurerClass.HOBBIT},
    {"name": "Kael the Ember", "adventurer_class": AdventurerClass.MAGIC_USER},
    {"name": "Lirael Moonshadow", "adventurer_class": AdventurerClass.ELF},
    {"name": "Thaddeus Grim", "adventurer_class": AdventurerClass.FIGHTER},
    {"name": "Fira Quickfoot", "adventurer_class": AdventurerClass.HOBBIT},
    {"name": "Durgan Ironbeard", "adventurer_class": AdventurerClass.DWARF},
    {"name": "Sylwen Starfall", "adventurer_class": AdventurerClass.ELF},
    {"name": "Brother Malric", "adventurer_class": AdventurerClass.CLERIC},
    {"name": "Vespera Nightshade", "adventurer_class": AdventurerClass.MAGIC_USER},
    {"name": "Galen Oakenshield", "adventurer_class": AdventurerClass.FIGHTER},
    {"name": "Pip Bramble", "adventurer_class": AdventurerClass.HOBBIT},
    {"name": "Eldrin Silverleaf", "adventurer_class": AdventurerClass.ELF},
    {"name": "Helga Stonehammer", "adventurer_class": AdventurerClass.DWARF},
    {"name": "Sister Mirabel", "adventurer_class": AdventurerClass.CLERIC},
    {"name": "Tamsin Willow", "adventurer_class": AdventurerClass.MAGIC_USER},
    {"name": "Rurik Axeborn", "adventurer_class": AdventurerClass.FIGHTER},
    {"name": "Nimble Nissa", "adventurer_class": AdventurerClass.HOBBIT},
]

def roll_hp(adventurer_class):
    base = random.randint(1, 6)
    if adventurer_class == AdventurerClass.FIGHTER:
        return base + 1
    return base

def seed():
    db = SessionLocal()
    for adv in adventurer_pool:
        exists = db.query(Adventurer).filter_by(name=adv["name"]).first()
        if not exists:
            hp_max = roll_hp(adv["adventurer_class"])
            adventurer = Adventurer(
                name=adv["name"],
                adventurer_class=adv["adventurer_class"],
                level=1,
                xp=0,
                hp_max=hp_max,
                hp_current=hp_max,
                gold=100,
                is_available=True,
            )
            db.add(adventurer)
    try:
        db.commit()
    except Exception as e:
        print("Error committing to DB:", e)
        db.rollback()
    finally:
        db.close()
    print("Adventurer pool seeded.")

if __name__ == "__main__":
    seed()