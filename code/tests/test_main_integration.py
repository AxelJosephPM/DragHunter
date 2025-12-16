import os
import shutil
import tempfile
import unittest
from pathlib import Path

import main as main_mod
import pipeline


class TestMainPipelineIntegration(unittest.TestCase):
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

    def test_generate_and_analyze_profiles_calls_run_case(self):
        # Monkeypatch pipeline.run_case to write files and return dummy results
        called = []

        def fake_run_case(dat_file, case_name, aoa=2.0, mach=0.2, Re=5e6, max_iter=None, retries=1, strict=False, cfl=None):
            called.append((case_name, dat_file))
            # create directories and sample output
            mesh_case_dir = Path('meshes') / case_name
            results_case_dir = Path('results') / 'su2' / case_name
            (mesh_case_dir).mkdir(parents=True, exist_ok=True)
            (results_case_dir / 'inviscid').mkdir(parents=True, exist_ok=True)
            (results_case_dir / 'viscous').mkdir(parents=True, exist_ok=True)
            # create a fake forces file
            with open(results_case_dir / 'inviscid' / 'forces_breakdown.dat', 'w') as f:
                f.write('Total CL: 0.7\nTotal CD: 0.07\nTotal CM: 0.007\n')
            # append to summary.csv like actual run_case
            os.makedirs('results', exist_ok=True)
            summary_file = Path('results') / 'summary.csv'
            if not summary_file.exists():
                with open(summary_file, 'w') as sf:
                    sf.write('timestamp,case,dat_file,aoa,mach,Re,CL_inv,CD_inv,CM_inv,CL_visc,CD_visc,CM_visc\n')
            with open(summary_file, 'a') as sf:
                sf.write(f"now,{case_name},{dat_file},{aoa},{mach},{Re},0.7,0.07,0.007,0.6,0.06,0.006\n")
            with open(results_case_dir / 'viscous' / 'forces_breakdown.dat', 'w') as f:
                f.write('Total CL: 0.6\nTotal CD: 0.06\nTotal CM: 0.006\n')
            return {"case": case_name, "inviscid": (0.7, 0.07, 0.007), "viscous": (0.6, 0.06, 0.006)}

        pipeline_run_backup = pipeline.run_case
        pipeline.run_case = fake_run_case

        try:
            # Generate and analyze for two simple profiles
            esp = [0.12, 0.14]
            cu = [1.0]
            profiles = main_mod.generate_airfoils(esp, cu, normalize=False, output_folder='generated_profiles')
            results = main_mod.analyze_profiles(profiles, aoa=2.0)
            # Confirm run_case called expected number of times (profiles × AoA_list × Mach_list × Re_list)
            expected_calls = len(profiles) * len(main_mod.DEFAULT_AOA_LIST) * len(main_mod.DEFAULT_MACH_LIST) * len(main_mod.DEFAULT_RE_LIST)
            self.assertEqual(len(called), expected_calls)

            # Confirm the results directories and files exist for each call we intercepted
            for call in called:
                case_name = call[0]
                self.assertTrue((Path('meshes') / case_name).exists())
                self.assertTrue((Path('results') / 'su2' / case_name / 'inviscid' / 'forces_breakdown.dat').exists())
                self.assertTrue((Path('results') / 'su2' / case_name / 'viscous' / 'forces_breakdown.dat').exists())

        finally:
            pipeline.run_case = pipeline_run_backup

    def test_analyze_profiles_aoa_sweep_and_summary(self):
        pipeline_run_backup = pipeline.run_case
        called = []

        def fake_run_case(dat_file, case_name, aoa=2.0, mach=0.2, Re=5e6, max_iter=None, retries=1, strict=False, cfl=None):
            called.append((case_name, aoa))
            mesh_case_dir = Path('meshes') / case_name
            results_case_dir = Path('results') / 'su2' / case_name
            mesh_case_dir.mkdir(parents=True, exist_ok=True)
            (results_case_dir / 'inviscid').mkdir(parents=True, exist_ok=True)
            (results_case_dir / 'viscous').mkdir(parents=True, exist_ok=True)
            with open(results_case_dir / 'inviscid' / 'forces_breakdown.dat', 'w') as f:
                f.write('Total CL: 0.7\nTotal CD: 0.07\nTotal CM: 0.007\n')
            # append to summary.csv like actual run_case
            os.makedirs('results', exist_ok=True)
            summary_file = Path('results') / 'summary.csv'
            if not summary_file.exists():
                with open(summary_file, 'w') as sf:
                    sf.write('timestamp,case,dat_file,aoa,mach,Re,CL_inv,CD_inv,CM_inv,CL_visc,CD_visc,CM_visc\n')
            with open(summary_file, 'a') as sf:
                sf.write(f"now,{case_name},{dat_file},{aoa},{mach},{Re},0.7,0.07,0.007,0.6,0.06,0.006\n")
            return {"case": case_name, "inviscid": (0.7, 0.07, 0.007), "viscous": (0.6, 0.06, 0.006)}

        pipeline.run_case = fake_run_case

        try:
            esp = [0.12]
            cu = [1.0]
            profiles = main_mod.generate_airfoils(esp, cu, normalize=False, output_folder='generated_profiles')
            aoa_list = [0.0, 2.0]
            results = main_mod.analyze_profiles(profiles, aoa=2.0, aoa_list=aoa_list)
            # Expect number of calls = profiles × aoa_list × default mach list × default re list
            expected_calls = len(profiles) * len(aoa_list) * len(main_mod.DEFAULT_MACH_LIST) * len(main_mod.DEFAULT_RE_LIST)
            self.assertEqual(len(called), expected_calls)
            # Check that CSV was created
            summary = Path('results') / 'summary.csv'
            self.assertTrue(summary.exists())
            text = summary.read_text()
            self.assertIn('CL_inv', text)
        finally:
            pipeline.run_case = pipeline_run_backup

    def test_overwrite_case_without_timestamp(self):
        """Check that rerunning analyze_profiles for the same case (no timestamp) overwrites previous CSV entries."""
        # We will directly call the real pipeline.run_case, mocking internals instead
        # backup
        gen_backup = pipeline.generate_su2_mesh
        run_backup = pipeline.run_su2
        try:
            esp = [0.12]
            cu = [1.0]
            profiles = main_mod.generate_airfoils(esp, cu, normalize=False, output_folder='generated_profiles')
            # Prepare a case name without timestamp
            key = list(profiles.keys())[0]
            dat_path = profiles[key]['dat']
            case_name = pipeline.generate_case_name(key, 2.0, 0.2, 5e6, add_ts=False)
            # run case twice (should overwrite previous case)
            # monkeypatch generate_su2_mesh and run_su2 to be fast
            def fake_gen(dat_file, mesh_file):
                os.makedirs(os.path.dirname(mesh_file), exist_ok=True)
                with open(mesh_file, 'w') as f:
                    f.write('mesh')

            def fake_run(mesh_file, cfg_template, aoa=2.0, mach=0.2, Re=5e6, viscous=False, max_iter=None, retries=1, strict=False, output_dir=None, cfl=None):
                os.makedirs(output_dir, exist_ok=True)
                fb = Path(output_dir) / 'forces_breakdown.dat'
                with open(fb, 'w') as ff:
                    ff.write('Total CL: 0.7\nTotal CD: 0.07\nTotal CM: 0.007\n')
                return (0.7, 0.07, 0.007)

            pipeline.generate_su2_mesh = fake_gen
            pipeline.run_su2 = fake_run
            pipeline.run_case(dat_path, case_name, aoa=2.0)
            pipeline.run_case(dat_path, case_name, aoa=2.0)
            # Check that CSV contains a single row for the case (excluding header)
            summary = Path('results') / 'summary.csv'
            self.assertTrue(summary.exists())
            rows = [r for r in summary.read_text().splitlines() if r.strip()]
            # header + 1 row
            self.assertEqual(len(rows), 2)
            # ensure case name appears once
            case_name = list(profiles.keys())[0] + "_AoA2.0_M0.20_Re5000000"
            # generate_case_name default uses no timestamp so case_name is as above
            self.assertIn('NACA0012_c1.0m_AoA2.0_M0.20_Re5000000', rows[1])
        finally:
            # restore
            pipeline.generate_su2_mesh = gen_backup
            pipeline.run_su2 = run_backup


if __name__ == '__main__':
    unittest.main()
