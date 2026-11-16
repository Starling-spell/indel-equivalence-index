**Contribution type** Builder → Intelligent Contracts

**Title** IndelEquivalenceIndex — Reference-Verified DNA Edit Equivalence

**Notes / Description**

IndelEquivalenceIndex gives equivalent descriptions of an insertion or deletion one on-chain event ID. It records the leftmost representation, the complete placement range, and the flanking bases that delimit it.

The leader and validators independently fetch the same versioned reference window from ENA and NCBI. They check the FASTA headers and compare the actual bases. Each derives the equivalent placements and must agree on the full report, including the window digest and event witness. Ambiguous, mismatched, and exhausted windows cannot create an event.

On StudioNet, inserting AT at boundary 27 and TA at boundary 28 gave the same event ID despite different fetched windows. A deletion in a separate repeat produced its own event. The contract evaluates sequence equivalence within bounded flanks.

**Evidence**

- [Repository](https://github.com/Starling-spell/indel-equivalence-index)
- [Deployed source](https://github.com/Starling-spell/indel-equivalence-index/blob/6658e4cd48bd2c071a793fe8bbf501872b3e3b84/contracts/IndelEquivalenceIndex.py)
- [StudioNet contract](https://explorer-studio.genlayer.com/address/0x239e9acd065718A87B47Df725bC74fef3f605812)
- [Live proof matrix](https://github.com/Starling-spell/indel-equivalence-index/blob/main/LIVE_PROOFS.md)
- [deploy](https://explorer-studio.genlayer.com/tx/0xc06acb331d8899ddd8b84fefabe1d8bdefcc612a3bcf696717e3175392321b39)
- [insert-first](https://explorer-studio.genlayer.com/tx/0x025e62e0385ec7d063a83fbf5293d19f423b250fff7bccb66cb4909f9e679103)
- [insert-shifted](https://explorer-studio.genlayer.com/tx/0xad3c104ff5ab87013c250b58de6d52ba50d350e71d80444b987fd330533da139)
- [delete-repeat](https://explorer-studio.genlayer.com/tx/0x23b686b17e11efdd5e4c73d58810e1f68eea79d0991e30f64d680197217b17c4)
