import os
from pathlib import Path
import su2_runner
import pipeline

# monkeypatch _check_su2_available
su2_runner._check_su2_available = lambda : 'SU2_CFD'
# monkeypatch subprocess.run
class FakeR:
    def __init__(self, out='SU2 finished', err=''):
        self.returncode = 0
        self.stdout = out
        self.stderr = err

su2_runner.subprocess.run = lambda *a, **kw: FakeR()

# Prepare tmp output
tmpdir = Path('tmp_tmp_run')
if tmpdir.exists():
    import shutil
    shutil.rmtree(tmpdir)
tmpdir.mkdir()

# ensure mesh exists
mesh_file = Path('meshes') / 'airfoil_mesh.su2'
mesh_file.parent.mkdir(parents=True, exist_ok=True)
mesh_file.write_text('mesh content')

cfg_template = pipeline.CFG_INVISCID
print('CFG template path:', cfg_template)
print('template exists:', Path(cfg_template).exists())

res = su2_runner.run_su2(str(mesh_file), cfg_template, output_dir=str(tmpdir), viscous=False)
print('Result:', res)

if (tmpdir / 'config_tmp.cfg').exists():
    print('config_tmp.cfg exists. Contents:')
    print((tmpdir / 'config_tmp.cfg').read_text())
else:
    print('No config_tmp.cfg found in tmpdir')

if (tmpdir / 'run_summary.json').exists():
    print('run_summary.json contents:')
    print((tmpdir / 'run_summary.json').read_text())
