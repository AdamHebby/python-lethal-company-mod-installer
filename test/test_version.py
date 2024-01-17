import unittest
from src.Version import Version

class TestVersion(unittest.TestCase):
    def test_versions(self):
        self.assertTrue(Version("1.12.1.1").gt(Version("1.12.1")))
        self.assertTrue(Version("1.0.0").gt(Version("0.0.0")))
        self.assertTrue(Version("1.0.0").gt(Version("0.99.99.99")))
        self.assertTrue(Version("1.1.1").gt(Version("1.1.0")))
        self.assertTrue(Version("1.1.1").gt(Version("1.0.1")))
        self.assertTrue(Version("2.1.1").gt(Version("1.1.1")))

        self.assertTrue(Version("1.12.1.1") > (Version("1.12.1")))
        self.assertTrue(Version("1.0.0") > (Version("0.0.0")))
        self.assertTrue(Version("1.0.0") > (Version("0.99.99.99")))
        self.assertTrue(Version("1.1.1") > (Version("1.1.0")))
        self.assertTrue(Version("1.1.1") > (Version("1.0.1")))
        self.assertTrue(Version("2.1.1") > (Version("1.1.1")))

        self.assertTrue(Version("1.12.1").lt(Version("1.12.1.1")))
        self.assertTrue(Version("0.0.0").lt(Version("1.0.0")))
        self.assertTrue(Version("0.99.99.99").lt(Version("1.0.0")))
        self.assertTrue(Version("1.1.0").lt(Version("1.1.1")))
        self.assertTrue(Version("1.0.1").lt(Version("1.1.1")))
        self.assertTrue(Version("1.1.1").lt(Version("2.1.1")))

        self.assertTrue(Version("1.12.1") < (Version("1.12.1.1")))
        self.assertTrue(Version("0.0.0") < (Version("1.0.0")))
        self.assertTrue(Version("0.99.99.99") < (Version("1.0.0")))
        self.assertTrue(Version("1.1.0") < (Version("1.1.1")))
        self.assertTrue(Version("1.0.1") < (Version("1.1.1")))
        self.assertTrue(Version("1.1.1") < (Version("2.1.1")))

        self.assertTrue(Version("1.0.0.0") == Version("1.0.0"))
        self.assertTrue(Version("1.0.0") == Version("1.0.0"))
        self.assertTrue(Version("1.0.0") == Version("1.0"))
        self.assertTrue(Version("1.0.0") == Version("1"))

        # test lte
        self.assertTrue(Version("1.12.1.0") <= Version("1.12.1"))
        self.assertTrue(Version("1.12.1.1") <= Version("1.12.1.1"))
        self.assertTrue(Version("1.12.1.1") <= Version("1.12.1.2"))
        self.assertTrue(Version("1.12.1") <= Version("1.12.1"))
        self.assertTrue(Version("1.12.1") <= Version("1.12.2"))
        self.assertTrue(Version("1.12.1") <= Version("1.13.1"))
        self.assertTrue(Version("1.12.1") <= Version("2.12.1"))
        self.assertTrue(Version("1.12.1") <= Version("2.12.2"))

        # test gte
        self.assertTrue(Version("1.12.1") >= Version("1.12.1"))
        self.assertTrue(Version("1.12.1.1") >= Version("1.12.1"))
        self.assertTrue(Version("1.12.2") >= Version("1.12.1"))
        self.assertTrue(Version("1.13.1") >= Version("1.12.1"))
        self.assertTrue(Version("2.12.1") >= Version("1.12.1"))
        self.assertTrue(Version("2.12.2") >= Version("1.12.1"))

        # test ne
        self.assertTrue(Version("1.12.1") != Version("1.12.2"))
        self.assertTrue(Version("1.12.1") != Version("1.13.1"))
        self.assertTrue(Version("1.12.1") != Version("2.12.1"))
        self.assertTrue(Version("1.12.1") != Version("2.12.2"))

        # test max
        self.assertEqual(Version.max(Version("1.12.1"), Version("1.12.2")), Version("1.12.2"))
        self.assertEqual(Version.max(Version("1.12.1"), Version("1.13.1")), Version("1.13.1"))
        self.assertEqual(Version.max(Version("1.12.1"), Version("2.12.1")), Version("2.12.1"))
        self.assertEqual(Version.max(Version("1.12.1"), Version("2.12.2")), Version("2.12.2"))

