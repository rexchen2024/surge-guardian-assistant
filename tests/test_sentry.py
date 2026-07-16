import unittest
import sqlite3
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import surge_sentry
from surge_sentry.config import SentryConfig, parse_maintenance_windows, write_env
from surge_sentry.cli import build_feedback_report, build_hermes_cron_command
from surge_sentry.cdn_watch import (
    AutoFixSpec,
    CdnWatchDaemon,
    HealthOutcome,
    ProfileEditor,
    ServiceSpec,
    ServiceTracker,
    WatchSettings,
    ack_pending,
    classify_cdn,
    consume_pending,
    extract_host,
    is_direct_policy,
    load_watch_settings,
    resolve_pending,
)
from surge_sentry.sentry import Incident, SurgeSentry
from surge_sentry.redact import redact_text, scan
from surge_sentry.state import StateStore
from surge_sentry.surge import SurgeClient
from surge_sentry.traffic import TrafficRecord, analyze_traffic, budget_day, diff_records, read_policy_records, records_to_snapshot


class SentryParsingTest(unittest.TestCase):
    def test_adaptive_active_request_poll_marks_target_playback(self):
        client = SurgeClient("/tmp/not-used")
        client.raw_json = lambda *_args, **_kwargs: ({"requests": [{
            "id": "media-1", "remoteHost": "vod-ap-aoc.tv.apple.com",
        }]}, {"ok": True})
        stream = client.watch_request_updates(
            poll_interval=2,
            idle_interval=10,
            is_target=lambda item: str(item.get("remoteHost", "")).startswith("vod-"),
        )
        self.assertEqual(next(stream)["id"], "media-1")
        tick = next(stream)
        self.assertTrue(tick["_poll_ok"])
        self.assertTrue(tick["_target_active"])
        stream.close()

    def test_cdn_watch_extracts_hostname_without_port(self):
        self.assertEqual(extract_host("vod-ap-aoc.tv.apple.com:443"), "vod-ap-aoc.tv.apple.com")
        self.assertEqual(extract_host("https://hls-amt.itunes.apple.com/path"), "hls-amt.itunes.apple.com")

    def test_cdn_watch_classifies_known_apple_tv_cdns(self):
        self.assertEqual(classify_cdn("146.75.115.6"), "fastly")
        self.assertEqual(classify_cdn("17.253.61.161"), "apple")
        self.assertEqual(classify_cdn(dns_path="x -> a1996.dscw154.akamai.net -> 203.0.113.3"), "akamai")
        self.assertEqual(classify_cdn("192.0.2.1 (Proxy)"), "proxy")
        self.assertEqual(
            classify_cdn(dns_path="vod-ap-aoc.tv.apple.com -> unclassified.example.net"),
            "unknown",
        )

    def test_direct_policy_accepts_localized_direct_name(self):
        self.assertTrue(is_direct_policy("DIRECT"))
        self.assertTrue(is_direct_policy("直连"))
        self.assertFalse(is_direct_policy("US-Proxy"))

    def test_cdn_watch_ignores_non_media_apple_requests(self):
        tracker = ServiceTracker(ServiceSpec(
            "apple-tv", "Apple TV", ("vod-*-aoc.tv.apple.com", "hls-amt.itunes.apple.com"),
        ))
        matched = tracker.ingest({
            "id": 1,
            "remoteHost": "bag.itunes.apple.com:443",
            "inBytes": 1000000,
            "inCurrentSpeed": 1000000,
        }, 100.0)
        self.assertFalse(matched)
        self.assertEqual(tracker.evaluate(100.0).status, "idle")

    def test_cdn_watch_marks_sustained_slow_transfer_critical(self):
        tracker = ServiceTracker(ServiceSpec(
            "apple-tv", "Apple TV", ("vod-*-aoc.tv.apple.com",),
            critical_seconds=20,
            degraded_seconds=30,
            min_transfer_mb=0.25,
        ))
        total = 0
        for offset in range(0, 26, 5):
            total += 125000
            tracker.ingest({
                "id": 7,
                "remoteHost": "vod-ap-aoc.tv.apple.com:443",
                "remoteAddress": "146.75.115.6",
                "policyName": "直连",
                "inBytes": total,
                "inCurrentSpeed": 25000,
                "startDate": 100,
                "status": "Active",
            }, 100.0 + offset)
        outcome = tracker.evaluate(125.0)
        self.assertEqual(outcome.status, "critical")
        self.assertLess(outcome.sustained_mbps, 3)
        self.assertEqual(outcome.cdn, "fastly")

    def test_cdn_watch_treats_fast_burst_as_healthy(self):
        tracker = ServiceTracker(ServiceSpec(
            "apple-tv", "Apple TV", ("vod-*-aoc.tv.apple.com",),
        ))
        tracker.ingest({
            "id": 8,
            "remoteHost": "vod-ap-aoc.tv.apple.com:443",
            "remoteAddress": "17.253.61.161",
            "policyName": "直连",
            "inBytes": 0,
            "inCurrentSpeed": 4_000_000,
            "startDate": 100,
            "status": "Active",
        }, 100.0)
        outcome = tracker.evaluate(100.0)
        self.assertEqual(outcome.status, "healthy")
        self.assertGreaterEqual(outcome.sustained_mbps, 20)

    def test_cdn_watch_zero_speed_without_transfer_stays_idle(self):
        tracker = ServiceTracker(ServiceSpec(
            "apple-tv", "Apple TV", ("vod-*-aoc.tv.apple.com",),
        ))
        tracker.ingest({
            "id": 9,
            "remoteHost": "vod-ap-aoc.tv.apple.com:443",
            "remoteAddress": "17.253.61.161",
            "policyName": "直连",
            "inBytes": 10_000_000,
            "inCurrentSpeed": 0,
            "status": "Active",
        }, 100.0)
        self.assertEqual(tracker.evaluate(130.0).status, "idle")

    def test_cdn_watch_bad_numeric_fields_do_not_kill_tracker(self):
        tracker = ServiceTracker(ServiceSpec("apple-tv", "Apple TV", ("vod-*.tv.apple.com",)))
        self.assertTrue(tracker.ingest({
            "id": "bad-numbers",
            "remoteHost": "vod-ap-amt.tv.apple.com",
            "inBytes": "not-a-number",
            "inCurrentSpeed": None,
            "startDate": "invalid",
        }, 100.0))
        self.assertEqual(tracker.evaluate(100.0).status, "idle")

    def test_profile_editor_updates_only_allowlisted_host_lines(self):
        class FakeClient:
            def dump_profile_text(self, _mode):
                return profile.read_text(), {"ok": True}

            def check_profile(self, _path):
                return {"ok": True}

            def reload(self):
                return {"ok": True}

            def flush_dns(self):
                return {"ok": True}

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "Mac.conf"
            profile.write_text(
                "[General]\nloglevel = notify\n\n[Host]\n"
                "vod-ap-aoc.tv.apple.com = server:223.5.5.5\n"
                "unrelated.example = server:8.8.8.8\n\n[Rule]\nFINAL,DIRECT\n"
            )
            editor = ProfileEditor(FakeClient(), root / "state")
            result = editor.ensure(
                profile,
                {
                    "vod-ap-aoc.tv.apple.com": "1.1.1.1",
                    "hls-amt.itunes.apple.com": "1.1.1.1",
                },
                reload_profile=True,
            )
            self.assertTrue(result.ok)
            self.assertTrue(result.changed)
            text = profile.read_text()
            self.assertIn("vod-ap-aoc.tv.apple.com = server:1.1.1.1", text)
            self.assertIn("hls-amt.itunes.apple.com = server:1.1.1.1", text)
            self.assertIn("unrelated.example = server:8.8.8.8", text)

    def test_profile_editor_restores_original_when_dns_flush_fails(self):
        class FakeClient:
            def dump_profile_text(self, _mode):
                return profile.read_text(), {"ok": True}

            def check_profile(self, _path):
                return {"ok": True}

            def reload(self):
                return {"ok": True}

            def flush_dns(self):
                return {"ok": False}

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "Mac.conf"
            original = "[Host]\nvod-ap-aoc.tv.apple.com = server:223.5.5.5\n"
            profile.write_text(original)
            result = ProfileEditor(FakeClient(), root / "state").ensure(
                profile,
                {"vod-ap-aoc.tv.apple.com": "1.1.1.1"},
                reload_profile=True,
            )
            self.assertFalse(result.ok)
            self.assertFalse(result.changed)
            self.assertEqual(profile.read_text(), original)

    def test_profile_editor_restores_original_when_runtime_override_is_missing(self):
        class FakeClient:
            def dump_profile_text(self, _mode):
                return original, {"ok": True}

            def check_profile(self, _path):
                return {"ok": True}

            def reload(self):
                return {"ok": True}

            def flush_dns(self):
                return {"ok": True}

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "Mac.conf"
            original = "[Host]\nvod-ap-aoc.tv.apple.com = server:223.5.5.5\n"
            profile.write_text(original)
            result = ProfileEditor(FakeClient(), root / "state").ensure(
                profile,
                {"vod-ap-aoc.tv.apple.com": "1.1.1.1"},
                reload_profile=True,
            )
            self.assertFalse(result.ok)
            self.assertEqual(profile.read_text(), original)
            self.assertIn("runtime verification failed", result.message)

    def test_pending_cdn_watch_events_are_consumed_once(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            write_env(root / ".env", {
                "EXPECTED_POLICIES": "Proxy",
                "PROXY_POLICY": "Proxy",
                "STATE_DIR": str(state_dir),
            })
            pending = state_dir / "cdn-watch-pending" / "event-one.json"
            StateStore(pending).save({
                "event_id": "event-one",
                "service": "Apple TV",
                "status": "critical",
                "reason": "test incident",
            })
            config = SentryConfig.load(root)
            self.assertEqual(len(consume_pending(config)), 1)
            self.assertEqual(consume_pending(config), [])
            self.assertEqual(ack_pending(config, "event-one"), (True, "acknowledged"))
            self.assertTrue((state_dir / "cdn-watch-processed" / "event-one.json").exists())

    def test_resolve_pending_acks_only_after_confirmed_delivery(self):
        class FakeNotifier:
            def __init__(self, ok):
                self.ok = ok

            def send(self, _message):
                return self.ok

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            write_env(root / ".env", {
                "EXPECTED_POLICIES": "Proxy", "PROXY_POLICY": "Proxy", "STATE_DIR": str(state_dir),
            })
            config = SentryConfig.load(root)
            inflight = state_dir / "cdn-watch-inflight" / "event-resolve.json"
            StateStore(inflight).save({
                "event_id": "event-resolve", "service": "Apple TV", "reason": "needs analysis",
            })
            failed = resolve_pending(
                config, "event-resolve", "修复失败，需要人工确认。", notifier=FakeNotifier(False),
            )
            self.assertFalse(failed[0])
            self.assertTrue(inflight.exists())
            succeeded = resolve_pending(
                config, "event-resolve", "修复失败，需要人工确认。", notifier=FakeNotifier(True),
            )
            self.assertEqual(succeeded, (True, "acknowledged"))
            self.assertFalse(inflight.exists())
            self.assertTrue((state_dir / "cdn-watch-processed" / "event-resolve.json").exists())

    def test_cdn_watch_known_fastly_incident_runs_allowlisted_repair(self):
        class FakeClient:
            def dump_profile_text(self, _mode):
                return profile.read_text(), {"ok": True}

            def dump_dns(self):
                return ({"dnsCache": [{
                    "domain": "vod-ap-aoc.tv.apple.com",
                    "path": "vod-ap-aoc.tv.apple.com -> h3.apis.apple.map.fastly.net",
                    "server": "https://dns.alidns.com/dns-query",
                }]}, {"ok": True})

            def check_profile(self, _path):
                return {"ok": True}

            def reload(self):
                return {"ok": True}

            def flush_dns(self):
                return {"ok": True}

        class FakeNotifier:
            def __init__(self):
                self.messages = []

            def send(self, message):
                self.messages.append(message)
                return True

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            profile = root / "Mac.conf"
            profile.write_text("[Host]\n\n[Rule]\nFINAL,DIRECT\n")
            write_env(root / ".env", {
                "EXPECTED_POLICIES": "Proxy",
                "PROXY_POLICY": "Proxy",
                "STATE_DIR": str(state_dir),
                "MAC_PROFILE": str(profile),
            })
            config = SentryConfig.load(root)
            spec = ServiceSpec(
                "apple-tv",
                "Apple TV",
                ("vod-*-aoc.tv.apple.com",),
                autofix=AutoFixSpec(
                    enabled=True,
                    dns_overrides={"vod-ap-aoc.tv.apple.com": "1.1.1.1"},
                    trigger_cdns=("fastly",),
                    expected_cdn="apple",
                ),
            )
            notifier = FakeNotifier()
            daemon = CdnWatchDaemon(
                config,
                WatchSettings(2, "telegram", (spec,)),
                client=FakeClient(),
                notifier=notifier,
                clock=lambda: 200.0,
            )
            daemon.handle_outcome(HealthOutcome(
                "critical", "apple-tv", "Apple TV", 0.2, 0.2, 0.3, 0.8, 25,
                "vod-ap-aoc.tv.apple.com", "fastly", "直连", "Apple TV", 100,
            ))
            state = StateStore(state_dir / "cdn-watch-state.json").load()
            self.assertEqual(state["services"]["apple-tv"]["phase"], "awaiting_restart")
            self.assertEqual(len(notifier.messages), 2)
            self.assertIn("vod-ap-aoc.tv.apple.com = server:1.1.1.1", profile.read_text())
            self.assertNotIn("hls-amt.itunes.apple.com = server:1.1.1.1", profile.read_text())

    def test_cdn_watch_repair_requires_new_expected_cdn_connection(self):
        class FakeClient:
            def dump_dns(self):
                return ({"dnsCache": []}, {"ok": True})

        class FakeNotifier:
            def __init__(self):
                self.messages = []

            def send(self, message):
                self.messages.append(message)
                return True

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            write_env(root / ".env", {"EXPECTED_POLICIES": "Proxy", "PROXY_POLICY": "Proxy", "STATE_DIR": str(state_dir)})
            spec = ServiceSpec(
                "apple-tv", "Apple TV", ("vod-*.tv.apple.com",),
                autofix=AutoFixSpec(enabled=True, expected_cdn="apple"),
            )
            notifier = FakeNotifier()
            daemon = CdnWatchDaemon(
                SentryConfig.load(root), WatchSettings(5, "telegram", (spec,)),
                client=FakeClient(), notifier=notifier, clock=lambda: 250.0,
            )
            StateStore(state_dir / "cdn-watch-state.json").save({"services": {"apple-tv": {
                "phase": "awaiting_restart", "repair_at": 200, "expected_cdn": "apple",
            }}})
            old = HealthOutcome(
                "healthy", "apple-tv", "Apple TV", 30, 28, 35, 10, 25,
                "vod-ap-aoc.tv.apple.com", "apple", "直连", "Apple TV", 199,
            )
            daemon.handle_outcome(old)
            self.assertEqual(StateStore(state_dir / "cdn-watch-state.json").load()["services"]["apple-tv"]["phase"], "awaiting_restart")
            self.assertEqual(notifier.messages, [])
            daemon.handle_outcome(HealthOutcome(
                "healthy", "apple-tv", "Apple TV", 32, 30, 36, 12, 25,
                "vod-ap-aoc.tv.apple.com", "apple", "直连", "Apple TV", 201,
            ))
            state = StateStore(state_dir / "cdn-watch-state.json").load()
            self.assertEqual(state["services"]["apple-tv"]["phase"], "healthy")
            self.assertEqual(len(notifier.messages), 1)

    def test_cdn_watch_new_wrong_cdn_connection_fails_and_escalates(self):
        class FakeClient:
            def dump_dns(self):
                return ({"dnsCache": []}, {"ok": True})

        class FakeNotifier:
            def send(self, _message):
                return True

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            write_env(root / ".env", {"EXPECTED_POLICIES": "Proxy", "PROXY_POLICY": "Proxy", "STATE_DIR": str(state_dir)})
            spec = ServiceSpec(
                "apple-tv", "Apple TV", ("vod-*.tv.apple.com",),
                autofix=AutoFixSpec(enabled=True, expected_cdn="apple", rollback_on_failure=False),
            )
            daemon = CdnWatchDaemon(
                SentryConfig.load(root), WatchSettings(5, "telegram", (spec,)),
                client=FakeClient(), notifier=FakeNotifier(), clock=lambda: 250.0,
            )
            StateStore(state_dir / "cdn-watch-state.json").save({"services": {"apple-tv": {
                "phase": "awaiting_restart", "repair_at": 200, "expected_cdn": "apple",
            }}})
            daemon.handle_outcome(HealthOutcome(
                "healthy", "apple-tv", "Apple TV", 30, 28, 35, 10, 25,
                "vod-ap-aoc.tv.apple.com", "fastly", "直连", "Apple TV", 201,
            ))
            state = StateStore(state_dir / "cdn-watch-state.json").load()
            self.assertEqual(state["services"]["apple-tv"]["phase"], "failed")
            self.assertEqual(len(list((state_dir / "cdn-watch-pending").glob("*.json"))), 1)

    def test_cdn_watch_new_expected_cdn_but_slow_connection_fails(self):
        class FakeClient:
            def dump_dns(self):
                return ({"dnsCache": []}, {"ok": True})

        class FakeNotifier:
            def send(self, _message):
                return True

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            write_env(root / ".env", {"EXPECTED_POLICIES": "Proxy", "PROXY_POLICY": "Proxy", "STATE_DIR": str(state_dir)})
            spec = ServiceSpec(
                "apple-tv", "Apple TV", ("vod-*.tv.apple.com",),
                autofix=AutoFixSpec(enabled=True, expected_cdn="apple", rollback_on_failure=False),
            )
            daemon = CdnWatchDaemon(
                SentryConfig.load(root), WatchSettings(5, "telegram", (spec,)),
                client=FakeClient(), notifier=FakeNotifier(), clock=lambda: 250.0,
            )
            StateStore(state_dir / "cdn-watch-state.json").save({"services": {"apple-tv": {
                "phase": "awaiting_restart", "repair_at": 200, "expected_cdn": "apple",
            }}})
            daemon.handle_outcome(HealthOutcome(
                "critical", "apple-tv", "Apple TV", 0.4, 0.3, 0.8, 1, 25,
                "vod-ap-aoc.tv.apple.com", "apple", "直连", "Apple TV", 201,
            ))
            state = StateStore(state_dir / "cdn-watch-state.json").load()
            self.assertEqual(state["services"]["apple-tv"]["phase"], "failed")
            self.assertIn("remained critical", state["services"]["apple-tv"]["diagnostic"])

    def test_cdn_watch_config_is_private_and_rejects_unsafe_autofix(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "watch.json"
            path.write_text('{"services":[{"id":"apple-tv","host_patterns":["vod-*.tv.apple.com"],"autofix":{"dns_overrides":{"*.apple.com":"resolver.example"}}}]}')
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                load_watch_settings(path)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_cdn_watch_rejects_unverifiable_autofix_and_bad_thresholds(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "watch.json"
            path.write_text(
                '{"services":[{"id":"apple-tv","host_patterns":["vod-*.tv.apple.com"],'
                '"health_mbps":10,"usable_mbps":20,"critical_mbps":3,'
                '"autofix":{"enabled":true,"dns_overrides":{"vod-ap-aoc.tv.apple.com":"1.1.1.1"},'
                '"trigger_cdns":["fastly"],"expected_cdn":"apple","reload":false}}]}'
            )
            with self.assertRaises(ValueError):
                load_watch_settings(path)

    def test_cdn_watch_quarantines_corrupt_pending_event(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            write_env(root / ".env", {
                "EXPECTED_POLICIES": "Proxy",
                "PROXY_POLICY": "Proxy",
                "STATE_DIR": str(state_dir),
            })
            pending = state_dir / "cdn-watch-pending" / "broken-event.json"
            pending.parent.mkdir(parents=True)
            pending.write_text("not-json")
            self.assertEqual(consume_pending(SentryConfig.load(root)), [])
            self.assertFalse(pending.exists())
            self.assertEqual(len(list((state_dir / "cdn-watch-quarantine").glob("*.json"))), 1)

    def test_cdn_watch_reminds_once_while_waiting_for_restart(self):
        class FakeNotifier:
            def __init__(self):
                self.messages = []

            def send(self, message):
                self.messages.append(message)
                return True

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            write_env(root / ".env", {
                "EXPECTED_POLICIES": "Proxy",
                "PROXY_POLICY": "Proxy",
                "STATE_DIR": str(state_dir),
            })
            spec = ServiceSpec("apple-tv", "Apple TV", ("vod-*.tv.apple.com",))
            notifier = FakeNotifier()
            daemon = CdnWatchDaemon(
                SentryConfig.load(root), WatchSettings(5, "telegram", (spec,)),
                client=object(), notifier=notifier, clock=lambda: 400.0,
            )
            StateStore(state_dir / "cdn-watch-state.json").save({"services": {"apple-tv": {
                "phase": "awaiting_restart", "repair_at": 100.25,
            }}})
            idle = HealthOutcome(
                "idle", "apple-tv", "Apple TV", 0, 0, 0, 0, 0,
                "", "unknown", "", "Apple TV", 0,
            )
            daemon.handle_outcome(idle)
            daemon.handle_outcome(idle)
            self.assertEqual(len(notifier.messages), 1)
            state = StateStore(state_dir / "cdn-watch-state.json").load()
            self.assertEqual(state["services"]["apple-tv"]["restart_reminded_at"], 400)

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

    def test_redact_scan_allows_documented_public_infrastructure_ips(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "public.txt").write_text("resolver=1.1.1.1 cdn=146.75.115.6")
            private_ip = "64.64." + "1.1"
            (root / "private.txt").write_text(f"server={private_ip}")
            findings = scan(root)
            self.assertFalse(any(item.path == Path("public.txt") for item in findings))
            self.assertTrue(any(item.path == Path("private.txt") for item in findings))

    def test_feedback_report_is_sanitized(self):
        with TemporaryDirectory() as tmp:
            config = SentryConfig.load(Path(tmp))
            report = build_feedback_report(config)
            self.assertIn("version:", report)
            self.assertNotIn(str(Path.home()), report)


if __name__ == "__main__":
    unittest.main()
