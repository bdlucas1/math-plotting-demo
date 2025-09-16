import time

# pretty print expr
def prt(expr, indent=1):
    if not hasattr(expr, "elements"):
        print("  " * indent + str(expr))
    else:
        print("  " * indent + str(expr.head))
        for elt in expr.elements:
            prt(elt, indent + 1)


timers = []

def start_timer(name):
    timers.append((name, time.time()))

def stop_timer():
    name, start = timers.pop()
    ms = (time.time() - start) * 1000
    print(f"{name}: {ms:.1f} ms")
