import os

use = os.getenv("DEMO_USE", "").split(",")

try:
    __IPYTHON__
    in_jupyter = True
except:
    in_jupyter = False

try:
    import pyodide
    in_jupyterlite = True
except:
    in_jupyterlite = False


# TODO: should this be harcoded?
if "ipy" in use:
    from mode_ipy import *
else:
    from mode_dash import *


if in_jupyter:

    # FE stub - just wraps a session
    # TODO: reconsider this?
    class FE:
        def __init__(self):
            self.session = mcs.MathicsSession()
    the_fe = FE()

    util.Timer.quiet = True
    
