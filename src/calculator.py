def add(a, b):
    """Return the sum of two numbers."""
    return a + b


def subtract(a, b):
    """Return the difference between two numbers."""
    return a - b


def multiply(a, b):
    """Return the product of two numbers."""
    return a * b


def divide(a, b):
    """Return the division of two numbers, handling divide-by-zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def power(a, b):
    """Return a raised to the power of b."""
    return a ** b


def modulus(a, b):
    """Return the remainder of a divided by b."""
    if b == 0:
        raise ValueError("Cannot perform modulus with zero")
    return a % b


def absolute(a):
    """Return the absolute value of a number."""
    return abs(a)