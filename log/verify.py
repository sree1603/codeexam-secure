from log.chain import GENESIS, compute_hash


def verify_entries(entries):
    expected_prev_hash = GENESIS

    for expected_seq, entry in enumerate(entries, start=1):

        if entry["seq"] != expected_seq:
            return False, expected_seq

        if entry["prev_hash"] != expected_prev_hash:
            return False, expected_seq

        calculated_hash = compute_hash(
            entry["seq"],
            entry["payload"],
            entry["prev_hash"]
        )

        if entry["hash"] != calculated_hash:
            return False, expected_seq

        expected_prev_hash = entry["hash"]

    return True, None
