# pylint: disable=missing-module-docstring, missing-function-docstring
from app.services.search_correction import correct_query


def test_corrects_misspelled_word():
    assert correct_query('jurrasic') == 'jurassic'


def test_corrects_within_phrase():
    assert correct_query('jurrasic park') == 'jurassic park'


def test_returns_none_when_already_correct():
    assert correct_query('jurassic') is None
    assert correct_query('the matrix') is None


def test_unknown_words_pass_through():
    # Proper nouns the dictionary can't fix don't block the phrase.
    result = correct_query('tarantino filmz')
    assert result is None or 'tarantino' in result


def test_empty_query():
    assert correct_query('') is None
    assert correct_query('   ') is None
