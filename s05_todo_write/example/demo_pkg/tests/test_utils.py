import unittest
from demo_pkg.utils import add

class TestAdd(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(-1, 1), 0)

cif __name__ == '__main__':
    unittest.main()