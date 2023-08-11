import subprocess
entry_point_sh_name = 123.sh
ret = subprocess.run('bash 123.sh', shell=True, capture_output=True, encoding='utf-8')
