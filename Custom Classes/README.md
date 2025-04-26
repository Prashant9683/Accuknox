Explanation of the [rectangle.py](rectangle.py) code:

The `__init__` function accepts length and width as integer parameters and saves them as instance variables. Simple type checking is present.

The `__iter__` method is defined as a generator function. It returns using the yield keyword first a dictionary of the length and then a dictionary of the width, in the correct format. This makes objects of the Rectangle class iterable.

The `__repr__` function is provided for better object representation (optional but recommended).
