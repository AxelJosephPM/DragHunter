import os
import shutil
import unittest
from pathlib import Path

import main as main_mod
import pipeline


class TestMainListIteration(unittest.TestCase):
    def setUp(self):
        self.root = Path.cwd()
        # ensure no artifacts remain
        if (self.root / 'meshes').exists():
            shutil.rmtree(self.root / 'meshes')
        if (self.root / 'results').exists():
            shutil.rmtree(self.root / 'results')
        if (self.root / 'generated_profiles').exists():
            shutil.rmtree(self.root / 'generated_profiles')

    def tearDown(self):
        if (self.root / 'meshes').exists():
            shutil.rmtree(self.root / 'meshes')
        if (self.root / 'results').exists():
            shutil.rmtree(self.root / 'results')
        if (self.root / 'generated_profiles').exists():
            shutil.rmtree(self.root / 'generated_profiles')

    def test_cartesian_product_iteration(self):
        called = []

        def fake_run_case(dat_file, case_name, aoa=2.0, mach=0.2, Re=5e6, max_iter=None, retries=1, strict=False, cfl=None):
            called.append((case_name, aoa, mach, Re))
            mesh_case_dir = Path('meshes') / case_name
            results_case_dir = Path('results') / 'su2' / case_name
            (mesh_case_dir).mkdir(parents=True, exist_ok=True)
            (results_case_dir / 'inviscid').mkdir(parents=True, exist_ok=True)
            (results_case_dir / 'viscous').mkdir(parents=True, exist_ok=True)
            # create a fake forces file
            with open(results_case_dir / 'inviscid' / 'forces_breakdown.dat', 'w') as f:
                f.write('Total CL: 0.7\nTotal CD: 0.07\nTotal CM: 0.007\n')
            with open(results_case_dir / 'viscous' / 'forces_breakdown.dat', 'w') as f:
                f.write('Total CL: 0.6\nTotal CD: 0.06\nTotal CM: 0.006\n')
            return {"case": case_name, "inviscid": (0.7, 0.07, 0.007), "viscous": (0.6, 0.06, 0.006)}

        pipeline_backup = pipeline.run_case
        pipeline.run_case = fake_run_case

        try:
            esp = [0.12]
            cu = [1.0]
            profiles = main_mod.generate_airfoils(esp, cu, normalize=False, output_folder='generated_profiles')
            aoa_list = [0.0, 2.0]
            mach_list = [0.15, 0.2]
            re_list = [1e6, 5e6]
            expected_calls = len(profiles) * len(aoa_list) * len(mach_list) * len(re_list)
            results = main_mod.analyze_profiles(profiles, aoa=2.0, mach=0.2, Re=5e6, aoa_list=aoa_list, mach_list=mach_list, Re_list=re_list)
            self.assertEqual(len(called), expected_calls)
            # check one of the case names contains the expected parameter string
            found_expected = False
            for call in called:
                _, a, m, r = call
                if a == aoa_list[1] and m == mach_list[1] and r == re_list[1]:
                    found_expected = True
                    break
            self.assertTrue(found_expected)

        finally:
            pipeline.run_case = pipeline_backup


if __name__ == '__main__':
    unittest.main()
