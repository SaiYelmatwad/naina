from app.matching.embeddings import TfidfEmbeddingProvider
from app.matching.scorer import score_role


def test_tfidf_similarity_identical_text_is_high():
    provider = TfidfEmbeddingProvider()
    sim = provider.similarity("python distributed systems", "python distributed systems")
    assert sim > 0.9


def test_tfidf_similarity_unrelated_text_is_low():
    provider = TfidfEmbeddingProvider()
    sim = provider.similarity("python backend engineer", "watercolor painting techniques")
    assert sim < 0.3


def test_score_role_ranks_strong_skills_first():
    skills = [
        {"name": "python", "level": 0.95},
        {"name": "kubernetes", "level": 0.1},
    ]
    result = score_role("python and kubernetes required for this role", skills)
    assert result.score > 0
    matched_names = [m.skill for m in result.matched]
    gap_names = [g.skill for g in result.gaps]
    assert "python" in matched_names
    assert "kubernetes" in gap_names


def test_score_role_handles_empty_profile():
    result = score_role("any role text here", [])
    assert result.score == 20
    assert result.matched == []
