"""Checks on the synthetic dataset itself (not one of T1–T11)."""

import json
from collections import Counter

from dppmadera.generator import write

ID_KEYS = ("product_id", "instance_id", "batch_id", "ifc_guid", "occurrence_id")


def test_twenty_components_with_expected_mix(dataset):
    kinds = Counter(c["kind"].split("_")[0] for c in dataset["components"])
    assert kinds == {"clt": 12, "glulam": 4, "connector": 4}


def test_instance_level_identifiers_are_unique(dataset):
    for key in ("instance_id", "ifc_guid", "occurrence_id"):
        values = [c["ids"][key] for c in dataset["components"]]
        assert len(set(values)) == 20, key
    assert all(len(c["ids"]["ifc_guid"]) == 22 for c in dataset["components"])


def test_every_component_has_all_identifier_types(dataset):
    for c in dataset["components"]:
        assert all(c["ids"][k] for k in ID_KEYS)
        assert c["ids"]["process_run_ids"]


def test_events_are_in_replay_order(dataset):
    times = [e["record_time"] for e in dataset["events"]]
    assert times == sorted(times)


def test_five_faults_are_present_in_the_data(dataset):
    gt, events = dataset["ground_truth"], dataset["events"]
    by_code = {c["code"]: c for c in dataset["components"]}
    assert len(gt["faults"]) == 5

    a, b = gt["faults"]["F1_ifc_guid_clash"]["components"]
    rec = next(e for e in events if e["type"] == "InstallationRecord" and e["component"] == a)
    assert rec["payload"]["ifc_guid"] == by_code[b]["ids"]["ifc_guid"]

    (p,) = gt["faults"]["F2_moisture_conflict"]["components"]
    vals = {e["payload"]["moisture_pct"] for e in events
            if e["component"] == p and e["payload"].get("schema") == "moisture_check/v1"}
    assert vals == set(gt["faults"]["F2_moisture_conflict"]["values"])

    (g,) = gt["faults"]["F4_custody_gap"]["components"]
    steps = {e["payload"].get("bizStep") for e in events if e["component"] == g}
    assert "receiving" in steps and "shipping" not in steps

    (late,) = gt["faults"]["F5_late_event"]["components"]
    ev = next(e for e in events if e["component"] == late
              and e["payload"].get("schema") == "installation_inspection/v1")
    assert ev["record_time"][:10] > ev["event_time"][:10]


def test_generator_is_reproducible(tmp_path, dataset):
    manifest = write(tmp_path, dataset["manifest"]["seed"])
    assert manifest["sha256"] == dataset["manifest"]["sha256"]


def _keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k.lower()
            yield from _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v)


def test_no_personal_data_fields(dataset):
    forbidden = {"person", "worker", "operator", "email", "rut", "phone", "user"}
    assert not forbidden & set(_keys(dataset))
    assert "@" not in json.dumps(dataset)
    roles = {e["source"] for e in dataset["events"]}
    assert all(r.islower() and " " not in r for r in roles)  # system roles, not names
