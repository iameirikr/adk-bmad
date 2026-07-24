from adk_bmad.tools import complexity


def test_simple_story_scores_low_and_is_standard_tier():
    text = "Add a button that shows a greeting message when clicked."
    score = complexity.score_story_text(text)
    assert score < 4
    assert complexity.tier_for_score(score) == "standard"


def test_story_with_auth_and_external_api_scores_high_and_is_heavy_tier():
    text = """
    Implement a login flow using JWT and SSO, integrating with a third-party
    API (Stripe) for billing, with a background job queue for event-driven
    processing.
    """
    score = complexity.score_story_text(text)
    assert score >= 4
    assert complexity.tier_for_score(score) == "heavy"
    matched = complexity.matched_rules(text)
    assert "auth" in matched
    assert "external_api" in matched
    assert "async_processing" in matched


def test_long_story_with_many_acceptance_criteria_gets_structural_bonus():
    ac_lines = "\n".join(f"{i}. Given X, when Y, then Z." for i in range(1, 12))
    short_text = f"## Acceptance Criteria\n\n{ac_lines}\n"
    long_text = short_text + " word" * 500

    assert complexity.score_story_text(long_text) > complexity.score_story_text(short_text)


def test_tier_threshold_is_configurable():
    assert complexity.tier_for_score(3, threshold=3) == "heavy"
    assert complexity.tier_for_score(2, threshold=3) == "standard"
