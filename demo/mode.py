import os
import sys

# install our plot
import plot

debug = os.getenv("DEMO_DEBUG", False)



#
# This is temporary scaffolding for experimenting with different implementation strategies
# TODO: if any of this needs to be permanent maybe consider using classes instead of import *
#

# in jupyter?
try:
    __IPYTHON__
    in_jupyter = True
except:
    in_jupyter = False

# in jupyter_lite?
try:
    import pyodide
    in_jupyterlite = True
except:
    in_jupyterlite = False


# defaults
if in_jupyter:
    use_widgets = "ipy"
    use_plot = "plotly"
else:
    use_widgets = "dash"
    use_plot = "plotly"

# which widgets to use    
use = os.getenv("DEMO_USE", "").split(",")
if "ipy" in use:
    use_widgets = "ipy"
elif "dash" in use:
    use_widgets = "dash"
if use_widgets == "ipy":
    from mode_ipy import *
    requires = ["ipywidgets", "plotly"]
elif use_widgets == "dash":
    from mode_dash import *
    requires = []

# which plotting library to use    
if "plotly" in use:
    use_plot = "plotly"
elif "matplotlib" in use:
    use_plot = "matplotlib"
if use_plot == "plotly":
    from mode_plotly import *
elif use_plot == "matplotlib":
    from mode_matplotlib import *

# whether to use boxes or not
use_boxes = "boxes" in use
if use_boxes:
    from mode_box import *
else:
    from mode_unbox import *


# in jupyterlite install requirements
# TODO: this would require an async function for it to be called from
# not sure how to do that (or if it's possible) while importing modules
async def install_requirements():
    import piplite
    for r in requires:
        print("installing", r)
        await piplite.install(r)

# stub fe for jupyter
if in_jupyter:

    # FE stub - just wraps a session
    # TODO: reconsider this?
    class FE:
        def __init__(self):
            self.session = mcs.MathicsSession()
    the_fe = FE()

    sys.stdout = sys.__stderr__
    if not os.getenv("DEMO_DEBUG", False):
        util.Timer.quiet = True
    
