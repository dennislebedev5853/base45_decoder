# Base45 Decoder

Encodes and decodes data using Base45, the encoding used in European Digital Green Certificate QR codes.

```python
from base45_decoder import encode, decode

assert encode(b"Hello!!") == "%69 VD92EX0"
assert decode("%69 VD92EX0") == b"Hello!!"
```

## Why this exists

QR codes have an alphanumeric mode that stores a fixed set of 45 characters far more densely than raw bytes. Base45 packs binary data into exactly that character set so that a QR encoder can use the efficient alphanumeric mode instead of falling back to byte mode. The trade-off versus Base64 is a larger output string (roughly 1.5x the input size) in exchange for a smaller, more scannable QR symbol.

## Exports

`encode(data: bytes) -> str` and `decode(text: str) -> bytes` are the public functions. `Base45Error`, a subclass of `ValueError`, is raised on malformed input.

## Edge cases

The Base45 alphabet includes space, `$`, `%`, `*`, `+`, `-`, `.`, `/`, and `:` after the digits and capital letters. Lowercase letters are not in the alphabet and are rejected on decode rather than silently uppercased. Input lengths that leave a single trailing character are invalid because Base45 groups bytes in pairs (emitting three characters) with an optional lone final byte (emitting two characters); a length with remainder 1 modulo 3 cannot arise from a correct encoder and is rejected.

A two-character chunk decoding above 255, or a three-character chunk decoding above 65535, is also rejected even though such values are representable as base-45 digits, because they could not have been produced by a compliant encoder.
