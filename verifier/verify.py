#!/usr/bin/env python3
"""
Independent (stdlib-only) verifier for the agent-bounties-action-ref-anchor
worked example. Trusts nothing in manifest.json's prose fields -- only
recomputes and re-queries the chain directly.

1. Recomputes action_ref from the 4 declared preimage fields (JCS RFC 8785 +
   SHA-256, per argentum-core/docs/spec/action-ref.md) and checks it matches
   manifest.json.
2. Re-fetches the source BountySettled transaction receipt from Base
   mainnet RPC directly (NOT from agentbounties.app's API) and confirms:
   topic0 == keccak256(BountySettled(...)), topic1/topic2/topic3 match
   bounty_id/round/solver, and abi-decodes the data field to confirm all
   eight non-indexed values (solver_reward, claim_bond_returned,
   timeout_bond_bonus, verifier_reward, submission_hash, evidence_hash,
   policy_hash, verification_hash) match the declared settlement object
   byte-for-byte.
3. If artifacts/anchor.json exists, queries Base mainnet RPC for our own
   Anchored(bytes32,address,uint256) event on AnchorRegistry and confirms
   it exists on-chain. Skipped (not a failure) if not yet anchored.

Run: python3 verifier/verify.py [--artifacts DIR] [--rpc URL]
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from jcs import jcs_dumps  # argentum-core's own JCS (RFC 8785) helper, vendored verbatim

ANCHOR_REGISTRY = "0x49fEcA52bC634a9Ab773226D16619deC547794aa"
ANCHORED_TOPIC0 = "0xfe2289542f7a0110ac112c3a4d712afdcaaf2900a1326f4e6f340b563a0e8734"
BOUNTY_SETTLED_TOPIC0 = "0x2ee7b1323824324868017119c9922527f2e2c8eb20a8044c3dd574bdbfb2dd71"
DEFAULT_RPC = "https://mainnet.base.org"


def jcs(obj):
    return jcs_dumps(obj)


def sha256_hex(s) -> str:
    if isinstance(s, str):
        s = s.encode()
    return hashlib.sha256(s).hexdigest()


def rpc(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "User-Agent": "agent-bounties-action-ref-anchor-verifier/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.loads(r.read())
    if "error" in out:
        raise RuntimeError(f"RPC {method} error: {out['error']}")
    return out["result"]


def decode_uint256(word_hex: str) -> int:
    return int(word_hex, 16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", default=os.environ.get("BASE_RPC", DEFAULT_RPC))
    ap.add_argument("--artifacts", default=os.path.join(os.path.dirname(__file__), "..", "artifacts"))
    args = ap.parse_args()

    art = os.path.abspath(args.artifacts)
    m = json.load(open(os.path.join(art, "manifest.json")))

    ok = True

    # --- 1. action_ref from the 4 preimage fields ---------------------------
    recomputed_action_ref = sha256_hex(jcs(m["preimage"]))
    check1 = recomputed_action_ref == m["action_ref"]
    print(f"[{'PASS' if check1 else 'FAIL'}] action_ref recompute            : {recomputed_action_ref}")
    ok &= check1

    # --- 2. re-fetch the source BountySettled event directly from chain ----
    src = m["source_event"]
    settlement = m["settlement"]
    receipt = rpc(args.rpc, "eth_getTransactionReceipt", [src["tx_hash"]])
    check2 = receipt is not None and receipt["status"] == "0x1"
    print(f"[{'PASS' if check2 else 'FAIL'}] source tx confirmed (status 0x1) : {src['tx_hash']}")
    ok &= check2

    settled_log = None
    if receipt:
        for log in receipt["logs"]:
            if (
                log["address"].lower() == src["bounty_contract"].lower()
                and log["topics"][0].lower() == BOUNTY_SETTLED_TOPIC0
            ):
                settled_log = log
                break

    check3 = settled_log is not None
    print(f"[{'PASS' if check3 else 'FAIL'}] BountySettled log found on bounty contract")
    ok &= check3

    if settled_log:
        # indexed: bounty_id, round, solver
        topic_bounty_id = settled_log["topics"][1]
        topic_round = decode_uint256(settled_log["topics"][2])
        topic_solver = "0x" + settled_log["topics"][3][-40:]

        check4 = topic_bounty_id.lower() == settlement["bounty_id"].lower()
        check5 = topic_round == settlement["round"]
        check6 = topic_solver.lower() == settlement["solver"].lower()
        print(f"[{'PASS' if check4 else 'FAIL'}] topic1 bounty_id matches : {topic_bounty_id}")
        print(f"[{'PASS' if check5 else 'FAIL'}] topic2 round matches     : {topic_round}")
        print(f"[{'PASS' if check6 else 'FAIL'}] topic3 solver matches    : {topic_solver}")
        ok &= check4 & check5 & check6

        # non-indexed data: 4 uint256 words then 4 bytes32 words
        data = settled_log["data"][2:]
        words = [data[i:i + 64] for i in range(0, len(data), 64)]
        solver_reward = decode_uint256("0x" + words[0])
        claim_bond_returned = decode_uint256("0x" + words[1])
        timeout_bond_bonus = decode_uint256("0x" + words[2])
        verifier_reward = decode_uint256("0x" + words[3])
        submission_hash = "0x" + words[4]
        evidence_hash = "0x" + words[5]
        policy_hash = "0x" + words[6]
        verification_hash = "0x" + words[7]

        decoded = {
            "solver_reward": solver_reward,
            "claim_bond_returned": claim_bond_returned,
            "timeout_bond_bonus": timeout_bond_bonus,
            "verifier_reward": verifier_reward,
            "submission_hash": submission_hash,
            "evidence_hash": evidence_hash,
            "policy_hash": policy_hash,
            "verification_hash": verification_hash,
        }
        check7 = all(
            (str(decoded[k]).lower() == str(settlement[k]).lower()) for k in decoded
        )
        print(f"[{'PASS' if check7 else 'FAIL'}] all 8 non-indexed fields decode-match declared settlement")
        if not check7:
            print(f"         decoded  : {decoded}")
            print(f"         declared : {settlement}")
        ok &= check7

    # --- 3. our own anchor -----------------------------------------------------
    ref = "0x" + m["action_ref"]
    try:
        with open(os.path.join(art, "anchor.json")) as f:
            anchor = json.load(f)
    except FileNotFoundError:
        print("[SKIP] no anchor.json yet -- action_ref not anchored on-chain")
        anchor = None

    if anchor:
        hint = int(anchor["block"])
        head = int(rpc(args.rpc, "eth_blockNumber", []), 16)
        from_block = hex(max(0, hint - 25))
        to_block = hex(min(hint + 25, head))

        logs = rpc(args.rpc, "eth_getLogs", [{
            "address": ANCHOR_REGISTRY,
            "fromBlock": from_block,
            "toBlock": to_block,
            "topics": [ANCHORED_TOPIC0, ref],
        }])

        check8 = bool(logs)
        if check8:
            log = logs[0]
            ts = int(log["data"], 16)
            anchored_by = "0x" + log["topics"][2][-40:]
            print(f"[PASS] on-chain Anchored event : AnchorRegistry {ANCHOR_REGISTRY} (Base 8453)")
            print(f"         tx               : {log['transactionHash']}")
            print(f"         block            : {int(log['blockNumber'], 16)}")
            print(f"         anchoredBy       : {anchored_by}")
            print(f"         block timestamp  : {ts}")
        else:
            print(f"[FAIL] no Anchored event for {ref} on AnchorRegistry near block {hint}")
        ok &= check8

    print()
    print("ALL CHECKS PASS" if ok else "SOME CHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
