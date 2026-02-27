"""
Pytest configuration and fixtures.
"""

import sys
from pathlib import Path

# Add all scripts directories to Python path
scripts_dirs = [
    Path(__file__).parent.parent / 'evolving-agent' / 'scripts',
]

for scripts_dir in scripts_dirs:
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
