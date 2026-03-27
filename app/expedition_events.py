"""Post-process simulation results to detect noteworthy events and auto-resolve
party decisions about them.

Detects real events from the simulation log:
- A party member actually died in a specific turn
- A specific turn produced treasure above the big haul threshold
- Stairs were discovered (random roll, once per expedition)

Parties auto-decide whether to press on or retreat. For now decisions are
random; eventually this will depend on party composition and morale.
"""

import random

from app.dungeons import DUNGEON_LEVEL_NAMES

# Treasure threshold for "big haul" event (gold pieces in a single turn)
BIG_HAUL_THRESHOLD = 8



def auto_decide(event_type: str, party: list = None) -> str:
    """Have the party automatically decide what to do at a decision point.

    Returns 'press_on' or 'retreat'.
    Eventually this will factor in party composition, morale, HP levels, etc.
    """
    # TODO: weight by party composition, current HP %, class abilities
    return random.choice(["press_on", "retreat"])


def build_phases(sim_result: dict, dungeon_level: int, max_dungeon_level: int) -> dict:
    """Scan simulation log for real trigger events and build decision points.

    Mutates sim_result by adding 'phases' and 'decision_points' keys.
    Returns the modified sim_result.
    """
    log = sim_result.get("log", [])
    total_turns = len(log)
    total_levels = len(DUNGEON_LEVEL_NAMES)

    if total_turns == 0:
        sim_result["phases"] = []
        sim_result["decision_points"] = []
        return sim_result

    decision_points = []

    # Scan turn-by-turn for real events
    for i, turn in enumerate(log):
        turn_num = turn.get("turn", i + 1)

        # Check for real deaths this turn
        deaths_this_turn = turn.get("deaths", [])
        for dead_name in deaths_this_turn:
            decision_points.append({
                "after_turn": turn_num,
                "type": "death",
                "message": f"{dead_name} has fallen in the dungeon! Press on or retreat?",
                "dead_member": dead_name,
                "options": ["press_on", "retreat"],
            })

        # Check for big haul this turn
        for event in turn.get("events", []):
            treasure = event.get("treasure")
            if treasure and treasure.get("gold", 0) >= BIG_HAUL_THRESHOLD:
                gold = treasure["gold"]
                decision_points.append({
                    "after_turn": turn_num,
                    "type": "big_haul",
                    "message": f"Your party found a massive treasure hoard worth {gold} gp! Secure the loot and retreat, or press deeper?",
                    "loot_so_far": gold,
                    "options": ["press_on", "retreat"],
                })

    # Stairs discovery — 15% chance per turn at the deepest unlocked level.
    # Each Dwarf in the party adds +5% per turn.
    # Stairs are NOT a decision point — they auto-unlock at expedition completion
    # and always produce a popup notification the player cannot miss.
    if dungeon_level >= max_dungeon_level and dungeon_level < total_levels and log:
        party_classes = sim_result.get("party_classes", [])
        dwarf_count = party_classes.count("Dwarf")
        stairs_chance_per_turn = 0.015 + dwarf_count * 0.01
        next_level = dungeon_level + 1
        next_name = DUNGEON_LEVEL_NAMES[dungeon_level] if dungeon_level < total_levels else "unknown depths"
        for _turn in log:
            if random.random() < stairs_chance_per_turn:
                sim_result["stairs_found"] = {
                    "new_level": next_level,
                    "new_level_name": next_name,
                }
                break

    # Sort by turn order
    decision_points.sort(key=lambda dp: dp["after_turn"])

    # Build phases from decision point boundaries
    phases = []
    phase_starts = [0] + [dp["after_turn"] for dp in decision_points] + [total_turns]

    for idx in range(len(phase_starts) - 1):
        start = phase_starts[idx]
        end = phase_starts[idx + 1]
        phase = _make_phase_from_log(start, end, log)
        phases.append(phase)

    sim_result["phases"] = phases
    sim_result["decision_points"] = decision_points
    return sim_result


def _make_phase_from_log(start_turn: int, end_turn: int, log: list) -> dict:
    """Build a phase dict for turns [start_turn, end_turn)."""
    phase_loot = 0
    phase_silver = 0
    phase_copper = 0
    phase_xp = 0
    phase_deaths = []

    for i in range(start_turn, min(end_turn, len(log))):
        turn = log[i]
        for event in turn.get("events", []):
            treasure = event.get("treasure")
            if treasure:
                phase_loot += treasure.get("gold", 0)
                phase_silver += treasure.get("silver", 0)
                phase_copper += treasure.get("copper", 0)
                phase_xp += treasure.get("xp_value", 0)
            combat = event.get("combat")
            if combat:
                phase_xp += combat.get("xp_earned", 0)
        phase_deaths.extend(turn.get("deaths", []))

    return {
        "start_turn": start_turn,
        "end_turn": end_turn,
        "loot": phase_loot,
        "silver": phase_silver,
        "copper": phase_copper,
        "xp": phase_xp,
        "deaths": phase_deaths,
    }


def calculate_retreat_results(sim_result: dict, current_decision_index: int) -> dict:
    """Calculate partial results when player retreats at decision point N.

    Includes everything up through the phase containing the trigger event.
    """
    phases = sim_result.get("phases", [])
    decision_points = sim_result.get("decision_points", [])

    # Include phase 0 through current_decision_index (the phase that ends
    # at the decision point, i.e. includes the trigger event itself)
    included_phases = phases[:current_decision_index + 1]

    partial_loot = sum(p["loot"] for p in included_phases)
    partial_silver = sum(p.get("silver", 0) for p in included_phases)
    partial_copper = sum(p.get("copper", 0) for p in included_phases)
    partial_xp = sum(p["xp"] for p in included_phases)
    partial_deaths = []
    for p in included_phases:
        partial_deaths.extend(p.get("deaths", []))

    # Calculate the cutoff turn for the log (everything up to the decision point)
    cutoff_turn = None
    if current_decision_index < len(decision_points):
        cutoff_turn = decision_points[current_decision_index].get("after_turn", 0)

    member_count = sim_result.get("party_status", {}).get("members_total", 1)

    return {
        "treasure_total": partial_loot,
        "treasure_silver": partial_silver,
        "treasure_copper": partial_copper,
        "xp_earned": partial_xp,
        "xp_per_party_member": partial_xp // max(1, member_count),
        "dead_members": partial_deaths,
        "retreated": True,
        "retreat_cutoff_turn": cutoff_turn,
        "phases_completed": current_decision_index + 1,
    }
