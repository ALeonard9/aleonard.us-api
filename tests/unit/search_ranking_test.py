# pylint: disable=missing-module-docstring, missing-function-docstring
from app.services.search_ranking import rank_and_cap


def test_exact_match_beats_partial_matches():
    hits = [
        {'title': 'Titanic II'},
        {'title': 'Titanic'},
        {'title': 'Raise the Titanic'},
    ]
    ranked = rank_and_cap('Titanic', hits)
    assert ranked[0]['title'] == 'Titanic'


def test_starts_with_beats_contains():
    hits = [
        {'title': 'The Legend of Zelda: Anniversary Edition'},
        {'title': 'Zelda II: The Adventure of Link'},
    ]
    ranked = rank_and_cap('Zelda', hits)
    assert ranked[0]['title'] == 'Zelda II: The Adventure of Link'


def test_match_is_case_and_punctuation_insensitive():
    hits = [{'title': 'Spider-Man'}]
    ranked = rank_and_cap('spider man', hits)
    assert ranked[0]['title'] == 'Spider-Man'


def test_ties_preserve_provider_order():
    # Same tier (both "contains") for every item, so the provider's own
    # relevance/popularity order should be the tiebreaker and survive
    # unchanged.
    hits = [
        {'title': 'Something Else Entirely'},
        {'title': 'A Whole New World'},
        {'title': 'Yet Another Unrelated Title'},
    ]
    ranked = rank_and_cap('e', hits)
    assert [r['title'] for r in ranked] == [r['title'] for r in hits]


def test_caps_to_limit():
    hits = [{'title': f'Match {i}'} for i in range(10)]
    ranked = rank_and_cap('Match', hits)
    assert len(ranked) == 5


def test_caps_to_custom_limit():
    hits = [{'title': f'Match {i}'} for i in range(10)]
    ranked = rank_and_cap('Match', hits, limit=3)
    assert len(ranked) == 3


def test_empty_results():
    assert rank_and_cap('anything', []) == []


def test_missing_title_does_not_crash():
    hits = [{'imdb': 'tt1'}, {'title': 'Real Title', 'imdb': 'tt2'}]
    ranked = rank_and_cap('Real Title', hits)
    assert ranked[0]['title'] == 'Real Title'
