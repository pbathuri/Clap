# First role pack demo: ops_reporting_pack

Repeatable flow to install the ops reporting pack and see pack-driven behavior.

## 1. Install pack

From repo root:

```bash
workflow-dataset packs install packs/ops_reporting_pack/manifest.json
```

Expected: `Installed ops_reporting_pack@1.0.0`.

## 2. Verify pack active

```bash
workflow-dataset packs list
workflow-dataset packs show ops_reporting_pack
workflow-dataset runtime status
workflow-dataset packs resolve --role ops
```

You should see `ops_reporting_pack` in the list and in resolve output (templates: ops_summarize_reporting, ops_scaffold_status, ops_next_steps).

## 3. Activate (optional)

So that `release run` uses the pack without passing `--role` every time:

```bash
workflow-dataset packs activate ops_reporting_pack
workflow-dataset runtime status
```

Runtime status should show "Active role: ops".

## 4. Run narrow workflow (release run)

With pack installed and either activated or explicit role:

```bash
workflow-dataset release run --role ops
# or, if you activated: workflow-dataset release run
```

Expected: line "Active pack(s): ops_reporting_pack", then three trials (ops_summarize_reporting, ops_scaffold_status, ops_next_steps) run with pack-driven retrieval_top_k. Results under `data/local/trials`.

## 5. Generate / review output

Check trial outputs in `data/local/trials`. Run pilot to see readiness and active pack in the report:

```bash
workflow-dataset pilot verify
workflow-dataset pilot latest-report
```

Open `data/local/pilot/pilot_readiness_report.md` — it should list **Active pack(s): ops_reporting_pack** when the pack is installed and scope is ops.

## 6. Bundle and adoption (optional)

To create an ops handoff bundle (pack declares output_adapters: ops_handoff):

```bash
workflow-dataset assist bundle-create --adapter-type ops_handoff --bundle-id my_ops_bundle ...
```

Adoption candidate and preview/apply flow are unchanged; use existing assist/adoption commands.

## 7. Why the pack added value

- **Without pack:** Release run uses a fixed list from `release_narrow.yaml` and default retrieval_top_k. You can still run the same trials, but there is no single "role pack" unit to install or inspect.
- **With pack:** One installable unit (ops_reporting_pack) defines role=ops, templates, retrieval profile, and output adapters. Release run and pilot report which pack is active; you can activate/deactivate and resolve by role. The same three trials run, but they are now explicitly tied to the pack and its metadata (version, safety, provenance).

## 8. Deactivate / uninstall

```bash
workflow-dataset packs deactivate
workflow-dataset packs uninstall ops_reporting_pack
```

After uninstall, `release run` falls back to release config trial_ids and default behavior.
