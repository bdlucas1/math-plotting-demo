import os

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
else:
    use_widgets = "dash"


# override with env variable    
use = os.getenv("DEMO_USE", "").split(",")
if "ipy" in use:
    use_widgets = "ipy"
elif "dash" in use:
    use_widgets = "dash"


# which widgets to use    
if use_widgets == "ipy":
    from mode_ipy import *
    requires = ["ipywidgets", "plotly"]
elif use_widgets == "dash":
    from mode_dash import *
    requires = []

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

    util.Timer.quiet = True
    
