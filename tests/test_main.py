from unittest.mock import patch

import pytest

import main


def test_filter_ignores_summary_matches():
    assert not main.check_logic_strictly(
        "A faster decoder for large models",
        "This paper applies speculative decoding to vision-language generation.",
    )


@pytest.mark.parametrize(
    ("title", "summary"),
    [
        (
            "SpecVLM: Enhancing Speculative Decoding of Video LLMs via "
            "Verifier-Guided Token Pruning",
            "",
        ),
        (
            "See the Forest for the Trees: Loosely Speculative Decoding via "
            "Visual-Semantic Guidance for Efficient Inference of Video LLMs",
            "",
        ),
        (
            "HIPPO: Accelerating Video Large Language Models Inference via "
            "Holistic-aware Parallel Speculative Decoding",
            "",
        ),
        (
            "ParallelVLM: Lossless Video-LLM Acceleration with Visual Alignment "
            "Aware Parallel Speculative Decoding",
            "",
        ),
        (
            "Sparrow: Text-Anchored Window Attention with Visual-Semantic "
            "Glimpsing for Speculative Decoding in Video LLMs",
            "",
        ),
    ],
)
def test_filter_accepts_video_speculative_decoding_papers(title, summary):
    assert main.check_logic_strictly(title, summary)
    assert main.is_video_paper(title)


def test_sparse_to_dense_is_left_for_manual_curation():
    assert not main.check_logic_strictly(
        "Sparse-to-Dense: A Free Lunch for Lossless Acceleration of Video "
        "Understanding in LLMs",
        "The fast sparse model speculatively decodes multiple tokens, while "
        "the slow dense model verifies them in parallel.",
    )


def test_filter_rejects_text_only_speculative_decoding():
    assert not main.check_logic_strictly(
        "Fast Speculative Decoding for Large Language Models"
    )


def test_filter_rejects_non_llm_video_generation():
    assert not main.check_logic_strictly(
        "Speculative Decoding for Autoregressive Video Generation"
    )


def test_filter_excludes_vla_acronym():
    assert not main.check_logic_strictly(
        "Speculative decoding for VLA models",
        "A multimodal acceleration method.",
    )


def test_filter_excludes_vision_language_action_variants():
    assert not main.check_logic_strictly(
        "Speculative decoding for vision language action models",
        "A multimodal acceleration method.",
    )


def test_search_query_includes_video_and_speculative_decoding():
    query = main.build_search_query()

    assert 'all:"video"' in query
    assert 'all:"speculative decoding"' in query


def test_update_readme_returns_when_markers_are_missing(tmp_path):
    readme = tmp_path / "README.md"
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

    assert readme.read_text(encoding="utf-8") == original_content


def test_update_readme_routes_video_papers_to_the_video_table(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Paper list\n"
        f"{main.START_MARKER}\n"
        "| Date | Title |\n"
        "|:---:|:---|\n"
        f"{main.END_MARKER}\n"
        f"{main.VIDEO_START_MARKER}\n"
        "| Date | Title |\n"
        "|:---:|:---|\n"
        f"{main.VIDEO_END_MARKER}\n",
        encoding="utf-8",
    )
    papers = [
        {
            "date": "2026-01-02",
            "title": "Speculative Decoding for Vision-Language Models",
            "link": "http://arxiv.org/abs/2601.00002v1",
            "id": "http://arxiv.org/abs/2601.00002v1",
        },
        {
            "date": "2026-01-01",
            "title": "Speculative Decoding for Video LLMs",
            "link": "http://arxiv.org/abs/2601.00001v1",
            "id": "http://arxiv.org/abs/2601.00001v1",
        },
    ]

    with patch.object(main, "README_FILE", str(readme)), patch.object(
        main, "fetch_arxiv_papers", return_value=papers
    ):
        main.update_readme()

    content = readme.read_text(encoding="utf-8")
    multimodal_block = content.split(main.START_MARKER, 1)[1].split(
        main.END_MARKER, 1
    )[0]
    video_block = content.split(main.VIDEO_START_MARKER, 1)[1].split(
        main.VIDEO_END_MARKER, 1
    )[0]

    assert "2601.00002v1" in multimodal_block
    assert "2601.00001v1" not in multimodal_block
    assert "2601.00001v1" in video_block
    assert "2601.00002v1" not in video_block
