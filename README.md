Installation

    pip install numpy dash plotly pywebview

Run demo with "shell" front end - does not actually take input but rather pops up two windows with graphics

    python plotting-plotly+dash/app.py --fe shell 

Run demo with "browser" front end. Displays a window that accepts an
"expression" string, which must be either "a" or "b", and "evaluates"
the expression and displays the resulting graphics. There's only one
field for now; you can change it and press shift-enter again to see a different
plot.

    python plotting-plotly+dash/app.py --fe browser 

