import os
import tempfile
import shutil
import unittest
from pathlib import Path

import su2_configurator


class TestSU2Configurator(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.template = os.path.join(self.tmpdir, 'template.cfg')
        with open(self.template, 'w') as f:
            f.write('MESH_FILENAME = mesh.su2\n')
            f.write('AOA = 2.0\n')
            f.write('MACH_NUMBER = 0.2\n')
            f.write('REYNOLDS_NUMBER = 5000000\n')
            f.write('ITER = 50\n')
            f.write('CFL = 0.5\n')
            f.write('BREAKDOWN_FILENAME = forces_breakdown.dat\n')
            f.write('RESTART_FILENAME = restart.csv\n')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_create_config_for_case_replaces_values(self):
        out = os.path.join(self.tmpdir, 'config_out.cfg')
        mesh = '/mnt/c/tmp/mesh.su2'
        breakdown = '/mnt/c/tmp/forces_breakdown.dat'
        su2_configurator.create_config_for_case(self.template, out, mesh_wsl=mesh, aoa=3.5, mach=0.25, Re=3e6, iter_val=200, cfl=1.0, breakdown_wsl=breakdown, restart_wsl='/mnt/c/tmp/restart.csv')
        self.assertTrue(os.path.exists(out))
        txt = Path(out).read_text()
        self.assertIn('MESH_FILENAME = /mnt/c/tmp/mesh.su2', txt)
        self.assertIn('AOA = 3.5', txt)
        self.assertIn('MACH_NUMBER = 0.25', txt)
        self.assertIn('REYNOLDS_NUMBER = 3000000.0', txt)
        self.assertIn('ITER = 200', txt)
        self.assertIn('CFL = 1.0', txt)
        self.assertIn('BREAKDOWN_FILENAME = /mnt/c/tmp/forces_breakdown.dat', txt)
        self.assertIn('RESTART_FILENAME = /mnt/c/tmp/restart.csv', txt)


if __name__ == '__main__':
    unittest.main()
