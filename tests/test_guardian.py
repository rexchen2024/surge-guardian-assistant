import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import guardian
from guardian.config import GuardianConfig, write_env
from guardian.cli import build_feedback_report, build_hermes_cron_command
from guardian.guardian import SurgeGuardian
from guardian.redact import redact_text, scan
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

    def test_package_version_matches_pyproject(self):
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        version_line = next(line for line in pyproject.read_text().splitlines() if line.startswith("version = "))
        self.assertEqual(guardian.__version__, version_line.split('"')[1])

    def test_hermes_cron_command_uses_display_name_without_missing_skill_flag(self):
        root = Path(__file__).resolve().parent.parent
        command = build_hermes_cron_command(root)
        self.assertIn("Surge 守护助手", command)
        self.assertNotIn("--skill", command)
        self.assertNotIn("--skills", command)

    def test_auto_update_defaults_on(self):
        with TemporaryDirectory() as tmp:
            config = GuardianConfig.load(Path(tmp))
            self.assertTrue(config.auto_update)
            self.assertEqual(config.auto_update_interval_seconds, 86400)

    def test_redact_text_removes_private_values(self):
        token = "g" + "hp_" + "abcdefghijklmnopqrstuvwxyz"
        user_path = "/" + "Users" + "/" + "example" + "/path"
        key = "to" + "ken"
        text = f"{key}={token} and {user_path}"
        redacted = redact_text(text)
        self.assertNotIn(token, redacted)
        self.assertNotIn(user_path, redacted)

    def test_redact_scan_skips_binary_assets(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_email = "fake" + "@" + "example.test"
            asset = root / "assets" / "brand" / "icon.png"
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b"\x89PNG\r\n" + fake_email.encode() + b"\x00")

            note = root / "note.txt"
            note.write_text(f"contact {fake_email}")

            findings = scan(root)
            self.assertFalse(any(item.path == Path("assets/brand/icon.png") for item in findings))
            self.assertTrue(any(item.path == Path("note.txt") for item in findings))

    def test_feedback_report_is_sanitized(self):
        with TemporaryDirectory() as tmp:
            config = GuardianConfig.load(Path(tmp))
            report = build_feedback_report(config)
            self.assertIn("version:", report)
            self.assertNotIn(str(Path.home()), report)


if __name__ == "__main__":
    unittest.main()
