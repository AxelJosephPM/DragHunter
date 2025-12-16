import os
import tempfile
import shutil
import unittest
from pathlib import Path

import pipeline
from su2_runner import run_su2


class TestOutputDirectories(unittest.TestCase):
    def setUp(self):
        # ensure a clean environment
        self.root = Path.cwd()
        self.mesh_dir = self.root / 'meshes'
        self.results_dir = self.root / 'results' / 'su2'
        # remove if exist
        if self.mesh_dir.exists():
            shutil.rmtree(self.mesh_dir)
        if (self.root / 'results').exists():
            shutil.rmtree(self.root / 'results')

    def tearDown(self):
        if self.mesh_dir.exists():
            shutil.rmtree(self.mesh_dir)
        if (self.root / 'results').exists():
            shutil.rmtree(self.root / 'results')

    def test_pipeline_makes_dirs_and_files(self):
        # Monkeypatch mesh generation to quickly create mesh file
        mesh_out = str(self.mesh_dir / 'airfoil_mesh.su2')

        def fake_generate_su2_mesh(dat_file, mesh_file):
            os.makedirs(os.path.dirname(mesh_file), exist_ok=True)
            with open(mesh_file, 'w') as f:
                f.write('mesh content')

        # Monkeypatch run_su2 to avoid running SU2; instead it will write forces_breakdown and return sample
        from su2_runner import run_su2 as original_run

        def fake_run_su2(mesh_file, cfg_template, aoa=2.0, mach=0.2, Re=5e6, viscous=False, max_iter=None, output_dir=None):
            os.makedirs(output_dir, exist_ok=True)
            # create a fake forces_breakdown.dat in the output dir
            fb = Path(output_dir) / 'forces_breakdown.dat'
            with open(fb, 'w') as f:
                f.write('Total CL: 0.5\nTotal CD: 0.05\nTotal CM: 0.01\n')
            return (0.5, 0.05, 0.01)

        # patch
        import mesh_generator
        # pipeline imported generate_su2_mesh directly; patch pipeline's reference
        pipeline.generate_su2_mesh = fake_generate_su2_mesh
        import su2_runner
        # pipeline imported run_su2 directly; patch pipeline's reference
        pipeline.run_su2 = fake_run_su2
        # keep original su2_runner.run_su2 untouched

        try:
            # run the pipeline (will use monkeypatched functions)
            pipeline.main()

            # Check directories and files exist
            self.assertTrue(self.mesh_dir.exists())
            self.assertTrue((self.mesh_dir / 'airfoil_mesh.su2').exists())
            self.assertTrue((self.results_dir / 'inviscid').exists())
            self.assertTrue((self.results_dir / 'viscous').exists())
            self.assertTrue((self.results_dir / 'inviscid' / 'forces_breakdown.dat').exists())
            self.assertTrue((self.results_dir / 'viscous' / 'forces_breakdown.dat').exists())
        finally:
            # restore
            pipeline.run_su2 = original_run

    def test_run_su2_writes_config_and_uses_output_dir(self):
        # This test will ensure that run_su2 writes config tmp with the proper paths and that
        # it parses the forces file in the output_dir. We mock subprocess and _check_su2_available.
        import su2_runner
        # fake _check_su2_available
        su2_runner._check_su2_available_backup = su2_runner._check_su2_available
        su2_runner._check_su2_available = lambda: 'SU2_CFD'

        # create a temporary output dir
        tmpdir = tempfile.mkdtemp()
        try:
            mesh_file = str(self.root / 'meshes' / 'airfoil_mesh.su2')
            os.makedirs(os.path.dirname(mesh_file), exist_ok=True)
            with open(mesh_file, 'w') as f:
                f.write('mesh content')

            # create cfg template
            cfg_template = pipeline.CFG_INVISCID

            # monkeypatch subprocess.run to avoid calling SU2
            import subprocess as real_sub
            def fake_subprocess_run(args, stdout, stderr, text):
                class R:
                    pass
                r = R()
                r.returncode = 0
                r.stdout = 'SU2 finished'
                r.stderr = ''
                return r

            su2_runner_backup_sub = su2_runner.subprocess.run
            su2_runner.subprocess.run = fake_subprocess_run

            # create a forces file in tmpdir
            fb = Path(tmpdir) / 'forces_breakdown.dat'
            with open(fb, 'w') as f:
                f.write('Total CL: 0.75\nTotal CD: 0.075\nTotal CM: 0.015\n')

            # create a minimal restart candidate file
            with open('restart.csv', 'w') as rfile:
                rfile.write('time,solution')

            # run the function
            result = su2_runner.run_su2(mesh_file, cfg_template, output_dir=tmpdir, viscous=False)
            cl, cd, cm = result[0], result[1], result[2]

            # check values
            self.assertAlmostEqual(cl, 0.75)
            self.assertAlmostEqual(cd, 0.075)
            self.assertAlmostEqual(cm, 0.015)

            # Check that logs were written
            self.assertTrue((Path(tmpdir) / 'su2_stdout.log').exists())
            self.assertTrue((Path(tmpdir) / 'su2_stderr.log').exists())
            # run_summary.json should also be present
            self.assertTrue((Path(tmpdir) / 'run_summary.json').exists())

            # check that config_tmp references the output dir for breakdown
            cfg_tmp = Path('config_tmp.cfg')
            text = cfg_tmp.read_text()
            import su2_runner as sr
            wsl_tmp = sr.to_wsl(str(Path(tmpdir).resolve()))
            self.assertIn('forces_breakdown.dat', text)
            self.assertIn(wsl_tmp, text)
            # check that run_summary.json is present
            self.assertTrue((Path(tmpdir) / 'run_summary.json').exists())

    def test_cfl_written_to_config_when_passed_to_run(self):
        import su2_runner
        su2_runner._check_su2_available_backup = su2_runner._check_su2_available
        su2_runner._check_su2_available = lambda: 'SU2_CFD'
        tmpdir = tempfile.mkdtemp()
        try:
            mesh_file = str(self.root / 'meshes' / 'airfoil_mesh.su2')
            os.makedirs(os.path.dirname(mesh_file), exist_ok=True)
            with open(mesh_file, 'w') as f:
                f.write('mesh content')
            # monkeypatch subprocess.run to avoid calling SU2
            def fake_subprocess_run(args, stdout, stderr, text):
                class R:
                    pass
                r = R()
                r.returncode = 0
                r.stdout = 'SU2 finished'
                r.stderr = ''
                return r
            su2_runner_backup_sub = su2_runner.subprocess.run
            su2_runner.subprocess.run = fake_subprocess_run
            # create a forces file in tmpdir
            fb = Path(tmpdir) / 'forces_breakdown.dat'
            with open(fb, 'w') as f:
                f.write('Total CL: 0.75\nTotal CD: 0.075\nTotal CM: 0.015\n')
            # run with cfl override
            su2_runner.run_su2(mesh_file, pipeline.CFG_INVISCID, output_dir=tmpdir, viscous=False, cfl=0.25)
            cfg_tmp = Path('config_tmp.cfg')
            text = cfg_tmp.read_text()
            self.assertIn('CFL = 0.25', text)
        finally:
            su2_runner._check_su2_available = su2_runner._check_su2_available_backup
            su2_runner.subprocess.run = su2_runner_backup_sub
            shutil.rmtree(tmpdir)

        finally:
            # restore
            su2_runner._check_su2_available = su2_runner._check_su2_available_backup
            su2_runner.subprocess.run = su2_runner_backup_sub
            if os.path.exists('restart.csv'):
                os.unlink('restart.csv')
            shutil.rmtree(tmpdir)


if __name__ == '__main__':
    unittest.main()
