import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base, Equipment, Supply, EquipmentType, SupplyType

# Database connection
DATABASE_URL = "sqlite:///./data/db.sqlite"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def seed_equipment_and_supplies():
    """Seed the database with initial equipment and supplies"""
    db = SessionLocal()
    
    try:
        # Check if we already have equipment
        equipment_count = db.query(Equipment).count()
        if equipment_count > 0:
            print(f"Database already has {equipment_count} equipment items. Skipping equipment seeding.")
        else:
            # Weapons
            weapons = [
                {
                    "name": "Longsword",
                    "equipment_type": EquipmentType.WEAPON,
                    "description": "A versatile double-edged sword. Favored by knights and warriors.",
                    "cost": 15,
                    "weight": 3.0,
                    "properties": {"damage": "1d8", "type": "slashing", "versatile": "1d10"}
                },
                {
                    "name": "Shortbow",
                    "equipment_type": EquipmentType.WEAPON,
                    "description": "A simple bow good for hunting and combat.",
                    "cost": 25,
                    "weight": 2.0,
                    "properties": {"damage": "1d6", "type": "piercing", "range": "80/320"}
                },
                {
                    "name": "Dagger",
                    "equipment_type": EquipmentType.WEAPON,
                    "description": "A small knife that can be used for stabbing or throwing.",
                    "cost": 2,
                    "weight": 1.0,
                    "properties": {"damage": "1d4", "type": "piercing", "finesse": True, "light": True, "thrown": "20/60"}
                },
                {
                    "name": "Quarterstaff",
                    "equipment_type": EquipmentType.WEAPON,
                    "description": "A wooden staff that can be wielded with one or two hands.",
                    "cost": 0.2,
                    "weight": 4.0,
                    "properties": {"damage": "1d6", "type": "bludgeoning", "versatile": "1d8"}
                },
                {
                    "name": "Mace",
                    "equipment_type": EquipmentType.WEAPON,
                    "description": "A heavy bludgeoning weapon.",
                    "cost": 5,
                    "weight": 4.0,
                    "properties": {"damage": "1d6", "type": "bludgeoning"}
                }
            ]
            
            # Armor
            armor = [
                {
                    "name": "Leather Armor",
                    "equipment_type": EquipmentType.ARMOR,
                    "description": "Light armor made of tanned hides.",
                    "cost": 10,
                    "weight": 10.0,
                    "properties": {"armor_class": 11, "type": "light"}
                },
                {
                    "name": "Chain Mail",
                    "equipment_type": EquipmentType.ARMOR,
                    "description": "Heavy armor made of interlocking metal rings.",
                    "cost": 75,
                    "weight": 55.0,
                    "properties": {"armor_class": 16, "type": "heavy", "strength_required": 13}
                },
                {
                    "name": "Shield",
                    "equipment_type": EquipmentType.SHIELD,
                    "description": "A wooden or metal shield worn on the arm.",
                    "cost": 10,
                    "weight": 6.0,
                    "properties": {"armor_class_bonus": 2}
                }
            ]
            
            # Magic Items
            magic_items = [
                {
                    "name": "Potion of Healing",
                    "equipment_type": EquipmentType.POTION,
                    "description": "A red potion that restores health when consumed.",
                    "cost": 50,
                    "weight": 0.5,
                    "properties": {"healing": "2d4+2", "consumable": True}
                },
                {
                    "name": "Scroll of Fireball",
                    "equipment_type": EquipmentType.MAGIC_ITEM,
                    "description": "A scroll containing the fireball spell.",
                    "cost": 200,
                    "weight": 0.1,
                    "properties": {"spell": "fireball", "spell_level": 3, "consumable": True}
                },
                {
                    "name": "Ring of Protection",
                    "equipment_type": EquipmentType.MAGIC_ITEM,
                    "description": "A ring that provides magical protection.",
                    "cost": 1000,
                    "weight": 0.1,
                    "properties": {"armor_class_bonus": 1, "saving_throw_bonus": 1, "requires_attunement": True}
                }
            ]
            
            # Tools and Miscellaneous
            miscellaneous = [
                {
                    "name": "Thieves' Tools",
                    "equipment_type": EquipmentType.TOOL,
                    "description": "Tools for picking locks and disarming traps.",
                    "cost": 25,
                    "weight": 1.0,
                    "properties": {"lockpicking_bonus": 2}
                },
                {
                    "name": "Backpack",
                    "equipment_type": EquipmentType.MISCELLANEOUS,
                    "description": "A leather backpack for carrying supplies.",
                    "cost": 2,
                    "weight": 5.0,
                    "properties": {"capacity": 30}
                }
            ]
            
            # Combine all equipment
            all_equipment = weapons + armor + magic_items + miscellaneous
            
            # Add to database
            for item_data in all_equipment:
                equipment = Equipment(**item_data)
                db.add(equipment)
            
            db.commit()
            print(f"Added {len(all_equipment)} equipment items to the database.")
        
        # Check if we already have supplies
        supply_count = db.query(Supply).count()
        if supply_count > 0:
            print(f"Database already has {supply_count} supply items. Skipping supply seeding.")
        else:
            # Supplies
            supplies = [
                {
                    "name": "Rations (1 day)",
                    "supply_type": SupplyType.FOOD,
                    "description": "Dried meat, fruit, and hardtack sufficient for one day.",
                    "cost": 0.5,
                    "weight": 2.0,
                    "uses_per_unit": 1
                },
                {
                    "name": "Waterskin",
                    "supply_type": SupplyType.WATER,
                    "description": "A half-gallon container made of leather for holding water.",
                    "cost": 0.2,
                    "weight": 5.0,
                    "uses_per_unit": 1
                },
                {
                    "name": "Torch",
                    "supply_type": SupplyType.LIGHT,
                    "description": "A wooden torch that burns for 1 hour, providing bright light.",
                    "cost": 0.01,
                    "weight": 1.0,
                    "uses_per_unit": 1
                },
                {
                    "name": "Lantern",
                    "supply_type": SupplyType.LIGHT,
                    "description": "A hooded lantern that burns oil and provides light.",
                    "cost": 5,
                    "weight": 2.0,
                    "uses_per_unit": 6
                },
                {
                    "name": "Oil Flask",
                    "supply_type": SupplyType.LIGHT,
                    "description": "A flask of oil that can fuel a lantern for 6 hours.",
                    "cost": 0.1,
                    "weight": 1.0,
                    "uses_per_unit": 1
                },
                {
                    "name": "Healer's Kit",
                    "supply_type": SupplyType.MEDICAL,
                    "description": "A kit with bandages, salves, and splints.",
                    "cost": 5,
                    "weight": 3.0,
                    "uses_per_unit": 10
                },
                {
                    "name": "Rope (50 feet)",
                    "supply_type": SupplyType.ADVENTURE,
                    "description": "Sturdy hemp rope that can hold up to 400 pounds.",
                    "cost": 1,
                    "weight": 10.0,
                    "uses_per_unit": 1
                },
                {
                    "name": "Grappling Hook",
                    "supply_type": SupplyType.ADVENTURE,
                    "description": "A metal hook for latching onto surfaces.",
                    "cost": 2,
                    "weight": 4.0,
                    "uses_per_unit": 1
                },
                {
                    "name": "Crowbar",
                    "supply_type": SupplyType.TOOL,
                    "description": "A metal bar for forcing doors and prying things open.",
                    "cost": 2,
                    "weight": 5.0,
                    "uses_per_unit": 1
                },
                {
                    "name": "Chalk",
                    "supply_type": SupplyType.MISCELLANEOUS,
                    "description": "A piece of chalk for marking paths or writing.",
                    "cost": 0.01,
                    "weight": 0.1,
                    "uses_per_unit": 10
                }
            ]
            
            # Add to database
            for item_data in supplies:
                supply = Supply(**item_data)
                db.add(supply)
            
            db.commit()
            print(f"Added {len(supplies)} supply items to the database.")
    
    finally:
        db.close()

if __name__ == "__main__":
    seed_equipment_and_supplies()