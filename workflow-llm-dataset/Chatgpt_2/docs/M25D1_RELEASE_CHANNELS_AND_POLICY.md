# M25D.1 — Release Channels + Registry Policies

First-draft release-channel and registry-policy behavior: stable / preview / internal channels, install policy by channel (allow / warn / block), optional per-role overrides. Local-first, operator-readable.

---

## 1. Files modified

| File | Change |
|------|--------|
| `packs/install_flows.py` | Import `check_channel_policy`, `get_active_role`. `install_pack_from_registry` and `update_pack` return `(ok, msg, warning_or_none)`; before install/update, resolve channel policy — block returns failure, warn proceeds and returns warning message. |
| `cli.py` | `packs install` (from registry) and `packs update`: unpack `(ok, msg, warning)`; print warning in yellow when present. New command: `packs registry policy`. |
| `packs/registry_report.py` | Add `format_blocked_install(message, pack_id)`, `format_warned_install(message)`. |
| `mission_control/state.py` | pack_registry block: add `channel_policy` with `block`, `warn` channel lists and `active_role`; load policy via `load_registry_policy`. |
| `mission_control/report.py` | [Pack registry]: print `channel_policy` (block=…, warn=…, role=…) when present. |
| `tests/test_pack_registry_m25.py` | Fix `install_pack_from_registry` unpack to 3 values. Add tests: load_registry_policy default/from file, check_channel_policy allow/warn/block and role override, install blocked by channel, install warn channel. |

## 2. Files created

| File | Purpose |
|------|--------|
| `packs/registry_policy.py` | `load_registry_policy(packs_dir)`, `check_channel_policy(release_channel, active_role, packs_dir)` → (action, reason). Policy file: `registry/policy.json`; default channels: stable=allow, preview=warn, internal=block, dev=warn, local=allow; optional `role_overrides`. |
| `data/local/packs/registry/policy.json.example` | Sample policy with channels and role_overrides (ops: preview=allow, internal=warn; founder: internal=allow). |
| `docs/M25D1_RELEASE_CHANNELS_AND_POLICY.md` | This doc. |

---

## 3. Sample release-channel policy

**data/local/packs/registry/policy.json** (copy from `policy.json.example` or use):

```json
{
  "channels": {
    "stable": "allow",
    "preview": "warn",
    "internal": "block",
    "dev": "warn",
    "local": "allow"
  },
  "default_channel_policy": "warn",
  "role_overrides": {
    "ops": {
      "preview": "allow",
      "internal": "warn"
    },
    "founder": {
      "internal": "allow"
    }
  }
}
```

- **allow**: install/update proceeds with no warning.
- **warn**: install/update proceeds; CLI prints a yellow warning; mission control can show channel in warn list.
- **block**: install/update fails with a “Blocked: …” message.

Per-role overrides apply when `active_role` is set (e.g. via `packs activate <pack_id>`); they override the machine-level channel policy for that role.

---

## 4. Sample blocked / warned install output

**Blocked install** (e.g. pack on `internal` channel, policy blocks `internal`):

```
Blocked: install from channel 'internal' not allowed. (channel 'internal' policy: block)
```

**Warned install** (e.g. pack on `preview`, policy warns):

```
Channel 'preview' is not recommended for this environment. (channel 'preview' policy: warn)
Installed founder_ops_pack@0.2.0
```

**Blocked update** (same as blocked install, for update path):

```
Blocked: update from channel 'internal' not allowed. (channel 'internal' policy: block)
```

---

## 5. Exact tests run

```bash
pytest tests/test_pack_registry_m25.py -v --tb=short
```

Covers: registry/install/verify/history/rollback/format (existing), plus M25D.1: `test_load_registry_policy_default`, `test_load_registry_policy_from_file`, `test_check_channel_policy_allow_block_warn`, `test_check_channel_policy_role_override`, `test_install_from_registry_blocked_by_channel`, `test_install_from_registry_warn_channel`.

---

## 6. Next recommended step for the pane

- **Policy file location flag**: Add optional `--policy-path` or `--registry-dir` to CLI so operators can point to a different `registry/` (e.g. per-environment policy) without changing `--packs-dir`.
- **Blocked-update visibility**: In mission control or `packs registry list`, optionally mark packs whose *available* update is on a blocked channel (e.g. “update available but blocked by channel policy”) so operators see why `packs update` would fail.
- **Policy validation**: Add a small validator for `registry/policy.json` (allowed keys, allowed action values) and optionally run it from `packs registry policy` or a dedicated `packs registry validate-policy`.
