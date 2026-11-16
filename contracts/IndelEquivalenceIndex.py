# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import hashlib
import json
import re

from genlayer import TreeMap, gl

FLANK = 64
ENA = "https://www.ebi.ac.uk/ena/browser/api/fasta/"
NCBI = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(text):
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def source_urls(accession, start, stop):
    first = start + 1
    return (
        f"{ENA}{accession}?range={first}-{stop}",
        f"{NCBI}?db=nuccore&id={accession}&seq_start={first}&seq_stop={stop}&rettype=fasta&retmode=text",
    )


def parse_fasta(body, accession, start, stop, ena):
    if not isinstance(body, bytes) or not 0 < len(body) <= 4096:
        raise ValueError("Unexpected FASTA body size")
    lines = body.decode("ascii").strip().splitlines()
    if len(lines) < 2:
        raise ValueError("Missing FASTA sequence")
    first = start + 1
    header = lines[0]
    if ena:
        name = f">ENA|{accession.split('.')[0]}|{accession} "
        if not header.startswith(name) or not header.endswith(f" : Location:{first}..{stop}"):
            raise ValueError("ENA returned another accession or interval")
    elif not header.startswith(f">{accession}:{first}-{stop} "):
        raise ValueError("NCBI returned another accession or interval")
    sequence = "".join(lines[1:]).upper()
    if len(sequence) != stop - start or not re.fullmatch(r"[ACGT]+", sequence):
        raise ValueError("Incomplete or ambiguous FASTA sequence")
    return sequence


def fetch_reference(fetch, accession, start, stop):
    sequences = []
    for index, url in enumerate(source_urls(accession, start, stop)):
        response = fetch(url)
        if response.status != 200:
            raise ValueError("Reference archive returned an unsuccessful response")
        sequences.append(parse_fasta(response.body, accession, start, stop, index == 0))
    if sequences[0] != sequences[1]:
        raise ValueError("Reference archives disagree")
    return sequences[0]


def equivalent_positions(sequence, index, kind, bases):
    left = right = index
    left_bases = right_bases = bases
    delete_size = 0
    if kind == "delete":
        delete_size = len(bases)
        if sequence[index:index + delete_size] != bases:
            return None
        while left > 0 and sequence[left - 1] == sequence[left + delete_size - 1]:
            left -= 1
        while right + delete_size < len(sequence) and sequence[right] == sequence[right + delete_size]:
            right += 1
        left_bases = sequence[left:left + delete_size]
        right_bases = sequence[right:right + delete_size]
    else:
        while left > 0 and sequence[left - 1] == left_bases[-1]:
            left_bases = left_bases[-1] + left_bases[:-1]
            left -= 1
        while right < len(sequence) and sequence[right] == right_bases[0]:
            right_bases = right_bases[1:] + right_bases[0]
            right += 1
    return left, right, left_bases, right_bases, delete_size


def evaluate_window(accession, start, sequence, boundary, kind, bases):
    index = boundary - start
    window = {"start": start, "stop": start + len(sequence), "sha256": digest(sequence)}
    submitted = {"accession": accession, "boundary": boundary, "kind": kind, "bases": bases}
    report = {"submitted": submitted, "window": window}
    placement = equivalent_positions(sequence, index, kind, bases)
    if placement is None:
        return {**report, "status": "REFERENCE_MISMATCH",
                "actual_bases": sequence[index:index + len(bases)]}
    left, right, left_bases, right_bases, delete_size = placement
    span = {"left_boundary": start + left, "right_boundary": start + right,
            "left_bases": left_bases, "right_bases": right_bases}
    if (left == 0 and start != 0) or right + delete_size == len(sequence):
        return {**report, "status": "WINDOW_EXHAUSTED", "observed_span": span}
    witness_start = max(0, left - 1)
    event = {
        "schema": "indel-equivalence/1",
        "accession": accession,
        "kind": kind,
        **span,
        "reference_start": start + witness_start,
        "reference_bases": sequence[witness_start:right + delete_size + 1],
    }
    return {**report, "status": "COMPLETE", "event_id": digest(canonical(event)), "event": event}


class IndelEquivalenceIndex(gl.Contract):
    events: TreeMap[str, str]

    def __init__(self):
        pass

    @gl.public.write
    def normalize(self, accession: str, boundary: int, kind: str, bases: str) -> dict:
        if not re.fullmatch(r"[A-Z]{1,6}[0-9]{4,12}\.[1-9][0-9]{0,4}", accession):
            raise gl.vm.UserError("Expected a versioned INSDC accession")
        if type(boundary) is not int or not 0 <= boundary <= 500_000_000:
            raise gl.vm.UserError("Invalid interbase coordinate")
        if kind not in ("insert", "delete") or not re.fullmatch(r"[ACGT]{1,32}", bases):
            raise gl.vm.UserError("Expected an insertion or deletion of 1-32 ACGT bases")
        start = max(0, boundary - FLANK)
        stop = boundary + FLANK + (len(bases) if kind == "delete" else 0)

        def evaluate():
            try:
                sequence = fetch_reference(gl.nondet.web.get, accession, start, stop)
                return canonical(evaluate_window(accession, start, sequence, boundary, kind, bases))
            except Exception:
                raise gl.vm.UserError("Reference archives unavailable, ambiguous or inconsistent")

        def validate(leader):
            if not isinstance(leader, gl.vm.Return):
                return False
            try:
                return evaluate() == leader.calldata
            except Exception:
                return False

        report = json.loads(gl.vm.run_nondet_unsafe(evaluate, validate))
        if report["status"] == "COMPLETE":
            key = report["event_id"]
            if key not in self.events:
                self.events[key] = canonical(report["event"])
        return report

    @gl.public.view
    def get_event(self, event_id: str) -> dict:
        if event_id not in self.events:
            raise gl.vm.UserError("Unknown event")
        return json.loads(self.events[event_id])
