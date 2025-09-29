import subprocess
import sys
import time
import webview

# TODO: generalize this to take url and command from command line?
# TODO: generalize to take flag to use either webview or system browser?

token = "foo"
url = f"http://localhost:8888/lab/tree/{sys.argv[1]}?token={token}"
cmd = ["jupyter-lab", "--no-browser", f"--ServerApp.token={token}"]

subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
time.sleep(1)

webview.create_window(url, url, x=50, y=50, width=900, height=1200)
webview.start()
