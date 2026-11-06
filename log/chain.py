import hashlib
import json

GENESIS = "0" * 64


def compute_hash(seq, payload_text, prev_hash):
    text = f"{seq}|{payload_text}|{prev_hash}"
    return hashlib.sha256(text.encode()).hexdigest()


def make_entry(seq, payload, prev_hash):
    payload_text = json.dumps(payload, sort_keys=True)

    return {
        "seq": seq,
        "payload": payload_text,
        "prev_hash": prev_hash,
        "hash": compute_hash(seq, payload_text, prev_hash)
    }
