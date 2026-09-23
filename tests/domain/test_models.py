import unittest

from searcher.domain import DomainName


class DomainNameTests(unittest.TestCase):
    def test_normalizes_case(self) -> None:
        domain = DomainName("mail.Google.com ")

        self.assertEqual(domain.value, "mail.google.com")
        self.assertEqual(str(domain), "mail.google.com")

    def test_recognizes_subdomains(self) -> None:
        parent = DomainName("google.com")

        sub1 = DomainName("mail.google.com")
        sub2 = DomainName("api.v1.google.com")
        sub3 = DomainName("yandex.ru")

        self.assertTrue(sub1.is_subdomain_of(parent))
        self.assertTrue(sub2.is_subdomain_of(parent))
        self.assertFalse(sub3.is_subdomain_of(parent))

    def test_converts_to_ascii_idna(self) -> None:
        domain = DomainName("почта.рф")

        self.assertEqual(domain.value, "xn--80a1acny.xn--p1ai")

    def test_detect_invalid_domains(self) -> None:
        invalid_domains = [
            "",
            ".",
            "google..com",
            "google-.com",
            "google_google.com",
            "*.google.com",
            f"{'a' * 64}.google.com",
        ]

        for domain in invalid_domains:
            with self.subTest(domain=domain), self.assertRaises(ValueError):
                DomainName(domain)


if __name__ == "__main__":
    unittest.main()
