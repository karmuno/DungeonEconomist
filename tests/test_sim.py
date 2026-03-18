from app.simulator import DungeonSimulator


def test_create_simulator():
    """Test creating a new simulator"""
    simulator = DungeonSimulator()
    assert simulator.parties == []
    assert simulator.active_expeditions == {}
    assert simulator.completed_expeditions == {}

def test_add_party():
    """Test adding a party to the simulator"""
    simulator = DungeonSimulator()
    party = [
        {"name": "Thorgar", "character_class": "Fighter", "level": 3, "hit_points": 24},
        {"name": "Elindra", "character_class": "Elf", "level": 2, "hit_points": 12}
    ]
    party_id = simulator.add_party(party)
    assert party_id == 0
    assert simulator.parties[0] == party

def test_start_expedition():
    """Test starting a new expedition"""
    simulator = DungeonSimulator()
    party = [
        {"name": "Thorgar", "character_class": "Fighter", "level": 3, "hit_points": 24},
        {"name": "Elindra", "character_class": "Elf", "level": 2, "hit_points": 12}
    ]
    party_id = simulator.add_party(party)

    expedition_id = simulator.start_expedition(party_id, dungeon_level=2)
    assert expedition_id == 0
    assert expedition_id in simulator.active_expeditions

    # Make sure the original party wasn't modified
    assert simulator.parties[0] == party

    # Check expedition properties
    expedition_data = simulator.active_expeditions[expedition_id]
    assert expedition_data["party_id"] == party_id
    assert expedition_data["turns_completed"] == 0

    expedition = expedition_data["expedition"]
    assert expedition.dungeon_level == 2
    assert len(expedition.party) == 2

    # Check that party is a copy (not the original)
    assert expedition.party is not party
    assert "current_hp" in expedition.party[0]

def test_advance_turn():
    """Test advancing the expedition by one turn"""
    simulator = DungeonSimulator()
    party = [
        {"name": "Thorgar", "character_class": "Fighter", "level": 3, "hit_points": 24},
        {"name": "Elindra", "character_class": "Elf", "level": 2, "hit_points": 12}
    ]
    party_id = simulator.add_party(party)
    expedition_id = simulator.start_expedition(party_id, dungeon_level=1)

    # Advance one turn
    result = simulator.advance_turn(expedition_id)

    # Check basic turn result structure
    assert "turn" in result
    assert result["turn"] == 1
    assert "events" in result
    assert "party_status" in result
    assert "expedition_ended" in result

    # Check that log was updated
    assert len(simulator.expedition_logs[expedition_id]) == 1
    assert simulator.expedition_logs[expedition_id][0]["turn"] == 1

def test_complete_expedition():
    """Test completing an expedition"""
    simulator = DungeonSimulator()
    party = [
        {"name": "Thorgar", "character_class": "Fighter", "level": 3, "hit_points": 24},
        {"name": "Elindra", "character_class": "Elf", "level": 2, "hit_points": 12}
    ]
    party_id = simulator.add_party(party)
    expedition_id = simulator.start_expedition(party_id, dungeon_level=1)

    # Run expedition to completion with limited turns to ensure it ends
    simulator.run_expedition_to_completion(expedition_id, max_turns=5)

    # Check that expedition moved from active to completed
    assert expedition_id not in simulator.active_expeditions
    assert expedition_id in simulator.completed_expeditions
    assert len(simulator.completed_expedition_list) == 1
    assert simulator.completed_expeditions[expedition_id]["party_id"] == party_id

    # Check results
    results = simulator.get_expedition_results(expedition_id)
    assert results["expedition_id"] == expedition_id
    assert results["party_id"] == party_id
    assert "treasure_total" in results
    assert "xp_earned" in results
    assert "log" in results

def test_party_management():
    """Test adding and removing party members"""
    simulator = DungeonSimulator()

    # Create empty party
    party_id = simulator.add_party([])

    # Add adventurer
    adventurer = {"id": "adv1", "name": "Thorgar", "character_class": "Fighter", "level": 3, "hit_points": 24}
    assert simulator.add_adventurer_to_party(party_id, adventurer)

    # Check party content
    assert len(simulator.parties[party_id]) == 1
    assert simulator.parties[party_id][0] == adventurer

    # Remove adventurer
    assert simulator.remove_adventurer_from_party(party_id, "adv1")
    assert len(simulator.parties[party_id]) == 0

    # Try removing non-existent adventurer
    assert not simulator.remove_adventurer_from_party(party_id, "non-existent")
