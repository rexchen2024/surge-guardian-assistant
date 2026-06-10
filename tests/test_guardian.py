import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from guardian.config import write_env
from guardian.guardian import SurgeGuardian
from guardian.state import StateStore


class GuardianParsingTest(unittest.TestCase):
    def test_parse_direct_failure_host(self):
        line = "<NETWORK-ERROR> Connection setup failed foo to example.com:443 via DIRECT"
        self.assertEqual(SurgeGuardian.parse_direct_failure_host(line), "example.com")

    def test_parse_direct_failure_ignores_private_ip(self):
        line = "<NETWORK-ERROR> Connection setup failed foo to 192.168.1.1:443 via DIRECT"
        self.assertEqual(SurgeGuardian.parse_direct_failure_host(line), "")

    def test_resource_update_success_is_ignored(self):
        line = "<NOTIFY> [SGExternalResource] Resource update completed: https://example.test/list, error: N/A"
        guardian = SurgeGuardian.__new__(SurgeGuardian)
        self.assertIsNone(guardian.classify_log(line))

    def test_resource_update_error_is_classified(self):
        line = "<ERROR> [SGExternalResource] Resource update completed: https://example.test/list, error: timeout"
        guardian = SurgeGuardian.__new__(SurgeGuardian)
        incident = guardian.classify_log(line)
        self.assertIsNotNone(incident)
        self.assertEqual(incident.kind, "external_resource")

    def test_cautious_direct_hosts_skip_temp_proxy(self):
        self.assertTrue(SurgeGuardian.should_skip_temp_proxy("dns.alidns.com"))
        self.assertTrue(SurgeGuardian.should_skip_temp_proxy("api.io.mi.com"))
        self.assertTrue(SurgeGuardian.should_skip_temp_proxy("gateway.icloud.com"))
        self.assertFalse(SurgeGuardian.should_skip_temp_proxy("example.com"))

    def test_rule_presence_checks_dump_text(self):
        rules = {"rules": [{"rule": "DOMAIN,example.com,Proxy"}]}
        self.assertTrue(SurgeGuardian.rule_present("DOMAIN,example.com,Proxy", rules))
        self.assertFalse(SurgeGuardian.rule_present("DOMAIN,missing.example,Proxy", rules))

    def test_legacy_temp_proxy_rules_migrate(self):
        guardian = SurgeGuardian.__new__(SurgeGuardian)
        guardian.client = type("Client", (), {
            "dump_rules": lambda _self: ({"rules": ["DOMAIN,example.com,Proxy"]}, {"ok": True})
        })()
        state = {"temp_proxy_rules": {"example.com": {"rule": "DOMAIN,example.com,Proxy"}}}
        guardian.reconcile_temp_rules(state)
        self.assertIn("example.com", state["temp_rules"])
        self.assertNotIn("temp_proxy_rules", state)

    def test_local_env_written_private(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            write_env(path, {"SURGE_CLI": "/tmp/surge-cli"})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_state_written_private(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            StateStore(path).save({"ok": True})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
