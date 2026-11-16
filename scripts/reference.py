"""Build proof vectors by enumerating actual edited strings, without rolling shifts."""
import hashlib
import json
import re
import sys
from pathlib import Path


ACCESSION = "U00096.3"
FLANK = 64


def fasta(path):
    head, *body = Path(path).read_text(encoding="ascii").strip().splitlines()
    assert ACCESSION in head
    sequence = "".join(body)
    assert len(sequence) == 200 and re.fullmatch("[ACGT]+", sequence)
    return sequence


def sha(text):
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def case(reference, boundary, kind, bases):
    k = len(bases)
    start = max(0, boundary - FLANK)
    stop = boundary + FLANK + (k if kind == "delete" else 0)
    assert stop <= len(reference)
    window = reference[start:stop]
    if kind == "insert":
        target = reference[:boundary] + bases + reference[boundary:]
        candidates = {
            i: target[i:i + k] for i in range(len(reference) + 1)
            if reference[:i] + target[i:i + k] + reference[i:] == target
        }
    else:
        assert reference[boundary:boundary + k] == bases
        target = reference[:boundary] + reference[boundary + k:]
        candidates = {
            i: reference[i:i + k] for i in range(len(reference) - k + 1)
            if reference[:i] + reference[i + k:] == target
        }
    left, right = min(candidates), max(candidates)
    witness_start = max(0, left - 1)
    witness_stop = right + (k if kind == "delete" else 0) + 1
    assert witness_start >= start and witness_stop <= stop
    event = {"schema": "indel-equivalence/1", "accession": ACCESSION, "kind": kind,
             "left_boundary": left, "right_boundary": right, "left_bases": candidates[left],
             "right_bases": candidates[right], "reference_start": witness_start,
             "reference_bases": reference[witness_start:witness_stop]}
    event_id = sha(json.dumps(event, sort_keys=True, separators=(",", ":")))
    return {"submitted": {"accession": ACCESSION, "boundary": boundary, "kind": kind, "bases": bases},
            "window": {"start": start, "stop": stop, "sha256": sha(window)},
            "status": "COMPLETE", "event_id": event_id, "event": event}


reference = fasta(sys.argv[1])
assert fasta(sys.argv[2]) == reference
repeat = re.search("(AT){2,}", reference)
assert repeat is not None
a = case(reference, repeat.start(), "insert", "AT")
b = case(reference, repeat.start() + 1, "insert", "TA")
assert a["event_id"] == b["event_id"] and a["window"] != b["window"]
run = re.search("A{4,}", reference)
assert run is not None
c = case(reference, run.start() + 1, "delete", "A")
assert c["event"]["right_boundary"] > c["event"]["left_boundary"]
Path("REFERENCE.json").write_text(
    json.dumps({"accession": ACCESSION, "sequence_sha256": sha(reference),
                "cases": {"insert-first": a, "insert-shifted": b, "delete-repeat": c}}, indent=2) + "\n",
    encoding="utf-8",
)
