@app.get("/parties/filter", response_class=HTMLResponse)
def filter_parties(
    request: Request, 
    filter_type: Optional[str] = "all",
    sort_by: Optional[str] = "name",
    db: Session = Depends(get_db)
):
    """Filter parties by their status"""
    query = db.query(Party)
    
    # Apply filters
    if filter_type == "available":
        query = query.filter(Party.on_expedition == False)
    elif filter_type == "expedition":
        query = query.filter(Party.on_expedition == True)
    
    # Apply sorting
    if sort_by == "members":
        # Using a subquery to count members since we can't sort directly by relationship length
        from sqlalchemy import func
        member_count = db.query(
            party_adventurer.c.party_id, 
            func.count(party_adventurer.c.adventurer_id).label('member_count')
        ).group_by(party_adventurer.c.party_id).subquery()
        
        # Join with the subquery and order by the count
        query = query.outerjoin(
            member_count, 
            Party.id == member_count.c.party_id
        ).order_by(member_count.c.member_count.desc(), Party.name)
    elif sort_by == "funds":
        query = query.order_by(Party.funds.desc(), Party.name)
    else:  # Default sort by name
        query = query.order_by(Party.name)
    
    parties = query.all()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    # Get game time
    game_time = db.query(GameTime).first()
    
    return templates.TemplateResponse(
        "partials/party_list_container.html", 
        {
            "request": request, 
            "parties": parties, 
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
    )

@app.get("/parties/sort", response_class=HTMLResponse)
def sort_parties(
    request: Request, 
    sort_by: Optional[str] = "name",
    filter_type: Optional[str] = "all",
    db: Session = Depends(get_db)
):
    """Sort parties by different criteria"""
    return filter_parties(request, filter_type, sort_by, db)

@app.get("/parties/{party_id}/filter-adventurers", response_class=HTMLResponse)
def filter_party_adventurers(
    request: Request,
    party_id: int,
    class_filter: Optional[str] = "",
    level_filter: Optional[str] = "",
    db: Session = Depends(get_db)
):
    """Filter available adventurers for adding to a party"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    
    # Base query: available adventurers not in this party
    query = db.query(Adventurer).filter(
        Adventurer.is_available == True,
        ~Adventurer.parties.any(Party.id == party_id)
    )
    
    # Apply class filter
    if class_filter and class_filter != "":
        query = query.filter(Adventurer.adventurer_class == class_filter)
    
    # Apply level filter
    if level_filter and level_filter != "":
        min_level = int(level_filter)
        query = query.filter(Adventurer.level >= min_level)
    
    # Sort by level and then name
    available_adventurers = query.order_by(Adventurer.level.desc(), Adventurer.name).all()
    
    # Add progression data
    available_adventurers = [add_progression_data(adv) for adv in available_adventurers]
    
    # Get game time for healing days display
    game_time = db.query(GameTime).first()
    
    return templates.TemplateResponse(
        "partials/available_adventurers_list.html", 
        {
            "request": request, 
            "party": party,
            "available_adventurers": available_adventurers,
            "game_time": game_time
        }
    )

@app.get("/parties/{party_id}/supplies", response_class=HTMLResponse)
def party_supplies(
    request: Request,
    party_id: int,
    type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Show and manage party supplies"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    
    # Get all supply types for the filter
    supply_types = list(SupplyType)
    
    # Query for available supplies to purchase
    query = db.query(Supply)
    
    # Filter by type if specified
    if type:
        query = query.filter(Supply.supply_type == type)
    
    # Get all available supplies
    available_supplies = query.order_by(Supply.supply_type, Supply.cost, Supply.name).all()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    return templates.TemplateResponse(
        "partials/party_supplies.html", 
        {
            "request": request, 
            "party": party,
            "supply_types": supply_types,
            "available_supplies": available_supplies,
            "active_filter": type,
            "treasury_gold": treasury_gold
        }
    )

@app.get("/parties/{party_id}/add-funds-form", response_class=HTMLResponse)
def add_party_funds_form(
    request: Request,
    party_id: int,
    db: Session = Depends(get_db)
):
    """Show form to add funds to a party"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    
    return templates.TemplateResponse(
        "partials/party_funds_form.html", 
        {
            "request": request, 
            "party": party,
            "action": "add"
        }
    )

@app.get("/parties/{party_id}/remove-funds-form", response_class=HTMLResponse)
def remove_party_funds_form(
    request: Request,
    party_id: int,
    db: Session = Depends(get_db)
):
    """Show form to remove funds from a party"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    
    return templates.TemplateResponse(
        "partials/party_funds_form.html", 
        {
            "request": request, 
            "party": party,
            "action": "remove"
        }
    )