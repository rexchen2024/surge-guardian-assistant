import unittest
import sqlite3
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import surge_sentry
from surge_sentry.config import SentryConfig, parse_maintenance_windows, write_env
from surge_sentry.cli import build_feedback_report, build_hermes_cron_command
from surge_sentry.sentry import Incident, SurgeSentry
from surge_sentry.redact import redact_text, scan
from surge_sentry.state import StateStore
from surge_sentry.traffic import TrafficRecord, analyze_traffic, budget_day, diff_records, read_policy_records, records_to_snapshot


class SentryParsingTest(unittest.TestCase):
    def test_parse_direct_failure_host(self):
        line = "<NETWORK-ERROR> Connection setup failed foo to example.com:443 via DIRECT"
        self.assertEqual(SurgeSentry.parse_direct_failure_host(line), "example.com")

    def test_parse_direct_failure_ignores_private_ip(self):
        line = "<NETWORK-ERROR> Connection setup failed foo to 192.168.1.1:443 via DIRECT"
        self.assertEqual(SurgeSentry.parse_direct_failure_host(line), "")

    def test_resource_update_success_is_ignored(self):
        line = "<NOTIFY> [SGExternalResource] Resource update completed: https://example.test/list, error: N/A"
        sentry = SurgeSentry.__new__(SurgeSentry)
        self.assertIsNone(sentry.classify_log(line))

    def test_resource_update_error_is_classified(self):
        line = "<ERROR> [SGExternalResource] Resource update completed: https://example.test/list, error: timeout"
        sentry = SurgeSentry.__new__(SurgeSentry)
        incident = sentry.classify_log(line)
        self.assertIsNotNone(incident)
        self.assertEqual(incident.kind, "external_resource")

    def test_cautious_direct_hosts_skip_temp_proxy(self):
        self.assertTrue(SurgeSentry.should_skip_temp_proxy("dns.alidns.com"))
        self.assertTrue(SurgeSentry.should_skip_temp_proxy("api.io.mi.com"))
        self.assertTrue(SurgeSentry.should_skip_temp_proxy("api.apple-cloudkit.com"))
        self.assertTrue(SurgeSentry.should_skip_temp_proxy("gateway.icloud.com"))
        self.assertTrue(SurgeSentry.should_skip_temp_proxy("pti.store.microsoft.com"))
        self.assertFalse(SurgeSentry.should_skip_temp_proxy("example.com"))

    def test_configured_maintenance_window_matches_local_time(self):
        window = parse_maintenance_windows("thu 05:00-05:10:dns,direct_domain_failure,proxy")[0]
        inside = time.struct_time((2026, 6, 11, 5, 3, 0, 3, 162, 0))
        outside = time.struct_time((2026, 6, 11, 5, 10, 0, 3, 162, 0))
        self.assertTrue(SurgeSentry.in_maintenance_window(window, inside))
        self.assertFalse(SurgeSentry.in_maintenance_window(window, outside))

    def test_maintenance_windows_default_empty(self):
        with TemporaryDirectory() as tmp:
            config = SentryConfig.load(Path(tmp))
            self.assertEqual(config.maintenance_windows, [])

    def test_suppressed_entries_are_coalesced_by_key(self):
        state = {}
        entry = {
            "time": "2026-06-16 12:00:00",
            "reason": "direct failure on cautious infrastructure host; no temp proxy rule added",
            "host": "dns.alidns.com",
        }
        SurgeSentry.remember_suppressed(state, entry)
        SurgeSentry.remember_suppressed(state, entry)
        self.assertEqual(len(state["suppressed"]), 1)
        self.assertEqual(state["suppressed"][0]["count"], 2)

    def test_recurring_noise_pattern_becomes_actionable_candidate(self):
        sentry = SurgeSentry.__new__(SurgeSentry)
        sentry.config = SentryConfig.load(Path("/tmp"))
        state = {
            "recurring_noise_patterns": {
                "3:300:dns:_": {
                    "weekday": 3,
                    "bucket_minute": 300,
                    "kind": "dns",
                    "host": "",
                    "dates": [
                        {"date": "2026-05-28", "ts": int(time.time()) - 14 * 86400},
                        {"date": "2026-06-04", "ts": int(time.time()) - 7 * 86400},
                    ],
                    "first": int(time.time()) - 14 * 86400,
                    "last": int(time.time()) - 7 * 86400,
                    "last_reported": 0,
                }
            }
        }
        candidates = sentry.record_recurring_noise_candidates(
            state,
            [Incident("dns", "low", "DNS query timeout")],
            local_time=time.struct_time((2026, 6, 11, 5, 3, 0, 3, 162, 0)),
        )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].kind, "recurring_noise_pattern")
        self.assertIn("MAINTENANCE_WINDOWS", candidates[0].message)

    def test_background_noise_is_recorded_without_incident(self):
        sentry = SurgeSentry.__new__(SurgeSentry)
        state = {}
        sample_ip_1 = "198.18." + "0.1"
        sample_ip_2 = "198.18." + "0.2"
        sentry.record_background_noise(state, [
            f"<WARNING> [SGTCPConnectionManager] Unknown VIF virtual IP: {sample_ip_1}",
            f"<NETWORK-ERROR> [SGConnectionSetupContext] Connection setup failed with error: timeout, to {sample_ip_2}:443 via DIRECT",
            "<NETWORK-ERROR> [SGConnectionSetupContext] Connection setup failed with error: timeout, to example.com:443 via DIRECT",
        ])
        counts = state["background_noise"]["counts"]
        self.assertEqual(counts["unknown_vif_virtual_ip"], 1)
        self.assertEqual(counts["direct_ip_connection_failure"], 1)
        self.assertNotIn("direct_domain_connection_failure", counts)

    def test_rule_presence_checks_dump_text(self):
        rules = {"rules": [{"rule": "DOMAIN,example.com,Proxy"}]}
        self.assertTrue(SurgeSentry.rule_present("DOMAIN,example.com,Proxy", rules))
        self.assertFalse(SurgeSentry.rule_present("DOMAIN,missing.example,Proxy", rules))

    def test_legacy_temp_sentry_rules_migrate(self):
        sentry = SurgeSentry.__new__(SurgeSentry)
        sentry.client = type("Client", (), {
            "dump_rules": lambda _self: ({"rules": ["DOMAIN,example.com,Proxy"]}, {"ok": True})
        })()
        state = {"temp_sentry_rules": {"example.com": {"rule": "DOMAIN,example.com,Proxy"}}}
        sentry.reconcile_temp_rules(state)
        self.assertIn("example.com", state["temp_rules"])
        self.assertNotIn("temp_sentry_rules", state)

    def test_local_env_written_private(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            write_env(path, {"SURGE_CLI": "/tmp/surge-cli"})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_env_expand_preserves_icloud_container_tilde(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            container = "iCloud" + "~" + "com" + "~" + "nssurge" + "~" + "inc"
            profile_name = "Primary.conf"
            value = f"${{HOME}}/Library/Mobile Documents/{container}/Documents/{profile_name}"
            write_env(path, {"MAC_PROFILE": value, "EXPECTED_POLICIES": "Proxy"})
            config = SentryConfig.load(Path(tmp))
            self.assertIn(container, config.mac_profile)
            self.assertNotIn("iCloud/Users/", config.mac_profile)

    def test_state_written_private(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            StateStore(path).save({"ok": True})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_package_version_matches_pyproject(self):
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        version_line = next(line for line in pyproject.read_text().splitlines() if line.startswith("version = "))
        self.assertEqual(surge_sentry.__version__, version_line.split('"')[1])

    def test_hermes_cron_command_uses_display_name_without_missing_skill_flag(self):
        root = Path(__file__).resolve().parent.parent
        command = build_hermes_cron_command(root)
        self.assertIn("Surge Sentry", command)
        self.assertNotIn("--skill", command)
        self.assertNotIn("--skills", command)

    def test_auto_update_defaults_on(self):
        with TemporaryDirectory() as tmp:
            config = SentryConfig.load(Path(tmp))
            self.assertTrue(config.auto_update)
            self.assertEqual(config.auto_update_interval_seconds, 86400)

    def test_traffic_config_defaults_off(self):
        with TemporaryDirectory() as tmp:
            config = SentryConfig.load(Path(tmp))
            self.assertFalse(config.traffic_analysis_enabled)
            self.assertEqual(config.traffic_policy_patterns, [])

    def test_traffic_config_loads_thresholds(self):
        with TemporaryDirectory() as tmp:
            write_env(Path(tmp) / ".env", {
                "TRAFFIC_ANALYSIS_ENABLED": "1",
                "TRAFFIC_POLICY_PATTERNS": "%Monitored%,%Backup%",
                "TRAFFIC_MONTHLY_CAP_GB": "1024",
                "TRAFFIC_RESET_DAY": "19",
                "TRAFFIC_DIRECT_HOST_PATTERNS": "*media*,direct-ok.example",
            })
            config = SentryConfig.load(Path(tmp))
            self.assertTrue(config.traffic_analysis_enabled)
            self.assertEqual(config.traffic_policy_patterns, ["%Monitored%", "%Backup%"])
            self.assertEqual(config.traffic_reset_day, 19)
            self.assertEqual(config.traffic_direct_host_patterns, ["*media*", "direct-ok.example"])

    def test_budget_day_handles_reset_before_current_month(self):
        current = time.struct_time((2026, 6, 18, 12, 0, 0, 3, 169, 0))
        self.assertEqual(budget_day(19, current), (31, 31))

    def test_budget_day_handles_reset_day(self):
        current = time.struct_time((2026, 6, 19, 12, 0, 0, 4, 170, 0))
        self.assertEqual(budget_day(19, current), (1, 30))

    def test_analyze_traffic_flags_daily_budget_and_direct_leak(self):
        current = time.struct_time((2026, 6, 19, 12, 0, 0, 4, 170, 0))
        records = [
            TrafficRecord("direct-ok.example", "", "Monitored-Proxy", 80.0, 80.0, 0.0, 100),
            TrafficRecord("streaming.example", "", "Monitored-Proxy", 20.0, 20.0, 0.0, 20),
        ]
        risks = analyze_traffic(
            records,
            [],
            monthly_cap_gb=1024,
            reset_day=19,
            daily_warn_ratio=1.2,
            daily_critical_ratio=2.0,
            direct_host_patterns=["*media*", "direct-ok.example"],
            direct_leak_min_gb=1.0,
            local_time=current,
        )
        self.assertEqual([item.severity for item in risks], ["high", "high"])
        self.assertIn("直连优先", risks[1].message)

    def test_read_policy_records_filters_monitored_policy(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "traffic.sqlite"
            with sqlite3.connect(str(db)) as conn:
                conn.execute(
                    "create table ZSGTRAFFICSTATRECORD (ZDOWN integer, ZREQUESTCOUNT integer, ZTOTAL integer, ZUP integer, ZHOST text, ZPATH text, ZPOLICY text)"
                )
                conn.execute(
                    "insert into ZSGTRAFFICSTATRECORD values (?,?, ?,?,?,?,?)",
                    (1024, 1, 1024, 0, "direct-ok.example", "", "Monitored-Proxy"),
                )
                conn.execute(
                    "insert into ZSGTRAFFICSTATRECORD values (?,?, ?,?,?,?,?)",
                    (4096, 1, 4096, 0, "example.com", "", "DIRECT"),
                )
            records = read_policy_records(db, ["%Monitored%"])
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].host, "direct-ok.example")

    def test_traffic_snapshot_diff_reports_event_usage(self):
        baseline_records = [
            TrafficRecord("stream.example", "", "AppleTV", 10.0, 9.0, 1.0, 100),
            TrafficRecord("api.example", "", "DIRECT", 1.0, 1.0, 0.0, 50),
        ]
        current_records = [
            TrafficRecord("stream.example", "", "AppleTV", 16.5, 15.0, 1.5, 180),
            TrafficRecord("api.example", "", "DIRECT", 1.2, 1.2, 0.0, 60),
            TrafficRecord("fox.example", "", "US-Proxy", 2.0, 2.0, 0.0, 40),
        ]
        deltas = diff_records(current_records, records_to_snapshot(baseline_records))
        self.assertEqual([item.host for item in deltas], ["stream.example", "fox.example", "api.example"])
        self.assertAlmostEqual(deltas[0].total_gb, 6.5)
        self.assertEqual(deltas[0].requests, 80)

    def test_redact_text_removes_private_values(self):
        token = "g" + "hp_" + "abcdefghijklmnopqrstuvwxyz"
        user_path = "/" + "Users" + "/" + "example" + "/path"
        key = "to" + "ken"
        text = f"{key}={token} and {user_path}"
        redacted = redact_text(text)
        self.assertNotIn(token, redacted)
        self.assertNotIn(user_path, redacted)

    def test_redact_text_uses_optional_local_words(self):
        with patch.dict("os.environ", {"SURGE_SENTRY_REDACT_WORDS": "PrivateLabel"}):
            self.assertNotIn("PrivateLabel", redact_text("PrivateLabel should be hidden"))

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
            config = SentryConfig.load(Path(tmp))
            report = build_feedback_report(config)
            self.assertIn("version:", report)
            self.assertNotIn(str(Path.home()), report)


if __name__ == "__main__":
    unittest.main()
