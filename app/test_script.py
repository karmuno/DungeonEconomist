"""
Test script for the Dungeon Economist simulator
Run with: python -m app.test_script
"""

from app.simulator import DungeonSimulator

def test_run_expedition():
    """Run a simple expedition simulation"""
    simulator = DungeonSimulator()
    
    # Create a party
    party = [
        {"name": "Thorgar", "character_class": "Fighter", "level": 3, "hit_points": 24},
        {"name": "Elindra", "character_class": "Elf", "level": 2, "hit_points": 12},
        {"name": "Morgrim", "character_class": "Dwarf", "level": 2, "hit_points": 18},
        {"name": "Thalia", "character_class": "Magic-User", "level": 2, "hit_points": 8},
        {"name": "Brother Galen", "character_class": "Cleric", "level": 2, "hit_points": 14}
    ]
    
    party_id = simulator.add_party(party)
    print(f"Created party ID: {party_id}")
    
    # Start expedition to a level 2 dungeon
    expedition_id = simulator.start_expedition(party_id, dungeon_level=2)
    print(f"Started expedition ID: {expedition_id} to dungeon level 2")
    
    # Run the expedition for 10 turns
    print("\nRunning expedition turn by turn:")
    for i in range(10):
        result = simulator.advance_turn(expedition_id)
        
        # Print turn summary
        print(f"\nTurn {result['turn']}:")
        
        if result['events']:
            for event in result['events']:
                event_type = event['type'].value
                print(f"  Encounter: {event_type}")
                
                if 'combat' in event:
                    monster = event['combat']['monster_type']
                    outcome = event['combat']['outcome'].value
                    hp_lost = event['combat']['hp_lost']
                    print(f"    Combat with {monster}, outcome: {outcome}, HP lost: {hp_lost}")
                    
                if 'trap_damage' in event:
                    print(f"    Trap damage: {event['trap_damage']}")
                    
                if 'treasure' in event:
                    gold = event['treasure']['gold']
                    special = event['treasure']['special_item']
                    print(f"    Treasure: {gold} gold" + (f", Special item: {special}" if special else ""))
        else:
            print("  No encounters this turn")
            
        # Print party status
        status = result['party_status']
        print(f"  Party status: {status['members_alive']}/{status['members_total']} members alive, " +
              f"{status['hp_current']}/{status['hp_max']} HP ({status['hp_percentage']:.1f}%)")
        
        # Check if expedition ended
        if result['expedition_ended']:
            print("\nExpedition ended early!")
            break
    
    # Get results
    results = simulator.get_expedition_results(expedition_id)
    
    # Print final summary
    print("\n=== EXPEDITION SUMMARY ===")
    print(f"Dungeon Level: {results['dungeon_level']}")
    print(f"Turns completed: {results['turns']}")
    print(f"Treasure found: {results['treasure_total']} gold")
    if results['special_items']:
        print(f"Special items: {', '.join(item for item in results['special_items'] if item)}")
    print(f"XP earned: {results['xp_earned']} total, {results['xp_per_party_member']} per character")
    print(f"Resources used: {results['resources_used']}")
    if results['dead_members']:
        print(f"Dead party members: {', '.join(results['dead_members'])}")
    else:
        print("All party members survived!")

if __name__ == "__main__":
    test_run_expedition()