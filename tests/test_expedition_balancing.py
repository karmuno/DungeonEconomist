import pytest
import statistics # For calculating averages/medians if needed

# Assuming the Expedition class is in app.expedition
# We need to import it carefully if there are naming conflicts or for clarity
from app.expedition import Expedition as SimulationExpedition, CombatOutcome

# Standard party composition for balancing tests
# Ensure current_hp is part of the initial setup for each member
BASE_PARTY_COMPOSITION = [
    {"name": "Valerius", "character_class": "Fighter", "level": 3, "hit_points": 30, "current_hp": 30, "equipment": []},
    {"name": "Sorina", "character_class": "Magic-User", "level": 3, "hit_points": 15, "current_hp": 15, "equipment": []},
    {"name": "Borin", "character_class": "Dwarf", "level": 3, "hit_points": 35, "current_hp": 35, "equipment": []},
    {"name": "Lyssa", "character_class": "Thief", "level": 3, "hit_points": 20, "current_hp": 20, "equipment": []},
]

NUM_SIMULATION_RUNS = 20 # Number of times to run the simulation for averaging
NUM_EXPEDITION_TURNS = 30 # Number of turns per expedition simulation

def run_multiple_expeditions(party_composition, dungeon_level, num_runs, num_turns):
    """Helper function to run multiple expedition simulations and collect results."""
    all_results = []
    for _ in range(num_runs):
        # Create a fresh copy of the party for each run to reset HP etc.
        current_party = [member.copy() for member in party_composition]
        # Ensure current_hp is correctly set from hit_points for each run
        for member in current_party:
            member["current_hp"] = member["hit_points"]

        exp = SimulationExpedition(party=current_party, dungeon_level=dungeon_level)
        run_result = exp.run_expedition(turns=num_turns)
        all_results.append(run_result)
    return all_results

def analyze_results(results_list):
    """Helper function to calculate average metrics from a list of expedition results."""
    total_xp_earned = sum(r['xp_earned'] for r in results_list)
    total_loot_obtained = sum(r['treasure_total'] for r in results_list)

    total_hp_lost_overall = 0
    total_initial_hp_overall = 0 # To calculate percentage HP loss

    # Calculate HP lost per run by comparing initial and final HP (implicitly)
    # The 'hp_lost' in resources_used is cumulative for the party in that run.
    total_party_hp_lost_sum = sum(r['resources_used'].get('hp_lost', 0) for r in results_list)

    # Count severe outcomes
    disaster_outcomes = 0
    retreat_outcomes = 0
    tough_fights = 0

    for r in results_list:
        for turn_log in r.get('log', []):
            for event in turn_log.get('events', []):
                if event.get('type') == "Monster" and event.get('combat'):
                    combat_outcome = event['combat']['outcome']
                    if combat_outcome == CombatOutcome.DISASTER:
                        disaster_outcomes += 1
                    elif combat_outcome == CombatOutcome.RETREAT:
                        retreat_outcomes += 1
                    elif combat_outcome == CombatOutcome.TOUGH_FIGHT:
                        tough_fights +=1

    num_results = len(results_list)
    return {
        "avg_xp_earned": total_xp_earned / num_results if num_results > 0 else 0,
        "avg_loot_obtained": total_loot_obtained / num_results if num_results > 0 else 0,
        "avg_party_hp_lost": total_party_hp_lost_sum / num_results if num_results > 0 else 0,
        "disasters_per_run_avg": disaster_outcomes / num_results if num_results > 0 else 0,
        "retreats_per_run_avg": retreat_outcomes / num_results if num_results > 0 else 0,
        "tough_fights_per_run_avg": tough_fights / num_results if num_results > 0 else 0,
    }


class TestExpeditionBalancing:

    @pytest.fixture(scope="class")
    def results_level1(self):
        return run_multiple_expeditions(BASE_PARTY_COMPOSITION, 1, NUM_SIMULATION_RUNS, NUM_EXPEDITION_TURNS)

    @pytest.fixture(scope="class")
    def results_level3(self):
        return run_multiple_expeditions(BASE_PARTY_COMPOSITION, 3, NUM_SIMULATION_RUNS, NUM_EXPEDITION_TURNS)

    @pytest.fixture(scope="class")
    def results_level5(self):
        return run_multiple_expeditions(BASE_PARTY_COMPOSITION, 5, NUM_SIMULATION_RUNS, NUM_EXPEDITION_TURNS)

    @pytest.fixture(scope="class")
    def analyzed_level1(self, results_level1):
        return analyze_results(results_level1)

    @pytest.fixture(scope="class")
    def analyzed_level3(self, results_level3):
        return analyze_results(results_level3)

    @pytest.fixture(scope="class")
    def analyzed_level5(self, results_level5):
        return analyze_results(results_level5)

    def test_xp_increases_with_level(self, analyzed_level1, analyzed_level3, analyzed_level5):
        """Asserts that average XP earned increases with dungeon level."""
        print(f"Avg XP L1: {analyzed_level1['avg_xp_earned']:.2f}, L3: {analyzed_level3['avg_xp_earned']:.2f}, L5: {analyzed_level5['avg_xp_earned']:.2f}")
        assert analyzed_level3['avg_xp_earned'] > analyzed_level1['avg_xp_earned'], "Avg XP from L1 to L3 should increase"
        assert analyzed_level5['avg_xp_earned'] > analyzed_level3['avg_xp_earned'], "Avg XP from L3 to L5 should increase"

    def test_loot_increases_with_level(self, analyzed_level1, analyzed_level3, analyzed_level5):
        """Asserts that average loot obtained increases with dungeon level."""
        print(f"Avg Loot L1: {analyzed_level1['avg_loot_obtained']:.2f}, L3: {analyzed_level3['avg_loot_obtained']:.2f}, L5: {analyzed_level5['avg_loot_obtained']:.2f}")
        assert analyzed_level3['avg_loot_obtained'] > analyzed_level1['avg_loot_obtained'], "Avg Loot from L1 to L3 should increase"
        assert analyzed_level5['avg_loot_obtained'] > analyzed_level3['avg_loot_obtained'], "Avg Loot from L3 to L5 should increase"

    def test_party_hp_loss_increases_with_level(self, analyzed_level1, analyzed_level3, analyzed_level5):
        """Asserts that average total party HP lost tends to increase with dungeon level."""
        print(f"Avg Party HP Lost L1: {analyzed_level1['avg_party_hp_lost']:.2f}, L3: {analyzed_level3['avg_party_hp_lost']:.2f}, L5: {analyzed_level5['avg_party_hp_lost']:.2f}")
        # This is a trend, so we expect higher levels to be more punishing.
        # Allow for some statistical noise, but generally, it should be higher.
        # A softer assertion might be that L5 > L1.
        assert analyzed_level3['avg_party_hp_lost'] > analyzed_level1['avg_party_hp_lost'], "Avg Party HP loss from L1 to L3 should generally increase"
        assert analyzed_level5['avg_party_hp_lost'] > analyzed_level3['avg_party_hp_lost'], "Avg Party HP loss from L3 to L5 should generally increase"
        assert analyzed_level5['avg_party_hp_lost'] > analyzed_level1['avg_party_hp_lost'], "Avg Party HP loss from L1 to L5 should be significantly higher"

    def test_negative_outcomes_increase_with_level(self, analyzed_level1, analyzed_level3, analyzed_level5):
        """Asserts that the frequency of 'Disaster' or 'Retreat' outcomes tends to increase."""
        total_negative_l1 = analyzed_level1['disasters_per_run_avg'] + analyzed_level1['retreats_per_run_avg']
        total_negative_l3 = analyzed_level3['disasters_per_run_avg'] + analyzed_level3['retreats_per_run_avg']
        total_negative_l5 = analyzed_level5['disasters_per_run_avg'] + analyzed_level5['retreats_per_run_avg']

        print(f"Avg Negative Outcomes (Disaster/Retreat) per run L1: {total_negative_l1:.2f}, L3: {total_negative_l3:.2f}, L5: {total_negative_l5:.2f}")

        # We expect more negative outcomes at higher levels.
        # These are averages of counts per run.
        assert total_negative_l3 > total_negative_l1, "Avg negative outcomes from L1 to L3 should generally increase"
        assert total_negative_l5 > total_negative_l3, "Avg negative outcomes from L3 to L5 should generally increase"

    def test_tough_fights_frequency(self, analyzed_level1, analyzed_level3, analyzed_level5):
        """Checks the frequency of 'Tough Fight' outcomes."""
        # The behavior of "Tough Fight" frequency is less predictable.
        # It might peak at mid-levels or vary. This is more exploratory.
        print(f"Avg Tough Fights per run L1: {analyzed_level1['tough_fights_per_run_avg']:.2f}, L3: {analyzed_level3['tough_fights_per_run_avg']:.2f}, L5: {analyzed_level5['tough_fights_per_run_avg']:.2f}")
        # No strict assertion here, more for observation.
        # One might expect that as difficulty ramps up, fights are less likely to be "easy wins"
        # but also might become "disasters" more often than just "tough".
        assert analyzed_level1 is not None # Placeholder to make test valid
        assert analyzed_level3 is not None
        assert analyzed_level5 is not None

# To run these tests:
# Ensure app.expedition.Expedition and its dependencies are correctly structured.
# Pytest will pick up this file and the TestExpeditionBalancing class.
# The fixtures will run the simulations once per class and then tests will use the analyzed results.
# This can take some time due to NUM_SIMULATION_RUNS * NUM_EXPEDITION_TURNS for each level.
# Consider reducing these numbers for faster local testing if needed, but higher numbers give more stable averages.
