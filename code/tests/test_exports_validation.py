import os
import shutil
import json
import unittest
from pathlib import Path

import main as main_mod


class TestExportsValidation(unittest.TestCase):
    def setUp(self):
        self.root = Path.cwd()
        if (self.root / 'results').exists():
            shutil.rmtree(self.root / 'results')

    def tearDown(self):
        if (self.root / 'results').exists():
            shutil.rmtree(self.root / 'results')

    def test_validate_exports_success(self):
        case = 'TESTCASE_A'
        base = Path('results') / 'su2' / case
        inv_dir = base / 'inviscid'
        visc_dir = base / 'viscous'
        inv_dir.mkdir(parents=True, exist_ok=True)
        visc_dir.mkdir(parents=True, exist_ok=True)
        # create forces files
        with open(inv_dir / 'forces_breakdown.dat', 'w') as f:
            f.write('Total CL: 0.7\nTotal CD: 0.07\nTotal CM: 0.007\n')
        with open(visc_dir / 'forces_breakdown.dat', 'w') as f:
            f.write('Total CL: 0.6\nTotal CD: 0.06\nTotal CM: 0.006\n')
        # create json summaries
        inv_sum = {'CL': 0.7, 'CD': 0.07, 'CM': 0.007}
        visc_sum = {'CL': 0.6, 'CD': 0.06, 'CM': 0.006}
        with open(inv_dir / 'run_summary.json', 'w') as jf:
            json.dump(inv_sum, jf)
        with open(visc_dir / 'run_summary.json', 'w') as jf:
            json.dump(visc_sum, jf)
        results_list = [{'case': case, 'inviscid': (0.7, 0.07, 0.007), 'viscous': (0.6, 0.06, 0.006)}]
        ok = main_mod.validate_exports(results_list)
        self.assertTrue(ok)

    def test_validate_exports_missing_forces(self):
        case = 'TESTCASE_B'
        base = Path('results') / 'su2' / case
        inv_dir = base / 'inviscid'
        visc_dir = base / 'viscous'
        inv_dir.mkdir(parents=True, exist_ok=True)
        # create only JSON for inviscid, missing forces
        inv_sum = {'CL': 0.7, 'CD': 0.07, 'CM': 0.007}
        with open(inv_dir / 'run_summary.json', 'w') as jf:
            json.dump(inv_sum, jf)
        results_list = [{'case': case, 'inviscid': (0.7, 0.07, 0.007), 'viscous': None}]
        ok = main_mod.validate_exports(results_list)
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main()
