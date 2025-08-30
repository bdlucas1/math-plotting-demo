Installation

    pip install numpy dash plotly pywebview

Run demo with "shell" front end - does not actually take input but rather pops up two windows with graphics

    python --fe shell plotting-plotly+dash/app.py

Run demo with "browser" front end. Displays a window that accepts an
"expression" string, which must be either "a" or "b", and "evaluates"
the expression and displays the resulting graphics

    python --fe browser plotting-plotly+dash/app.py

