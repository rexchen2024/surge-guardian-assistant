import unittest

from guardian.guardian import SurgeGuardian


class GuardianParsingTest(unittest.TestCase):
    def test_parse_direct_failure_host(self):
        line = "<NETWORK-ERROR> Connection setup failed foo to example.com:443 via DIRECT"
        self.assertEqual(SurgeGuardian.parse_direct_failure_host(line), "example.com")

    def test_parse_direct_failure_ignores_private_ip(self):
        line = "<NETWORK-ERROR> Connection setup failed foo to 192.168.1.1:443 via DIRECT"
        self.assertEqual(SurgeGuardian.parse_direct_failure_host(line), "")


if __name__ == "__main__":
    unittest.main()

