import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import main


class PaperFilterTests(unittest.TestCase):
    def test_filter_ignores_summary_matches(self):
        self.assertFalse(
            main.check_logic_strictly(
                "A faster decoder for large models",
                "This paper applies speculative decoding to vision-language generation.",
            )
        )

    def test_filter_excludes_vla_acronym(self):
        self.assertFalse(
            main.check_logic_strictly(
                "Speculative decoding for VLA models",
                "A multimodal acceleration method.",
            )
        )

    def test_filter_excludes_vision_language_action_variants(self):
        self.assertFalse(
            main.check_logic_strictly(
                "Speculative decoding for vision language action models",
                "A multimodal acceleration method.",
            )
        )


class ReadmeUpdateTests(unittest.TestCase):
    def test_update_readme_returns_when_markers_are_missing(self):
        with TemporaryDirectory() as temp_dir:
            readme = Path(temp_dir) / "README.md"
            original_content = "# Paper list\n"
            readme.write_text(original_content, encoding="utf-8")

            paper = {
                "date": "2026-01-01",
                "title": "Speculative Decoding for Vision-Language Models",
                "link": "http://arxiv.org/abs/2601.00001v1",
                "id": "http://arxiv.org/abs/2601.00001v1",
            }

            with patch.object(main, "README_FILE", str(readme)), patch.object(
                main, "fetch_arxiv_papers", return_value=[paper]
            ):
                main.update_readme()

            self.assertEqual(readme.read_text(encoding="utf-8"), original_content)


if __name__ == "__main__":
    unittest.main()
