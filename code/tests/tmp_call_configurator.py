from pathlib import Path
import su2_configurator
import pipeline

cfg_template = pipeline.CFG_INVISCID
print('cfg_template', cfg_template)
print('exists', Path(cfg_template).exists())
try:
    su2_configurator.create_config_for_case(cfg_template, 'config_tmp.cfg', mesh_wsl='/mnt/c/tmp/testmesh.su2', aoa=2.1, mach=0.2, Re=5e6, iter_val=100, cfl=1.0)
    print('config_tmp.cfg created')
    print(Path('config_tmp.cfg').read_text())
except Exception as e:
    import traceback
    traceback.print_exc()
