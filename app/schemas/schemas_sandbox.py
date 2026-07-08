"""
This module contains Pydantic schemas for Sandbox entities.
"""

# pylint: disable=missing-class-docstring

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# --- Countries ---
class CountryBase(BaseModel):
    title: str
    country_code: str


class CountryCreate(CountryBase):
    pass


class CountryUpdate(BaseModel):
    title: Optional[str] = None
    country_code: Optional[str] = None


class CountryResponse(CountryBase):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserCountryBase(BaseModel):
    rank: Optional[int] = None
    completed: Optional[int] = None
    notes: Optional[str] = None
    first_visited: Optional[datetime] = None


class UserCountryCreate(UserCountryBase):
    pass


class UserCountryUpdate(UserCountryBase):
    pass


class UserCountryResponse(UserCountryBase):
    id: str
    country: CountryResponse
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Movies ---
class MovieBase(BaseModel):
    title: str
    imdb: str
    release_date: Optional[datetime] = None
    rating_imdb: Optional[float] = None
    runtime: Optional[int] = None
    language: Optional[str] = None
    rated: Optional[str] = None
    poster_url: Optional[str] = None


class MovieCreate(MovieBase):
    pass


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    imdb: Optional[str] = None
    release_date: Optional[datetime] = None
    rating_imdb: Optional[float] = None
    runtime: Optional[int] = None
    language: Optional[str] = None
    rated: Optional[str] = None
    poster_url: Optional[str] = None


class MovieResponse(MovieBase):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MovieSearchResult(BaseModel):
    imdb: str
    title: str
    year: Optional[str] = None
    poster_url: Optional[str] = None
    type: Optional[str] = None


class UserMovieBase(BaseModel):
    on_watchlist: Optional[bool] = None
    on_rankings: Optional[bool] = None
    rank: Optional[int] = None
    completed: Optional[int] = None
    notes: Optional[str] = None


class UserMovieCreate(UserMovieBase):
    pass


class UserMovieUpdate(UserMovieBase):
    pass


class UserMovieResponse(UserMovieBase):
    id: str
    movie: MovieResponse
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RankingReorder(BaseModel):
    """Ordered list of movie (catalog) ids defining the new ranking order."""

    movie_ids: List[str]


class RankPlacement(BaseModel):
    """Target 1-based position at which to place a movie in the ranked list."""

    position: int


# --- TV Shows ---
class TVShowBase(BaseModel):
    title: str
    imdb: Optional[str] = None
    tvmaze: Optional[int] = None
    status: Optional[str] = None
    poster_url: Optional[str] = None


class TVShowCreate(TVShowBase):
    pass


class TVShowUpdate(BaseModel):
    title: Optional[str] = None
    imdb: Optional[str] = None
    tvmaze: Optional[int] = None
    status: Optional[str] = None
    poster_url: Optional[str] = None


class TVShowResponse(TVShowBase):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserTVShowBase(BaseModel):
    rank: Optional[int] = None
    status: Optional[str] = None
    freeze: Optional[int] = 0


class UserTVShowCreate(UserTVShowBase):
    pass


class UserTVShowUpdate(UserTVShowBase):
    pass


class UserTVShowResponse(UserTVShowBase):
    id: str
    tv_show: TVShowResponse
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- TV Episodes ---
class TVEpisodeBase(BaseModel):
    title: str
    tvmaze: Optional[int] = None
    airdate: Optional[datetime] = None
    season: Optional[int] = None
    season_number: Optional[int] = None


class TVEpisodeCreate(TVEpisodeBase):
    pass


class TVEpisodeUpdate(BaseModel):
    title: Optional[str] = None
    tvmaze: Optional[int] = None
    airdate: Optional[datetime] = None
    season: Optional[int] = None
    season_number: Optional[int] = None


class TVEpisodeResponse(TVEpisodeBase):
    id: str
    tv_show_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserTVEpisodeBase(BaseModel):
    watched: Optional[int] = 0


class UserTVEpisodeCreate(UserTVEpisodeBase):
    pass


class UserTVEpisodeUpdate(UserTVEpisodeBase):
    pass


class UserTVEpisodeResponse(UserTVEpisodeBase):
    id: str
    episode: TVEpisodeResponse
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Video Games ---
class VideoGameBase(BaseModel):
    title: str
    igdb: Optional[int] = None
    poster_url: Optional[str] = None
    release_date: Optional[datetime] = None
    rating: Optional[float] = None
    time_to_beat: Optional[int] = None
    igdb_last_update: Optional[datetime] = None
    slug: Optional[str] = None


class VideoGameCreate(VideoGameBase):
    pass


class VideoGameUpdate(BaseModel):
    title: Optional[str] = None
    igdb: Optional[int] = None
    poster_url: Optional[str] = None
    release_date: Optional[datetime] = None
    rating: Optional[float] = None
    time_to_beat: Optional[int] = None
    igdb_last_update: Optional[datetime] = None
    slug: Optional[str] = None


class VideoGameResponse(VideoGameBase):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserVideoGameBase(BaseModel):
    rank: Optional[int] = None
    completed: Optional[int] = None
    notes: Optional[str] = None
    is_100_percent: Optional[bool] = False


class UserVideoGameCreate(UserVideoGameBase):
    pass


class UserVideoGameUpdate(UserVideoGameBase):
    pass


class UserVideoGameResponse(UserVideoGameBase):
    id: str
    game: VideoGameResponse
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Books ---
class BookBase(BaseModel):
    title: str
    isbn: Optional[str] = None
    googleid: Optional[str] = None
    poster_url: Optional[str] = None


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    isbn: Optional[str] = None
    googleid: Optional[str] = None
    poster_url: Optional[str] = None


class BookResponse(BookBase):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserBookBase(BaseModel):
    rank: Optional[int] = None
    completed: Optional[int] = None
    notes: Optional[str] = None


class UserBookCreate(UserBookBase):
    pass


class UserBookUpdate(UserBookBase):
    pass


class UserBookResponse(UserBookBase):
    id: str
    book: BookResponse
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
