import unittest
from keccak256 import keccak256_hex
class KeccakTests(unittest.TestCase):
    def test_known_vectors(self):
        self.assertEqual(keccak256_hex(b''),'0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470')
        self.assertEqual(keccak256_hex(b'abc'),'0x4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45')
