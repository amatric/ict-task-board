"""零依赖计算工具，支持四则运算。"""


def add(a, b):
    """加法。"""
    return a + b


def sub(a, b):
    """减法。"""
    return a - b


def mul(a, b):
    """乘法。"""
    return a * b


def div(a, b):
    """除法，除数为 0 时抛 ValueError。"""
    if b == 0:
        raise ValueError("除数不能为 0")
    return a / b
