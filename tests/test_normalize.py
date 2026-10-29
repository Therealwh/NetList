import unittest

from scripts.netlist_data.normalize import slugify


class SlugifyTest(unittest.TestCase):
    def test_transliterates_cyrillic(self):
        self.assertEqual(slugify("Яндекс"), "yandex")
        self.assertEqual(slugify("Одноклассники"), "odnoklassniki")
        self.assertEqual(slugify("Дзен"), "dzen")
        self.assertEqual(slugify("Рамблер"), "rambler")

    def test_digits_and_mixed(self):
        self.assertEqual(slugify("2ГИС"), "2gis")
        self.assertEqual(slugify("1С"), "1c")
        self.assertEqual(slugify("Т2"), "t2")

    def test_ascii_names(self):
        self.assertEqual(slugify("Last.fm"), "last-fm")
        self.assertEqual(slugify("HDRezka"), "hdrezka")
        self.assertEqual(slugify("1337x"), "1337x")
        self.assertEqual(slugify("Yandex Cloud"), "yandex-cloud")

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            slugify("   ")


if __name__ == "__main__":
    unittest.main()
