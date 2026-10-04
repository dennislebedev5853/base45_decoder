import unittest

from base45_decoder import Base45Error, decode, encode


class TestRoundTrip(unittest.TestCase):
    """Inputs of varying lengths must survive an encode/decode cycle."""

    def test_empty(self):
        self.assertEqual(encode(b""), "")
        self.assertEqual(decode(""), b"")

    def test_single_byte_zero(self):
        self.assertEqual(encode(b"\x00"), "00")
        self.assertEqual(decode("00"), b"\x00")

    def test_single_byte_high(self):
        # 0x3D = 61 = 1*45 + 16; LSB-first digits [16, 1] -> 'G' and '1'
        self.assertEqual(encode(b"="), "G1")
        self.assertEqual(decode("G1"), b"=")

    def test_two_bytes(self):
        # 'BB8' in RFC 8985 examples decodes to b'AB'.
        self.assertEqual(decode("BB8"), b"AB")
        self.assertEqual(encode(b"AB"), "BB8")

    def test_three_bytes(self):
        self.assertEqual(decode("%69 VD92EX0"), b"Hello!!")
        self.assertEqual(encode(b"Hello!!"), "%69 VD92EX0")

    def test_long_round_trip(self):
        data = bytes(range(256))
        self.assertEqual(decode(encode(data)), data)

    def test_memoryview_input(self):
        data = b"abc"
        self.assertEqual(encode(memoryview(data)), encode(data))

    def test_bytearray_input(self):
        data = bytearray(b"abc")
        self.assertEqual(encode(data), "0EC92")


class TestDecodeErrors(unittest.TestCase):
    """Malformed input must be rejected, not silently mangled."""

    def test_lowercase_rejected(self):
        with self.assertRaises(Base45Error):
            decode("bb8")

    def test_invalid_character_rejected(self):
        with self.assertRaises(Base45Error):
            decode("!@#")

    def test_invalid_length_one(self):
        with self.assertRaises(Base45Error):
            decode("0")

    def test_invalid_length_four(self):
        with self.assertRaises(Base45Error):
            decode("0000")

    def test_two_byte_chunk_overflow(self):
        # ":: " = 43*45 + 44*45 + 43 = 3913, which fits in two bytes.
        # To exceed 0xFFFF we need a three-char chunk decoding above
        # 65535. The largest valid three-char chunk is 44*45*45 +
        # 44*45 + 44 = 91034, which is > 65535 and thus invalid.
        with self.assertRaises(Base45Error):
            decode(":::")

    def test_single_byte_chunk_overflow(self):
        # A two-character chunk decoding above 255 is invalid because
        # it would not fit in the single byte the grouping implies.
        # "::" = 43*45 + 43 = 1978, which exceeds 255.
        with self.assertRaises(Base45Error):
            decode("::")

    def test_type_error_on_bytes_input(self):
        with self.assertRaises(TypeError):
            decode(b"BB8")  # type: ignore[arg-type]

    def test_base45_error_is_value_error(self):
        self.assertTrue(issubclass(Base45Error, ValueError))


class TestEncodeErrors(unittest.TestCase):
    def test_type_error_on_str_input(self):
        with self.assertRaises(TypeError):
            encode("abc")  # type: ignore[arg-type]

    def test_type_error_on_int_input(self):
        with self.assertRaises(TypeError):
            encode(42)  # type: ignore[arg-type]


class TestAlphabet(unittest.TestCase):
    """The alphabet ordering matters: space, $, %, *, +, -, ., /, :
    come after the alphanumerics, not in ASCII order.
    """

    def test_space_is_index_36(self):
        # '0' is index 0, '9' is 9, 'A' is 10, 'Z' is 35, ' ' is 36.
        # b'\x24' = 36 = 0*45 + 36; LSB-first -> " 0"
        self.assertEqual(encode(b"$"), " 0")
        self.assertEqual(decode(" 0"), b"$")

    def test_colon_is_last_index(self):
        # ':' is index 44.
        # b'\x2C' = 44 = 0*45 + 44; LSB-first -> ":0"
        self.assertEqual(encode(b","), ":0")
        self.assertEqual(decode(":0"), b",")


if __name__ == "__main__":
    unittest.main()
