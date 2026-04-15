import random
import sys
from enum import Enum

from app.class_config import get_combat_hd, get_thac0, get_to_hit_bonus
from app.monsters import (
    get_monster_ac,
    get_monster_count,
    get_monster_hit_dice,
    get_monster_morale,
    get_random_monster,
    is_monster_undead,
)

# Re-export with old names for backward compatibility
get_pc_hd = get_combat_hd
get_pc_thac0 = get_thac0

# ─── PC combat constants ──────────────────────────────────────────────────────

PC_AC = 7  # All PCs in leather-equivalent armor (descending AC system)


def get_monster_thac0(hit_dice: float) -> int:
    """Monster THAC0 based on HD."""
    return max(10, 20 - int(hit_dice))


# ─── Target selection (bag-of-stones) ────────────────────────────────────────

def pick_target(targets: list[dict]) -> dict:
    """Pick a random target weighted by HD. Each whole HD = 1 stone, min 1."""
    bag = []
    for t in targets:
        bag.extend([t] * max(1, int(t["hd"])))
    return random.choice(bag)


# ─── Turn undead ──────────────────────────────────────────────────────────────

# [hd_row][cleric_level_index]
# hd_row 0=≤1HD … 6=7+HD   |   level_index 0=L1 … 7=L8+
# None=cannot, int=2d6 threshold, "T"=auto-turn/destroy, "D"=auto-destroy
_TURN_TABLE = [
    [7,    "T",  "T",  "D",  "D",  "D",  "D",  "D"],   # ≤1 HD
    [9,     7,   "T",  "T",  "D",  "D",  "D",  "D"],   # 2 HD
    [11,    9,    7,   "T",  "T",  "D",  "D",  "D"],   # 3 HD
    [None, 11,    9,    7,   "T",  "T",  "D",  "D"],   # 4 HD
    [None, None, 11,    9,    7,   "T",  "T",  "D"],   # 5 HD
    [None, None, None, 11,    9,    7,   "T",  "T"],   # 6 HD
    [None, None, None, None, 11,    9,    7,   "T"],   # 7+ HD
]


def _undead_hd_row(hd: float) -> int:
    if hd <= 1:
        return 0
    if hd <= 2:
        return 1
    if hd <= 3:
        return 2
    if hd <= 4:
        return 3
    if hd <= 5:
        return 4
    if hd <= 6:
        return 5
    return 6


def _turn_result(cleric_level: int, monster_hd: float):
    """Turn table entry: None, int, 'T', or 'D'."""
    return _TURN_TABLE[_undead_hd_row(monster_hd)][min(cleric_level - 1, 7)]


def cleric_can_turn(cleric_level: int, monster_hd: float) -> bool:
    return _turn_result(cleric_level, monster_hd) is not None


def _do_turn_attempt(cleric: dict, monsters: list[dict]) -> tuple[list[dict], dict]:
    """Spend one turn attempt. Returns (destroyed_monsters, log_entry)."""
    cleric_level = cleric["level"]
    destroyed = []
    log_entries = []

    # OSE: First roll 2d6 to see if any are turned
    # However, since monsters may have different HD, we check against the LOWEST HD first
    # to see if a turn is even possible.
    sorted_monsters = sorted(monsters, key=lambda m: m["hd"])
    lowest_hd = sorted_monsters[0]["hd"]
    result = _turn_result(cleric_level, lowest_hd)

    if result is None:
        return [], {"cleric": cleric["name"], "turn_log": [], "message": "Undead too powerful"}

    turn_success = False
    roll_to_turn = 0
    if result in ("T", "D"):
        turn_success = True
    else:
        roll_to_turn = random.randint(1, 6) + random.randint(1, 6)
        if roll_to_turn >= result:
            turn_success = True
        else:
            log_entries.append({"monster": "all", "result": "resisted",
                                 "roll": roll_to_turn, "needed": result})

    if turn_success:
        # Roll 2d6 for total HD affected
        hd_affected = random.randint(1, 6) + random.randint(1, 6)
        remaining_hd = hd_affected

        for monster in sorted_monsters:
            if remaining_hd <= 0:
                break

            # Re-check result for THIS monster's HD
            m_result = _turn_result(cleric_level, monster["hd"])
            if m_result is None:
                continue # this specific monster too powerful

            # If the roll_to_turn was used, it must also beat this monster's needed value
            if isinstance(m_result, int) and result not in ("T", "D") and roll_to_turn < m_result:
                continue

            destroyed.append(monster)
            outcome = "destroyed" if m_result == "D" else "turned"
            log_entries.append({"monster": monster["name"], "result": outcome,
                                 "roll": roll_to_turn if isinstance(m_result, int) else None,
                                 "needed": m_result if isinstance(m_result, int) else None})
            remaining_hd -= monster["hd"]

    cleric["turn_attempts_remaining"] = max(0, cleric.get("turn_attempts_remaining", 0) - 1)
    return destroyed, {"cleric": cleric["name"], "turn_log": log_entries}


# ─── MU/Elf spell ─────────────────────────────────────────────────────────────

_SPELL_NAMES = {1: "Sleep", 2: "Hold Person", 3: "Fireball",
                4: "Lightning Bolt", 5: "Cloudkill"}


def get_spell_name(level: int) -> str:
    return _SPELL_NAMES.get(level, "Disintegrate")


# ─── Attack resolution ────────────────────────────────────────────────────────

def _do_attack(attacker: dict, target: dict) -> dict:
    """Resolve one attack. Mutates target['current_hp']. Returns log dict."""
    thac0 = attacker["thac0"]
    # Building bonus & class inherent bonus: to_hit_bonus lowers THAC0 (Training Grounds Tier I, etc.)
    thac0 -= attacker.get("to_hit_bonus", 0)
    needed = thac0 - target["ac"]
    roll = random.randint(1, 20)
    hit = roll >= needed
    damage = 0
    target_died = False
    if hit:
        damage = random.randint(1, 6) + attacker.get("damage_bonus", 0)
        damage = max(1, damage)  # minimum 1 damage on a hit
        target["current_hp"] -= damage
        if target["current_hp"] <= 0:
            target["current_hp"] = 0
            target_died = True
    return {
        "attacker": attacker["name"],
        "target": target["name"],
        "roll": roll,
        "needed": needed,
        "hit": hit,
        "damage": damage,
        "target_died": target_died,
    }


def _morale_check(side_name: str, morale: int, penalty: int = 0) -> dict:
    """2d6 morale check. Pass if roll <= morale rating (adjusted by penalty)."""
    effective_morale = morale + penalty  # penalty is negative for monsters
    roll = random.randint(1, 6) + random.randint(1, 6)
    return {"side": side_name, "roll": roll, "morale": effective_morale, "passed": roll <= effective_morale}


# ─── Core combat engine ───────────────────────────────────────────────────────

def resolve_combat_rounds(party: list[dict], monsters: list[dict], morale_penalty: int = 0) -> dict:
    """Run full round-based combat.

    party: PC combatant dicts (name, character_class, level, current_hp, ac, hd, thac0,
           turn_attempts_remaining, spells_remaining, revivals_remaining,
           to_hit_bonus, damage_bonus, has_potion)
    monsters: monster combatant dicts (name, type, hd, ac, morale, is_undead, current_hp, thac0)
    morale_penalty: penalty applied to monster morale checks (e.g. -2 from Castle)

    Mutates current_hp on both sides. Returns combat result dict.
    """
    round_log = []
    monsters_killed = 0
    monsters_fled = 0
    hp_lost_party = 0
    mu_spell_used = None
    mu_caster_name: str | None = None
    cleric_turned = False
    monsters_turned = 0
    revived_adventurers = []

    # Cumulative death counters for morale trigger tracking
    party_deaths_total = 0
    monster_deaths_total = 0
    party_morale_done: set[str] = set()    # "first", "half"
    monster_morale_done: set[str] = set()
    party_fled = False
    monsters_fled_flag = False

    def living_party() -> list[dict]:
        return [m for m in party if m["current_hp"] > 0]

    def living_monsters() -> list[dict]:
        return [m for m in monsters if m["current_hp"] > 0]

    # ── Round 0: Halfling pre-round ───────────────────────────────────────────
    halflings = [m for m in living_party() if m.get("character_class") == "Halfling"]
    if halflings and living_monsters():
        r0_attacks = []
        for halfling in halflings:
            for _ in range(halfling["hd"]):
                alive_m = living_monsters()
                if not alive_m:
                    break
                target = pick_target(alive_m)
                atk = _do_attack(halfling, target)
                r0_attacks.append(atk)
                if atk["target_died"]:
                    monsters_killed += 1
                    monster_deaths_total += 1
        round_log.append({"round": 0, "halfling_pre_round": r0_attacks})
        if not living_monsters():
            xp = sum(max(1, int(m["hd"])) * 100 for m in monsters)
            return {
                "outcome": "Victory",
                "monster_type": monsters[0]["type"],
                "monster_count": len(monsters),
                "rounds_fought": 0,
                "mu_spell_used": None,
                "cleric_turned": False,
                "monsters_turned": 0,
                "revived_adventurers": [],
                "hp_lost": 0,
                "xp_earned": xp,
                "monsters_killed": monsters_killed,
                "monsters_fled": 0,
                "party_fled": False,
                "round_log": round_log,
            }

    # ── Combat rounds ─────────────────────────────────────────────────────────
    round_num = 0
    while living_party() and living_monsters() and round_num < 20:
        round_num += 1
        round_entry: dict = {
            "round": round_num,
            "attacks": [],
            "morale_checks": [],
        }

        # Snapshot alive party at start of round (PCs killed in B still act in C)
        party_snapshot = list(living_party())

        # ── A. Initiative ──────────────────────────────────────────────────────
        party_init = random.randint(1, 6)
        monster_init = random.randint(1, 6)
        if party_init > monster_init:
            initiative = "party"
        elif monster_init > party_init:
            initiative = "monsters"
        else:
            initiative = "tie"
        round_entry["initiative_winner"] = initiative
        round_entry["initiative_rolls"] = {"party": party_init, "monsters": monster_init}

        # ── Cleric turn undead (uses their action regardless of initiative) ────
        # Deaths and counters for this round (turned monsters count toward morale)
        monster_deaths_in_round = 0
        party_deaths_in_round = 0
        turned_clerics: set[str] = set()
        round_spell_casters: set[str] = set()
        cleric_turns = []
        for pc in party_snapshot:
            if pc["current_hp"] <= 0:
                continue
            if pc.get("character_class") != "Cleric":
                continue
            if pc.get("turn_attempts_remaining", 0) <= 0:
                continue
            undead = [m for m in living_monsters() if m.get("is_undead")]
            if not undead:
                continue
            turnable = [m for m in undead if cleric_can_turn(pc["level"], m["hd"])]
            if not turnable:
                continue  # all undead too powerful — cleric attacks instead
            destroyed, turn_log = _do_turn_attempt(pc, turnable)
            cleric_turned = True
            turned_clerics.add(pc["name"])
            cleric_turns.append(turn_log)
            for m in destroyed:
                if m["current_hp"] > 0:
                    m["current_hp"] = 0
                    monsters_killed += 1
                    monster_deaths_total += 1
                    monsters_turned += 1
                    monster_deaths_in_round += 1
        if cleric_turns:
            round_entry["cleric_turns"] = cleric_turns

        monster_snapshot: list[dict] = []

        def do_party_attacks(use_snapshot: bool = False) -> None:
            nonlocal monster_deaths_in_round, monsters_killed, monster_deaths_total
            attackers = party_snapshot if use_snapshot else living_party()  # noqa: B023
            for pc in attackers:
                if pc["current_hp"] <= 0 and not use_snapshot:
                    continue
                if pc.get("name") in turned_clerics:  # noqa: B023
                    continue
                if pc.get("name") in round_spell_casters:  # noqa: B023
                    continue
                for _ in range(pc["hd"]):
                    alive_m = living_monsters()
                    if not alive_m:
                        break
                    target = pick_target(alive_m)
                    atk = _do_attack(pc, target)
                    round_entry["attacks"].append(atk)  # noqa: B023
                    if atk["target_died"]:
                        monster_deaths_in_round += 1
                        monsters_killed += 1
                        monster_deaths_total += 1

        def do_monster_attacks(use_snapshot: bool = False) -> None:
            nonlocal party_deaths_in_round, hp_lost_party, party_deaths_total
            attackers = monster_snapshot if use_snapshot else living_monsters()  # noqa: B023
            for mon in attackers:
                if mon["current_hp"] <= 0 and not use_snapshot:
                    continue
                alive_p = living_party()
                if not alive_p:
                    break
                for _ in range(max(1, int(mon["hd"]))):
                    alive_p = living_party()
                    if not alive_p:
                        break
                    target = pick_target(alive_p)
                    atk = _do_attack(mon, target)
                    hp_lost_party += atk["damage"]
                    round_entry["attacks"].append(atk)  # noqa: B023
                    if atk["target_died"]:
                        party_deaths_in_round += 1
                        party_deaths_total += 1

        # ── B & C. Attacks in initiative order ────────────────────────────────
        # MU/Elf spells fire only on the party's initiative turn.
        # Monsters killed by a spell do NOT get a retaliation attack (snapshot after spell).
        # On monster initiative, no spell fires — monsters always get at least one round.
        #
        # Spell HD limit: base spells insta-kill HD ≤ caster_level + 3 only.
        # Scrolls (spells_remaining ≤ scroll_count) insta-kill any HD.

        def _try_fire_spell() -> bool:
            """Attempt to cast a spell from the first willing caster. Returns True if a spell fired."""
            nonlocal mu_spell_used, mu_caster_name, monsters_killed, monster_deaths_in_round, monster_deaths_total
            _casters = [m for m in living_party()
                        if m.get("character_class") in ("Magic-User", "Elf")
                        and m.get("spells_remaining", 0) > 0]
            for _caster in _casters:
                if random.randint(1, 6) < 4:
                    continue  # caster didn't manage to cast this round
                is_scroll = _caster.get("spells_remaining", 0) <= _caster.get("scroll_count", 0)
                hd_limit = _caster["level"] + 3
                _all_targets = living_monsters()
                killable = _all_targets if is_scroll else [m for m in _all_targets if m["hd"] <= hd_limit]
                if not killable:
                    continue  # monsters too tough for a base spell; caster holds back
                _spell = get_spell_name(_caster["level"])
                mu_spell_used = _spell
                mu_caster_name = _caster["name"]
                _n = len(killable)
                for _m in killable:
                    _m["current_hp"] = 0
                monsters_killed += _n
                monster_deaths_in_round += _n
                monster_deaths_total += _n
                _caster["spells_remaining"] -= 1
                round_spell_casters.add(_caster["name"])  # noqa: B023
                round_entry.setdefault("spell_casts", []).append({  # noqa: B023
                    "caster": _caster["name"],
                    "spell": _spell,
                    "monsters_destroyed": _n,
                    "scroll_used": is_scroll,
                })
                return True
            return False

        if initiative == "party":
            _try_fire_spell()
            monster_snapshot = list(living_monsters())      # snapshot AFTER spell; spell-killed don't retaliate
            do_party_attacks()                               # spell casters are auto-skipped
            do_monster_attacks(use_snapshot=True)            # monsters killed in B still retaliate
        elif initiative == "monsters":
            do_monster_attacks()                             # monsters go first
            _try_fire_spell()                               # MUs cast on their turn (second)
            monster_snapshot = list(living_monsters())       # snapshot AFTER spell
            do_party_attacks(use_snapshot=True)              # spell casters are auto-skipped
        else:  # tie — simultaneous; spell fires but snapshot taken first so killed monsters still retaliate
            monster_snapshot = list(living_monsters())
            _try_fire_spell()
            do_party_attacks(use_snapshot=True)              # spell casters are auto-skipped
            do_monster_attacks(use_snapshot=True)

        # ── D. Morale checks ──────────────────────────────────────────────────
        monster_morale_val = monsters[0]["morale"] if monsters else 8

        if monster_deaths_in_round > 0 and living_monsters() and not monsters_fled_flag:
            if "first" not in monster_morale_done:
                monster_morale_done.add("first")
                check = _morale_check("monsters", monster_morale_val, morale_penalty)
                round_entry["morale_checks"].append(check)
                if not check["passed"]:
                    monsters_fled_flag = True
                    monsters_fled = len(living_monsters())
                    for m in living_monsters():
                        m["current_hp"] = 0

            if (not monsters_fled_flag
                    and "half" not in monster_morale_done
                    and monster_deaths_total >= len(monsters) / 2):
                monster_morale_done.add("half")
                check = _morale_check("monsters", monster_morale_val, morale_penalty)
                round_entry["morale_checks"].append(check)
                if not check["passed"]:
                    monsters_fled_flag = True
                    monsters_fled = len(living_monsters())
                    for m in living_monsters():
                        m["current_hp"] = 0

        if party_deaths_in_round > 0 and not party_fled:
            if "first" not in party_morale_done:
                party_morale_done.add("first")
                check = _morale_check("party", 11)
                round_entry["morale_checks"].append(check)
                if not check["passed"]:
                    party_fled = True

            if (not party_fled
                    and "half" not in party_morale_done
                    and party_deaths_total >= len(party) / 2):
                party_morale_done.add("half")
                check = _morale_check("party", 11)
                round_entry["morale_checks"].append(check)
                if not check["passed"]:
                    party_fled = True

        round_log.append(round_entry)

        if party_fled or monsters_fled_flag:
            break

    # ── Post-combat: Potion auto-revive ────────────────────────────────────────
    potion_revived = []
    if not party_fled:
        for pc in party:
            if pc["current_hp"] <= 0 and pc.get("has_potion") and pc["name"] not in revived_adventurers:
                pc["current_hp"] = 1
                pc["has_potion"] = False
                pc["potion_consumed"] = True
                potion_revived.append(pc["name"])
                revived_adventurers.append(pc["name"])

    # ── Post-combat: Cleric revival ───────────────────────────────────────────
    if not party_fled:
        for pc in party:
            if pc.get("character_class") != "Cleric":
                continue
            if pc["current_hp"] <= 0:
                continue
            if pc.get("level", 1) < 2:
                continue
            capacity = pc.get("revivals_remaining", 0)
            dead_allies = [m for m in party
                           if m["current_hp"] <= 0 and m["name"] not in revived_adventurers]
            for dead in dead_allies:
                if capacity <= 0:
                    break
                dead["current_hp"] = 1
                revived_adventurers.append(dead["name"])
                capacity -= 1
            pc["revivals_remaining"] = capacity

    # ── Post-combat: Cleric heal ──────────────────────────────────────────────
    healed_adventurers: list[dict] = []
    if not party_fled:
        for pc in party:
            if pc.get("character_class") != "Cleric":
                continue
            if pc["current_hp"] <= 0:
                continue
            charges = pc.get("heals_remaining", 0)
            while charges > 0:
                wounded = [
                    m for m in party
                    if m["current_hp"] > 0 and m["current_hp"] < m.get("hit_points", m["current_hp"])
                ]
                if not wounded:
                    break
                target = min(wounded, key=lambda m: m["current_hp"] / m.get("hit_points", 1))
                amount = random.randint(1, 6) + 1
                old_hp = target["current_hp"]
                target["current_hp"] = min(target.get("hit_points", old_hp + amount), old_hp + amount)
                healed = target["current_hp"] - old_hp
                healed_adventurers.append({"name": target["name"], "hp": healed})
                charges -= 1
            pc["heals_remaining"] = charges

    # ── Determine outcome ─────────────────────────────────────────────────────
    if party_fled:
        outcome = "Party Fled"
    elif not living_party():
        outcome = "TPK"
    elif monsters_fled_flag:
        outcome = "Monsters Fled"
    else:
        outcome = "Victory"

    # XP: floor(hd)*100 per monster killed or fled; 0 if party fled
    if party_fled:
        xp = 0
    else:
        per_monster_xp = max(1, int(monsters[0]["hd"])) * 100 if monsters else 0
        xp = per_monster_xp * (monsters_killed + monsters_fled)

    return {
        "outcome": outcome,
        "monster_type": monsters[0]["type"] if monsters else "Unknown",
        "monster_count": len(monsters),
        "rounds_fought": round_num,
        "mu_spell_used": mu_spell_used,
        "mu_caster": mu_caster_name,
        "cleric_turned": cleric_turned,
        "monsters_turned": monsters_turned,
        "revived_adventurers": revived_adventurers,
        "healed_adventurers": healed_adventurers,
        "hp_lost": hp_lost_party,
        "xp_earned": xp,
        "monsters_killed": monsters_killed,
        "monsters_fled": monsters_fled,
        "party_fled": party_fled,
        "round_log": round_log,
    }


# ─── Encounter / Expedition ───────────────────────────────────────────────────

class EncounterType(Enum):
    MONSTER = "Monster"
    TRAP = "Trap/Hazard"
    CLUE = "Clue or Empty Room"
    TREASURE = "Unguarded Treasure"


class Expedition:
    def __init__(self, party: list[dict], dungeon_level: int) -> None:
        for member in party:
            if "current_hp" not in member:
                member["current_hp"] = member.get("hit_points", 1)
            cls = member.get("character_class", "")
            level = member.get("level", 1)
            member["hd"] = get_combat_hd(cls, level)
            member["ac"] = PC_AC
            member["thac0"] = get_thac0(cls, level)
            member["to_hit_bonus"] = get_to_hit_bonus(cls)
            if cls == "Cleric":
                member.setdefault("turn_attempts_remaining", level)
                member.setdefault("revivals_remaining", level // 2)
                member.setdefault("heals_remaining", level // 2)
            if cls in ("Magic-User", "Elf"):
                base_spells = level * member.get("spell_multiplier", 1)
                scrolls = member.get("scroll_count", 0)
                member["base_spells"] = base_spells
                member.setdefault("spells_remaining", base_spells + scrolls)

        self.party = party
        self.dungeon_level = dungeon_level
        self.turns = 0
        self.encounters: list = []
        self.treasure: list = []
        self.xp_earned = 0
        self.resources_used = {"hp_lost": 0}
        self.dead: list = []

    def determine_room_contents(self) -> list[EncounterType]:
        """Roll room contents.

        1/3 chance monster (4/6 of those also have treasure).
        No-monster rooms: 1/6 each trap/clue/treasure, rest empty.
        """
        roll = random.randint(1, 6)
        if roll <= 2:
            if random.randint(1, 6) <= 4:
                return [EncounterType.MONSTER, EncounterType.TREASURE]
            return [EncounterType.MONSTER]
        sub = random.randint(1, 6)
        if sub == 1:
            return [EncounterType.TREASURE]
        if sub == 2:
            return [EncounterType.TRAP]
        if sub == 3:
            return [EncounterType.CLUE]
        return []

    def resolve_combat(self, monster_type: str) -> dict:
        """Build monster combatants and run round-based combat."""
        alive_members = [m for m in self.party if m.get("current_hp", 0) > 0]

        monster_count = get_monster_count(monster_type)
        monster_hd = get_monster_hit_dice(monster_type)
        monster_ac = get_monster_ac(monster_type)
        monster_morale = get_monster_morale(monster_type)
        undead = is_monster_undead(monster_type)
        monster_thac0 = get_monster_thac0(monster_hd)

        monsters = []
        for i in range(monster_count):
            hp = sum(random.randint(1, 6) for _ in range(max(1, int(monster_hd))))
            monsters.append({
                "name": f"{monster_type} #{i + 1}",
                "type": monster_type,
                "hd": monster_hd,
                "ac": monster_ac,
                "morale": monster_morale,
                "is_undead": undead,
                "current_hp": hp,
                "thac0": monster_thac0,
            })

        morale_penalty = self.party[0].get("morale_penalty", 0) if self.party else 0
        result = resolve_combat_rounds(alive_members, monsters, morale_penalty=morale_penalty)

        self.resources_used["hp_lost"] += result["hp_lost"]

        # Sync expedition.dead with post-combat HP state (handle revivals)
        for member in self.party:
            if member["current_hp"] <= 0 and member not in self.dead:
                self.dead.append(member)
            elif member["current_hp"] > 0 and member in self.dead:
                self.dead.remove(member)

        return result

    def generate_treasure(self, monster_type: str = None) -> dict:
        """Generate treasure using JSON config."""
        from app.treasure import generate_treasure as _gen_treasure
        return _gen_treasure(self.dungeon_level)

    def run_expedition(self, turns: int = 10) -> dict:
        """Run the expedition for a number of turns (used for standalone testing)."""
        expedition_log = []

        for _ in range(turns):
            self.turns += 1
            turn_log: dict = {"turn": self.turns, "events": []}

            for encounter_type in self.determine_room_contents():
                encounter_log: dict = {"type": encounter_type.value}

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

        return {
            "turns": self.turns,
            "party_classes": [m.get("character_class", "") for m in self.party],
            "encounters": len(self.encounters),
            "treasure_total": sum(t["gold"] for t in self.treasure),
            "treasure_silver": sum(t.get("silver", 0) for t in self.treasure),
            "treasure_copper": sum(t.get("copper", 0) for t in self.treasure),
            "special_items": [t["special_item"] for t in self.treasure if t["special_item"]],
            "xp_earned": self.xp_earned,
            "xp_per_party_member": self.xp_earned // len(self.party) if self.party else 0,
            "resources_used": self.resources_used,
            "dead": [member["name"] for member in self.dead],
            "log": expedition_log,
            "spells_left": sum(m.get("spells_remaining", 0) for m in self.party),
            "heals_left": sum(m.get("heals_remaining", 0) for m in self.party),
        }

    def _get_random_monster(self) -> str:
        return get_random_monster(self.dungeon_level)


def main(argv: list[str]) -> None:
    party = [
        {"name": "Thorgar",      "character_class": "Fighter",    "level": 3, "hit_points": 18},
        {"name": "Elindra",      "character_class": "Elf",         "level": 2, "hit_points": 12},
        {"name": "Morgrim",      "character_class": "Dwarf",       "level": 2, "hit_points": 12},
        {"name": "Thalia",       "character_class": "Magic-User",  "level": 2, "hit_points": 6},
        {"name": "Brother Galen","character_class": "Cleric",      "level": 2, "hit_points": 9},
    ]
    expedition = Expedition(party, dungeon_level=2)
    results = expedition.run_expedition(turns=20)
    print(f"Turns: {results['turns']}  |  XP: {results['xp_earned']}  |  "
          f"Gold: {results['treasure_total']}  |  Dead: {results['dead']}")


if __name__ == "__main__":
    main(sys.argv)
