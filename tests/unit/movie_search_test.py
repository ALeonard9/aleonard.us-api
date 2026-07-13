# pylint: disable=missing-module-docstring, missing-function-docstring
# pylint: disable=protected-access, missing-class-docstring
from unittest.mock import MagicMock, patch

from app.config import Settings
from app.services import movie_search


def test_na_and_parsers():
    assert movie_search._na('N/A') is None
    assert movie_search._na('') is None
    assert movie_search._na('Drama') == 'Drama'
    assert movie_search._to_int('2002') == 2002
    assert movie_search._to_int('113 min') == 113
    assert movie_search._to_int('N/A') is None
    assert movie_search._to_float('8.6') == 8.6
    assert movie_search._to_float('N/A') is None


def test_apply_detail_truncates_and_skips_none():
    class Movie:  # simple stand-in
        director = None
        genre = None
        plot = None

    m = Movie()
    movie_search.apply_detail_to_movie(
        m, {'director': 'x' * 999, 'genre': 'Sci-Fi', 'plot': None}
    )
    assert len(m.director) == 512  # truncated to column limit
    assert m.genre == 'Sci-Fi'
    assert m.plot is None  # None values are skipped


@patch('app.services.movie_search.get_settings')
@patch('app.services.movie_search.requests.get')
def test_get_movie_detail_maps_fields(mock_get, mock_settings):
    mock_settings.return_value = Settings(omdb_api_key='k', env='github')
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        'Response': 'True',
        'Title': 'The Matrix',
        'Year': '1999',
        'Runtime': '136 min',
        'Genre': 'Action, Sci-Fi',
        'Director': 'Lana Wachowski, Lilly Wachowski',
        'Actors': 'Keanu Reeves, Laurence Fishburne',
        'Plot': 'A hacker learns the truth.',
        'imdbRating': '8.7',
        'Poster': 'https://x/p.jpg',
    }
    mock_get.return_value = resp

    detail = movie_search.get_movie_detail('tt0133093')
    assert detail['year'] == 1999
    assert detail['runtime'] == 136
    assert detail['genre'] == 'Action, Sci-Fi'
    assert detail['director'].startswith('Lana')
    assert detail['rating_imdb'] == 8.7


@patch('app.services.movie_search.get_settings')
def test_get_movie_detail_unconfigured_returns_none(mock_settings):
    mock_settings.return_value = Settings(omdb_api_key=None, env='github')
    assert movie_search.get_movie_detail('tt1') is None
