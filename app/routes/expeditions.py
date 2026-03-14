import json
from fastapi import APIRouter, HTTPException, Depends
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

# Shared simulator instance
simulator = DungeonSimulator()


def resolve_expedition(expedition: Expedition, db: Session, keep: Keep) -> dict:
    """Apply stored simulation results when an expedition returns.
    Returns a summary dict with events for notifications."""
    sim_result = expedition.simulation_data
    if not sim_result:
        return {"events": []}

    party = expedition.party
    events = []

    expedition.result = "completed"
    expedition.finished_at = datetime.now()

    # Store node result logs
    for node_result in sim_result.get("log", []):
        log_entries = sim_result.get("log", [])
        exp_node = ExpeditionNodeResult(
            expedition_id=expedition.id,
            node_id=1,
            success=True,
            xp_earned=int(sim_result["xp_earned"] / len(log_entries)) if log_entries else 0,
            loot=int(sim_result["treasure_total"] / len(log_entries)) if log_entries else 0,
            log=json.dumps(node_result)
        )
        db.add(exp_node)

    # Apply results to adventurers
    dead_names = set(sim_result.get("dead_members", []))
    living_members = []

    if party:
        party.on_expedition = False
        party.current_expedition_id = None

        for member in party.members:
            is_dead = member.name in dead_names
            log = ExpeditionLog(
                expedition_id=expedition.id,
                adventurer_id=member.id,
                xp_share=int(sim_result["xp_per_party_member"]),
                hp_change=-member.hp_max if is_dead else -(member.hp_max - max(1, member.hp_current - 5)),
                status="dead" if is_dead else "alive"
            )
            db.add(log)

            # XP goes to all members (dead included, they earned it)
            member.xp += int(sim_result["xp_per_party_member"])

            if is_dead:
                member.hp_current = 0
                member.is_dead = True
                member.death_day = keep.current_day
                member.on_expedition = False
                member.is_available = False
                events.append({"type": "death", "message": f"{member.name} died during the expedition"})
            else:
                # Apply damage from the expedition
                member.hp_current = max(1, member.hp_current - 5)
                member.on_expedition = False
                member.is_available = True  # Immediately available on return
                living_members.append(member)

        # All loot goes to living adventurers evenly (loot is in copper)
        # Keep treasury is funded only through monthly upkeep
        total_loot_copper = sim_result.get("treasure_total", 0) * 100  # convert GP to copper
        living_count = len(living_members)
        if living_count > 0 and total_loot_copper > 0:
            individual_share_copper = total_loot_copper // living_count
            for member in living_members:
                member.add_currency(individual_share_copper)

        if total_loot_copper > 0:
            from app.routes.game import format_currency, copper_to_parts
            share_copper = total_loot_copper // max(1, living_count)
            g, s, c = copper_to_parts(share_copper)
            total_g, total_s, total_c = copper_to_parts(total_loot_copper)
            events.append({"type": "loot", "message": f"Earned {format_currency(total_g, total_s, total_c)} ({format_currency(g, s, c)} each to {living_count} adventurer{'s' if living_count != 1 else ''})"})

        # Collect deferred upkeep for any cycles missed while on expedition
        import math
        from app.routes.game import format_currency, copper_to_parts

        # Count upkeep days that fell during the expedition (exclude current_day;
        # if today is an upkeep day, the normal process_upkeep handles it)
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
                    # Bankrupt: seize remaining funds, send to debtor's prison
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

        # Remove dead members from party
        party.members = [m for m in party.members if not m.is_dead and not m.is_bankrupt]

    return {"events": events, "simulation_data": sim_result}


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
    party_members = []
    for member in party.members:
        party_members.append({
            "id": member.id,
            "name": member.name,
            "character_class": member.adventurer_class.value,
            "level": member.level,
            "hit_points": member.hp_max,
            "current_hp": member.hp_current,
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
    return_day = start_day + expedition_data.duration_days - 1

    # Run simulation now but store results for later
    sim_result = simulator.run_expedition_to_completion(expedition_id_sim)

    db_expedition = Expedition(
        party_id=expedition_data.party_id,
        start_day=start_day,
        duration_days=expedition_data.duration_days,
        return_day=return_day,
        started_at=datetime.now(),
        result="in_progress",
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
        "duration_days": expedition_data.duration_days,
        "result": "in_progress",
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
    return [
        {
            "id": e.id,
            "party_id": e.party_id,
            "start_day": e.start_day,
            "duration_days": e.duration_days,
            "return_day": e.return_day,
            "result": e.result,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "finished_at": e.finished_at.isoformat() if e.finished_at else None,
        }
        for e in expeditions
    ]


@router.get("/expeditions/{expedition_id}/summary")
def get_expedition_summary(
    expedition_id: int,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Get expedition summary with member results and readiness estimate."""
    expedition = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(
        Expedition.id == expedition_id,
        Party.keep_id == keep.id,
    ).first()
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")

    party = db.query(Party).filter(Party.id == expedition.party_id).first()
    logs = db.query(ExpeditionLog).filter(
        ExpeditionLog.expedition_id == expedition_id
    ).all()

    member_results = []
    max_heal_days = 0
    for log in logs:
        adv = log.adventurer
        is_alive = log.status != "dead"
        if is_alive and adv.hp_current < adv.hp_max:
            heal_days = adv.hp_max - adv.hp_current
            max_heal_days = max(max_heal_days, heal_days)
        member_results.append({
            "name": adv.name,
            "adventurer_class": adv.adventurer_class.value,
            "level": adv.level,
            "alive": is_alive,
            "hp_current": adv.hp_current,
            "hp_max": adv.hp_max,
            "xp_gained": log.xp_share,
            "gold": adv.gold,
            "silver": adv.silver,
            "copper": adv.copper,
        })

    estimated_readiness_day = keep.current_day + max_heal_days if max_heal_days > 0 else keep.current_day

    node_results = db.query(ExpeditionNodeResult).filter(
        ExpeditionNodeResult.expedition_id == expedition_id
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
        "expedition_id": expedition_id,
        "party_id": expedition.party_id,
        "party_name": party.name if party else "Unknown",
        "start_day": expedition.start_day,
        "return_day": expedition.return_day,
        "duration_days": expedition.duration_days,
        "result": expedition.result,
        "member_results": member_results,
        "total_loot": total_loot,
        "total_xp": total_xp,
        "events_log": events_log,
        "estimated_readiness_day": estimated_readiness_day,
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
