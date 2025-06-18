import sys
import random
from enum import Enum

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
            "spells_used": 0,
            "supplies_used": 0
        }
        self.dead = []
        
    def check_for_encounter(self):
        """Check if an encounter occurs on this turn"""
        roll = random.randint(1, 6)
        return roll == 1 or (roll == 6 and random.random() < 0.5)  # 50% chance on a 6
    
    def determine_encounter_type(self):
        """Determine what type of encounter occurs"""
        roll = random.randint(1, 6)
        if roll <= 3:
            return EncounterType.MONSTER
        elif roll == 4:
            return EncounterType.TRAP
        elif roll == 5:
            return EncounterType.CLUE
        else:
            return EncounterType.TREASURE
    
    def resolve_combat(self, monster_type):
        """Resolve combat with a monster encounter"""
        # Calculate party strength
        party_strength = sum(
            member["level"] * self._get_class_multiplier(member["character_class"])
            for member in self.party if member.get("current_hp", 1) > 0
        )
        
        # Calculate monster strength based on type and dungeon level
        monster_hit_dice = self._get_monster_hit_dice(monster_type, self.dungeon_level)
        monster_difficulty = self._get_monster_difficulty(monster_type)
        monster_strength = monster_hit_dice * monster_difficulty
        
        # Determine outcome
        strength_ratio = party_strength / monster_strength if monster_strength else 1
        
        if strength_ratio > 2.0:
            outcome = CombatOutcome.CLEAR_VICTORY
            hp_loss_percentage = 0.1  # 10% HP loss
        elif strength_ratio > 1.2:
            outcome = CombatOutcome.VICTORY
            hp_loss_percentage = 0.25  # 25% HP loss
        elif strength_ratio > 0.8:
            outcome = CombatOutcome.TOUGH_FIGHT
            hp_loss_percentage = 0.5  # 50% HP loss
        elif strength_ratio > 0.5:
            outcome = CombatOutcome.RETREAT
            hp_loss_percentage = 0.6  # 60% HP loss
        else:
            outcome = CombatOutcome.DISASTER
            hp_loss_percentage = 0.8  # 80% HP loss or worse
            
        # Calculate resource depletion
        alive_members = [m for m in self.party if m["current_hp"] > 0]
        total_party_hp = sum(member["current_hp"] for member in alive_members)
        hp_lost = int(total_party_hp * hp_loss_percentage)
        
        # Distribute damage among alive members
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
        
        # Update resources used
        self.resources_used["hp_lost"] += hp_lost
        self.resources_used["spells_used"] += self._calculate_spells_used(outcome)
        self.resources_used["supplies_used"] += 1
        
        # Calculate XP from monster
        monster_xp = int(monster_hit_dice * (100 + (self.dungeon_level * 10))) # Base XP + bonus per dungeon level
        
        # Add bonus XP for surviving encounters in higher dungeon levels
        if outcome not in [CombatOutcome.DISASTER, CombatOutcome.RETREAT]:
            monster_xp += self.dungeon_level * 10

        return {
            "outcome": outcome,
            "monster_type": monster_type,
            "hp_lost": hp_lost,
            "xp_earned": monster_xp
        }
    
    def generate_treasure(self, monster_type=None):
        """Generate treasure based on encounter"""
        # Basic treasure generation logic
        base_value = self.dungeon_level * 100  # 100gp per dungeon level as base
        
        if monster_type:
            # Treasure from monster
            treasure_modifier = self._get_monster_treasure_modifier(monster_type)
            treasure_value = int(base_value * treasure_modifier * random.uniform(0.5, 1.5))
        else:
            # Unguarded treasure
            treasure_value = int(base_value * random.uniform(1.0, 3.0))
        
        # Chance for special items
        special_item = None
        # Increase chance for special item: 10% at L1, 15% at L2, ..., up to 50%
        special_item_chance = min(0.5, 0.05 + (0.05 * self.dungeon_level))
        if random.random() < special_item_chance:
            special_item = self._generate_special_item()
        
        return {
            "gold": treasure_value,
            "special_item": special_item,
            "xp_value": treasure_value  # 1 XP per GP
        }
    
    def run_expedition(self, turns=10):
        """Run the expedition for a number of turns"""
        expedition_log = []
        
        for _ in range(turns):
            self.turns += 1
            turn_log = {"turn": self.turns, "events": []}
            
            # Check for encounter
            if self.check_for_encounter():
                encounter_type = self.determine_encounter_type()
                encounter_log = {"type": encounter_type}
                
                if encounter_type == EncounterType.MONSTER:
                    monster_type = self._get_random_monster()
                    combat_result = self.resolve_combat(monster_type)
                    encounter_log["combat"] = combat_result
                    self.xp_earned += combat_result["xp_earned"]
                    
                    # Generate treasure if monster defeated
                    if combat_result["outcome"] in [CombatOutcome.CLEAR_VICTORY, CombatOutcome.VICTORY]:
                        treasure = self.generate_treasure(monster_type)
                        encounter_log["treasure"] = treasure
                        self.treasure.append(treasure)
                        self.xp_earned += treasure["xp_value"]
                
                elif encounter_type == EncounterType.TRAP:
                    trap_damage = random.randint(1, 6) * self.dungeon_level
                    self.resources_used["hp_lost"] += trap_damage
                    # Distribute trap damage among alive members
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
                
                elif encounter_type == EncounterType.TREASURE:
                    treasure = self.generate_treasure()
                    encounter_log["treasure"] = treasure
                    self.treasure.append(treasure)
                    self.xp_earned += treasure["xp_value"]
                
                turn_log["events"].append(encounter_log)
            
            expedition_log.append(turn_log)
        
        # Calculate final results
        results = {
            "turns": self.turns,
            "encounters": len(self.encounters),
            "treasure_total": sum(t["gold"] for t in self.treasure),
            "special_items": [t["special_item"] for t in self.treasure if t["special_item"]],
            "xp_earned": self.xp_earned,
            "xp_per_party_member": self.xp_earned // len(self.party) if self.party else 0,
            "resources_used": self.resources_used,
            "dead": [member["name"] for member in self.dead],
            "log": expedition_log
        }
        
        return results
    
    # Helper methods
    def _get_class_multiplier(self, character_class):
        """Get the strength multiplier for a character class"""
        multipliers = {
            "Fighter": 1.2,
            "Cleric": 1.0,
            "Magic-User": 0.8,
            "Thief": 0.9,
            "Dwarf": 1.3,
            "Elf": 1.1,
            "Hobbit": 0.8
        }
        return multipliers.get(character_class, 1.0)
    
    def _get_monster_hit_dice(self, monster_type, dungeon_level):
        """Get hit dice for a monster based on type and dungeon level"""
        # Simplified version - would be expanded with actual monster tables
        base_hd = dungeon_level # Base HD directly scales with dungeon_level
        monster_hd_modifiers = {
            "Goblin": 0.5,
            "Orc": 1.0,
            "Hobgoblin": 1.5,
            "Ogre": 2.5,  # Increased
            "Troll": 3.5,  # Increased
            "Dragon": 6.0  # Increased
        }
        return max(1, base_hd * monster_hd_modifiers.get(monster_type, 1.0)) # Ensure at least 1 HD
    
    def _get_monster_difficulty(self, monster_type):
        """Get difficulty factor for a monster type"""
        difficulties = {
            "Goblin": 0.8,
            "Orc": 1.0,
            "Hobgoblin": 1.3, # Increased
            "Ogre": 1.8,     # Increased
            "Troll": 2.5,    # Increased
            "Dragon": 4.0    # Increased
        }
        return difficulties.get(monster_type, 1.0)
    
    def _get_monster_treasure_modifier(self, monster_type):
        """Get treasure modifier for a monster type"""
        modifiers = {
            "Goblin": 0.5,
            "Orc": 1.0,
            "Hobgoblin": 1.5, # Increased
            "Ogre": 3.0,     # Increased
            "Troll": 4.0,    # Increased
            "Dragon": 8.0    # Increased
        }
        return modifiers.get(monster_type, 1.0)
    
    def _generate_special_item(self):
        """Generate a special magic item"""
        items = [
            "Potion of Healing",
            "Scroll of Protection",
            "Ring of Protection +1",
            "Sword +1",
            "Wand of Magic Detection"
        ]
        return random.choice(items)
    
    def _get_random_monster(self):
        """Get a random monster appropriate for the dungeon level"""
        # Simplified - would have proper monster tables by level
        monster_tables = {
            1: ["Goblin", "Orc", "Skeleton"],
            2: ["Hobgoblin", "Zombie", "Ghoul"],
            3: ["Ogre", "Wight", "Werewolf"],
            4: ["Troll", "Wraith", "Owlbear"],
            5: ["Giant", "Spectre", "Chimera"],
            6: ["Dragon", "Vampire", "Demon"]
        }
        
        level_table = monster_tables.get(
            min(self.dungeon_level, max(monster_tables.keys())), 
            monster_tables[1]
        )
        return random.choice(level_table)
    
    def _calculate_spells_used(self, combat_outcome):
        """Calculate spells used based on combat outcome"""
        spell_use = {
            CombatOutcome.CLEAR_VICTORY: 1,
            CombatOutcome.VICTORY: 2,
            CombatOutcome.TOUGH_FIGHT: 3,
            CombatOutcome.RETREAT: 4,
            CombatOutcome.DISASTER: 5
        }
        return spell_use.get(combat_outcome, 0)
    
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