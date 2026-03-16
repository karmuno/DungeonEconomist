import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.expedition import Expedition, EncounterType, CombatOutcome

def calculate_loot_split(total_loot, party_size=1, player_split=0.3):
    """
    Calculate the loot split between adventurers, party fund, and player treasury.
    
    Args:
        total_loot (int): The total amount of gold from the expedition
        party_size (int): Number of adventurers in the party
        player_split (float): Percentage of loot that goes to player treasury (0.0-1.0)
        
    Returns:
        dict: A dictionary containing the split amounts for player, party, and individual adventurers
    """
    # Calculate player's share (treasury)
    player_share = int(total_loot * player_split)
    
    # Calculate adventurers' share (70% by default)
    adventurers_share = total_loot - player_share
    
    # Calculate individual adventurer share
    individual_share = 0
    if party_size > 0:
        individual_share = adventurers_share // party_size
    
    return {
        "player_treasury": player_share,
        "adventurers_share": adventurers_share,
        "individual_share": individual_share,
        "total_loot": total_loot
    }

class DungeonSimulator:
    """
    Main simulation engine that handles running expeditions, tracking party status,
    and managing simulation outcomes.
    """
    def __init__(self, parties: List[Dict[str, Any]] = None):
        self.parties = parties or []
        self.active_expeditions = {}
        self.completed_expeditions = {}  # Dictionary for id-based access
        self.completed_expedition_list = []  # List for order preservation
        self.expedition_logs = {}
        
    def add_party(self, party: List[Dict[str, Any]]) -> int:
        """Add a new party to the simulator and return its ID"""
        party_id = len(self.parties)
        self.parties.append(party)
        return party_id
        
    def start_expedition(self, party_id: int, dungeon_level: int) -> int:
        """Start a new expedition with the specified party"""
        if party_id >= len(self.parties) or not self.parties[party_id]:
            raise ValueError(f"Invalid party ID: {party_id}")
            
        # Create a copy of the party to avoid modifying the original
        party_copy = [member.copy() for member in self.parties[party_id]]
        
        # Create new expedition
        expedition = Expedition(party_copy, dungeon_level)
        
        # Generate expedition ID and store it
        expedition_id = len(self.active_expeditions) + len(self.completed_expedition_list)
        self.active_expeditions[expedition_id] = {
            "expedition": expedition,
            "party_id": party_id,
            "start_time": datetime.now(),
            "turns_completed": 0
        }
        
        # Initialize expedition log
        self.expedition_logs[expedition_id] = []
        
        return expedition_id
        
    def advance_turn(self, expedition_id: int) -> Dict[str, Any]:
        """Advance the expedition by one turn and return the results"""
        if expedition_id not in self.active_expeditions:
            raise ValueError(f"Invalid expedition ID: {expedition_id}")
            
        expedition_data = self.active_expeditions[expedition_id]
        expedition = expedition_data["expedition"]
        
        # Run one turn
        expedition_data["turns_completed"] += 1
        turn_number = expedition_data["turns_completed"]
        
        # Check for encounter and resolve it
        turn_log = {"turn": turn_number, "events": [], "deaths": []}

        # Track who was alive before the turn
        alive_before = {m["name"] for m in expedition.party if m["current_hp"] > 0}

        if expedition.check_for_encounter():
            encounter_type = expedition.determine_encounter_type()
            encounter_log = {"type": encounter_type.value}

            if encounter_type == EncounterType.MONSTER:
                monster_type = expedition._get_random_monster()
                combat_result = expedition.resolve_combat(monster_type)
                encounter_log["combat"] = combat_result
                expedition.xp_earned += combat_result["xp_earned"]

                # Generate treasure if monster defeated
                if combat_result["outcome"] in [CombatOutcome.CLEAR_VICTORY, CombatOutcome.VICTORY]:
                    treasure = expedition.generate_treasure(monster_type)
                    encounter_log["treasure"] = treasure
                    expedition.treasure.append(treasure)
                    expedition.xp_earned += treasure["xp_value"]

            elif encounter_type == EncounterType.TRAP:
                trap_damage = random.randint(1, 6) * expedition.dungeon_level
                expedition.resources_used["hp_lost"] += trap_damage
                # Distribute trap damage among alive members
                alive_members = [m for m in expedition.party if m["current_hp"] > 0]
                if alive_members:
                    base_loss = trap_damage // len(alive_members)
                    remainder = trap_damage % len(alive_members)
                    for i, member in enumerate(alive_members):
                        loss = base_loss + (1 if i < remainder else 0)
                        member["current_hp"] -= loss
                        if member["current_hp"] <= 0:
                            member["current_hp"] = 0
                            if member not in expedition.dead:
                                expedition.dead.append(member)
                encounter_log["trap_damage"] = trap_damage

            elif encounter_type == EncounterType.TREASURE:
                treasure = expedition.generate_treasure()
                encounter_log["treasure"] = treasure
                expedition.treasure.append(treasure)
                expedition.xp_earned += treasure["xp_value"]

            turn_log["events"].append(encounter_log)

        # Record who died THIS turn
        alive_after = {m["name"] for m in expedition.party if m["current_hp"] > 0}
        newly_dead = alive_before - alive_after
        turn_log["deaths"] = list(newly_dead)
        
        # Update the expedition log
        self.expedition_logs[expedition_id].append(turn_log)
        
        # Check if expedition should end
        should_end = self._should_end_expedition(expedition)
        
        # Return turn results
        turn_result = {
            "turn": turn_number,
            "events": turn_log["events"],
            "party_status": self._get_party_status(expedition),
            "expedition_ended": should_end
        }
        
        # End expedition if needed
        if should_end:
            self._complete_expedition(expedition_id)
        
        return turn_result
    
    def run_expedition_to_completion(self, expedition_id: int, max_turns: int = 30) -> Dict[str, Any]:
        """Run the expedition until it completes or reaches max turns"""
        turn_count = 0
        while expedition_id in self.active_expeditions and turn_count < max_turns:
            result = self.advance_turn(expedition_id)
            turn_count += 1
            if result["expedition_ended"]:
                break
                
        # If expedition still active after max turns, complete it
        if expedition_id in self.active_expeditions:
            self._complete_expedition(expedition_id)
            
        # Return the final results
        return self.get_expedition_results(expedition_id)
    
    def get_expedition_results(self, expedition_id: int) -> Dict[str, Any]:
        """Get the complete results for an expedition"""
        # Check if expedition exists in completed or active
        expedition_data = None
        if expedition_id in self.completed_expeditions:
            expedition_data = self.completed_expeditions[expedition_id]
        elif expedition_id in self.active_expeditions:
            expedition_data = self.active_expeditions[expedition_id]
            
        if not expedition_data:
            raise ValueError(f"Invalid expedition ID: {expedition_id}")
            
        expedition = expedition_data["expedition"]
        
        # Build comprehensive results
        results = {
            "expedition_id": expedition_id,
            "party_id": expedition_data["party_id"],
            "dungeon_level": expedition.dungeon_level,
            "turns": expedition_data["turns_completed"],
            "start_time": expedition_data["start_time"],
            "end_time": expedition_data.get("end_time", None),
            "treasure_total": sum(t["gold"] for t in expedition.treasure),
            "special_items": [t["special_item"] for t in expedition.treasure if t["special_item"]],
            "xp_earned": expedition.xp_earned,
            "xp_per_party_member": expedition.xp_earned // len(expedition.party) if expedition.party else 0,
            "resources_used": expedition.resources_used,
            "dead_members": [member["name"] for member in expedition.dead],
            "party_status": self._get_party_status(expedition),
            "log": self.expedition_logs.get(expedition_id, [])
        }
        
        return results
    
    def get_all_parties(self) -> List[Dict[str, Any]]:
        """Get information about all parties in the simulator"""
        return [
            {
                "party_id": idx, 
                "members": party, 
                "size": len(party)
            } 
            for idx, party in enumerate(self.parties)
        ]
    
    def get_party_status(self, party_id: int) -> Dict[str, Any]:
        """Get the current status of a party"""
        if party_id >= len(self.parties) or not self.parties[party_id]:
            raise ValueError(f"Invalid party ID: {party_id}")
            
        # Check if party is on an expedition
        active_expedition_id = None
        for exp_id, exp_data in self.active_expeditions.items():
            if exp_data["party_id"] == party_id:
                active_expedition_id = exp_id
                break
                
        return {
            "party_id": party_id,
            "members": self.parties[party_id],
            "size": len(self.parties[party_id]),
            "on_expedition": active_expedition_id is not None,
            "expedition_id": active_expedition_id
        }
    
    def add_adventurer_to_party(self, party_id: int, adventurer: Dict[str, Any]) -> bool:
        """Add an adventurer to a party"""
        if party_id >= len(self.parties):
            # Create new party if it doesn't exist
            while len(self.parties) <= party_id:
                self.parties.append([])
                
        # Don't add if party is on expedition
        for exp_data in self.active_expeditions.values():
            if exp_data["party_id"] == party_id:
                return False
                
        # Add adventurer to party
        self.parties[party_id].append(adventurer)
        return True
    
    def remove_adventurer_from_party(self, party_id: int, adventurer_id: str) -> bool:
        """Remove an adventurer from a party"""
        if party_id >= len(self.parties) or not self.parties[party_id]:
            return False
            
        # Don't remove if party is on expedition
        for exp_data in self.active_expeditions.values():
            if exp_data["party_id"] == party_id:
                return False
                
        # Find and remove adventurer
        for i, adv in enumerate(self.parties[party_id]):
            if adv.get("id") == adventurer_id:
                self.parties[party_id].pop(i)
                return True
                
        return False
    
    # Helper methods
    def _should_end_expedition(self, expedition: Expedition) -> bool:
        """Determine if an expedition should end"""
        # End if all party members are dead
        if all(member["current_hp"] <= 0 for member in expedition.party):
            return True
            
        # End if party has taken too much damage
        total_max_hp = sum(member.get("hit_points", 1) for member in expedition.party)
        total_current_hp = sum(member.get("current_hp", 0) for member in expedition.party)
        if total_current_hp < total_max_hp * 0.3:  # End if below 30% total HP
            return True
            
        # Random chance to end expedition increases with each turn
        chance_to_end = min(0.05 * expedition.turns, 0.5)  # 5% per turn, max 50%
        return random.random() < chance_to_end
    
    def _complete_expedition(self, expedition_id: int) -> None:
        """Complete an expedition and update party status"""
        if expedition_id not in self.active_expeditions:
            return
            
        # Get expedition data
        expedition_data = self.active_expeditions[expedition_id]
        expedition = expedition_data["expedition"]
        party_id = expedition_data["party_id"]
        
        # Update expedition data
        expedition_data["end_time"] = datetime.now()
        
        # Move from active to completed
        self.completed_expedition_list.append(expedition_data)
        self.completed_expeditions[expedition_id] = expedition_data
        del self.active_expeditions[expedition_id]
        
        # Update original party with results
        self._apply_expedition_results(party_id, expedition)
    
    def _apply_expedition_results(self, party_id: int, expedition: Expedition) -> None:
        """Apply expedition results to the original party"""
        if party_id >= len(self.parties):
            return
            
        # Get original party
        original_party = self.parties[party_id]
        
        # XP distribution
        xp_per_member = expedition.xp_earned // len(expedition.party) if expedition.party else 0
        
        # Update each party member
        for exp_member in expedition.party:
            # Find corresponding original member
            for original_member in original_party:
                if original_member.get("id") == exp_member.get("id") or original_member.get("name") == exp_member.get("name"):
                    # Add XP
                    original_member["xp"] = original_member.get("xp", 0) + xp_per_member
                    
                    # Check if member died
                    if exp_member["current_hp"] <= 0:
                        # Handle death (for now, just reset HP to 1)
                        original_member["hit_points"] = 1
                    else:
                        # Update hit points (keeping between 1 and max)
                        max_hp = original_member.get("hit_points", 10)
                        original_member["hit_points"] = min(max_hp, max(1, exp_member["current_hp"]))
                    break
    
    def _get_party_status(self, expedition: Expedition) -> Dict[str, Any]:
        """Get the current status of the party on expedition"""
        alive_members = sum(1 for member in expedition.party if member.get("current_hp", 0) > 0)
        total_max_hp = sum(member.get("hit_points", 1) for member in expedition.party)
        total_current_hp = sum(member.get("current_hp", 0) for member in expedition.party)
        
        return {
            "members_total": len(expedition.party),
            "members_alive": alive_members,
            "members_dead": len(expedition.dead),
            "hp_current": total_current_hp,
            "hp_max": total_max_hp,
            "hp_percentage": (total_current_hp / total_max_hp) * 100 if total_max_hp > 0 else 0
        }