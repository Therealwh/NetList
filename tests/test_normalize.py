import unittest

from scripts.netlist_data.normalize import (
    normalize_cidr,
    normalize_domain,
    normalize_ip,
    slugify,
)


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


class DomainTest(unittest.TestCase):
    def test_plain_and_case(self):
        self.assertEqual(normalize_domain("Example.COM"), "example.com")

    def test_strips_scheme_path_port_userinfo(self):
        self.assertEqual(normalize_domain("https://vk.com:443/feed?x=1"), "vk.com")
        self.assertEqual(normalize_domain("http://user@example.com"), "example.com")

    def test_trailing_dot(self):
        self.assertEqual(normalize_domain("ya.ru."), "ya.ru")

    def test_idn_to_punycode(self):
        converted = normalize_domain("кто.рф")
        self.assertIsNotNone(converted)
        self.assertTrue(all(p.startswith("xn--") for p in converted.split(".")))

    def test_rejects_invalid(self):
        for bad in ("", "*", "*.example.com", "localhost", "example",
                    "bad site.com", "http://", "-bad-.example.com"):
            self.assertIsNone(normalize_domain(bad), repr(bad))


class IpTest(unittest.TestCase):
    def test_ipv4(self):
        self.assertEqual(normalize_ip("8.8.8.8"), "8.8.8.8")
        self.assertIsNone(normalize_ip("999.1.1.1"))
        self.assertIsNone(normalize_ip("not-an-ip"))

    def test_ipv6_compressed(self):
        self.assertEqual(normalize_ip("2001:0db8:0000:0000:0000:0000:0000:0001"), "2001:db8::1")

    def test_cidr(self):
        self.assertEqual(normalize_cidr("1.2.3.4/24"), ("1.2.3.0/24", 4))
        self.assertEqual(normalize_cidr("2001:db8::/32"), ("2001:db8::/32", 6))
        # одиночный IP не CIDR: в cidr-файл не превращается
        self.assertIsNone(normalize_cidr("8.8.8.8"))
        self.assertIsNone(normalize_cidr("1.2.3.4/33"))


if __name__ == "__main__":
    unittest.main()
