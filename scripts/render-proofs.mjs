import fs from 'node:fs';
import assert from 'node:assert/strict';

const proof = JSON.parse(fs.readFileSync('PROOFS.json', 'utf8'));
const github = 'https://github.com/Starling-spell/indel-equivalence-index';
const explorer = 'https://explorer-studio.genlayer.com';
assert(proof.verified && proof.source.source_match && proof.unknown_event_reverted);
assert.equal(proof.transactions.length, 4);
assert.equal(Object.keys(proof.calls).length, 3);
assert(proof.transactions.every(({receipt}) => receipt.committed && receipt.status === 'FINALIZED' &&
  receipt.execution === 'SUCCESS' && receipt.consensus === 'MAJORITY_AGREE' &&
  receipt.leader_only === false && receipt.agree_votes >= 2));

const deployment = `[StudioNet contract](${explorer}/address/${proof.address})`;
const source = `[Deployed source](${github}/blob/${proof.source_commit}/contracts/IndelEquivalenceIndex.py)`;
const tx = t => `[${t.step}](${explorer}/tx/${t.hash})`;
const rows = proof.transactions.map(t => {
  const call = proof.calls[t.step]?.report;
  const result = call
    ? `${call.submitted.kind} \`${call.submitted.bases}\` at ${call.submitted.boundary} → ${call.event.left_boundary}–${call.event.right_boundary} · \`${call.event_id}\``
    : 'Deployed source matched the pinned commit.';
  return `| ${tx(t)} | ${result} | ${t.receipt.agree_votes} / ${t.receipt.initial_validators} |`;
});

fs.writeFileSync('LIVE_PROOFS.md', `# StudioNet proof matrix

${deployment} · ${source} · [Receipts and exact events](PROOFS.json)

Deployed source SHA-256 \`${proof.source.sha256}\`.
All four receipts finalized with successful execution and majority agreement.
The proof runner checked each exact returned report and read back each event
from storage. The two insertion calls fetched different reference windows
and produced one shared ID. The deletion produced a separate ID.
An unknown event reverted.

| Transaction | Verified result | Agree votes / initial validators |
| --- | --- | --- |
${rows.join('\n')}

[Independent reference vectors](REFERENCE.json) were computed by enumerating
all positions that recreate the same edited string. The local tests also
cover malformed FASTA, archive disagreement, and exhausted windows.
`);

const notes = `IndelEquivalenceIndex gives equivalent descriptions of an insertion or deletion one on-chain event ID. It records the leftmost representation, the complete placement range, and the flanking bases that delimit it.

The leader and validators independently fetch the same versioned reference window from ENA and NCBI. They check the FASTA headers and compare the actual bases. Each derives the equivalent placements and must agree on the full report, including the window digest and event witness. Ambiguous, mismatched, and exhausted windows cannot create an event.

On StudioNet, inserting AT at boundary 27 and TA at boundary 28 gave the same event ID despite different fetched windows. A deletion in a separate repeat produced its own event. The contract evaluates sequence equivalence within bounded flanks.`;
assert(notes.length <= 1000);
fs.writeFileSync('SUBMISSION.md', `**Contribution type** Builder → Intelligent Contracts

**Title** IndelEquivalenceIndex — Reference-Verified DNA Edit Equivalence

**Notes / Description**

${notes}

**Evidence**

- [Repository](${github})
- ${source}
- ${deployment}
- [Live proof matrix](${github}/blob/main/LIVE_PROOFS.md)
${proof.transactions.map(t => '- ' + tx(t)).join('\n')}
`);
