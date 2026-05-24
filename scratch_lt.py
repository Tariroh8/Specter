import subprocess
import time
import os

proc = subprocess.Popen(
    ["npx.cmd", "-y", "localtunnel", "--port", "5000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    creationflags=0x08000000
)

# wait a little bit for it to output
time.sleep(2)
url = None
# We use readline with a timeout or just wait for 1 line
line = proc.stdout.readline()
if "your url is:" in line:
    url = line.split("your url is:")[1].strip()

print(f"Got URL: {url}")
proc.terminate()
