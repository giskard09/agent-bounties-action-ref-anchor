# Provenance — read this before drawing any conclusion

This document states exactly what is real and what is synthetic in this
worked example. Hard honesty is the point: the artifact is worthless if its
provenance is fuzzy.

## What is real

- `action_ref` is derived exactly per `action-ref-v1`
  ([argentum-core/docs/spec/action-ref.md](https://github.com/giskard09/argentum-core/blob/master/docs/spec/action-ref.md)):
  SHA-256 of the RFC 8785 JCS canonicalization of the four preimage fields
  (`agent_id`, `action_type`, `scope`, `timestamp`), computed with this
  repo's own `jcs.py` (vendored verbatim from `argentum-core`).
- **Everything under `settlement` in `artifacts/manifest.json` is a real,
  already-settled on-chain event — not a mock, not a synthetic fixture.**
  Source: `AgentBounty.sol` (`contracts/base-escrow/src/AgentBounty.sol:148-158`
  in `NSPG13/agent-bounties`), event `BountySettled`, emitted by bounty
  contract `0x3d0e396dd4c07c8a7dff13ec93e59c4e7e5a270e` on Base mainnet, tx
  [`0xdc0dc865...`](https://basescan.org/tx/0xdc0dc865c4ee5b404b49dfce985c3964bb4098fe011d26abdd4e7789d26c46fa),
  block 48721937, 2026-07-16T20:20:21Z.
- **This event was independently re-verified against Base mainnet RPC
  directly — not merely trusted from `agentbounties.app`'s own API.**
  `agentbounties.app/v1/base/autonomous-bounties/events` (their own
  published, authoritative endpoint) was used only to *locate* the
  candidate tx hash; `verifier/verify.py` then re-fetches the transaction
  receipt from `https://mainnet.base.org` directly and confirms, byte for
  byte:
  - `topic0` == `keccak256("BountySettled(bytes32,uint64,address,uint256,uint256,uint256,uint256,bytes32,bytes32,bytes32,bytes32)")`
    == `0x2ee7b1323824324868017119c9922527f2e2c8eb20a8044c3dd574bdbfb2dd71`
  - `topic1`/`topic2`/`topic3` (indexed `bounty_id`/`round`/`solver`) match
    the declared settlement object.
  - The non-indexed `data` word, ABI-decoded independently in
    `verify.py` (not via any library, plain word-slicing per the Solidity
    ABI spec), matches all eight remaining fields — `solver_reward`,
    `claim_bond_returned`, `timeout_bond_bonus`, `verifier_reward`,
    `submission_hash`, `evidence_hash`, `policy_hash`,
    `verification_hash`.
  This is the strongest provenance standard used in this worked-example
  series to date: the underlying claim is not "we replicated an
  algorithm from their source code" (Keycard) or "we reused their test
  fixture" (Cashu) — it is "we independently re-derived a live production
  event from the chain itself."
- `AgentBountyFactory` (`0x082c52131aaf0c56e76b075f895eab6fcab6d2f9`) and
  the wider `agent-bounties/autonomous-v1` protocol are real, in
  production: `agentbounties.app`, an MCP server, and a documented OpenAI
  Build Week 2026 collaboration (`docs/evidence/openai-build-week-2026.json`,
  19 confirmed settlements totaling 14.6 USDC across 5 unique solver
  wallets, as of the file's 2026-07-19 snapshot — re-read the live
  endpoint for current values, not this snapshot).
- The on-chain anchor of `action_ref` itself, once executed, is a real
  transaction on Base mainnet, independently checkable by anyone via
  `verifier/verify.py`.

## What is synthetic — declared

- **`agent_id` and the `scope`/`action_type` strings in the `action_ref`
  preimage are this repo's own construction**, not emitted by
  agent-bounties. The protocol has no concept of `action_ref` — `scope`
  cites the real, on-chain `bounty_id` + `round` as the reference, per the
  two-layer pattern used throughout this series: `action_ref` wraps the
  agent's action of observing/reporting a settlement; it does not replace
  or reinterpret `BountySettled`'s own four hash fields, which are carried
  verbatim in the `settlement` envelope.
- **No new interaction with the agent-bounties protocol occurred.** No
  bounty was created, claimed, or settled by this repo — the settlement
  cited here happened on 2026-07-16, independent of and prior to this
  worked example. This is retrospective, not participatory.
- **The four hash fields (`submission_hash`/`evidence_hash`/`policy_hash`/
  `verification_hash`) are cited, not decoded further.** What
  `submissionHash`/`evidenceHash` actually commit to (e.g. what evidence
  format, what policy document) is internal to agent-bounties' own
  verification pipeline and out of scope for this worked example — we
  confirm the hashes exist and match the on-chain event, not what
  produced them.

## What this therefore does and does not show

- **Does show:** `action_ref` derivation applies unchanged to a real,
  already-settled production event from a live protocol with real
  economic activity (confirmed solver payouts on Base mainnet), citing
  that event's own real identifiers (`bounty_id`, `round`) and its own
  four real settlement hashes — independently re-verified from the chain,
  not merely read from the protocol's own API.
- **Does not show:** that NSPG13/agent-bounties has integrated, endorsed,
  or adopted `action_ref`. It is not a response to NSPG13's 2026-07-16
  offer to collaborate on a binding, and was not shared with them before
  this artifact existed — same sequencing as the Cashu worked example in
  this series: build first, decide what to say afterward. No claim of
  adoption, no claim that this resolves anything requested in that
  thread, no cited quote from any agent-bounties maintainer.
