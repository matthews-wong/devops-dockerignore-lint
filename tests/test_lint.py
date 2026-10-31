import tempfile
import unittest
from pathlib import Path

from dockerignorelint import (BLOATED_CONTEXT, ERROR, LEAKED_SECRET, MISSING_FILE,
                              WARNING, copies_whole_context, lint, main)

ROOT = Path(__file__).resolve().parent.parent
COPY_ALL = "FROM alpine:3.20\nCOPY . /app\n"
COPY_SRC = "FROM alpine:3.20\nCOPY src/ /app\n"


class CopiesWholeContextTest(unittest.TestCase):
    def test_dot_source(self):
        self.assertTrue(copies_whole_context(COPY_ALL))
        self.assertTrue(copies_whole_context("ADD ./ /app"))

    def test_flags_are_not_sources(self):
        self.assertTrue(copies_whole_context("COPY --chown=1000:1000 . /app"))

    def test_named_paths_and_other_stages_are_not_broad(self):
        self.assertFalse(copies_whole_context(COPY_SRC))
        self.assertFalse(copies_whole_context("COPY --from=build . /app"))

    def test_line_continuation(self):
        self.assertTrue(copies_whole_context("COPY \\\n  . /app"))


class LintTest(unittest.TestCase):
    def codes(self, ignore, dockerfile=COPY_ALL):
        return {f.code for f in lint(ignore, dockerfile)}

    def test_missing_file_is_error_when_context_is_copied(self):
        (finding,) = lint(None, COPY_ALL)
        self.assertEqual((finding.code, finding.severity), (MISSING_FILE, ERROR))

    def test_missing_file_is_warning_for_narrow_copy(self):
        (finding,) = lint(None, COPY_SRC)
        self.assertEqual((finding.code, finding.severity), (MISSING_FILE, WARNING))

    def test_empty_file_leaks_everything(self):
        self.assertEqual(self.codes(""), {LEAKED_SECRET, BLOATED_CONTEXT})

    def test_negation_that_reincludes_a_secret_is_reported(self):
        ignore = (ROOT / "examples/good/.dockerignore").read_text() + "!.env\n"
        findings = lint(ignore, COPY_ALL)
        self.assertEqual([f.message.split()[0] for f in findings], [".env"])

    def test_good_example_is_clean(self):
        self.assertEqual(lint((ROOT / "examples/good/.dockerignore").read_text(), COPY_ALL), [])


class MainTest(unittest.TestCase):
    def test_exit_codes(self):
        self.assertEqual(main([str(ROOT / "examples/good")]), 0)
        self.assertEqual(main([str(ROOT / "examples/leaky")]), 1)

    def test_missing_dockerfile_is_usage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(main([tmp]), 2)


if __name__ == "__main__":
    unittest.main()
