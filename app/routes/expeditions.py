import json
import math
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import (
    Adventurer, Party, Expedition, ExpeditionNodeResult, ExpeditionLog, Keep,
)
from app.schemas import ExpeditionCreate, ExpeditionResult, TurnResult
from app.simulator import DungeonSimulator, calculate_loot_split
from app.progression import check_for_level_up
from app.auth import get_current_keep
from app.dungeons import DUNGEON_LEVEL_NAMES, get_level_duration
from app.expedition_events import build_phases, calculate_retreat_results

router = APIRouter()


def _make_json_safe(obj):
    """Recursively convert datetime objects to ISO strings for JSON storage."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_json_safe(v) for v in obj]
    return obj

import random as _random

# Shared simulator instance
simulator = DungeonSimulator()


def _get_combat_bonus(keep: Keep, db: Session) -> int:
    """Get party strength bonus from Training Grounds (1 per assigned Fighter)."""
    from app.models import Building
    tg = db.query(Building).filter(
        Building.keep_id == keep.id,
        Building.building_type == "training_grounds",
    ).first()
    if not tg:
        return 0
    return len(tg.assigned_adventurers)


def _get_magic_item_chance(keep: Keep, db: Session) -> float:
    """Get magic item discovery chance from Library (1% per assigned Magic-User)."""
    from app.models import Building
    lib = db.query(Building).filter(
        Building.keep_id == keep.id,
        Building.building_type == "library",
    ).first()
    if not lib:
        return 0.0
    return len(lib.assigned_adventurers) * 0.01


def resolve_expedition(expedition: Expedition, db: Session, keep: Keep) -> dict:
    """Resolve an expedition on return. If unresolved decision points remain,
    pauses with awaiting_choice. Otherwise completes fully."""
    sim_result = expedition.simulation_data
    if not sim_result:
        return {"events": []}

    decision_points = sim_result.get("decision_points", [])
    resolved = expedition.resolved_phases or 0

    # If there are still unresolved decision points, pause
    if resolved < len(decision_points):
        dp = decision_points[resolved]
        expedition.result = "awaiting_choice"
        expedition.pending_event = dp
        expedition.decision_day = expedition.return_day
        return {"events": [], "awaiting_choice": True, "pending_event": dp}

    # All decisions resolved (or none existed) — finalize
    return _finalize_expedition(expedition, sim_result, db, keep)


def _finalize_expedition(
    expedition: Expedition,
    sim_result: dict,
    db: Session,
    keep: Keep,
    retreat: bool = False,
) -> dict:
    """Apply final results to adventurers and complete the expedition."""
    from app.routes.game import format_currency, copper_to_parts

    party = expedition.party
    events = []

    expedition.result = "completed"
    expedition.finished_at = datetime.now()
    expedition.pending_event = None

    # If retreating, use partial results
    if retreat:
        resolved = expedition.resolved_phases or 0
        partial = calculate_retreat_results(sim_result, resolved)
        effective_result = {**sim_result, **partial}
    else:
        effective_result = sim_result

    # Determine which log entries to store
    full_log = effective_result.get("log", [])
    cutoff_turn = effective_result.get("retreat_cutoff_turn")
    if cutoff_turn is not None:
        stored_log = [t for t in full_log if t.get("turn", 0) <= cutoff_turn]
    else:
        stored_log = full_log

    # Store node result logs
    for node_result in stored_log:
        log_entries = stored_log
        exp_node = ExpeditionNodeResult(
            expedition_id=expedition.id,
            node_id=1,
            success=True,
            xp_earned=int(effective_result["xp_earned"] / len(log_entries)) if log_entries else 0,
            loot=int(effective_result["treasure_total"] / len(log_entries)) if log_entries else 0,
            log=json.dumps(node_result)
        )
        db.add(exp_node)

    # Replay simulation to get actual per-member HP
    dead_names = set(effective_result.get("dead_members", []))
    living_members = []

    # Determine which log entries to replay (respect retreat cutoff)
    full_log = effective_result.get("log", [])
    cutoff_turn = effective_result.get("retreat_cutoff_turn")
    if cutoff_turn is not None:
        replay_log = [t for t in full_log if t.get("turn", 0) <= cutoff_turn]
    else:
        replay_log = full_log

    if party:
        party.on_expedition = False
        party.current_expedition_id = None

        # Replay HP from simulation using starting_hp snapshot
        starting_hp = effective_result.get("starting_hp", {})
        sim_hp = _replay_member_hp(party.members, replay_log, dead_names, starting_hp)

        xp_per_member = int(effective_result.get("xp_per_party_member", 0))

        for member in party.members:
            is_dead = member.name in dead_names
            replayed_hp = sim_hp.get(member.name, member.hp_current)
            # Clamp to real hp_max (armor buffer may have inflated starting_hp)
            final_hp = max(1, min(replayed_hp, member.hp_max)) if not is_dead else 0

            log = ExpeditionLog(
                expedition_id=expedition.id,
                adventurer_id=member.id,
                xp_share=xp_per_member,
                hp_change=final_hp - member.hp_current if not is_dead else -member.hp_current,
                status="dead" if is_dead else "alive"
            )
            db.add(log)

            member.xp += xp_per_member

            if is_dead:
                member.hp_current = 0
                member.is_dead = True
                member.death_day = keep.current_day
                member.death_party_name = party.name if party else None
                member.on_expedition = False
                member.is_available = False
                events.append({"type": "death", "message": f"{member.name} died during the expedition"})
            else:
                member.hp_current = final_hp
                member.on_expedition = False
                member.is_available = True
                living_members.append(member)

        # Distribute loot
        total_loot_copper = effective_result.get("treasure_total", 0) * 100
        living_count = len(living_members)
        if living_count > 0 and total_loot_copper > 0:
            individual_share_copper = total_loot_copper // living_count
            for member in living_members:
                member.add_currency(individual_share_copper)

        if total_loot_copper > 0:
            share_copper = total_loot_copper // max(1, living_count)
            g, s, c = copper_to_parts(share_copper)
            total_g, total_s, total_c = copper_to_parts(total_loot_copper)
            events.append({"type": "loot", "message": f"Earned {format_currency(total_g, total_s, total_c)} ({format_currency(g, s, c)} each to {living_count} adventurer{'s' if living_count != 1 else ''})"})

        # Deferred upkeep
        missed_cycles = 0
        if expedition.start_day and keep.current_day > expedition.start_day:
            for day in range(expedition.start_day + 1, keep.current_day):
                if day % 30 == 0:
                    missed_cycles += 1

        deferred_upkeep_collected = 0
        if missed_cycles > 0:
            for member in list(living_members):
                cost_copper = math.floor(member.xp * 1) * missed_cycles
                if cost_copper <= 0:
                    continue
                if member.total_copper() >= cost_copper:
                    member.subtract_currency(cost_copper)
                    keep.add_treasury(cost_copper)
                    keep.total_score += cost_copper
                    deferred_upkeep_collected += cost_copper
                else:
                    remaining = member.total_copper()
                    if remaining > 0:
                        keep.add_treasury(remaining)
                        keep.total_score += remaining
                    member.gold = 0
                    member.silver = 0
                    member.copper = 0
                    member.is_bankrupt = True
                    member.bankruptcy_day = keep.current_day
                    member.is_available = False
                    member.parties = []
                    living_members.remove(member)
                    events.append({"type": "upkeep", "message": f"{member.name} couldn't pay deferred upkeep and was sent to debtor's prison"})

        if deferred_upkeep_collected > 0:
            g, s, c = copper_to_parts(deferred_upkeep_collected)
            events.append({"type": "upkeep", "message": f"Collected {format_currency(g, s, c)} in deferred upkeep from returning adventurers"})

        party.members = [m for m in party.members if not m.is_dead and not m.is_bankrupt]

    # Magic item discovery (Library bonus)
    if living_members:
        magic_chance = _get_magic_item_chance(keep, db)
        if magic_chance > 0 and _random.random() < magic_chance:
            from app.magic_items import generate_magic_item, can_equip
            from app.models import MagicItem
            dungeon_lvl = expedition.dungeon_level or 1
            item = generate_magic_item(dungeon_lvl)
            # Find a recipient who has a free slot for this item type
            eligible = [m for m in living_members if can_equip(m, item["item_type"])]
            if eligible:
                recipient = _random.choice(eligible)
                magic_item = MagicItem(
                    adventurer_id=recipient.id,
                    name=item["name"],
                    item_type=item["item_type"],
                    bonus=item["bonus"],
                    found_day=keep.current_day,
                    found_expedition_id=expedition.id,
                )
                db.add(magic_item)
                events.append({
                    "type": "loot",
                    "message": f"{recipient.name} found a magic item: {item['name']}!",
                })

    # Apply stairs discovery from decision points (if player pressed on through them)
    for dp in sim_result.get("decision_points", []):
        if dp["type"] == "stairs":
            # Only unlock if the player didn't retreat before this point
            dp_index = sim_result["decision_points"].index(dp)
            if (expedition.resolved_phases or 0) > dp_index or not retreat:
                new_level = dp.get("new_level", 0)
                if new_level > keep.max_dungeon_level:
                    keep.max_dungeon_level = new_level
                    events.append({
                        "type": "stairs",
                        "message": dp["message"],
                    })

    if retreat:
        events.insert(0, {"type": "expedition_complete", "message": "The party retreated from the dungeon"})

    return {"events": events, "simulation_data": effective_result}


def _auto_launch_expedition(party, keep, db) -> dict | None:
    """Launch an expedition automatically for auto-delve. Returns summary or None on failure."""
    from app.magic_items import get_weapon_bonus, get_armor_bonus

    if not party.members or party.on_expedition:
        return None

    # Check for dead/bankrupt members
    for member in party.members:
        if member.is_bankrupt or member.is_dead:
            return None

    dungeon_level = keep.max_dungeon_level or 1
    combat_bonus = _get_combat_bonus(keep, db)

    party_members = []
    for member in party.members:
        weapon_bonus = get_weapon_bonus(member)
        armor_bonus = get_armor_bonus(member)
        party_members.append({
            "id": member.id,
            "name": member.name,
            "character_class": member.adventurer_class.value,
            "level": member.level + weapon_bonus + combat_bonus,
            "base_level": member.level,
            "hit_points": member.hp_max,
            "current_hp": member.hp_current + armor_bonus,
            "armor_buffer": armor_bonus,
            "xp": member.xp,
        })

    simulator_party_idx = simulator.add_party(party_members)
    expedition_id_sim = simulator.start_expedition(simulator_party_idx, dungeon_level=dungeon_level)

    start_day = keep.current_day
    duration = get_level_duration(dungeon_level)
    return_day = start_day + duration - 1

    sim_result = simulator.run_expedition_to_completion(expedition_id_sim)
    sim_result["starting_hp"] = {
        m["name"]: m.get("current_hp", m.get("hit_points", 10))
        for m in party_members
    }
    build_phases(sim_result, dungeon_level, keep.max_dungeon_level)

    decision_points = sim_result.get("decision_points", [])
    first_decision_day = None
    if decision_points:
        earliest = start_day + 1
        latest = max(earliest, return_day - 1)
        first_decision_day = _random.randint(earliest, latest)

    db_expedition = Expedition(
        party_id=party.id,
        dungeon_level=dungeon_level,
        start_day=start_day,
        duration_days=duration,
        return_day=return_day,
        started_at=datetime.now(),
        result="in_progress",
        resolved_phases=0,
        decision_day=first_decision_day,
        simulation_data=_make_json_safe(sim_result),
    )
    db.add(db_expedition)
    db.commit()
    db.refresh(db_expedition)

    party.on_expedition = True
    party.current_expedition_id = db_expedition.id
    for member in party.members:
        member.on_expedition = True
        member.is_available = False
    db.commit()

    return {
        "expedition_id": db_expedition.id,
        "party_id": party.id,
        "dungeon_level": dungeon_level,
    }


@router.post("/expeditions/")
def launch_expedition(
    expedition_data: ExpeditionCreate,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Launch a new expedition. The party departs and results are applied on return."""

    party = db.query(Party).filter(
        Party.id == expedition_data.party_id,
        Party.keep_id == keep.id,
    ).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")

    if not party.members:
        raise HTTPException(status_code=400, detail="Party has no members")

    if party.on_expedition:
        raise HTTPException(status_code=400, detail="Party is already on an expedition")

    # Validate dungeon level is unlocked
    requested_level = expedition_data.dungeon_level
    if requested_level > keep.max_dungeon_level:
        raise HTTPException(
            status_code=400,
            detail=f"Dungeon level {requested_level} is not yet unlocked. Max unlocked: {keep.max_dungeon_level}",
        )
    if requested_level > len(DUNGEON_LEVEL_NAMES):
        raise HTTPException(status_code=400, detail="Invalid dungeon level")

    for member in party.members:
        if member.is_bankrupt:
            raise HTTPException(
                status_code=400,
                detail=f"Party contains bankrupt members who cannot go on expeditions. Member: {member.name} is bankrupt."
            )
        if member.is_dead:
            raise HTTPException(
                status_code=400,
                detail=f"Party contains dead members. Member: {member.name} is dead."
            )

    # Convert party to simulator format
    from app.magic_items import get_weapon_bonus, get_armor_bonus
    combat_bonus = _get_combat_bonus(keep, db)  # Training Grounds bonus

    party_members = []
    for member in party.members:
        weapon_bonus = get_weapon_bonus(member)
        armor_bonus = get_armor_bonus(member)
        party_members.append({
            "id": member.id,
            "name": member.name,
            "character_class": member.adventurer_class.value,
            "level": member.level + weapon_bonus + combat_bonus,  # effective level for combat
            "base_level": member.level,  # actual level for XP etc.
            "hit_points": member.hp_max,
            "current_hp": member.hp_current + armor_bonus,  # armor buffer adds to starting HP
            "armor_buffer": armor_bonus,  # track buffer separately
            "xp": member.xp,
        })

    # Add party to simulator
    simulator_party_idx = None
    if party_members:
        for idx, sim_party in enumerate(simulator.parties):
            if len(sim_party) > 0 and sim_party[0].get("id") == party_members[0].get("id"):
                simulator_party_idx = idx
                break

    if simulator_party_idx is None:
        simulator_party_idx = simulator.add_party(party_members)

    expedition_id_sim = simulator.start_expedition(
        simulator_party_idx,
        dungeon_level=expedition_data.dungeon_level
    )

    start_day = keep.current_day
    duration = get_level_duration(requested_level)
    return_day = start_day + duration - 1

    # Run simulation now, then build interactive phases
    sim_result = simulator.run_expedition_to_completion(expedition_id_sim)

    # Store starting HP snapshot for accurate replay later
    sim_result["starting_hp"] = {
        m["name"]: m.get("current_hp", m.get("hit_points", 10))
        for m in party_members
    }

    build_phases(sim_result, requested_level, keep.max_dungeon_level)

    # If there are decision points, schedule the first one on a random day
    decision_points = sim_result.get("decision_points", [])
    first_decision_day = None
    if decision_points:
        import random as _rand
        # Random day between start+1 and return-1 (at least 1 day in)
        earliest = start_day + 1
        latest = max(earliest, return_day - 1)
        first_decision_day = _rand.randint(earliest, latest)

    db_expedition = Expedition(
        party_id=expedition_data.party_id,
        dungeon_level=requested_level,
        start_day=start_day,
        duration_days=duration,
        return_day=return_day,
        started_at=datetime.now(),
        result="in_progress",
        resolved_phases=0,
        decision_day=first_decision_day,
        simulation_data=_make_json_safe(sim_result),
    )
    db.add(db_expedition)
    db.commit()
    db.refresh(db_expedition)

    party.on_expedition = True
    party.current_expedition_id = db_expedition.id

    for member in party.members:
        member.on_expedition = True
        member.is_available = False

    db.commit()

    return {
        "expedition_id": db_expedition.id,
        "party_id": party.id,
        "start_day": start_day,
        "return_day": return_day,
        "duration_days": duration,
        "result": "in_progress",
    }


class ExpeditionChoice(BaseModel):
    choice: str  # "press_on", "retreat", or "auto"


@router.post("/expeditions/{expedition_id}/choose")
def make_expedition_choice(
    expedition_id: int,
    data: ExpeditionChoice,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Make a choice at an expedition decision point."""
    expedition = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(
        Expedition.id == expedition_id,
        Party.keep_id == keep.id,
    ).first()
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")

    if expedition.result != "awaiting_choice":
        raise HTTPException(status_code=400, detail="Expedition is not awaiting a choice")

    if data.choice not in ("press_on", "retreat", "auto"):
        raise HTTPException(status_code=400, detail="Invalid choice. Must be 'press_on', 'retreat', or 'auto'")

    # Auto: let the party decide
    choice = data.choice
    if choice == "auto":
        from app.expedition_events import auto_decide
        dp = expedition.pending_event or {}
        choice = auto_decide(dp.get("type", ""), expedition.party.members if expedition.party else [])

    sim_result = expedition.simulation_data
    decision_points = sim_result.get("decision_points", [])
    resolved = expedition.resolved_phases or 0

    was_auto = data.choice == "auto"

    if choice == "retreat":
        result = _finalize_expedition(expedition, sim_result, db, keep, retreat=True)
        db.commit()
        return {
            "status": "completed",
            "retreated": True,
            "auto_choice": "retreat" if was_auto else None,
            "events": result.get("events", []),
        }

    # Press on
    expedition.resolved_phases = resolved + 1
    expedition.pending_event = None

    if expedition.resolved_phases < len(decision_points):
        expedition.decision_day = expedition.return_day
        expedition.result = "in_progress"
        db.commit()
        return {
            "status": "in_progress",
            "auto_choice": "press_on" if was_auto else None,
            "message": "The expedition continues...",
            "events": [],
        }

    # No more decision points — resume normal expedition (resolves on return_day)
    expedition.decision_day = None
    expedition.result = "in_progress"
    db.commit()
    return {
        "status": "in_progress",
        "auto_choice": "press_on" if was_auto else None,
        "message": "The expedition continues...",
        "events": [],
    }


@router.get("/expeditions/{expedition_id}/pending")
def get_pending_event(
    expedition_id: int,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Get the pending decision event for an expedition awaiting choice."""
    expedition = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(
        Expedition.id == expedition_id,
        Party.keep_id == keep.id,
    ).first()
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")

    if expedition.result != "awaiting_choice":
        return {"pending": False}

    return {
        "pending": True,
        "expedition_id": expedition.id,
        "party_name": expedition.party.name if expedition.party else "Unknown",
        "pending_event": expedition.pending_event,
    }


@router.get("/expeditions/{expedition_id}", response_model=ExpeditionResult)
def get_expedition_results(
    expedition_id: int,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Get detailed results of an expedition"""
    db_expedition = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(
        Expedition.id == expedition_id,
        Party.keep_id == keep.id,
    ).first()
    if not db_expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")

    try:
        result = simulator.get_expedition_results(expedition_id)

        if "party_members_ready_for_level_up" not in result:
            party = db.query(Party).filter(Party.id == db_expedition.party_id).first()
            if party:
                members_ready = []
                for member in party.members:
                    if check_for_level_up(member.level, member.xp):
                        members_ready.append({
                            "id": member.id,
                            "name": member.name,
                            "current_level": member.level,
                            "next_level": member.level + 1
                        })
                result["party_members_ready_for_level_up"] = members_ready

        return result
    except ValueError:
        party = db.query(Party).filter(Party.id == db_expedition.party_id).first()
        node_results = db.query(ExpeditionNodeResult).filter(
            ExpeditionNodeResult.expedition_id == expedition_id
        ).all()
        expedition_logs = db.query(ExpeditionLog).filter(
            ExpeditionLog.expedition_id == expedition_id
        ).all()

        log = []
        for node in node_results:
            try:
                turn_log = json.loads(node.log)
                log.append(turn_log)
            except (json.JSONDecodeError, TypeError):
                pass

        party_status = {
            "members_total": len(party.members) if party else 0,
            "members_alive": len([m for m in party.members if m.hp_current > 0]) if party else 0,
            "members_dead": len([l for l in expedition_logs if l.status == "dead"]),
            "hp_current": sum(m.hp_current for m in party.members) if party else 0,
            "hp_max": sum(m.hp_max for m in party.members) if party else 0,
            "hp_percentage": (sum(m.hp_current for m in party.members) /
                             sum(m.hp_max for m in party.members)) * 100 if party and sum(m.hp_max for m in party.members) > 0 else 0
        }

        members_ready_for_level_up = []
        if party:
            for member in party.members:
                if check_for_level_up(member.level, member.xp):
                    members_ready_for_level_up.append({
                        "id": member.id,
                        "name": member.name,
                        "current_level": member.level,
                        "next_level": member.level + 1
                    })

        result = {
            "expedition_id": expedition_id,
            "party_id": db_expedition.party_id,
            "dungeon_level": 1,
            "turns": len(node_results),
            "start_time": db_expedition.started_at,
            "end_time": db_expedition.finished_at,
            "start_day": db_expedition.start_day,
            "duration_days": db_expedition.duration_days,
            "return_day": db_expedition.return_day,
            "treasure_total": sum(node.loot for node in node_results),
            "special_items": [],
            "xp_earned": sum(node.xp_earned for node in node_results),
            "xp_per_party_member": sum(node.xp_earned for node in node_results) / max(1, len(party.members)) if party else 0,
            "resources_used": {"hp_lost": 0},
            "dead_members": [l.adventurer.name for l in expedition_logs if l.status == "dead"],
            "party_status": party_status,
            "log": log,
            "party_members_ready_for_level_up": members_ready_for_level_up
        }

        return result


@router.get("/expeditions/")
def list_expeditions(keep: Keep = Depends(get_current_keep), db: Session = Depends(get_db)):
    """List all expeditions for this keep"""
    expeditions = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(Party.keep_id == keep.id).all()
    results = []
    for e in expeditions:
        sim = e.simulation_data or {}
        results.append({
            "id": e.id,
            "party_id": e.party_id,
            "party_name": e.party.name if e.party else "Unknown",
            "dungeon_level": e.dungeon_level or 1,
            "start_day": e.start_day,
            "duration_days": e.duration_days,
            "return_day": e.return_day,
            "result": e.result,
            "treasure_total": sim.get("treasure_total", 0),
            "xp_earned": sim.get("xp_earned", 0),
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "finished_at": e.finished_at.isoformat() if e.finished_at else None,
        })
    return results


@router.get("/expeditions/{expedition_id}/summary")
def get_expedition_summary(
    expedition_id: int,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Get expedition summary. Works for in-progress, awaiting_choice, and completed."""
    expedition = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(
        Expedition.id == expedition_id,
        Party.keep_id == keep.id,
    ).first()
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")

    party = db.query(Party).filter(Party.id == expedition.party_id).first()
    is_active = expedition.result in ("in_progress", "awaiting_choice")

    if is_active:
        # Pull data from simulation_data for in-progress expeditions
        return _build_active_summary(expedition, party, keep)
    else:
        # Pull from finalized DB records for completed expeditions
        return _build_completed_summary(expedition, party, keep, db)


def _replay_member_hp(party_members, events_log: list, deaths: set, starting_hp: dict = None) -> dict:
    """Replay simulation turns to reconstruct per-member HP.

    Args:
        starting_hp: {name: hp} snapshot from expedition launch. Falls back
                     to live DB hp_current if not available (old expeditions).

    Returns {name: current_hp} for each member.
    """
    hp = {}
    alive = {}
    for m in party_members:
        if starting_hp and m.name in starting_hp:
            hp[m.name] = starting_hp[m.name]
        else:
            hp[m.name] = m.hp_current
        alive[m.name] = True

    for turn in events_log:
        for event in turn.get("events", []):
            # Combat damage distributed evenly among alive members
            combat = event.get("combat")
            if combat:
                hp_lost = combat.get("hp_lost", 0)
                alive_names = [n for n, a in alive.items() if a]
                if alive_names and hp_lost > 0:
                    per_member = hp_lost // len(alive_names)
                    remainder = hp_lost % len(alive_names)
                    for i, name in enumerate(alive_names):
                        loss = per_member + (1 if i < remainder else 0)
                        hp[name] = max(0, hp[name] - loss)

            # Trap damage distributed evenly
            trap_dmg = event.get("trap_damage")
            if trap_dmg:
                alive_names = [n for n, a in alive.items() if a]
                if alive_names:
                    per_member = trap_dmg // len(alive_names)
                    remainder = trap_dmg % len(alive_names)
                    for i, name in enumerate(alive_names):
                        loss = per_member + (1 if i < remainder else 0)
                        hp[name] = max(0, hp[name] - loss)

        # Mark deaths from this turn
        for dead_name in turn.get("deaths", []):
            alive[dead_name] = False
            hp[dead_name] = 0

    return hp


def _build_active_summary(expedition: Expedition, party, keep: Keep) -> dict:
    """Build summary from simulation_data for an in-progress expedition."""
    sim = expedition.simulation_data or {}
    log = sim.get("log", [])
    phases = sim.get("phases", [])
    decision_points = sim.get("decision_points", [])
    resolved = expedition.resolved_phases or 0

    # Calculate totals from phases resolved so far + current phase
    total_loot = 0
    total_xp = 0
    all_deaths = []
    for i, phase in enumerate(phases):
        if i > resolved:
            break
        total_loot += phase.get("loot", 0)
        total_xp += phase.get("xp", 0)
        all_deaths.extend(phase.get("deaths", []))

    # Events log: show turns up to the current decision point
    cutoff_turn = None
    if resolved < len(decision_points):
        cutoff_turn = decision_points[resolved].get("after_turn")

    events_log = []
    for turn in log:
        turn_num = turn.get("turn", 0)
        if cutoff_turn and turn_num > cutoff_turn:
            break
        events_log.append(turn)

    # Reconstruct per-member HP from simulation replay
    member_hp = {}
    if party:
        member_hp = _replay_member_hp(party.members, events_log, set(all_deaths), sim.get("starting_hp"))

    member_results = []
    if party:
        for member in party.members:
            is_dead = member.name in all_deaths
            current_hp = member_hp.get(member.name, member.hp_current)
            member_results.append({
                "name": member.name,
                "adventurer_class": member.adventurer_class.value,
                "level": member.level,
                "alive": not is_dead,
                "hp_current": 0 if is_dead else current_hp,
                "hp_max": member.hp_max,
                "xp_gained": 0,
                "gold": member.gold,
                "silver": member.silver,
                "copper": member.copper,
            })

    # Include pending event if awaiting choice
    pending_event = None
    if expedition.result == "awaiting_choice" and expedition.pending_event:
        pending_event = expedition.pending_event

    return {
        "expedition_id": expedition.id,
        "party_id": expedition.party_id,
        "party_name": party.name if party else "Unknown",
        "start_day": expedition.start_day,
        "return_day": expedition.return_day,
        "duration_days": expedition.duration_days,
        "result": expedition.result,
        "dungeon_level": expedition.dungeon_level,
        "member_results": member_results,
        "total_loot": total_loot,
        "total_xp": total_xp,
        "events_log": events_log,
        "estimated_readiness_day": None,
        "pending_event": pending_event,
    }


def _build_completed_summary(expedition: Expedition, party, keep: Keep, db) -> dict:
    """Build summary from finalized DB records for a completed expedition."""
    logs = db.query(ExpeditionLog).filter(
        ExpeditionLog.expedition_id == expedition.id
    ).all()

    # Replay simulation to get HP at expedition end (not current live HP)
    sim = expedition.simulation_data or {}
    sim_log = sim.get("log", [])
    cutoff = sim.get("retreat_cutoff_turn")
    if cutoff is not None:
        replay_log = [t for t in sim_log if t.get("turn", 0) <= cutoff]
    else:
        replay_log = sim_log

    dead_names = set(sim.get("dead_members", []))
    # For retreats, deaths come from the partial result
    if sim.get("retreated"):
        dead_names = set(sim.get("dead_members", []))

    sim_hp = {}
    if party:
        sim_hp = _replay_member_hp(party.members, replay_log, dead_names, sim.get("starting_hp"))

    member_results = []
    max_heal_days = 0
    for log in logs:
        adv = log.adventurer
        is_alive = log.status != "dead"
        # Use replayed HP for the "at expedition end" snapshot
        end_hp = sim_hp.get(adv.name)
        if end_hp is None:
            # Fallback: approximate from hp_change
            end_hp = max(0, adv.hp_max + log.hp_change) if is_alive else 0
        if is_alive and end_hp < adv.hp_max:
            heal_days = adv.hp_max - end_hp
            max_heal_days = max(max_heal_days, heal_days)
        member_results.append({
            "name": adv.name,
            "adventurer_class": adv.adventurer_class.value,
            "level": adv.level,
            "alive": is_alive,
            "hp_current": 0 if not is_alive else end_hp,
            "hp_max": adv.hp_max,
            "xp_gained": log.xp_share,
            "gold": adv.gold,
            "silver": adv.silver,
            "copper": adv.copper,
        })

    estimated_readiness_day = keep.current_day + max_heal_days if max_heal_days > 0 else keep.current_day

    node_results = db.query(ExpeditionNodeResult).filter(
        ExpeditionNodeResult.expedition_id == expedition.id
    ).all()
    total_loot = sum(n.loot for n in node_results)
    total_xp = sum(n.xp_earned for n in node_results)

    events_log = []
    for node in node_results:
        try:
            events_log.append(json.loads(node.log))
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "expedition_id": expedition.id,
        "party_id": expedition.party_id,
        "party_name": party.name if party else "Unknown",
        "start_day": expedition.start_day,
        "return_day": expedition.return_day,
        "duration_days": expedition.duration_days,
        "result": expedition.result,
        "dungeon_level": expedition.dungeon_level,
        "member_results": member_results,
        "total_loot": total_loot,
        "total_xp": total_xp,
        "events_log": events_log,
        "estimated_readiness_day": estimated_readiness_day,
        "pending_event": None,
    }


@router.post("/expeditions/{expedition_id}/advance", response_model=TurnResult)
def advance_expedition_turn(
    expedition_id: int,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Advance an expedition by one turn"""
    db_expedition = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(
        Expedition.id == expedition_id,
        Party.keep_id == keep.id,
    ).first()
    if not db_expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")

    if db_expedition.result != "in_progress":
        raise HTTPException(status_code=400, detail="Expedition is already completed")

    try:
        result = simulator.advance_turn(expedition_id)

        if result["expedition_ended"]:
            db_expedition.result = "completed"
            db_expedition.finished_at = datetime.now()

            party = db.query(Party).filter(Party.id == db_expedition.party_id).first()
            if party:
                party.on_expedition = False
                party.current_expedition_id = None

                for member in party.members:
                    member.on_expedition = False
                    member.is_available = (member.hp_current == member.hp_max)

            db.commit()

        exp_node = ExpeditionNodeResult(
            expedition_id=db_expedition.id,
            node_id=1,
            success=True,
            xp_earned=sum(event.get("xp_earned", 0) for event in result["events"]) if "events" in result else 0,
            loot=sum(event.get("treasure", {}).get("gold", 0) for event in result["events"] if "treasure" in event) if "events" in result else 0,
            log=json.dumps(result)
        )
        db.add(exp_node)
        db.commit()

        return result
    except ValueError:
        raise HTTPException(status_code=404, detail="Expedition not found in simulator")
