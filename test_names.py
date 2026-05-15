import os
import sys

# Add current dir to path to import app
sys.path.append(os.getcwd())

from app.models import AdventurerClass
from app.names import generate_adventurer_name


def test_names():
    print("Testing name generation for all classes...")
    for adv_class in AdventurerClass:
        try:
            name = generate_adventurer_name(adv_class)
            print(f"{adv_class.value}: {name}")
        except Exception as e:
            print(f"FAILED for {adv_class.value}: {e}")

if __name__ == "__main__":
    test_names()
