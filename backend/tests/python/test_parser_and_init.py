import ctypes
import tempfile
import unittest
from pathlib import Path

from backend.src.init import TrieNode, create_trie_root, init_trie, init_type
from backend.src.parser import parse_header


class HeaderParserTests(unittest.TestCase):
    def test_parser_preserves_multiword_and_pointer_types(self) -> None:
        header = """
        unsigned char* transform(unsigned char * data, unsigned int length);
        int insert(TrieNode **root, char* text);
        """

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.h"
            path.write_text(header, encoding="utf-8")
            functions = parse_header(str(path))

        self.assertEqual(
            functions,
            [
                (
                    "transform",
                    ["unsigned char*", "unsigned int"],
                    "unsigned char*",
                ),
                ("insert", ["TrieNode**", "char*"], "int"),
            ],
        )


class CtypesInitializationTests(unittest.TestCase):
    def test_builtin_and_pointer_types_are_resolved(self) -> None:
        self.assertIs(init_type("int"), ctypes.c_int)
        self.assertIs(init_type("char*"), ctypes.c_char_p)
        self.assertIs(
            init_type("unsigned char*")._type_,
            ctypes.c_ubyte,
        )

        trie_pointer = init_type("TrieNode**")
        self.assertIs(trie_pointer._type_._type_, TrieNode)

    def test_unknown_type_has_a_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown C type"):
            init_type("MissingType*")

    def test_trie_functions_receive_expected_ctypes_signatures(self) -> None:
        functions = init_trie()
        insert = functions["insertTrieNode"]

        self.assertIs(insert.argtypes[0]._type_._type_, TrieNode)
        self.assertIs(insert.argtypes[1], ctypes.c_char_p)
        self.assertIs(insert.restype, ctypes.c_int)

        root = create_trie_root()
        self.assertFalse(bool(root))


if __name__ == "__main__":
    unittest.main()
