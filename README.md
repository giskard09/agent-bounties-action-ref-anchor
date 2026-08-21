# agent-bounties-action-ref-anchor

A worked example that derives an **`action_ref`** — a deterministic,
content-addressed identifier for an agent action
([`action-ref-v1`](https://github.com/giskard09/argentum-core/blob/master/docs/spec/action-ref.md)) —
over a **real, already-settled** `BountySettled` event from
[`NSPG13/agent-bounties`](https://github.com/NSPG13/agent-bounties)
(`agentbounties.app`, live production, Base mainnet, OpenAI Build Week 2026
collaboration), and anchors it permissionlessly on-chain.

This is the strongest provenance standard in this worked-example series to
date: not a replicated algorithm (Keycard), not a test fixture (Cashu) —
a **live production settlement, independently re-verified against Base
mainnet RPC directly**, not merely trusted from agent-bounties' own API.

> **Provenance, up front (read `PROVENANCE.md` for the full statement).**
> `action_ref` is derived exactly per `action-ref-v1`. The `settlement`
> object is the literal `BountySettled` event emitted by a real bounty
> contract on Base mainnet — every field independently re-confirmed by
> `verifier/verify.py` via `eth_getTransactionReceipt` against
> `mainnet.base.org` directly, including manual ABI-decoding of the raw
> log data (topic0/1/2/3 + all 8 non-indexed words). No bounty was
> created, claimed, or settled by this repo. No contact with NSPG13.
> Nothing implies integration, endorsement, or adoption.

## The gap — and why this event in particular

`BountySettled` already carries four hash fields —
`submissionHash`, `evidenceHash`, `policyHash`, `verificationHash` —
mapping directly onto the funded → delivered → settled lifecycle
NSPG13 described when they offered their own fixtures for a binding on
2026-07-16, the same day this specific settlement happened. Unlike a
single opaque id, this event already gives a verifier four independent
commitments to check. `action_ref` doesn't replace any of them — it wraps
the agent-facing action of citing this settlement, with `scope` pointing
at the real `bounty_id` + `round`, and carries all four hashes verbatim
in an additive envelope field.

```
   agent-bounties BountySettled (real)      public chain (Base)
   ┌───────────────────────────┐           ┌────────────────────────┐
   │ agent_id, action_type,     │ JCS+SHA256│ AnchorRegistry         │
   │ scope (cites bounty_id +   │──────────▶│  anchor(bytes32 ref)   │
   │ round), timestamp          │ action_ref│  Anchored(ref,by,time) │
   │ + 4 real settlement hashes │           └────────────────────────┘
   └───────────────────────────┘             operator-independent
                                              timestamp / finality
```

## Doctrine: spec-agnostic to agent-bounties' format, two-layer pattern

We derive `action_ref` from the four canonical fields only. We do **not**
ask agent-bounties to adopt any anchoring infrastructure or emit any new
fields — `submissionHash`/`evidenceHash`/`policyHash`/`verificationHash`
are already their own real, on-chain values; this repo cites them, not
reinterprets them.

## What's here

| Path | What it is |
|------|-----------|
| `scripts/produce.py` | Derives `action_ref` per `action-ref-v1` (JCS RFC 8785 + SHA-256, via `scripts/jcs.py`) over the real `BountySettled` event's fields. |
| `scripts/jcs.py` | `argentum-core`'s own JCS helper, vendored verbatim. |
| `verifier/verify.py` | Independent (stdlib-only) verifier: recomputes `action_ref`, re-fetches and manually ABI-decodes the source `BountySettled` receipt from Base mainnet RPC directly, and confirms the `Anchored` event once anchored. |
| `artifacts/` | The canonical instance: `manifest.json` (preimage, settlement, envelope) and `anchor.json` (tx/block, once anchored). |
| `scripts/anchor.sh` | The equivalent `cast` command to anchor `action_ref`. |
| `PROVENANCE.md` | Exact tx/block/log provenance of the underlying settlement. Read it. |

## Reproduce

```bash
# 1. derive action_ref over the real settlement fields
python3 scripts/produce.py artifacts

# 2. independently verify -- re-fetches the source tx from Base RPC directly
python3 verifier/verify.py

# 3. anchor action_ref on Base mainnet
bash scripts/anchor.sh
```

## This instance

- `action_ref`: `2100c3b322cc926ead04aab87c8f6aaf400d355c4c8f47df2c242a694e6e0424`
- Source: `BountySettled`, bounty contract
  `0x3d0e396dd4c07c8a7dff13ec93e59c4e7e5a270e`, tx
  [`0xdc0dc865...`](https://basescan.org/tx/0xdc0dc865c4ee5b404b49dfce985c3964bb4098fe011d26abdd4e7789d26c46fa),
  block 48721937 (2026-07-16, Base mainnet)
- Anchor status: **anchored** — Base mainnet, tx
  [`0x7c8692c0...`](https://basescan.org/tx/0x7c8692c003b80a48bb8123ae6965e26464d271ee2041404cc025e0f15e5fcaba),
  block 50277597.

## License

MIT — see `LICENSE`.
