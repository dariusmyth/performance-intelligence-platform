import os
import subprocess
from datetime import datetime

RUN_ID = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
BASE = f"results/{RUN_ID}"

os.makedirs(BASE, exist_ok=True)

cmd = f"""
jmeter -n -t jmx/test_plan.jmx \
-l {BASE}/results.jtl \
-e -o {BASE}/jmeter-report
"""

subprocess.run(cmd, shell=True, check=True)

print(RUN_ID)