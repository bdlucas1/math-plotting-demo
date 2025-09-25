import time
import urllib.parse

import dash_extensions


#
# pretty print expr
#

def prt(expr, indent=1):
    if not hasattr(expr, "elements"):
        print("  " * indent + str(expr))
    else:
        print("  " * indent + str(expr.head))
        for elt in expr.elements:
            prt(elt, indent + 1)


#
# to time a block of code use with Timer(name): code
# use Timer.level to control max  nesting level:
#     -1 all, 0 none, 1 only top level, etc.

class Timer:

    level = -1 # all
    quiet = False
    timers = []

    def start(name):
        Timer.timers.append((name, time.time()))

    def stop():
        name, start = Timer.timers.pop()
        ms = (time.time() - start) * 1000
        if Timer.level < 0 or len(Timer.timers) < Timer.level:
            if not Timer.quiet:
                print(f"{"  "*len(Timer.timers)}{name}: {ms:.1f} ms")

    def __init__(self, name, quiet = False):
        self.name = name
        self.quiet = quiet
    def __enter__(self):
        if not self.quiet:
            Timer.start(self.name)
    def __exit__(self, *args):
        if not self.quiet:
            Timer.stop()

#
# use in a layout to arrange for js to be executed after the layout is loaded
# see code for examples
#
# TODO: this is a bit hacky - can we do better?
#

def exec_js(js):
    params = urllib.parse.urlencode(dict(js=js))
    url = f"/assets/exec_js.js?{params}"
    return dash_extensions.DeferScript(src=url)


            
