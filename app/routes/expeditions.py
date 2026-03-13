import json
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.requests import Request
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models import (
    Adventurer, Party, Expedition, ExpeditionNodeResult, ExpeditionLog,
    Player, GameTime,
)
from app.schemas import ExpeditionCreate, ExpeditionResult, TurnResult
from app.simulator import DungeonSimulator, calculate_loot_split
from app.progression import check_for_level_up

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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


def resolve_expedition(expedition: Expedition, db: Session, current_day: int) -> dict:
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
                member.death_day = current_day
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
        # Player treasury is funded only through monthly upkeep
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

        # Remove dead members from party
        party.members = [m for m in party.members if not m.is_dead]

    return {"events": events, "simulation_data": sim_result}


@router.get("/expeditions/active", response_class=HTMLResponse)
def expeditions_active(request: Request, db: Session = Depends(get_db)):
    """Get active expeditions partial"""
    active_expeditions = db.query(Expedition).filter(Expedition.result == "in_progress").all()

    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=1)
        db.add(game_time)
        db.commit()
        db.refresh(game_time)

    return templates.TemplateResponse(
        "partials/active_expeditions.html",
        {
            "request": request,
            "active_expeditions": active_expeditions,
            "game_time": game_time
        }
    )


@router.get("/expeditions/completed", response_class=HTMLResponse)
def expeditions_completed(request: Request, db: Session = Depends(get_db)):
    """Get completed expeditions partial"""
    completed_expeditions = db.query(Expedition).filter(
        Expedition.result == "completed"
    ).order_by(Expedition.finished_at.desc()).limit(10).all()

    return templates.TemplateResponse(
        "partials/completed_expeditions.html",
        {
            "request": request,
            "completed_expeditions": completed_expeditions
        }
    )


@router.get("/expeditions/create-form", response_class=HTMLResponse)
def expedition_create_form(request: Request, party_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """Return the expedition creation form"""
    parties = db.query(Party).filter(Party.on_expedition == False).all()

    selected_party = None
    if party_id:
        selected_party = db.query(Party).filter(Party.id == party_id).first()

    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury

    return templates.TemplateResponse(
        "partials/expedition_form.html",
        {
            "request": request,
            "parties": parties,
            "party": selected_party,
            "treasury_gold": treasury_gold
        }
    )


@router.post("/expeditions/")
def launch_expedition(
    expedition_data: ExpeditionCreate,
    db: Session = Depends(get_db)
):
    """Launch a new expedition. The party departs and results are applied on return."""

    party = db.query(Party).filter(Party.id == expedition_data.party_id).first()
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

    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=0, day_started_at=datetime.now(), last_updated=datetime.now())
        db.add(game_time)
        db.commit()
        db.refresh(game_time)

    start_day = game_time.current_day
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


@router.get("/expeditions/{expedition_id}/details", response_class=HTMLResponse)
def expedition_details_page(request: Request, expedition_id: int, db: Session = Depends(get_db)):
    """Render the expedition details page"""
    expedition = db.query(Expedition).filter(Expedition.id == expedition_id).first()
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")

    node_results = db.query(ExpeditionNodeResult).filter(ExpeditionNodeResult.expedition_id == expedition_id).all()

    processed_logs = []
    total_loot = 0
    total_xp = 0

    for node in node_results:
        try:
            log_data = json.loads(node.log)
            processed_logs.append({"log_data": log_data})
        except (json.JSONDecodeError, TypeError):
            processed_logs.append({"log_data": {"error": "Could not parse log entry."}})
        total_loot += node.loot or 0
        total_xp += node.xp_earned or 0

    player = db.query(Player).first()
    treasury_gold = player.treasury if player else 0

    return templates.TemplateResponse(
        "expedition_details.html",
        {
            "request": request,
            "expedition": expedition,
            "expedition_logs": processed_logs,
            "total_loot": total_loot,
            "total_xp": total_xp,
            "treasury_gold": treasury_gold,
        }
    )


@router.get("/expeditions/{expedition_id}", response_model=ExpeditionResult)
def get_expedition_results(expedition_id: int, db: Session = Depends(get_db)):
    """Get detailed results of an expedition"""
    db_expedition = db.query(Expedition).filter(Expedition.id == expedition_id).first()
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
def list_expeditions(db: Session = Depends(get_db)):
    """List all expeditions in the database"""
    expeditions = db.query(Expedition).all()
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


@router.post("/expeditions/{expedition_id}/advance", response_model=TurnResult)
def advance_expedition_turn(expedition_id: int, db: Session = Depends(get_db)):
    """Advance an expedition by one turn"""
    db_expedition = db.query(Expedition).filter(Expedition.id == expedition_id).first()
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


# --- Frontend Routes ---

@router.get("/expeditions", response_class=HTMLResponse)
def expeditions_page(request: Request, db: Session = Depends(get_db)):
    """Render the expeditions page"""
    active_expeditions = db.query(Expedition).filter(Expedition.result == "in_progress").all()

    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=1)
        db.add(game_time)
        db.commit()
        db.refresh(game_time)

    player = db.query(Player).first()
    treasury_gold = player.treasury if player else 0

    return templates.TemplateResponse(
        "expeditions.html",
        {
            "request": request,
            "active_expeditions": active_expeditions,
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
    )
