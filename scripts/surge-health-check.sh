#!/bin/bash
# Silent-on-success Surge health check.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.env"
  set +a
fi

SURGE_CLI="${SURGE_CLI:-/Applications/Surge.app/Contents/Applications/surge-cli}"
CHECK_DOMAIN="${CHECK_DOMAIN:-}"
CHECK_IP="${CHECK_IP:-}"
EXPECTED_POLICIES="${EXPECTED_POLICIES:-}"
MAC_PROFILE="${MAC_PROFILE:-}"
MOBILE_PROFILE="${MOBILE_PROFILE:-}"
MAC_FORBIDDEN_REGEX="${MAC_FORBIDDEN_REGEX:-}"
MOBILE_FORBIDDEN_REGEX="${MOBILE_FORBIDDEN_REGEX:-}"
STATE_DIR="${STATE_DIR:-${HOME}/.hermes/state/surge-hermes-healthcheck}"
CERT_FAIL_STATE="${STATE_DIR}/cert-fail-count"

mkdir -p "${STATE_DIR}"

errors=()
warnings=()

add_error() {
  errors+=("$*")
}

add_warning() {
  warnings+=("$*")
}

require_setting() {
  local name="$1"
  local value="$2"
  [[ -n "$value" ]] || add_error "missing required setting: ${name}"
}

json_has_expected_policies() {
  local raw="$1"
  /usr/bin/python3 - "$raw" "$EXPECTED_POLICIES" <<'PY' >/dev/null 2>&1
import json
import sys

data = json.loads(sys.argv[1])
expected = {item.strip() for item in sys.argv[2].split(",") if item.strip()}
actual = set(data.get("proxies", []))
sys.exit(0 if expected.issubset(actual) else 1)
PY
}

public_doh_has_ip() {
  local cf="$1"
  local google="$2"
  /usr/bin/python3 - "$CHECK_IP" "$cf" "$google" <<'PY' >/dev/null 2>&1
import json
import sys

ip = sys.argv[1]
answers = []
for raw in sys.argv[2:]:
    if not raw:
        continue
    try:
        answers.extend(
            answer.get("data")
            for answer in json.loads(raw).get("Answer", [])
            if answer.get("type") == 1
        )
    except Exception:
        pass
sys.exit(0 if ip in answers else 1)
PY
}

check_profile() {
  local label="$1"
  local path="$2"
  local forbidden_regex="$3"

  if [[ -z "$path" ]]; then
    return
  fi
  if [[ ! -f "$path" ]]; then
    add_error "${label} missing: ${path}"
    return
  fi
  "$SURGE_CLI" --check "$path" >/dev/null 2>&1 || add_error "${label} failed surge-cli --check"
  if [[ -n "$forbidden_regex" ]] && grep -qE "$forbidden_regex" "$path"; then
    add_error "${label} contains forbidden legacy or local-only content"
  fi
}

fetch_cert_text() {
  local attempt
  local text=""
  for attempt in 1 2 3; do
    text="$(openssl s_client -connect "${CHECK_IP}:443" -servername "$CHECK_DOMAIN" </dev/null 2>/dev/null | openssl x509 -noout -subject -dates -ext subjectAltName 2>/dev/null || true)"
    if [[ "$text" == *"DNS:${CHECK_DOMAIN}"* && "$text" == *"notAfter="* ]]; then
      printf '%s\n' "$text"
      return 0
    fi
    sleep 2
  done
  printf '%s\n' "$text"
}

check_policy_connectivity() {
  local policy
  local result
  IFS=',' read -r -a policies <<< "$EXPECTED_POLICIES"
  for policy in "${policies[@]}"; do
    policy="${policy#"${policy%%[![:space:]]*}"}"
    policy="${policy%"${policy##*[![:space:]]}"}"
    [[ -n "$policy" ]] || continue
    result="$("$SURGE_CLI" --raw test-policy "$policy" 2>/dev/null || true)"
    if [[ -z "$result" || "$result" == "{}" || "$result" == *'"error"'* ]]; then
      add_error "${policy} test-policy failed"
    fi
  done
}

check_certificate() {
  local cert_text
  local not_after
  local count
  local expire_epoch
  local now_epoch
  local days_left

  cert_text="$(fetch_cert_text)"
  not_after="$(printf '%s\n' "$cert_text" | awk -F= '/^notAfter=/{print $2}')"

  if [[ -z "$not_after" ]]; then
    count=0
    [[ -f "$CERT_FAIL_STATE" ]] && count="$(cat "$CERT_FAIL_STATE" 2>/dev/null || echo 0)"
    count=$((count + 1))
    printf '%s\n' "$count" > "$CERT_FAIL_STATE"
    if (( count >= 3 )); then
      add_error "unable to read ${CHECK_DOMAIN} certificate after ${count} consecutive checks"
    fi
    return
  fi

  printf '0\n' > "$CERT_FAIL_STATE"
  if [[ "$cert_text" != *"DNS:${CHECK_DOMAIN}"* ]]; then
    add_error "${CHECK_IP}:443 certificate SAN does not include ${CHECK_DOMAIN}"
    return
  fi

  expire_epoch="$(date -j -f "%b %d %T %Y %Z" "$not_after" +%s 2>/dev/null || true)"
  now_epoch="$(date +%s)"
  if [[ -n "$expire_epoch" ]]; then
    days_left=$(( (expire_epoch - now_epoch) / 86400 ))
    if (( days_left < 7 )); then
      add_error "${CHECK_DOMAIN} TLS certificate expires in ${days_left} days"
    elif (( days_left < 21 )); then
      add_warning "${CHECK_DOMAIN} TLS certificate expires in ${days_left} days"
    fi
  fi
}

require_setting "CHECK_DOMAIN" "$CHECK_DOMAIN"
require_setting "CHECK_IP" "$CHECK_IP"
require_setting "EXPECTED_POLICIES" "$EXPECTED_POLICIES"
[[ -x "$SURGE_CLI" ]] || add_error "surge-cli is not executable: ${SURGE_CLI}"

if (( ${#errors[@]} == 0 )); then
  check_profile "MAC_PROFILE" "$MAC_PROFILE" "$MAC_FORBIDDEN_REGEX"
  check_profile "MOBILE_PROFILE" "$MOBILE_PROFILE" "$MOBILE_FORBIDDEN_REGEX"

  policy_json="$("$SURGE_CLI" --raw dump policy 2>/dev/null || true)"
  if [[ -z "$policy_json" || "$policy_json" == "(null)" ]]; then
    add_error "Surge dump policy unavailable"
  elif ! json_has_expected_policies "$policy_json"; then
    add_error "Surge runtime policies do not include all EXPECTED_POLICIES"
  fi

  dns_cf="$(curl -fsS --max-time 10 "https://cloudflare-dns.com/dns-query?name=${CHECK_DOMAIN}&type=A" -H 'Accept: application/dns-json' 2>/dev/null || true)"
  dns_google="$(curl -fsS --max-time 10 "https://dns.google/resolve?name=${CHECK_DOMAIN}&type=A" 2>/dev/null || true)"
  public_doh_has_ip "$dns_cf" "$dns_google" || add_error "${CHECK_DOMAIN} does not resolve to ${CHECK_IP} via public DoH"

  nc -vz -G 5 "$CHECK_IP" 80 >/dev/null 2>&1 || add_warning "${CHECK_IP}:80 is not reachable; ACME renewal may fail"
  check_policy_connectivity
  check_certificate
fi

if (( ${#errors[@]} == 0 && ${#warnings[@]} == 0 )); then
  exit 0
fi

if (( ${#errors[@]} > 0 )); then
  printf '结论：严重，Surge/Hermes 巡检发现关键异常\n'
  printf '【严重】\n'
  printf -- '- %s\n' "${errors[@]}"
else
  printf '结论：警告，Surge/Hermes 巡检发现低优先级异常\n'
fi

if (( ${#warnings[@]} > 0 )); then
  printf '【警告】\n'
  printf -- '- %s\n' "${warnings[@]}"
fi

