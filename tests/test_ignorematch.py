import unittest

from ignorematch import is_ignored, parse


def ignored(patterns: str, path: str) -> bool:
    return is_ignored(path, parse(patterns))


class IgnoreMatchTest(unittest.TestCase):
    def test_comments_and_blank_lines_are_skipped(self):
        self.assertFalse(ignored("# .env\n\n", ".env"))

    def test_exact_name(self):
        self.assertTrue(ignored(".env", ".env"))
        self.assertFalse(ignored(".env", ".env.local"))

    def test_pattern_is_anchored_to_the_context_root(self):
        self.assertFalse(ignored(".env", "app/.env"))
        self.assertTrue(ignored("**/.env", "app/.env"))
        self.assertTrue(ignored("**/.env", ".env"))

    def test_star_does_not_cross_directories(self):
        self.assertTrue(ignored("*.pem", "server.pem"))
        self.assertFalse(ignored("*.pem", "certs/server.pem"))

    def test_directory_pattern_covers_children(self):
        self.assertTrue(ignored("node_modules", "node_modules/a/b.js"))
        self.assertTrue(ignored("node_modules/", "node_modules/a/b.js"))

    def test_leading_slash_is_stripped(self):
        self.assertTrue(ignored("/.git", ".git/config"))

    def test_last_match_wins(self):
        self.assertFalse(ignored(".env*\n!.env.example", ".env.example"))
        self.assertTrue(ignored("!.env.example\n.env*", ".env.example"))

    def test_question_mark_and_class(self):
        self.assertTrue(ignored("id_?sa", "id_rsa"))
        self.assertTrue(ignored("log[0-9]", "log7"))
        self.assertFalse(ignored("log[^0-9]", "log7"))

    def test_regex_metacharacters_are_literal(self):
        self.assertFalse(ignored("a.b", "axb"))
        self.assertFalse(ignored("a+b", "aab"))


if __name__ == "__main__":
    unittest.main()
