import random
import sys
from enum import Enum

from app.monsters import (
    get_monster_count,
    get_monster_hit_dice,
    get_random_monster,
    roll_monster_hd,
)

# PC hit die size by class (matches progression.py comments)
PC_HIT_DIE = {
    "Fighter": 8,
    "Dwarf": 8,
    "Cleric": 6,
    "Elf": 6,
    "Hobbit": 6,
    "Magic-User": 4,
}

class EncounterType(Enum):
    MONSTER = "Monster"
    TRAP = "Trap/Hazard"
    CLUE = "Clue or Empty Room"
    TREASURE = "Unguarded Treasure"

class CombatOutcome(Enum):
    CLEAR_VICTORY = "Clear Victory"
    VICTORY = "Victory"
    TOUGH_FIGHT = "Tough Fight"
    RETREAT = "Retreat"
    DISASTER = "Disaster"

class Expedition:
    def __init__(self, party, dungeon_level):
        # Add current_hp to each member if not present
        for member in party:
            if "current_hp" not in member:
                member["current_hp"] = member.get("hit_points", 1)
        self.party = party
        self.dungeon_level = dungeon_level
        self.turns = 0
        self.encounters = []
        self.treasure = []
        self.xp_earned = 0
        self.resources_used = {
            "hp_lost": 0,
        }
        self.dead = []

    def determine_room_contents(self):
        """Determine what's in this room.

        Returns a list of encounter types (may be empty, or contain
        MONSTER + TREASURE together).

        Odds:
          1/3 monster (of those, 4/6 also have treasure)
          If no monster: 1/6 treasure, 1/6 trap, 1/6 clue, 3/6 empty
        """
        roll = random.randint(1, 6)
        if roll <= 2:  # 2/6 = 1/3 monster
            # Monster room — 4/6 chance of treasure too
            if random.randint(1, 6) <= 4:
                return [EncounterType.MONSTER, EncounterType.TREASURE]
            return [EncounterType.MONSTER]
        else:  # 4/6 = 2/3 no monster
            sub = random.randint(1, 6)
            if sub == 1:
                return [EncounterType.TREASURE]
            elif sub == 2:
                return [EncounterType.TRAP]
            elif sub == 3:
                return [EncounterType.CLUE]
            else:  # 4, 5, 6 = empty
                return []


    def resolve_combat(self, monster_type):
        """Resolve combat by rolling HD for both sides.

        PCs roll their class HD per level; monsters roll their HD per monster.
        Outcome is determined by comparing the two totals.
        """
        alive_members = [m for m in self.party if m.get("current_hp", 1) > 0]

        # Roll party HD: each living PC rolls (level)d(class_hit_die)
        party_roll = 0
        for member in alive_members:
            die_size = PC_HIT_DIE.get(member.get("character_class", ""), 6)
            level = member.get("level", 1)
            party_roll += sum(random.randint(1, die_size) for _ in range(level))

        # Determine number of monsters and roll their HD
        monster_count = get_monster_count(monster_type)
        monster_hd = get_monster_hit_dice(monster_type)
        monster_roll = roll_monster_hd(monster_type, monster_count)
        total_monster_hd = monster_hd * monster_count

        # Compare rolls to determine outcome
        if monster_roll == 0:
            ratio = 2.0
        else:
            ratio = party_roll / monster_roll

        if ratio >= 2.0:
            outcome = CombatOutcome.CLEAR_VICTORY
            hp_loss_percentage = 0.1
        elif ratio >= 1.2:
            outcome = CombatOutcome.VICTORY
            hp_loss_percentage = 0.25
        elif ratio >= 0.83:  # within ~20% of each other
            outcome = CombatOutcome.TOUGH_FIGHT
            hp_loss_percentage = 0.5
        elif ratio >= 0.5:
            outcome = CombatOutcome.RETREAT
            hp_loss_percentage = 0.6
        else:
            outcome = CombatOutcome.DISASTER
            hp_loss_percentage = 0.8

        # Apply damage to party
        total_party_hp = sum(member["current_hp"] for member in alive_members)
        hp_lost = int(total_party_hp * hp_loss_percentage)

        if alive_members:
            base_loss = hp_lost // len(alive_members)
            remainder = hp_lost % len(alive_members)
            for i, member in enumerate(alive_members):
                loss = base_loss + (1 if i < remainder else 0)
                member["current_hp"] -= loss
                if member["current_hp"] <= 0:
                    member["current_hp"] = 0
                    if member not in self.dead:
                        self.dead.append(member)

        self.resources_used["hp_lost"] += hp_lost

        # XP based on total monster HD defeated
        monster_xp = int(total_monster_hd * (100 + (self.dungeon_level * 10)))
        if outcome not in [CombatOutcome.DISASTER, CombatOutcome.RETREAT]:
            monster_xp += self.dungeon_level * 10

        return {
            "outcome": outcome.value,
            "monster_type": monster_type,
            "monster_count": monster_count,
            "party_roll": party_roll,
            "monster_roll": monster_roll,
            "hp_lost": hp_lost,
            "xp_earned": monster_xp,
        }

    def generate_treasure(self, monster_type=None):
        """Generate treasure using JSON config."""
        from app.treasure import generate_treasure as _gen_treasure
        return _gen_treasure(self.dungeon_level)

    def run_expedition(self, turns=10):
        """Run the expedition for a number of turns"""
        expedition_log = []

        for _ in range(turns):
            self.turns += 1
            turn_log = {"turn": self.turns, "events": []}

            room_contents = self.determine_room_contents()
            for encounter_type in room_contents:
                encounter_log = {"type": encounter_type.value}

                if encounter_type == EncounterType.MONSTER:
                    monster_type = self._get_random_monster()
                    combat_result = self.resolve_combat(monster_type)
                    encounter_log["combat"] = combat_result
                    self.xp_earned += combat_result["xp_earned"]

                elif encounter_type == EncounterType.TREASURE:
                    treasure = self.generate_treasure()
                    encounter_log["treasure"] = treasure
                    self.treasure.append(treasure)
                    self.xp_earned += treasure["xp_value"]

                elif encounter_type == EncounterType.TRAP:
                    trap_damage = random.randint(1, 6) * self.dungeon_level
                    self.resources_used["hp_lost"] += trap_damage
                    alive_members = [m for m in self.party if m["current_hp"] > 0]
                    if alive_members:
                        base_loss = trap_damage // len(alive_members)
                        remainder = trap_damage % len(alive_members)
                        for i, member in enumerate(alive_members):
                            loss = base_loss + (1 if i < remainder else 0)
                            member["current_hp"] -= loss
                            if member["current_hp"] <= 0:
                                member["current_hp"] = 0
                                if member not in self.dead:
                                    self.dead.append(member)
                    encounter_log["trap_damage"] = trap_damage

                turn_log["events"].append(encounter_log)

            expedition_log.append(turn_log)

        # Calculate final results
        results = {
            "turns": self.turns,
            "encounters": len(self.encounters),
            "treasure_total": sum(t["gold"] for t in self.treasure),
            "treasure_silver": sum(t.get("silver", 0) for t in self.treasure),
            "treasure_copper": sum(t.get("copper", 0) for t in self.treasure),
            "special_items": [t["special_item"] for t in self.treasure if t["special_item"]],
            "xp_earned": self.xp_earned,
            "xp_per_party_member": self.xp_earned // len(self.party) if self.party else 0,
            "resources_used": self.resources_used,
            "dead": [member["name"] for member in self.dead],
            "log": expedition_log
        }

        return results

    # Helper methods (delegates to app.monsters JSON config)
    def _get_random_monster(self):
        return get_random_monster(self.dungeon_level)

def main(argv):
    # Create a party of adventurers
    party = [
        {"name": "Thorgar", "character_class": "Fighter", "level": 3, "hit_points": 24},
        {"name": "Elindra", "character_class": "Elf", "level": 2, "hit_points": 12},
        {"name": "Morgrim", "character_class": "Dwarf", "level": 2, "hit_points": 18},
        {"name": "Thalia", "character_class": "Magic-User", "level": 2, "hit_points": 8},
        {"name": "Brother Galen", "character_class": "Cleric", "level": 2, "hit_points": 14}
    ]

    # Create expedition
    expedition = Expedition(party, dungeon_level=2)

    # Run expedition
    results = expedition.run_expedition(turns=20)

    # Display results
    print(f"Expedition completed in {results['turns']} turns")
    print(f"Encounters: {results['encounters']}")
    print(f"Treasure found: {results['treasure_total']} gold")
    print(f"Special items: {', '.join(results['special_items']) if results['special_items'] else 'None'}")
    print(f"XP earned: {results['xp_earned']} ({results['xp_per_party_member']} per character)")
    print(f"Resources used: {results['resources_used']}")
    print(f"Dead party members: {', '.join(results['dead']) if results['dead'] else 'None'}")

if __name__ == "__main__":
    main(sys.argv)
