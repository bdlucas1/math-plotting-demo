import time

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
# start_timer and stop_timer must be paired
# use timer_level to control max  nesting level:
#     -1 all, 0 none, 1 only top level, etc.
#

timers = []
timer_level = -1 # all

def start_timer(name):
    timers.append((name, time.time()))

def stop_timer():
    name, start = timers.pop()
    ms = (time.time() - start) * 1000
    if timer_level < 0 or len(timers) < timer_level:
        print(f"{"  "*len(timers)}{name}: {ms:.1f} ms")
