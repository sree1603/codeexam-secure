import unittest
from copy import deepcopy

from log.chain import GENESIS, make_entry
from log.verify import verify_entries


def build_chain(count):
    entries = []
    prev_hash = GENESIS

    for seq in range(1, count + 1):
        entry = make_entry(seq, {"event": f"test{seq}"}, prev_hash)
        entries.append(entry)
        prev_hash = entry["hash"]

    return entries


class TestHashChain(unittest.TestCase):

    def test_five_entries_are_linked(self):
        entries = build_chain(5)
        self.assertEqual(len(entries), 5)

        for i in range(1, 5):
            self.assertEqual(entries[i]["prev_hash"], entries[i - 1]["hash"])

    def test_valid_chain(self):
        entries = build_chain(10)
        self.assertEqual(verify_entries(entries), (True, None))

    def test_payload_tampering(self):
        entries = deepcopy(build_chain(10))
        entries[1]["payload"] = '{"event":"changed"}'
        self.assertEqual(verify_entries(entries), (False, 2))

    def test_middle_entry_deleted(self):
        entries = build_chain(10)
        del entries[4]
        self.assertEqual(verify_entries(entries), (False, 5))

    def test_entries_swapped(self):
        entries = build_chain(10)
        entries[2], entries[3] = entries[3], entries[2]
        self.assertEqual(verify_entries(entries), (False, 3))


if __name__ == "__main__":
    unittest.main()
