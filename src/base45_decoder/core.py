"""Base45 encoding and decoding.

Base45 encodes arbitrary bytes into printable ASCII using a 45-symbol
alphabet. It is used by the European Digital Green Certificate (DGC)
QR codes because it stays within the alphanumeric subset that QR
mode encoders handle efficiently, yielding denser QR codes than
Base64.

The scheme groups bytes into either two-byte or three-byte chunks.
A three-byte chunk (big-endian value 0..16777215) maps to three base-45
digits; the remaining two bytes (0..65535) map to two base-45 digits.
Digits are emitted least-significant first, and each digit is looked up
in the alphabet:

    0-9 A-Z space $ % * + - . / :

Decoding inverts this. Because the alphabet deliberately excludes
lowercase letters, a lowercase input is rejected rather than silently
mangled.
"""

_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"

_VALUE = {c: i for i, c in enumerate(_ALPHABET)}


class Base45Error(ValueError):
    """Raised when input is not valid Base45.

    Subclassing ValueError keeps the exception familiar to callers who
    already catch ValueError for malformed input, while still allowing
    targeted handling of Base45-specific failures.
    """


def encode(data: bytes) -> str:
    """Encode bytes into a Base45 string.

    Args:
        data: Arbitrary bytes.

    Returns:
        A string containing only characters from the Base45 alphabet.

    Raises:
        TypeError: if ``data`` is not bytes-like.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError(
            "encode() expects a bytes-like object, got %s" % type(data).__name__
        )

    data = bytes(data)
    out = []
    for i in range(0, len(data), 2):
        chunk = data[i : i + 2]
        if len(chunk) == 2:
            value = (chunk[0] << 8) + chunk[1]
            out.append(_ALPHABET[value % 45])
            out.append(_ALPHABET[(value // 45) % 45])
            out.append(_ALPHABET[value // 45 // 45])
        else:
            value = chunk[0]
            out.append(_ALPHABET[value % 45])
            out.append(_ALPHABET[value // 45])
    return "".join(out)


def decode(text: str) -> bytes:
    """Decode a Base45 string back into bytes.

    Args:
        text: A Base45 string.

    Returns:
        The original bytes.

    Raises:
        TypeError: if ``text`` is not a str.
        Base45Error: if ``text`` contains characters outside the Base45
            alphabet, has a length that is not a valid grouping, or
            decodes to a value that cannot be represented in the
            expected number of bytes.
    """
    if not isinstance(text, str):
        raise TypeError(
            "decode() expects a str, got %s" % type(text).__name__
        )

    length = len(text)
    if length == 0:
        return b""

    # A valid Base45 string is composed of runs of three characters
    # (each encoding two bytes) optionally followed by a single run of
    # two characters (encoding the final one byte). The spec does not
    # permit one- or four-character remainders.
    if length % 3 == 1:
        raise Base45Error("Invalid Base45 length %d: remainder 1" % length)

    out = bytearray()
    for i in range(0, length, 3):
        chunk = text[i : i + 3]
        if len(chunk) == 3:
            try:
                c1 = _VALUE[chunk[0]]
                c2 = _VALUE[chunk[1]]
                c3 = _VALUE[chunk[2]]
            except KeyError:
                raise Base45Error(
                    "Invalid Base45 character in chunk %r" % chunk
                )
            # Digits are stored least-significant first, so chunk[0]
            # is the least significant and chunk[2] the most.
            value = c3 * 45 * 45 + c2 * 45 + c1
            # Two bytes cover 0..65535. A larger value means the input
            # was not produced by a compliant encoder.
            if value > 0xFFFF:
                raise Base45Error(
                    "Base45 chunk %r decodes to %d, exceeds 0xFFFF" % (chunk, value)
                )
            out.append(value >> 8)
            out.append(value & 0xFF)
        elif len(chunk) == 2:
            try:
                c1 = _VALUE[chunk[0]]
                c2 = _VALUE[chunk[1]]
            except KeyError:
                raise Base45Error(
                    "Invalid Base45 character in chunk %r" % chunk
                )
            value = c2 * 45 + c1
            if value > 0xFF:
                raise Base45Error(
                    "Base45 chunk %r decodes to %d, exceeds 0xFF" % (chunk, value)
                )
            out.append(value)
        else:
            # A one-character trailing chunk: this can only happen when
            # length % 3 == 1, which we rejected above. Guard anyway so
            # that a future alphabet change cannot silently truncate.
            raise Base45Error(
                "Invalid Base45 length %d: trailing single character" % length
            )
    return bytes(out)
