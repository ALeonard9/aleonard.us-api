# pylint: disable=missing-module-docstring, missing-function-docstring
# pylint: disable=protected-access, missing-class-docstring
from unittest.mock import MagicMock, patch

from app.services import book_search


def test_helpers():
    assert book_search._cover(11481354) == (
        'https://covers.openlibrary.org/b/id/11481354-L.jpg'
    )
    assert book_search._cover(None) is None
    assert book_search._authors({'author_name': ['Frank Herbert']}) == 'Frank Herbert'
    assert book_search._authors({}) is None
    # ISBN-13 preferred over ISBN-10 regardless of order.
    assert (
        book_search._pick_isbn({'isbn': ['0441172717', '9780441172719']})
        == '9780441172719'
    )
    assert book_search._pick_isbn({'isbn': ['0441172717']}) == '0441172717'
    assert book_search._pick_isbn({}) is None
    assert book_search._genre({'subject': ['Sci-fi', 'Deserts', 'Spice', 'Worms']}) == (
        'Sci-fi, Deserts, Spice'
    )


def test_apply_detail_truncates_and_skips_none():
    class Book:
        authors = None
        genre = None
        description = None

    b = Book()
    book_search.apply_detail_to_book(
        b, {'authors': 'x' * 999, 'genre': 'Fiction', 'description': None}
    )
    assert len(b.authors) == 512  # truncated to column limit
    assert b.genre == 'Fiction'
    assert b.description is None  # None values are skipped


@patch('app.services.book_search._work_description', return_value='A desert planet.')
@patch('app.services.book_search.requests.get')
def test_get_book_detail_maps_fields(mock_get, mock_desc):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        'docs': [
            {
                'key': '/works/OL893415W',
                'title': 'Dune',
                'author_name': ['Frank Herbert'],
                'first_publish_year': 1965,
                'number_of_pages_median': 592,
                'subject': ['Science fiction', 'Deserts'],
                'ratings_average': 4.2345,
                'language': ['eng', 'fre'],
                'cover_i': 11481354,
            }
        ]
    }
    mock_get.return_value = resp

    detail = book_search.get_book_detail('978-0441172719')
    assert detail['title'] == 'Dune'
    assert detail['isbn'] == '9780441172719'  # dashes stripped
    assert detail['authors'] == 'Frank Herbert'
    assert detail['year'] == 1965
    assert detail['genre'] == 'Science fiction, Deserts'
    assert detail['description'] == 'A desert planet.'
    assert detail['page_count'] == 592
    assert detail['rating'] == 4.23
    assert detail['language'] == 'eng'
    assert detail['poster_url'] == 'https://covers.openlibrary.org/b/id/11481354-L.jpg'
    mock_desc.assert_called_once_with('/works/OL893415W')


def test_get_book_detail_without_isbn_returns_none():
    assert book_search.get_book_detail(None) is None
    assert book_search.get_book_detail('') is None


def test_work_description_unwraps_dict():
    with patch('app.services.book_search.requests.get') as mock_get:
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {'description': {'value': 'Nested text.'}}
        mock_get.return_value = resp
        assert book_search._work_description('/works/OL1W') == 'Nested text.'
    assert book_search._work_description(None) is None


_BIBKEYS_PAYLOAD = {
    'ISBN:9780441172719': {
        'title': 'Dune',
        'authors': [{'name': 'Frank Herbert'}],
        'publish_date': 'August 3, 1990',
        'identifiers': {
            'isbn_10': ['0441172717'],
            'isbn_13': ['9780441172719'],
        },
        'cover': {
            'small': 'https://covers.openlibrary.org/b/id/1-S.jpg',
            'medium': 'https://covers.openlibrary.org/b/id/1-M.jpg',
            'large': 'https://covers.openlibrary.org/b/id/1-L.jpg',
        },
    }
}


@patch('app.services.book_search.requests.get')
def test_search_books_hyphenated_isbn_resolves_via_bibkeys(mock_get):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = _BIBKEYS_PAYLOAD
    mock_get.return_value = resp

    results = book_search.search_books('978-0-441-17271-9')

    assert results == [
        {
            'isbn': '9780441172719',
            'title': 'Dune',
            'authors': 'Frank Herbert',
            'year': '1990',
            'poster_url': 'https://covers.openlibrary.org/b/id/1-L.jpg',
        }
    ]
    args, kwargs = mock_get.call_args
    assert args[0] == 'https://openlibrary.org/api/books'
    assert kwargs['params']['bibkeys'] == 'ISBN:9780441172719'


@patch('app.services.book_search.requests.get')
def test_search_books_bare_isbn_resolves_via_bibkeys(mock_get):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = _BIBKEYS_PAYLOAD
    mock_get.return_value = resp

    results = book_search.search_books('9780441172719')

    assert len(results) == 1
    assert results[0]['isbn'] == '9780441172719'
    assert results[0]['title'] == 'Dune'


@patch('app.services.book_search.requests.get')
def test_search_books_unknown_isbn_returns_empty_list(mock_get):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {}
    mock_get.return_value = resp

    assert not book_search.search_books('0000000000')


@patch('app.services.book_search.requests.get')
def test_search_books_title_query_unaffected(mock_get):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        'docs': [
            {
                'title': 'Dune',
                'author_name': ['Frank Herbert'],
                'first_publish_year': 1965,
                'isbn': ['9780441172719'],
                'cover_i': 11481354,
            }
        ]
    }
    mock_get.return_value = resp

    results = book_search.search_books('Dune')

    assert results == [
        {
            'isbn': '9780441172719',
            'title': 'Dune',
            'authors': 'Frank Herbert',
            'year': '1965',
            'poster_url': 'https://covers.openlibrary.org/b/id/11481354-L.jpg',
        }
    ]
    args, kwargs = mock_get.call_args
    assert args[0] == 'https://openlibrary.org/search.json'
    assert kwargs['params']['q'] == 'Dune'
