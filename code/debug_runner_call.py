import os
from pathlib import Path
import su2_runner
import pipeline

logf = open('debug_runner_call.log','w')
logf.write('Starting debug runner call\n')

su2_runner._check_su2_available = lambda : 'SU2_CFD'

class FakeR:
    def __init__(self, out='SU2 finished', err=''):
        self.returncode = 0
        self.stdout = out
        self.stderr = err

su2_runner.subprocess.run = lambda *a, **kw: FakeR()

# set up
root = Path.cwd()
mesh_file = root / 'meshes' / 'airfoil_mesh.su2'
mesh_file.parent.mkdir(parents=True, exist_ok=True)
mesh_file.write_text('mesh content')

cfg_template = pipeline.CFG_INVISCID
logf.write(f'cfg_template: {cfg_template}, exists: {Path(cfg_template).exists()}\n')

outdir = Path('tmp_debug_output')
if outdir.exists():
    import shutil
    shutil.rmtree(outdir)
outdir.mkdir()

# Pre-create forces file to emulate SU2 output
with open(outdir / 'forces_breakdown.dat', 'w') as f:
    f.write('Total CL: 0.65\nTotal CD: 0.065\nTotal CM: 0.0065\n')

try:
    res = su2_runner.run_su2(str(mesh_file), cfg_template, output_dir=str(outdir), viscous=False)
    logf.write(f'result: {res}\n')
except Exception as e:
    import traceback
    logf.write('exception during run:\n')
    traceback.print_exc(file=logf)
finally:
    logf.close()

print('done, check debug_runner_call.log')
