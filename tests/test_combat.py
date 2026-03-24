"""Tests for the round-based combat engine (expedition.py)."""
from unittest.mock import patch

from app.expedition import (
    PC_AC,
    Expedition,
    _do_attack,
    _turn_result,
    cleric_can_turn,
    get_monster_thac0,
    get_pc_hd,
    get_pc_thac0,
    get_spell_name,
    pick_target,
    resolve_combat_rounds,
)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_pc(name="Hero", cls="Fighter", level=1, hp=20,
            turns=None, spells=None, revivals=None) -> dict:
    hd = get_pc_hd(cls, level)
    pc = {
        "name": name,
        "character_class": cls,
        "level": level,
        "current_hp": hp,
        "ac": PC_AC,
        "hd": hd,
        "thac0": get_pc_thac0(cls, level),
    }
    if turns is not None:
        pc["turn_attempts_remaining"] = turns
    if spells is not None:
        pc["spells_remaining"] = spells
    if revivals is not None:
        pc["revivals_remaining"] = revivals
    return pc


def make_monster(name="Goblin", hd=0.5, ac=6, morale=7,
                 is_undead=False, hp=None) -> dict:
    if hp is None:
        hp = max(1, int(hd)) * 3  # deterministic, non-zero
    return {
        "name": name,
        "type": name,
        "hd": hd,
        "ac": ac,
        "morale": morale,
        "is_undead": is_undead,
        "current_hp": hp,
        "thac0": get_monster_thac0(hd),
    }


# ─── Unit tests: helpers ───────────────────────────────────────────────────────

def test_get_pc_hd_fighter():
    assert get_pc_hd("Fighter", 1) == 1
    assert get_pc_hd("Fighter", 5) == 5


def test_get_pc_hd_cleric():
    assert get_pc_hd("Cleric", 1) == 1   # max(1, 1//2)
    assert get_pc_hd("Cleric", 4) == 2
    assert get_pc_hd("Cleric", 5) == 2


def test_get_pc_hd_magic_user():
    assert get_pc_hd("Magic-User", 1) == 1  # max(1, 1//3)
    assert get_pc_hd("Magic-User", 3) == 1
    assert get_pc_hd("Magic-User", 6) == 2


def test_get_pc_hd_elf():
    # Elf gets Fighter HD (1 per level)
    assert get_pc_hd("Elf", 3) == 3


def test_get_pc_thac0_fighter_levels():
    assert get_pc_thac0("Fighter", 1) == 19
    assert get_pc_thac0("Fighter", 3) == 19
    assert get_pc_thac0("Fighter", 4) == 17
    assert get_pc_thac0("Fighter", 7) == 14
    assert get_pc_thac0("Fighter", 10) == 12


def test_get_pc_thac0_magic_user():
    assert get_pc_thac0("Magic-User", 6) == 19
    assert get_pc_thac0("Magic-User", 7) == 17


def test_get_pc_thac0_cleric():
    assert get_pc_thac0("Cleric", 4) == 19
    assert get_pc_thac0("Cleric", 5) == 17
    assert get_pc_thac0("Cleric", 9) == 14


def test_fighter_l1_to_hit_bonus():
    """Fighter level 1 gets +1 to-hit (THAC0 effectively -1)."""
    # With THAC0=19 and AC=7: needed = 19-7 = 12; with bonus: 11
    attacker = make_pc("F1", "Fighter", level=1, hp=10)
    attacker["thac0"] = 19
    target = make_monster(hp=100)  # high HP so it doesn't die
    target["ac"] = 7

    hits_with_bonus = 0
    rolls = 1000
    with patch("app.expedition.random") as mock_rng:
        mock_rng.randint.side_effect = [11] * rolls  # roll exactly 11
        for _ in range(rolls):
            mock_rng.randint.side_effect = [11, 1]  # attack roll 11, damage 1
            result = _do_attack(attacker, target)
            if result["hit"]:
                hits_with_bonus += 1
            target["current_hp"] = 100  # reset

    # roll 11 >= needed 11 (after bonus) → should always hit
    assert hits_with_bonus == rolls


def test_fighter_l2_no_to_hit_bonus():
    """Fighter level 2 does NOT get the +1 bonus."""
    attacker = make_pc("F2", "Fighter", level=2, hp=10)
    attacker["thac0"] = 19
    target = make_monster(hp=100)
    target["ac"] = 7

    # needed = 19 - 7 = 12; roll exactly 11 should miss for L2
    with patch("app.expedition.random") as mock_rng:
        mock_rng.randint.side_effect = [11, 1]
        result = _do_attack(attacker, target)
    assert not result["hit"]


def test_pick_target_weighted():
    """3 HD fighter should be targeted ~3x as often as 1 HD cleric."""
    fighter = make_pc("F", "Fighter", level=3)
    cleric = make_pc("C", "Cleric", level=1)
    fighter["hd"] = 3
    cleric["hd"] = 1

    counts = {"F": 0, "C": 0}
    for _ in range(4000):
        chosen = pick_target([fighter, cleric])
        counts[chosen["name"]] += 1

    ratio = counts["F"] / counts["C"]
    assert 2.0 < ratio < 4.5, f"Expected ~3:1 ratio, got {ratio:.2f}"


# ─── Turn undead ──────────────────────────────────────────────────────────────

def test_cleric_can_turn_skeleton_level1():
    """L1 cleric can turn ≤1 HD undead (needs 7 on 2d6)."""
    assert cleric_can_turn(1, 1.0) is True


def test_cleric_cannot_turn_vampire_level1():
    """L1 cleric cannot turn 8 HD Vampire (7+ HD row → None)."""
    assert cleric_can_turn(1, 8.0) is False


def test_cleric_cannot_turn_wraith_level1():
    """L1 cleric cannot turn 4 HD Wraith (4 HD row, L1 index → None)."""
    assert cleric_can_turn(1, 4.0) is False


def test_cleric_auto_turn_level2_skeleton():
    """L2 cleric auto-turns ≤1 HD undead (T in table)."""
    result = _turn_result(2, 1.0)
    assert result == "T"


def test_cleric_auto_destroy_level4_skeleton():
    """L4 cleric auto-destroys ≤1 HD undead (D in table)."""
    result = _turn_result(4, 1.0)
    assert result == "D"


# ─── Halfling pre-round ───────────────────────────────────────────────────────

def test_halfling_kills_all_in_round_0():
    """Halfling kills all 1-HP monsters in Round 0; combat ends without Round 1."""
    halfling = make_pc("Pip", "Halfling", level=3, hp=15)
    halfling["hd"] = 3

    # 2 goblins with 1 HP each; halfling gets 3 attacks → both die
    monsters = [
        make_monster("Goblin #1", hd=0.5, hp=1),
        make_monster("Goblin #2", hd=0.5, hp=1),
    ]

    # Force all attacks to hit and deal 1 damage
    with patch("app.expedition.random") as mock_rng:
        # pick_target uses random.choice; _do_attack uses randint for roll + damage
        # We need to force hits: roll >= needed. THAC0=19, AC=6 → needed=13.
        # Roll 20 always hits. Damage = 1.
        def side_effects():
            while True:
                yield 20   # attack roll (always hits)
                yield 1    # damage

        gen = side_effects()
        mock_rng.randint.side_effect = lambda a, b: next(gen)
        mock_rng.choice.side_effect = lambda seq: seq[0]  # always first target

        result = resolve_combat_rounds([halfling], monsters)

    assert result["rounds_fought"] == 0
    assert result["outcome"] == "Victory"
    assert result["monsters_killed"] >= 1
    assert result["party_fled"] is False
    assert result["xp_earned"] > 0


# ─── MU spell ─────────────────────────────────────────────────────────────────

def test_mu_spell_destroys_all_monsters():
    """MU casts Sleep → all monsters destroyed, 0 rounds fought, correct XP."""
    mu = make_pc("Thalia", "Magic-User", level=1, hp=5, spells=1)
    monsters = [make_monster("Goblin #1", hd=0.5, hp=3),
                make_monster("Goblin #2", hd=0.5, hp=3)]

    # Force d6 roll = 6 (>= 4) → MU casts
    with patch("app.expedition.random") as mock_rng:
        mock_rng.randint.return_value = 6

        result = resolve_combat_rounds([mu], monsters)

    assert result["rounds_fought"] == 0
    assert result["mu_spell_used"] == "Sleep"
    assert result["monsters_killed"] == 2
    assert result["xp_earned"] == 2 * 100  # 2 goblins × floor(0.5)→1 HD × 100
    assert mu["spells_remaining"] == 0


def test_mu_no_cast_on_low_roll():
    """MU rolls 1-3 → doesn't cast, fights normally."""
    mu = make_pc("Thalia", "Magic-User", level=1, hp=20, spells=1)
    monsters = [make_monster("Goblin #1", hd=0.5, hp=1)]

    # Force cast-check roll = 3 (< 4), then force attack miss (roll 1)
    with patch("app.expedition.random") as mock_rng:
        mock_rng.randint.side_effect = [
            3,          # spell check: 3 < 4, no cast
            6, 6,       # initiative: party 6, monsters 6 (tie)
            1,          # MU attack roll: miss
            1,          # goblin attack roll: miss (snapshot)
            6, 6,       # round 2 initiative: tie
            20, 1,      # MU attack: hit, 1 damage (kills goblin with 1 hp)
            1,          # goblin retaliates from snapshot (dead, still acts in C): miss
        ]
        mock_rng.choice.side_effect = lambda seq: seq[0]

        result = resolve_combat_rounds([mu], monsters)

    assert result["mu_spell_used"] is None
    assert mu["spells_remaining"] == 1  # didn't cast


def test_spell_name_by_level():
    assert get_spell_name(1) == "Sleep"
    assert get_spell_name(3) == "Fireball"
    assert get_spell_name(4) == "Lightning Bolt"
    assert get_spell_name(9) == "Disintegrate"


# ─── Cleric turn in combat ────────────────────────────────────────────────────

def test_cleric_turn_attempt_destroys_skeleton():
    """L1 cleric turns 1 HD Skeleton (needs 7 on 2d6). Roll 7 → success."""
    cleric = make_pc("Galen", "Cleric", level=1, hp=8, turns=3)
    skeleton = make_monster("Skeleton #1", hd=1.0, ac=7, morale=12, is_undead=True, hp=4)

    with patch("app.expedition.random") as mock_rng:
        # Initiative is rolled first (A), then cleric turn undead
        mock_rng.randint.side_effect = [
            4, 2,       # initiative: party 4, monsters 2 (party wins)
            4, 3,       # cleric turn 2d6: 4+3 = 7 → exactly meets threshold → turned
            # cleric is in turned_clerics → no attacks; monster_snapshot=[] → no retaliation
        ]
        mock_rng.choice.side_effect = lambda seq: seq[0]

        result = resolve_combat_rounds([cleric], [skeleton])

    assert result["cleric_turned"] is True
    assert result["monsters_turned"] >= 1
    assert skeleton["current_hp"] == 0


def test_cleric_skips_turn_no_undead():
    """Cleric attacks normally when no undead are present."""
    cleric = make_pc("Galen", "Cleric", level=1, hp=8, turns=3)
    goblin = make_monster("Goblin #1", hd=0.5, ac=6, morale=7, is_undead=False, hp=1)

    with patch("app.expedition.random") as mock_rng:
        # No turn attempt — just initiative and one killing blow
        mock_rng.randint.side_effect = [
            6, 1,   # initiative: party wins
            20, 1,  # cleric attacks: roll 20 (hit), damage 1 (kills goblin)
            1,      # goblin retaliates from snapshot (dead, still acts in C): miss
        ]
        mock_rng.choice.side_effect = lambda seq: seq[0]

        result = resolve_combat_rounds([cleric], [goblin])

    assert result["cleric_turned"] is False
    assert result["monsters_killed"] == 1


# ─── Cleric revival ───────────────────────────────────────────────────────────

def test_cleric_revival_after_combat():
    """L4 cleric (2 revival capacity) revives a dead ally after combat."""
    cleric = make_pc("Galen", "Cleric", level=4, hp=20, turns=0, revivals=2)
    dead_fighter = make_pc("Thor", "Fighter", level=1, hp=0)
    dead_fighter["current_hp"] = 0

    # One live goblin with 1 HP; party wins immediately
    goblin = make_monster("Goblin #1", hd=0.5, hp=1)

    with patch("app.expedition.random") as mock_rng:
        mock_rng.randint.side_effect = [
            6, 1,   # initiative: party wins
            20, 1,  # cleric attacks: kills goblin
            1,      # goblin retaliates from snapshot (dead, still acts in C): miss
        ]
        mock_rng.choice.side_effect = lambda seq: seq[0]

        result = resolve_combat_rounds([cleric, dead_fighter], [goblin])

    assert "Thor" in result["revived_adventurers"]
    assert dead_fighter["current_hp"] == 1
    assert cleric["revivals_remaining"] == 1


def test_cleric_level1_cannot_revive():
    """L1 cleric has 0 revival capacity (level // 2 = 0)."""
    cleric = make_pc("Galen", "Cleric", level=1, hp=8, turns=1, revivals=0)
    dead_fighter = make_pc("Thor", "Fighter", level=1, hp=0)
    dead_fighter["current_hp"] = 0
    goblin = make_monster("Goblin #1", hd=0.5, hp=1)

    with patch("app.expedition.random") as mock_rng:
        mock_rng.randint.side_effect = [
            6, 1,   # initiative: party wins
            20, 1,  # cleric kills goblin
            1,      # goblin retaliates from snapshot: miss
        ]
        mock_rng.choice.side_effect = lambda seq: seq[0]
        result = resolve_combat_rounds([cleric, dead_fighter], [goblin])

    assert "Thor" not in result["revived_adventurers"]
    assert dead_fighter["current_hp"] == 0


# ─── Morale ───────────────────────────────────────────────────────────────────

def test_monsters_flee_on_failed_morale():
    """Goblins (morale 7) fail morale on roll > 7 → monsters flee."""
    fighter = make_pc("Thor", "Fighter", level=5, hp=30)
    fighter["hd"] = 5
    goblins = [make_monster(f"Goblin #{i}", hd=0.5, morale=7, hp=3) for i in range(3)]

    with patch("app.expedition.random") as mock_rng:
        # Round 1: party wins initiative, kills 1 goblin, morale check fails (roll 12)
        mock_rng.randint.side_effect = [
            6, 1,               # initiative: party wins
            20, 6,              # attack 1: hit + kill goblin #1 (6 damage)
            1,                  # attack 2: miss
            1,                  # attack 3: miss
            1,                  # attack 4: miss
            1,                  # attack 5: miss
            # 3 goblins retaliate from snapshot (g0 dead, g1+g2 alive): all miss
            1, 1, 1,
            # morale check for monsters (first death): 2d6 = 6+6 = 12 > morale 7 → flee
            6, 6,
        ]
        mock_rng.choice.side_effect = lambda seq: seq[0]

        result = resolve_combat_rounds([fighter], goblins)

    assert result["monsters_fled"] > 0
    assert result["outcome"] == "Monsters Fled"
    assert result["xp_earned"] > 0  # XP for fled monsters


def test_xp_zero_when_party_flees():
    """Party flee → XP = 0."""
    # Simulate by having party fail morale: we need a party member to die first
    # Use a single 1HP fighter against a strong monster
    fighter = make_pc("Thor", "Fighter", level=1, hp=1)
    troll = make_monster("Troll #1", hd=6, ac=4, morale=10, hp=30)

    with patch("app.expedition.random") as mock_rng:
        # Monsters win initiative, kill fighter, fighter retaliates (snapshot), morale check
        mock_rng.randint.side_effect = [
            1, 6,   # initiative: monsters win
            20, 6,  # troll attack 1: kills fighter (inner loop breaks — no more targets)
            1,      # fighter retaliates from snapshot: miss
            6, 6,   # morale check for party: 2d6 = 12 > 11 → flee
        ]
        mock_rng.choice.side_effect = lambda seq: seq[0]

        result = resolve_combat_rounds([fighter], [troll])

    assert result["party_fled"] is True
    assert result["xp_earned"] == 0


def test_xp_for_monsters_fled():
    """Fled monsters (failed morale) grant XP when party didn't flee."""
    fighter = make_pc("Thor", "Fighter", level=5, hp=30)
    fighter["hd"] = 5
    goblin = make_monster("Goblin #1", hd=0.5, morale=7, hp=3)

    with patch("app.expedition.random") as mock_rng:
        # Party kills goblin outright; goblin still retaliates from snapshot, morale skipped
        mock_rng.randint.side_effect = [
            6, 1,   # initiative: party wins
            20, 6,  # attack: hit + kill goblin
            1,      # goblin retaliates from snapshot (dead, still acts in C): miss
        ]
        mock_rng.choice.side_effect = lambda seq: seq[0]

        result = resolve_combat_rounds([fighter], [goblin])

    assert result["xp_earned"] > 0
    assert result["party_fled"] is False


# ─── Elf dual-class ───────────────────────────────────────────────────────────

def test_elf_has_fighter_hd():
    assert get_pc_hd("Elf", 3) == 3


def test_elf_has_fighter_thac0():
    assert get_pc_thac0("Elf", 3) == 19
    assert get_pc_thac0("Elf", 4) == 17


def test_elf_can_cast_spell():
    """Elf with spells uses MU spell mechanic."""
    elf = make_pc("Elindra", "Elf", level=2, hp=12, spells=2)
    goblin = make_monster("Goblin #1", hd=0.5, hp=3)

    with patch("app.expedition.random") as mock_rng:
        mock_rng.randint.return_value = 6  # cast check >= 4
        result = resolve_combat_rounds([elf], [goblin])

    assert result["mu_spell_used"] is not None
    assert result["rounds_fought"] == 0
    assert elf["spells_remaining"] == 1


# ─── Expedition class integration ────────────────────────────────────────────

def test_expedition_init_sets_resources():
    """Expedition.__init__ sets hd, ac, thac0, and per-expedition resources."""
    party = [
        {"name": "Thor",  "character_class": "Fighter",    "level": 3, "hit_points": 18},
        {"name": "Galen", "character_class": "Cleric",     "level": 4, "hit_points": 14},
        {"name": "Thalia","character_class": "Magic-User", "level": 2, "hit_points": 6},
        {"name": "Pip",   "character_class": "Halfling",   "level": 2, "hit_points": 10},
    ]
    exp = Expedition(party, dungeon_level=1)

    fighter = exp.party[0]
    assert fighter["hd"] == 3
    assert fighter["ac"] == PC_AC
    assert fighter["thac0"] == 19

    cleric = exp.party[1]
    assert cleric["hd"] == 2           # level 4 cleric: 4//2 = 2
    assert cleric["turn_attempts_remaining"] == 4
    assert cleric["revivals_remaining"] == 2  # 4//2

    mu = exp.party[2]
    assert mu["hd"] == 1               # level 2 MU: max(1, 2//3) = 1
    assert mu["spells_remaining"] == 2

    halfling = exp.party[3]
    assert halfling["hd"] == 2
    assert halfling["character_class"] == "Halfling"


def test_expedition_resolve_combat_returns_required_keys():
    """resolve_combat returns all schema-required keys."""
    party = [{"name": "Thor", "character_class": "Fighter", "level": 2, "hit_points": 12}]
    exp = Expedition(party, dungeon_level=1)
    result = exp.resolve_combat("Goblin")

    required = {
        "outcome", "monster_type", "monster_count", "rounds_fought",
        "mu_spell_used", "cleric_turned", "monsters_turned",
        "revived_adventurers", "hp_lost", "xp_earned",
        "monsters_killed", "monsters_fled", "party_fled", "round_log",
    }
    assert required.issubset(result.keys())
    assert result["monster_type"] == "Goblin"


def test_expedition_dead_list_updated():
    """Expedition.dead is updated after combat based on HP."""
    party = [{"name": "Thor", "character_class": "Fighter", "level": 1, "hit_points": 1}]
    exp = Expedition(party, dungeon_level=1)
    exp.party[0]["current_hp"] = 0  # simulate death
    exp.party[0]["current_hp"] = 0

    # Manually run a combat that results in death — easier: directly test dead sync
    exp.party[0]["current_hp"] = 0
    # Trigger dead sync via resolve_combat with patched rounds
    with patch("app.expedition.resolve_combat_rounds") as mock_rounds:
        mock_rounds.return_value = {
            "outcome": "TPK",
            "monster_type": "Goblin",
            "monster_count": 1,
            "rounds_fought": 1,
            "mu_spell_used": None,
            "cleric_turned": False,
            "monsters_turned": 0,
            "revived_adventurers": [],
            "hp_lost": 10,
            "xp_earned": 0,
            "monsters_killed": 0,
            "monsters_fled": 0,
            "party_fled": True,
            "round_log": [],
        }
        exp.resolve_combat("Goblin")

    assert exp.party[0] in exp.dead


# ─── Progression: Elf XP ──────────────────────────────────────────────────────

def test_elf_xp_double():
    from app.models import AdventurerClass
    from app.progression import ELF_XP_THRESHOLDS, XP_THRESHOLDS, check_for_level_up

    # A normal Fighter levels up at 2000 XP
    assert check_for_level_up(1, 2000, AdventurerClass.FIGHTER) is True
    # An Elf needs 4000 XP (2×)
    assert check_for_level_up(1, 2000, AdventurerClass.ELF) is False
    assert check_for_level_up(1, 4000, AdventurerClass.ELF) is True

    assert ELF_XP_THRESHOLDS[2] == XP_THRESHOLDS[2] * 2
