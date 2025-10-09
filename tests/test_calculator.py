import pytest
from src import calculator

def test_add():
    assert calculator.add(2, 3) == 5

def test_subtract():
    assert calculator.subtract(5, 3) == 2

def test_multiply():
    assert calculator.multiply(4, 3) == 12

def test_divide():
    assert calculator.divide(10, 2) == 5

def test_divide_by_zero():
    with pytest.raises(ValueError):
        calculator.divide(10, 0)

def test_power():
    assert calculator.power(2, 3) == 8

def test_modulo():
    assert calculator.modulo(10, 3) == 1

def test_square_root():
    assert calculator.square_root(16) == 4

def test_square_root_negative():
    with pytest.raises(ValueError):
        calculator.square_root(-4)