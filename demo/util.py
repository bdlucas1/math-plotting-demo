import os
import time
import urllib.parse

import mcs


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


class Timer:

    """
    Times a block of code. Maybe be used as a decorator or as a context manager:

        # decorator
        @Timer(name):
        def f(...):
            ...

        # context manager
        with Timer(name):
            ...

    Timings are nested (in execution order), and the output prints the nested
    timings as an "upside-down" indented outline, with an outer level printed after
    all nested inner levels, supporting both detailed and summary timings.
    
    Timing.level controls how deeply nested timings are displayed:
    -1 all, 0 none, 1 only top level, etc.  Default is 0. Use MATHICS_TIMING
    environment variable to change.
    """

    level = int(os.getenv("MATHICS_TIMING", "0"))
    timers = []

    def __init__(self, name):
        self.name = name

    def __call__(self, fun):
        def timed_fun(*args, **kwargs):
            with self:
                return fun(*args, **kwargs)
        return timed_fun

    def start(name):
        Timer.timers.append((name, time.time()))

    def stop():
        name, start = Timer.timers.pop()
        ms = (time.time() - start) * 1000
        if Timer.level < 0 or len(Timer.timers) < Timer.level:
            print(f"{'  '*len(Timer.timers)}{name}: {ms:.1f} ms")

    def __enter__(self):
        if self.name:
            Timer.start(self.name)

    def __exit__(self, *args):
        if self.name:
            Timer.stop()

# possibly override our local definition
if os.getenv("DEMO_USE_MATHICS", False):
    print("using mathics version of Timer")
    from mathics.core.util import Timer
else:
    print("using demo version of Timer")

#
#
#

def get_rules(expr):
    for e in expr.elements:
        if hasattr(e, "head") and e.head == mcs.SymbolRule:
            yield e

def get_rule_values(expr):
    for rule in get_rules(expr):
        yield rule.elements[0], rule.elements[1].to_python()

