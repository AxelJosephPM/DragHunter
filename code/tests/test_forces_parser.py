import unittest
import tempfile
from pathlib import Path

from su2_runner import parse_forces_file
from su2_runner import _get_config_restart_filename


BASE_SAMPLE = """
Some header text
Total CL: 0.123456
Total CD: -0.04567
Total CMz: 0.01234
Some other data
"""


BASE_SAMPLE_CM = """
Total CL: 1.001
Total CD: -0.200
Total CM: 0.0025
"""


class TestForcesParser(unittest.TestCase):
    def test_basic_parse_cl_cd_cmz(self):
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tf:
            tf.write(BASE_SAMPLE)
            tf.flush()
            tfp = Path(tf.name)
        try:
            cl, cd, cm = parse_forces_file(str(tfp))
            self.assertAlmostEqual(cl, 0.123456)
            self.assertAlmostEqual(cd, -0.04567)
            self.assertAlmostEqual(cm, 0.01234)
        finally:
            tfp.unlink()

    def test_cm_fallback(self):
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tf:
            tf.write(BASE_SAMPLE_CM)
            tf.flush()
            tfp = Path(tf.name)
        try:
            cl, cd, cm = parse_forces_file(str(tfp))
            self.assertAlmostEqual(cl, 1.001)
            self.assertAlmostEqual(cd, -0.2)
            self.assertAlmostEqual(cm, 0.0025)
        finally:
            tfp.unlink()

    def test_missing_raises(self):
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tf:
            tf.write("no values here\n")
            tf.flush()
            tfp = Path(tf.name)
        try:
            with self.assertRaises(RuntimeError):
                parse_forces_file(str(tfp))
        finally:
            tfp.unlink()

    def test_get_restart_filename(self):
        sample_cfg = """
        RESTART_SOL          = YES
        RESTART_FILENAME     = restart.csv
        READ_BINARY_RESTART  = NO
        """
        import tempfile
        from pathlib import Path
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tf:
            tf.write(sample_cfg)
            tf.flush()
            cfp = Path(tf.name)
        try:
            rname, read_bin = _get_config_restart_filename(str(cfp))
            self.assertEqual(rname, 'restart.csv')
            self.assertFalse(read_bin)
        finally:
            cfp.unlink()


if __name__ == '__main__':
    unittest.main()
