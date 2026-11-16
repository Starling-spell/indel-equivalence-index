import itertools
import json
import re
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "contracts/IndelEquivalenceIndex.py"


@pytest.fixture
def indexer(direct_deploy):
    contract = direct_deploy(str(CODE))
    return contract, sys.modules[type(contract._instance).__module__]


def test_shift_logic_against_brute_force(indexer):
    _, mod = indexer
    for length in range(1, 7):
        for letters in itertools.product("AT", repeat=length):
            sequence = "".join(letters)
            for point in range(length + 1):
                for bases in ("A", "T", "AT", "TA", "ATA"):
                    size = len(bases)
                    inserted = sequence[:point] + bases + sequence[point:]
                    matches = [
                        i for i in range(length + 1)
                        if sequence[:i] + inserted[i:i + size] + sequence[i:] == inserted
                    ]
                    left, right, a, b, _ = mod.equivalent_positions(sequence, point, "insert", bases)
                    assert (left, right) == (matches[0], matches[-1])
                    assert (a, b) == (inserted[left:left + size], inserted[right:right + size])
                    if sequence[point:point + size] != bases:
                        assert mod.equivalent_positions(sequence, point, "delete", bases) is None
                        continue
                    deleted = sequence[:point] + sequence[point + size:]
                    matches = [i for i in range(length - size + 1)
                               if sequence[:i] + sequence[i + size:] == deleted]
                    left, right, a, b, _ = mod.equivalent_positions(sequence, point, "delete", bases)
                    assert (left, right) == (matches[0], matches[-1])
                    assert (a, b) == (sequence[left:left + size], sequence[right:right + size])


@pytest.mark.parametrize("offset,bases,kind,status", [
    (7, "A", "insert", "WINDOW_EXHAUSTED"),
    (0, "A", "delete", "WINDOW_EXHAUSTED"),
    (0, "G", "delete", "REFERENCE_MISMATCH"),
    (0, "C", "insert", "COMPLETE"),
])
def test_fail_closed_at_window_or_reference_mismatch(indexer, offset, bases, kind, status):
    _, mod = indexer
    report = mod.evaluate_window("U00096.3", offset, "AAAA", offset + 2, kind, bases)
    assert report["status"] == status
    assert ("event_id" in report) is (status == "COMPLETE")


def fasta(accession, start, stop, sequence, ena):
    header = (f">ENA|{accession.split('.')[0]}|{accession} Sample : Location:{start + 1}..{stop}"
              if ena else f">{accession}:{start + 1}-{stop} Sample")
    return (header + "\n" + sequence[:17] + "\n" + sequence[17:] + "\n").encode()


@pytest.mark.parametrize("replacement", [b"Location:2..8", b"Location:1..7", b"Location:1..8\n>second"])
def test_fasta_rejects_wrong_interval_or_multiple_records(indexer, replacement):
    _, mod = indexer
    raw = fasta("U00096.3", 0, 8, "ACGTACGT", True).replace(b"Location:1..8", replacement)
    with pytest.raises(ValueError):
        mod.parse_fasta(raw, "U00096.3", 0, 8, True)


def test_direct_consensus_and_canonical_index_reuse(indexer, direct_vm):
    contract, mod = indexer
    accession = "U00096.3"
    reference = "GATATC" + "G" * 100

    def install(mismatch=False):
        direct_vm.clear_mocks()
        for p in (1, 2):
            stop = p + mod.FLANK
            for j, url in enumerate(mod.source_urls(accession, 0, stop)):
                sequence = reference[:stop]
                if mismatch and j == 1:
                    sequence = sequence[:-1] + "A"
                direct_vm.mock_web(re.escape(url) + "$", {"method": "GET", "response": {
                    "status": 200, "headers": {}, "body": fasta(accession, 0, stop, sequence, j == 0),
                }})

    install()
    first = contract.normalize(accession, 1, "insert", "AT")
    second = contract.normalize(accession, 2, "insert", "TA")
    assert first["event_id"] == second["event_id"]
    assert first["window"] != second["window"]
    assert contract.get_event(first["event_id"])["right_boundary"] == 5
    assert direct_vm.run_validator()
    forged = {**second, "event_id": "0" * 64}
    assert not direct_vm.run_validator(leader_result=json.dumps(forged, sort_keys=True, separators=(",", ":")))
    install(mismatch=True)
    assert not direct_vm.run_validator()
    with direct_vm.expect_revert("archives unavailable, ambiguous or inconsistent"):
        contract.normalize(accession, 1, "insert", "AT")
    assert contract.get_event(first["event_id"]) == first["event"]
