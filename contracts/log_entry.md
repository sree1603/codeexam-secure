# Log Entry Format

Each log entry contains four fields:

- `seq`: Sequential number starting from 1.
- `payload`: The event details stored as JSON text.
- `prev_hash`: SHA-256 hash of the previous entry.
- `hash`: SHA-256 hash calculated using `seq|payload|prev_hash`.

## Hash Calculation

The hash is calculated as:

    hash = sha256("seq|payload|prev_hash")

For the first entry, `prev_hash` must contain 64 zeros.

## Worked Example

Entry 1:

    seq = 1
    payload = {"event":"test"}
    prev_hash = 0000000000000000000000000000000000000000000000000000000000000000

The string being hashed is:

    1|{"event":"test"}|0000000000000000000000000000000000000000000000000000000000000000

The resulting SHA-256 hash is:

    f6405ee04f91591f32f7fc78f52c7b2375822c62154a3ef53d4a6264d72185b9
