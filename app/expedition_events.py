"""Post-process simulation results to insert interactive decision points.

Takes raw simulation output and splits it into phases separated by
decision points (PC death, big haul, stairs discovery).
"""

import random
from app.dungeons import DUNGEON_LEVEL_NAMES

# Treasure threshold for "big haul" event (gold pieces in a single turn)
BIG_HAUL_THRESHOLD = 8

BASE_STAIRS_CHANCE = 0.05


def build_phases(sim_result: dict, dungeon_level: int, max_dungeon_level: int) -> dict:
    """Scan simulation results and build phases with decision points.

    Mutates sim_result by adding 'phases' and 'decision_points' keys.
    Returns the modified sim_result.
    """
    log = sim_result.get("log", [])
    dead_members = set(sim_result.get("dead_members", []))
    total_levels = len(DUNGEON_LEVEL_NAMES)

    phases = []
    decision_points = []
    current_phase_start = 0
    deaths_seen_so_far = set()
    loot_so_far = 0
    xp_so_far = 0
    stairs_offered = False

    for i, turn in enumerate(log):
        turn_loot = 0
        turn_xp = 0
        turn_deaths = []

        for event in turn.get("events", []):
            # Tally loot from this turn
            treasure = event.get("treasure")
            if treasure:
                turn_loot += treasure.get("gold", 0)
                turn_xp += treasure.get("xp_value", 0)

            combat = event.get("combat")
            if combat:
                turn_xp += combat.get("xp_earned", 0)

        loot_so_far += turn_loot
        xp_so_far += turn_xp

    total_turns = len(log)
    if total_turns == 0:
        sim_result["phases"] = [_make_phase(0, 0, sim_result)]
        sim_result["decision_points"] = []
        return sim_result

    decision_points = []
    treasure_total = sim_result.get("treasure_total", 0)

    # Decision point 1: If anyone died, trigger at ~60% through the expedition
    if dead_members:
        death_turn = max(1, int(total_turns * 0.6))
        first_dead = list(dead_members)[0]
        decision_points.append({
            "after_turn": death_turn,
            "type": "death",
            "message": f"{first_dead} has fallen! Do you press on or retreat?",
            "dead_member": first_dead,
            "options": ["press_on", "retreat"],
        })

    # Decision point 2: If treasure is significant, trigger at ~40% through
    if treasure_total >= BIG_HAUL_THRESHOLD:
        haul_turn = max(1, int(total_turns * 0.4))
        # Don't place at same turn as death
        if any(dp["after_turn"] == haul_turn for dp in decision_points):
            haul_turn = max(1, haul_turn - 1)
        decision_points.append({
            "after_turn": haul_turn,
            "type": "big_haul",
            "message": f"Your party found a massive treasure hoard! Secure the loot and retreat, or press deeper?",
            "loot_so_far": treasure_total // 2,  # roughly half found by this point
            "options": ["press_on", "retreat"],
        })

    # Decision point 3: Stairs (only at deepest unlocked level, with more levels to go)
    if dungeon_level >= max_dungeon_level and dungeon_level < total_levels:
        # TODO: add building bonuses to stairs_chance
        stairs_chance = BASE_STAIRS_CHANCE
        if random.random() < stairs_chance:
            stairs_turn = max(1, int(total_turns * 0.75))
            # Don't collide with existing decision points
            existing_turns = {dp["after_turn"] for dp in decision_points}
            while stairs_turn in existing_turns and stairs_turn > 0:
                stairs_turn -= 1
            if stairs_turn > 0:
                next_level = dungeon_level + 1
                next_name = DUNGEON_LEVEL_NAMES[dungeon_level] if dungeon_level < total_levels else "unknown depths"
                decision_points.append({
                    "after_turn": stairs_turn,
                    "type": "stairs",
                    "message": f"Your party discovered stairs leading down to {next_name}! (Level {next_level})",
                    "new_level": next_level,
                    "new_level_name": next_name,
                    "options": ["press_on", "retreat"],
                })

    # Sort decision points by turn
    decision_points.sort(key=lambda dp: dp["after_turn"])

    # Build phases from decision points
    phases = []
    phase_boundaries = [0] + [dp["after_turn"] for dp in decision_points] + [total_turns]

    for idx in range(len(phase_boundaries) - 1):
        start = phase_boundaries[idx]
        end = phase_boundaries[idx + 1]
        phase = _make_phase_from_log(start, end, log, sim_result, dead_members, total_turns)
        phases.append(phase)

    sim_result["phases"] = phases
    sim_result["decision_points"] = decision_points
    return sim_result


def _make_phase_from_log(
    start_turn: int,
    end_turn: int,
    log: list,
    sim_result: dict,
    all_dead: set,
    total_turns: int,
) -> dict:
    """Build a phase dict for turns [start_turn, end_turn)."""
    phase_loot = 0
    phase_xp = 0

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

    # Distribute deaths proportionally: deaths happen in later phases
    total_dead = list(all_dead)
    phase_deaths = []
    if total_dead and end_turn == total_turns:
        # All remaining deaths assigned to the last phase
        phase_deaths = total_dead

    return {
        "start_turn": start_turn,
        "end_turn": end_turn,
        "loot": phase_loot,
        "xp": phase_xp,
        "deaths": phase_deaths,
    }


def calculate_retreat_results(sim_result: dict, phases_completed: int) -> dict:
    """Calculate partial results when player retreats after N phases.

    Returns a modified sim_result with reduced totals.
    """
    phases = sim_result.get("phases", [])
    completed = phases[:phases_completed]

    partial_loot = sum(p["loot"] for p in completed)
    partial_xp = sum(p["xp"] for p in completed)
    # On retreat, no deaths (they got out before the worst happened)
    # unless deaths were in completed phases
    partial_deaths = []
    for p in completed:
        partial_deaths.extend(p.get("deaths", []))

    return {
        "treasure_total": partial_loot,
        "xp_earned": partial_xp,
        "xp_per_party_member": partial_xp // max(1, sim_result.get("party_status", {}).get("members_total", 1)),
        "dead_members": partial_deaths,
        "retreated": True,
        "phases_completed": phases_completed,
    }
