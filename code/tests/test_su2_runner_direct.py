import os
import tempfile
import shutil
import unittest
from pathlib import Path

import su2_runner
import pipeline


class TestSU2RunnerDirect(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path.cwd()
        self.mesh_file = str(self.root / 'meshes' / 'airfoil_mesh.su2')
        os.makedirs(os.path.dirname(self.mesh_file), exist_ok=True)
        with open(self.mesh_file, 'w') as f:
            f.write('mesh')
        self.cfg_template = pipeline.CFG_INVISCID

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        if Path(self.root / 'meshes').exists():
            shutil.rmtree(self.root / 'meshes')

    def test_run_su2_direct_happy_path(self):
        su2_runner._check_su2_available = lambda: 'SU2_CFD'
        # Make subprocess.run create the forces file in the output dir on run
        calls = {'n': 0}

        def fake_run(*args, **kwargs):
            class R:
                pass
            calls['n'] += 1
            r = R()
            r.returncode = 0
            r.stdout = 'SU2 finished'
            r.stderr = ''
            return r

        su2_runner.subprocess.run = fake_run

        # create forces file in tmpdir
        fb = Path(self.tmpdir) / 'forces_breakdown.dat'
        with open(fb, 'w') as f:
            f.write('Total CL: 0.5\nTotal CD: 0.05\nTotal CM: 0.01\n')

        result = su2_runner.run_su2(self.mesh_file, self.cfg_template, output_dir=self.tmpdir, viscous=False)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 0.5)


if __name__ == '__main__':
    unittest.main()
