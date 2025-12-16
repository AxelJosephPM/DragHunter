import os
import tempfile
import shutil
import unittest
from pathlib import Path

import su2_runner


class TestSU2RunnerRetries(unittest.TestCase):
    def setUp(self):
        self.root = Path.cwd()
        self.tmpdir = tempfile.mkdtemp()
        self.mesh_file = str(self.root / 'meshes' / 'airfoil_mesh.su2')
        os.makedirs(os.path.dirname(self.mesh_file), exist_ok=True)
        with open(self.mesh_file, 'w') as f:
            f.write('mesh')
        # Make sure we have a config template path available
        self.cfg_template = str(self.root / 'config' / 'su2_template_inv.cfg')
        if not Path(self.cfg_template).exists():
            # make a minimal config template for testing including CFL and ITER
            os.makedirs(Path(self.cfg_template).parent, exist_ok=True)
            with open(self.cfg_template, 'w') as c:
                c.write('CFL = 8.0\n')
                c.write('ITER = 50\n')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        if (self.root / 'meshes').exists():
            shutil.rmtree(self.root / 'meshes')

    def test_retry_on_nonconvergence(self):
        # Simulate SU2 subprocess output: first is non-converged, second is converged
        calls = {'n': 0}

        def fake_check():
            return '/usr/bin/SU2_CFD'

        def fake_run(cmd, stdout, stderr, text):
            class R:
                pass
            calls['n'] += 1
            r = R()
            if calls['n'] == 1:
                r.returncode = 0
                r.stdout = 'Maximum number of iterations reached'
                r.stderr = ''
                # first attempt: no forces created
            else:
                r.returncode = 0
                r.stdout = 'SU2 finished'
                r.stderr = ''
                # second attempt: create forces file
                fb = Path(self.tmpdir) / 'forces_breakdown.dat'
                with open(fb, 'w') as f:
                    f.write('Total CL: 0.9\nTotal CD: 0.09\nTotal CM: 0.009\n')
            return r

        su2_runner._check_su2_available_backup = su2_runner._check_su2_available
        su2_runner._check_su2_available = lambda: 'SU2_CFD'
        su2_runner_backup_sub = su2_runner.subprocess.run
        su2_runner.subprocess.run = fake_run

        try:
            result = su2_runner.run_su2(self.mesh_file, self.cfg_template, output_dir=self.tmpdir, max_iter=50, retries=1, strict=True)
            self.assertIsNotNone(result)
            # result should now have extended fields (CL,CD,CM, final_iter, final_rms, converged)
            self.assertEqual(len(result), 6)
            self.assertAlmostEqual(result[0], 0.9)
            # run_summary.json must be present in output dir
            self.assertTrue((Path(self.tmpdir) / 'run_summary.json').exists())
            # run_summary.json must indicate the final CFL (should be less than initial default or template value)
            import json
            summary = json.loads((Path(self.tmpdir) / 'run_summary.json').read_text())
            self.assertIn('final_CFL', summary)
            # final CFL should be a float and less or equal to the starting default 0.5
            self.assertIsInstance(summary['final_CFL'], float)
            self.assertLessEqual(summary['final_CFL'], 0.5)
        finally:
            su2_runner._check_su2_available = su2_runner._check_su2_available_backup
            su2_runner.subprocess.run = su2_runner_backup_sub


if __name__ == '__main__':
    unittest.main()
