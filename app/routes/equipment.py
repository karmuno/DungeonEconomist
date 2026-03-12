from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Equipment, EquipmentType
from app.schemas import EquipmentOut, EquipmentCreate

router = APIRouter()


@router.post("/equipment/", response_model=EquipmentOut)
def create_equipment(equipment: EquipmentCreate, db: Session = Depends(get_db)):
    """Create a new equipment item"""
    db_equipment = Equipment(
        name=equipment.name,
        equipment_type=equipment.equipment_type,
        description=equipment.description,
        cost=equipment.cost,
        weight=equipment.weight,
        properties=equipment.properties
    )
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment


@router.get("/equipment/", response_model=List[EquipmentOut])
def list_equipment(
    type_filter: Optional[EquipmentType] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all equipment items, optionally filtered by type"""
    query = db.query(Equipment)
    if type_filter:
        query = query.filter(Equipment.equipment_type == type_filter)
    return query.offset(skip).limit(limit).all()


@router.get("/equipment/{equipment_id}", response_model=EquipmentOut)
def get_equipment(equipment_id: int, db: Session = Depends(get_db)):
    """Get a specific equipment item by ID"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment
