import unittest


class SmokeTest(unittest.TestCase):
    def test_smoke(self) -> None:
        """Simple smoke test to ensure test discovery works."""
        self.assertEqual(1 + 1, 2)


if __name__ == "__main__":
    unittest.main()
