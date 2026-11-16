# StudioNet proof matrix

[StudioNet contract](https://explorer-studio.genlayer.com/address/0x239e9acd065718A87B47Df725bC74fef3f605812) · [Deployed source](https://github.com/Starling-spell/indel-equivalence-index/blob/6658e4cd48bd2c071a793fe8bbf501872b3e3b84/contracts/IndelEquivalenceIndex.py) · [Receipts and exact events](PROOFS.json)

Deployed source SHA-256 `a2b5e46f20a51052285435a317b5146e0aeb29530bce01bcbf6ba33bd5560bbc`.
All four receipts finalized with successful execution and majority agreement.
The proof runner checked each exact returned report and read back each event
from storage. The two insertion calls fetched different reference windows
and produced one shared ID. The deletion produced a separate ID.
An unknown event reverted.

| Transaction | Verified result | Agree votes / initial validators |
| --- | --- | --- |
| [deploy](https://explorer-studio.genlayer.com/tx/0xc06acb331d8899ddd8b84fefabe1d8bdefcc612a3bcf696717e3175392321b39) | Deployed source matched the pinned commit. | 3 / 5 |
| [insert-first](https://explorer-studio.genlayer.com/tx/0x025e62e0385ec7d063a83fbf5293d19f423b250fff7bccb66cb4909f9e679103) | insert `AT` at 27 → 27–31 · `a044e2d2cc01c17ea68943e4d621484f2a86e66a429100c6f930157d3dabbd52` | 3 / 5 |
| [insert-shifted](https://explorer-studio.genlayer.com/tx/0xad3c104ff5ab87013c250b58de6d52ba50d350e71d80444b987fd330533da139) | insert `TA` at 28 → 27–31 · `a044e2d2cc01c17ea68943e4d621484f2a86e66a429100c6f930157d3dabbd52` | 3 / 5 |
| [delete-repeat](https://explorer-studio.genlayer.com/tx/0x23b686b17e11efdd5e4c73d58810e1f68eea79d0991e30f64d680197217b17c4) | delete `A` at 47 → 46–52 · `f4c9ac1d20cc4e5a374d034f6d36ea83d4f80108081899fc18ca1f5fc643f521` | 3 / 5 |

[Independent reference vectors](REFERENCE.json) were computed by enumerating
all positions that recreate the same edited string. The local tests also
cover malformed FASTA, archive disagreement, and exhausted windows.
