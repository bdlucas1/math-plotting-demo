Task: evaluate an expression at 40,000 (x,y) pairs, simulating the
work needed to plot a function on a 200x200 grid. Three expressions tried:

* expr1: Sin[(x^2+y^2) * a] * b

* expr2: Sin[(x^2+y^2) * a] / Sqrt[x^2+y^2+1] * b

* expr3: Hypergeometric1F1[a, b, (x + I y) ^ 2]. (Note: testing with
  this expression is incomplete because compilation failed; see [Issue
  1502](https://github.com/Mathics3/mathics-core/issues/1502).

Five compilation/execution strategies tried. The first two are based
on code lifted directly from the [current Plot
implementation](https://github.com/Mathics3/mathics-core/blob/master/mathics/eval/drawing/plot.py):

* [none](https://github.com/bdlucas1/math-plotting-demo/blob/62297f94db02cc39f784cb5e4135db8662e45d17/compile-timings/compile-timings.py#L48): has_compile is false. Just wraps expression in N[] and
  evaluates it. The 40,000 evaluations of the expression are [done
  point-by-point](https://github.com/bdlucas1/math-plotting-demo/blob/62297f94db02cc39f784cb5e4135db8662e45d17/compile-timings/compile-timings.py#L177), i.e. invoking the compiled expression 40,000 times.

* [llvm](https://github.com/bdlucas1/math-plotting-demo/blob/62297f94db02cc39f784cb5e4135db8662e45d17/compile-timings/compile-timings.py#L29): compiles expression using llvm via
  compile._compile. Expression is evaluated point-by-point.


Three of the strategies are based on a [quick hack I wrote](https://github.com/bdlucas1/math-plotting-demo/blob/62297f94db02cc39f784cb5e4135db8662e45d17/compile-timings/compile-timings.py#L83) to translate
Mathics expressions into Python, ignoring any subtleties of Mathics
semantics:

* python_math: translates Sin, Sqrt, etc. in math.sin, math.sqrt, etc.
  Expression is evaluated point-by-point.

* python_np: translates Sin, Sqrt, etc. in np.sin, np.sqrt, etc.
  Expression is evaluated point-by-point.

* python_np_vec: like python_np, but [evaluation is vectorized](https://github.com/bdlucas1/math-plotting-demo/blob/62297f94db02cc39f784cb5e4135db8662e45d17/compile-timings/compile-timings.py#L175),
  i.e. numpy arrays of values are passed in and therefore invoke numpy
  vectorized evaluations of sin, sqrt, +, ^, etc.

Timings for evaluating the expressions at 40,000 points.

                        expr1             expr2            expr3

    none               9600 ms           15600 ms          compile failed
    llvm                 13 ms           15600 ms          compile failed
    python_math          10 ms              14 ms          33 ms
    python_np            19 ms              34 ms          33 ms
    python_np_vec         0.18 ms            0.23 ms        0.70 ms


Interpretation:

* none: Execution with no compilation is not nearly fast enough to support
  reasonable interactivity using Manipulate to vary a and b.

* llvm: Execution with the current llvm-based compilation improves
  expr1 by almost three orders of magnitude, but not expr2.  This
  would be good enough with expr1 for interactivity, but not expr2. Is
  this something easily fixed in llvm compilation, or is it inherent
  in llvm compilation preserving Mathics semantics?

* python_math: Translating to Python and using the Python math library
  gives about the same performance as llvm-based compilation for
  expr1, and also improves expr2 by almost three orders of
  magnitude. This would be good enough for interactivity in both
  cases.

* python_np: Translating to Python and using the numpy library is a
  little slower than using the math library for the point-by-point
  evaluation case.

* python_np_vec: But translating to Python and using the numpy library
  for sin, sqrt, etc. allows vectorized execution which gains about
  another two orders of magnitude in performance. This may not be
  necessary for these test expressions, but might be needed for
  interactivity for some more complicated expressions.

Conclusions:

* The current llvm-based compilation probably won't be sufficiently
  performant (by a lot) for implementing Manipulate for a lot of cases.

* A compilation based on translating to Python seems promising to
  me. I haven't looked at the compile module to see what it looks
  like, but I wonder if a compilation strategy based on translating to
  Python might not be easier to implement and maintain. It would also
  remove the dependency on llvm and llvmlite.
