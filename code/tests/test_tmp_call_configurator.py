import unittest
from pathlib import Path
import su2_configurator
import pipeline


class TestLauncherConfig(unittest.TestCase):
    def test_template_with_project_template(self):
        cfg_template = pipeline.CFG_INVISCID
        self.assertTrue(Path(cfg_template).exists())
        su2_configurator.create_config_for_case(cfg_template, 'config_tmp.cfg', mesh_wsl='/mnt/c/tmp/testmesh.su2', aoa=2.1, mach=0.2, Re=5e6, iter_val=100, cfl=1.0)
        self.assertTrue(Path('config_tmp.cfg').exists())


if __name__ == '__main__':
    unittest.main()
