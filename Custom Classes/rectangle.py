class Rectangle:
    def __init__(self, length: int, width: int):
        """
        Initializes a Rectangle instance.
        Args: length, width
        """
        if not isinstance(length, int) or not isinstance(width, int):
            raise TypeError("Length and width must be integers.")
        if length <= 0 or width <= 0:
             raise ValueError("Length and width must be positive integers.")
             
        self.length = length
        self.width = width

    def __iter__(self):
        # Yield length first, then width, in the required format
        yield {'length': self.length}
        yield {'width': self.width}

    def __repr__(self):
        return f"Rectangle(length={self.length}, width={self.width})"

rect = Rectangle(5, 3)
for item in rect:
    print(item)