# IndelEquivalenceIndex

In a repeated DNA sequence, the same hypothetical insertion or deletion can
be described at different positions. IndelEquivalenceIndex gives equivalent
descriptions one on-chain event ID. It stores the leftmost representation,
the other end of the equivalence interval, and the actual flanking bases
that delimit it.

`normalize(accession, boundary, kind, bases)` accepts a versioned INSDC
accession, a zero-based boundary between bases, and a pure insertion or
deletion of 1–32 ACGT bases. For a deletion, the submitted sequence must match
the reference at the nominated position. Only a bounded 64-base flank on
each side is requested. The left flank stops at the start of the reference.
The right flank must be available in full.

The leader and validators independently request the same accession and exact
subrange from ENA and NCBI. Each checks both FASTA headers and exact sequence
length, normalizes line wrapping and case, and requires the base sequences to
match. Each derives the set of equivalent placements by shifting one position
at a time. For an insertion, the bases can rotate as its boundary moves.
Validators must exactly reproduce the full result, including the observed
window digest and the event witness. Only complete events are indexed.

| Return status | Meaning |
| --- | --- |
| `COMPLETE` | Both limits were established. `get_event(event_id)` can read the shared event. |
| `REFERENCE_MISMATCH` | The proposed deleted bases differ from the observed reference. |
| `WINDOW_EXHAUSTED` | A reference window ends before an equivalence limit is established. |

The contract trusts the archives for the accession's reference sequence.
It evaluates mathematical equivalence of hypothetical edits. The demonstration
uses an archived E. coli K-12 reference and does not interpret health effects.

[ENA FASTA API](https://www.ebi.ac.uk/ena/browser/api/swagger-ui/index.html) ·
[NCBI EFetch sequence parameters](https://www.ncbi.nlm.nih.gov/sites/books/NBK25499/)

```sh
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
genvm-lint check contracts/IndelEquivalenceIndex.py
```

`scripts/reference.py` generates the independent proof vectors by brute-force
enumeration of edited strings from the two archives' first 200 bases.
The proof runner checks the live receipts and state against those vectors.
It requires the pinned JS SDK (`npm ci`) and supports `--verify-only`
to recheck the existing receipts without broadcasting.
