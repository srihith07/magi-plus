"""
run.py
------
Project entry point. Run this from the project root directory.
Handles sys.path so all imports resolve correctly.

Usage:
  python run.py --mode simulated
  python run.py --mode simulated --case data/simulated_cases/case_depression_moderate.json
  python run.py --mode interactive --participant P001
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run
from src.main import main

if __name__ == "__main__":
    main()
