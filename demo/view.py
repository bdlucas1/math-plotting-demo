#!/usr/bin/env python3

import argparse
import subprocess
import sys
import time
import webbrowser
import webview

parser = argparse.ArgumentParser(description="Graphics demo")
parser.add_argument("url", type=str)
parser.add_argument("--browser", choices=["webview", "webbrowser"], default="webview")
parser.add_argument("--delay", type=float, default=1.0)
parser.add_argument("-", nargs=argparse.REMAINDER, dest="cmd")
args = parser.parse_args()

process = subprocess.Popen(args.cmd, stdout=sys.stdout, stderr=sys.stderr)
time.sleep(args.delay)

if args.browser == "webview":
    webview.create_window(args.url, args.url, x=50, y=50, width=900, height=1200)
    webview.start()
elif args.browser == "webbrowser":
    webbrowser.open_new(args.url)
    process.wait()
    
