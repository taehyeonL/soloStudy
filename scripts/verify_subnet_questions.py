"""Verify recorded IPv4 subnet calculations using Python's ipaddress module."""
import json
import ipaddress
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
paths = sorted((ROOT / "questions" / "_instructor").glob("*.json"))
checked = 0
for path in paths:
    item = json.loads(path.read_text(encoding="utf-8"))
    calc = item.get("verification", {}).get("subnet_calculation")
    if not calc:
        continue
    interface = ipaddress.ip_interface(calc["address_cidr"])
    network = interface.network
    assert str(network.netmask) == calc["mask"], f"mask mismatch: {path.name}"
    if calc["operation"] == "network_address":
        assert str(network.network_address) == calc["expected_network"], f"network mismatch: {path.name}"
        assert calc["expected_network"] in item["choices"], f"network answer missing: {path.name}"
        assert item["choices"].count(calc["expected_network"]) == 1, f"duplicate network choice: {path.name}"
        assert item["choices"][item["answer"] - 1] == calc["expected_network"], f"answer mismatch: {path.name}"
    elif calc["operation"] == "last_octet_and":
        expected = int(interface.ip.packed[-1]) & int(network.netmask.packed[-1])
        assert expected == calc["expected_result"], f"last-octet result mismatch: {path.name}"
        assert item["choices"][item["answer"] - 1] == f"{interface.ip.packed[-1]} AND {network.netmask.packed[-1]} = {expected}", f"answer mismatch: {path.name}"
    else:
        raise AssertionError(f"unsupported calculation operation: {path.name}")
    checked += 1
assert checked > 0, "no subnet calculation cases found"
print(f"PASS: {checked} subnet calculation(s) checked with ipaddress.")
