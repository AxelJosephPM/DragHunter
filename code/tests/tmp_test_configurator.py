from pathlib import Path
import su2_configurator

print('template exists:', Path('config/su2_template_inv.cfg').exists())
try:
    su2_configurator.create_config_for_case('config/su2_template_inv.cfg','config_tmp.cfg', mesh_wsl='/mnt/c/tmp/test.su2', aoa=3.5, mach=0.25, Re=5000000, iter_val=200, cfl=1.0)
    print('out_exists:', Path('config_tmp.cfg').exists())
    print('---OUTPUT---')
    with open('config_tmp.cfg', 'r', encoding='utf-8') as f:
        print(f.read())
except Exception as e:
    import traceback
    traceback.print_exc()
