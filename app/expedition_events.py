"""Post-process simulation results to detect noteworthy events and auto-resolve
party decisions about them.

Every non-empty room becomes a decision point. When auto-decide is enabled the
existing auto-resolve machinery handles them silently. When disabled the player
sees the full expedition event modal for each one.

Parties auto-decide whether to press on or retreat based on event type:
deaths make retreat more likely (66%), big hauls tempt retreat (33%).
"""

import random

from app.dungeons import DUNGEON_LEVEL_NAMES

# Treasure threshold for "big haul" event (gold-equivalent value in a single turn)
BIG_HAUL_THRESHOLD = 8


def _format_coins(gold: int, silver: int, copper: int) -> str:
    """Format coin amounts into a readable string like '5gp 20sp'."""
    parts = []
    if gold:
        parts.append(f"{gold}gp")
    if silver:
        parts.append(f"{silver}sp")
    if copper:
        parts.append(f"{copper}cp")
    return " ".join(parts) if parts else "0gp"


def auto_decide(event_type: str, party: list = None) -> str:
    """Have the party automatically decide what to do at a decision point.

    Returns 'press_on' or 'retreat'.
    Retreat probability varies by event type:
      - death: 66% retreat (morale shaken by losing a companion)
      - big_haul: 33% retreat (tempted to secure the loot)
      - other: 50% retreat (coin flip)
    """
    retreat_chance = {"death": 0.66, "big_haul": 0.33}.get(event_type, 0.50)
    return "retreat" if random.random() < retreat_chance else "press_on"


def _summarize_turn(turn: dict) -> str:
    """Produce a compact one-line summary of a turn for the collapsed log."""
    turn_num = turn.get("turn", "?")
    events = turn.get("events", [])
    deaths = turn.get("deaths", [])

    if not events and not deaths:
        return f"Turn {turn_num}: Empty room"

    parts = []
    for event in events:
        if event.get("combat"):
            combat = event["combat"]
            monster = combat.get("monster_type", "monsters")
            count = combat.get("monster_count", 1)
            xp = combat.get("xp_earned", 0)
            if count > 1:
                # Simple English plural: Wolf→Wolves, most others just add 's'
                if monster.endswith("f"):
                    monster_label = f"{count} {monster[:-1]}ves"
                elif monster.endswith("fe"):
                    monster_label = f"{count} {monster[:-2]}ves"
                else:
                    monster_label = f"{count} {monster}s"
            else:
                monster_label = monster
            outcome = combat.get("outcome", "")
            parts.append(f"Fought {monster_label} ({outcome}, +{xp} XP)")
        elif event.get("treasure"):
            t = event["treasure"]
            gold = t.get("gold", 0)
            silver = t.get("silver", 0)
            copper = t.get("copper", 0)
            loot_parts = []
            if gold:
                loot_parts.append(f"{gold}gp")
            if silver:
                loot_parts.append(f"{silver}sp")
            if copper:
                loot_parts.append(f"{copper}cp")
            parts.append(f"Found {' '.join(loot_parts)}" if loot_parts else "Found treasure")
        elif event.get("trap_damage"):
            victims = event.get("trap_victims", [])
            if victims:
                victim_parts = [f"{v['name']} ({v['damage']})" for v in victims]
                parts.append(f"Trap! {', '.join(victim_parts)}")
            else:
                parts.append(f"Trap! {event['trap_damage']} damage")
        elif event.get("type") == "Clue":
            parts.append("Found a clue")

    if deaths:
        parts.append(f"Deaths: {', '.join(deaths)}")

    return f"Turn {turn_num}: {'; '.join(parts)}" if parts else f"Turn {turn_num}: Empty room"


def _classify_turn(turn: dict) -> tuple[str, str]:
    """Classify a turn into a decision point type and message.

    Returns (type, message). Priority: death > big_haul > combat > trap > treasure > clue.
    """
    events = turn.get("events", [])
    deaths = turn.get("deaths", [])

    has_combat = False
    has_big_haul = False
    has_trap = False
    has_treasure = False
    has_clue = False
    monster_name = ""
    monster_count = 0
    trap_damage = 0
    treasure_gold = 0
    treasure_silver = 0
    treasure_copper = 0

    for event in events:
        if event.get("combat"):
            has_combat = True
            monster_name = event["combat"].get("monster_type", "monsters")
            monster_count = event["combat"].get("monster_count", 1)
        if event.get("treasure"):
            has_treasure = True
            treasure_gold = event["treasure"].get("gold", 0)
            treasure_silver = event["treasure"].get("silver", 0)
            treasure_copper = event["treasure"].get("copper", 0)
            # Compare GP-equivalent value for big haul threshold
            gp_equivalent = treasure_gold + treasure_silver / 10 + treasure_copper / 100
            if gp_equivalent >= BIG_HAUL_THRESHOLD:
                has_big_haul = True
        if event.get("trap_damage"):
            has_trap = True
            trap_damage = event["trap_damage"]
        if event.get("type") == "Clue":
            has_clue = True

    # Build readable treasure string
    treasure_label = _format_coins(treasure_gold, treasure_silver, treasure_copper)

    if deaths:
        dead_names = ", ".join(deaths)
        return "death", f"{dead_names} {'has' if len(deaths) == 1 else 'have'} fallen in the dungeon!"

    if has_big_haul:
        return "big_haul", f"Your party found a massive treasure hoard worth {treasure_label}!"

    if has_combat:
        if monster_count > 1:
            if monster_name.endswith("f"):
                monster_label = f"{monster_count} {monster_name[:-1]}ves"
            elif monster_name.endswith("fe"):
                monster_label = f"{monster_count} {monster_name[:-2]}ves"
            else:
                monster_label = f"{monster_count} {monster_name}s"
        else:
            monster_label = monster_name
        return "combat", f"Your party fought {monster_label}."

    if has_trap:
        return "trap", f"Your party triggered a trap dealing {trap_damage} damage!"

    if has_treasure:
        return "treasure", f"Your party found unguarded treasure worth {treasure_label}."

    if has_clue:
        return "clue", "Your party discovered a mysterious clue."

    return "room", "Your party explored a room."


def build_phases(sim_result: dict, dungeon_level: int, max_dungeon_level: int) -> dict:
    """Scan simulation log and build decision points for every non-empty turn.

    Mutates sim_result by adding 'phases', 'decision_points', and
    'turn_summaries' keys. Returns the modified sim_result.
    """
    log = sim_result.get("log", [])
    total_turns = len(log)
    total_levels = len(DUNGEON_LEVEL_NAMES)

    if total_turns == 0:
        sim_result["phases"] = []
        sim_result["decision_points"] = []
        sim_result["turn_summaries"] = []
        return sim_result

    decision_points = []
    turn_summaries = []

    # Track cumulative deaths to detect TPK
    all_dead: set[str] = set()
    party_size = len(sim_result.get("party_classes", []))

    for i, turn in enumerate(log):
        turn_num = turn.get("turn", i + 1)
        turn_summaries.append(_summarize_turn(turn))

        events = turn.get("events", [])
        deaths = turn.get("deaths", [])
        all_dead.update(deaths)

        # Skip empty rooms — no decision point
        if not events and not deaths:
            continue

        event_type, message = _classify_turn(turn)

        # Skip trivial rooms (clues, empty) — not worth a popup
        if event_type in ("clue", "room"):
            continue

        is_tpk = party_size > 0 and len(all_dead) >= party_size

        decision_points.append({
            "after_turn": turn_num,
            "type": "tpk" if is_tpk else event_type,
            "message": message,
            "options": ["press_on", "retreat"],
        })

    # Stairs discovery — 1.5% chance per turn at the deepest unlocked level.
    # Each Dwarf in the party adds +1% per turn.
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
    sim_result["turn_summaries"] = turn_summaries
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
