import tempfile
import unittest
from pathlib import Path

from scripts.netlist_data.io_lists import read_list, write_list


class IoListsTest(unittest.TestCase):
    def test_roundtrip_sorted_unique(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sub" / "domains.txt"
            write_list(path, ["z.ru", "a.ru", "a.ru"], comments=["header"])
            self.assertEqual(read_list(path), ["a.ru", "z.ru"])
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("# header\n"))
            self.assertTrue(text.endswith("\n"))
            self.assertNotIn("\r", text)

    def test_read_missing_and_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nope.txt"
            self.assertEqual(read_list(path), [])
            path.write_text("# comment\n\nb.ru\n a.ru \n", encoding="utf-8")
            self.assertEqual(read_list(path), ["b.ru", "a.ru"])


if __name__ == "__main__":
    unittest.main()
