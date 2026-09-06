"""Run shared-kernel sector sensitivities and economic invariants.

The previous separate bisections, first-sector hours reuse and hypothetical
six-group firm-size numbers are archived in the original snapshot. This entry
point never interprets that exercise as empirical within-sector incidence.
"""

import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.sectoral.model.sensitivity import main as sensitivity_main


def run_all_tests(argv=None):
    suite = unittest.defaultTestLoader.discover(str(PROJECT_ROOT / "tests"),
                                               pattern="test_sectoral_corrected.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    return sensitivity_main(argv)


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
