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

BASE_STAIRS_CHANCE = 0.01


def auto_decide(event_type: str, party: list = None) -> str:
    """Have the party automatically decide what to do at a decision point.

    Returns 'press_on' or 'retreat'. Eventually this will factor in party
    composition, morale, HP levels, etc.
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

    # Stairs discovery — 5% chance per turn, only at deepest unlocked level
    if dungeon_level >= max_dungeon_level and dungeon_level < total_levels:
        # TODO: add building bonuses to stairs_chance
        stairs_chance = BASE_STAIRS_CHANCE
        for i, turn in enumerate(log):
            if random.random() < stairs_chance:
                turn_num = turn.get("turn", i + 1)
                next_level = dungeon_level + 1
                next_name = DUNGEON_LEVEL_NAMES[dungeon_level] if dungeon_level < total_levels else "unknown depths"
                decision_points.append({
                    "after_turn": turn_num,
                    "type": "stairs",
                    "message": f"Your party discovered stairs leading down to {next_name}! (Level {next_level})",
                    "new_level": next_level,
                    "new_level_name": next_name,
                    "options": ["press_on", "retreat"],
                })
                break  # Only one stairs discovery per expedition

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
    phase_xp = 0
    phase_deaths = []

    for i in range(start_turn, min(end_turn, len(log))):
        turn = log[i]
        for event in turn.get("events", []):
            treasure = event.get("treasure")
            if treasure:
                phase_loot += treasure.get("gold", 0)
                phase_xp += treasure.get("xp_value", 0)
            combat = event.get("combat")
            if combat:
                phase_xp += combat.get("xp_earned", 0)
        phase_deaths.extend(turn.get("deaths", []))

    return {
        "start_turn": start_turn,
        "end_turn": end_turn,
        "loot": phase_loot,
        "xp": phase_xp,
        "deaths": phase_deaths,
    }


def calculate_retreat_results(sim_result: dict, current_decision_index: int) -> dict:
    """Calculate partial results when player retreats at decision point N.

    Includes everything up through the phase containing the trigger event,
    plus one retreat turn (the turn right after the decision point).
    """
    phases = sim_result.get("phases", [])
    log = sim_result.get("log", [])
    decision_points = sim_result.get("decision_points", [])

    # Include phase 0 through current_decision_index (the phase that ends
    # at the decision point, i.e. includes the trigger event itself)
    included_phases = phases[:current_decision_index + 1]

    partial_loot = sum(p["loot"] for p in included_phases)
    partial_xp = sum(p["xp"] for p in included_phases)
    partial_deaths = []
    for p in included_phases:
        partial_deaths.extend(p.get("deaths", []))

    # Retreat turn: one turn after the decision point
    retreat_turn_idx = None
    if current_decision_index < len(decision_points):
        dp_turn = decision_points[current_decision_index].get("after_turn", 0)
        # The retreat turn is the next turn in the log after dp_turn
        for i, turn in enumerate(log):
            if turn.get("turn", 0) > dp_turn:
                retreat_turn_idx = i
                break

    # Add retreat turn results (may encounter something on the way out)
    retreat_log = None
    if retreat_turn_idx is not None and retreat_turn_idx < len(log):
        retreat_log = log[retreat_turn_idx]
        for event in retreat_log.get("events", []):
            treasure = event.get("treasure")
            if treasure:
                partial_loot += treasure.get("gold", 0)
                partial_xp += treasure.get("xp_value", 0)
            combat = event.get("combat")
            if combat:
                partial_xp += combat.get("xp_earned", 0)
        partial_deaths.extend(retreat_log.get("deaths", []))

    # Calculate the cutoff turn for the log (everything up to retreat turn)
    cutoff_turn = None
    if retreat_log:
        cutoff_turn = retreat_log.get("turn", 0)
    elif current_decision_index < len(decision_points):
        cutoff_turn = decision_points[current_decision_index].get("after_turn", 0)

    member_count = sim_result.get("party_status", {}).get("members_total", 1)

    return {
        "treasure_total": partial_loot,
        "xp_earned": partial_xp,
        "xp_per_party_member": partial_xp // max(1, member_count),
        "dead_members": partial_deaths,
        "retreated": True,
        "retreat_cutoff_turn": cutoff_turn,
        "phases_completed": current_decision_index + 1,
    }
