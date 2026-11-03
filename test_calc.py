"""calc.py 的单元测试（无第三方依赖，直接 python3 test_calc.py 运行）。"""

import unittest

from calc import add, sub, mul, div, format_number


class TestCalc(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(-1, 1), 0)

    def test_sub(self):
        self.assertEqual(sub(5, 3), 2)

    def test_mul(self):
        self.assertEqual(mul(4, 5), 20)
        self.assertEqual(mul(0, 99), 0)

    def test_div(self):
        self.assertEqual(div(10, 4), 2.5)

    def test_div_by_zero(self):
        with self.assertRaises(ValueError):
            div(1, 0)

    def test_format_number(self):
        self.assertEqual(format_number(1234.5), "1,234.50")
        self.assertEqual(format_number(0), "0.00")


if __name__ == "__main__":
    unittest.main(verbosity=2)
