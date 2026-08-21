#!/usr/bin/env python3
"""
Produces an action_ref for a REAL, already-settled Base-mainnet bounty in
NSPG13/agent-bounties (agentbounties.app) -- following action-ref-v1
(argentum-core, JCS RFC 8785 + SHA-256) byte-for-byte -- and emits the
artifacts needed to anchor + independently verify it.

Unlike the Cashu worked example (test mocks only), every field used here
is a REAL, already-executed on-chain event: a BountySettled emitted by a
real AgentBounty.sol instance on Base mainnet, independently confirmed
against eth_getTransactionReceipt (not just read from agentbounties.app's
own API -- see PROVENANCE.md for the byte-exact cross-check).

BountySettled already carries four hash fields (submissionHash,
evidenceHash, policyHash, verificationHash) -- mapping directly to the
funded/delivered/settled phases NSPG13 described and to this repo's own
composition-ref/delegation-chain-ref pattern. Two-layer structure, same as
every prior worked example: action_ref does not replace those four
hashes -- it is the agent-action wrapper citing the bounty_id + round as
scope, with the four real settlement hashes carried as an additive
envelope field for convenience (not recomputed or reinterpreted -- cited
verbatim from the real event).

PROVENANCE (summary): the underlying BountySettled event, tx, and all
eleven event fields are 100% real -- verified independently via
eth_getTransactionReceipt against Base mainnet, not merely trusted from
agentbounties.app's API. agent_id and the action_ref preimage wrapper
itself are this repo's own construction, not emitted by agent-bounties.
No claim that NSPG13/agent-bounties emits action_ref today, and no claim
of integration, adoption, or endorsement.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from jcs import jcs_dumps  # argentum-core's own JCS (RFC 8785) helper, vendored verbatim

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "artifacts"
os.makedirs(OUT_DIR, exist_ok=True)


def jcs(obj):
    return jcs_dumps(obj)


def sha256_hex(s) -> str:
    if isinstance(s, str):
        s = s.encode()
    return hashlib.sha256(s).hexdigest()


# --- 0. The real, already-settled BountySettled event ---------------------
# AgentBounty.sol event (contracts/base-escrow/src/AgentBounty.sol:148-158),
# emitted on Base mainnet. Every value below is the literal on-chain value,
# independently confirmed via eth_getTransactionReceipt against
# https://mainnet.base.org (see PROVENANCE.md for the full byte comparison,
# including topic0 = keccak256(BountySettled(...)) and log-data decoding).
bounty_id = "0xa9ecd20c70da07dea26ff531dcbd3422d04ff921fcbc872a7fbb3062832a1677"
round_ = 1
solver = "0x1dbe963c9cc0189c7d0594f0d06377dab555cef3"
settlement = {
    "bounty_id": bounty_id,
    "round": round_,
    "solver": solver,
    "solver_reward": 100000,
    "claim_bond_returned": 10000,
    "timeout_bond_bonus": 0,
    "verifier_reward": 10000,
    "submission_hash": "0x800a7d7ccdfbdc9857d853781a8aa4ffc1f2fec33bb34c44ce30faaa6d50b4da",
    "evidence_hash": "0x8933412ea994fbd6232c03ce680c745c559d1d533df5badb29d6f6d0407e60bd",
    "policy_hash": "0x1d7e68562787f29017d89446a47c8ee70f82c0b9208271445f0d9f73293e7158",
    "verification_hash": "0x97442e138eabd45266a8785e75cad9850cae90b8d381b3d0a79dded1bc123317",
}
tx_hash = "0xdc0dc865c4ee5b404b49dfce985c3964bb4098fe011d26abdd4e7789d26c46fa"
block_number = 48721937
bounty_contract = "0x3d0e396dd4c07c8a7dff13ec93e59c4e7e5a270e"

# --- 1. The four required action-ref-v1 preimage fields --------------------
# Per argentum-core/docs/spec/action-ref.md. scope cites the real bounty_id
# + round -- the settlement's own on-chain identity, not invented.
timestamp = "2026-07-16T20:20:21.000Z"  # real block timestamp of tx_hash (0x6a593d05)
preimage = {
    "agent_id": "worked-example.agent-bounties-action-ref-anchor",
    "action_type": "agentbounties.bounty.settled",
    "scope": f"agentbounties:bounty_id:{bounty_id}:round:{round_}",
    "timestamp": timestamp,
}
jcs_payload = jcs(preimage)
action_ref = sha256_hex(jcs_payload)

envelope = {
    "packet_version": "1.0",
    "action_ref": action_ref,
    "hash_algo": "sha256",
    "preimage_format": "jcs-rfc8785-v1",
    "preimage": preimage,
    "capability": "bounty_settled",
    "settlement": settlement,
    "generated_at_utc": timestamp,
}

manifest = {
    "fixture_id": "agent-bounties-settled-worked-example",
    "spec": "action-ref-v1 (argentum-core, docs/spec/action-ref.md)",
    "preimage": preimage,
    "jcs_payload": jcs_payload,
    "action_ref": action_ref,
    "anchor_ref_bytes32": "0x" + action_ref,
    "anchor_registry": "0x49fEcA52bC634a9Ab773226D16619deC547794aa",
    "anchor_chain": "Base mainnet (chainId 8453)",
    "envelope": envelope,
    "settlement": settlement,
    "source_event": {
        "protocol": "NSPG13/agent-bounties (agentbounties.app)",
        "event": "BountySettled",
        "contract_source": "contracts/base-escrow/src/AgentBounty.sol:148-158",
        "bounty_contract": bounty_contract,
        "tx_hash": tx_hash,
        "block_number": block_number,
        "chain": "Base mainnet (8453)",
    },
    "provenance": (
        "Worked example over a REAL, already-settled on-chain event -- not a "
        "test mock. Every settlement field is the literal BountySettled log "
        "data, independently confirmed via eth_getTransactionReceipt against "
        "Base mainnet (topic0/topic1/topic2/topic3 + abi-decoded data, see "
        "PROVENANCE.md). agent_id and the action_ref preimage wrapper are "
        "this repo's own construction. No live interaction with the "
        "NSPG13/agent-bounties protocol beyond reading its public chain "
        "state and its own published API. No claim of integration, "
        "adoption, or endorsement."
    ),
}

with open(os.path.join(OUT_DIR, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2, sort_keys=False)
    f.write("\n")

print(f"action_ref: {action_ref}")
print(f"jcs_payload: {jcs_payload}")
print(f"wrote {os.path.join(OUT_DIR, 'manifest.json')}")
