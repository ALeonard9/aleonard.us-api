"""
This module defines the database models for the Sandbox entities.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.db.models import DBBaseModel


class DbCountry(DBBaseModel):
    __tablename__ = 'countries'

    title = Column(String(255))
    country_code = Column(String(4), unique=True)

    user_countries = relationship('DbUserCountry', back_populates='country')


class DbUserCountry(DBBaseModel):
    __tablename__ = 'user_countries'

    country_id = Column(Integer, ForeignKey('countries.pk'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.pk'), nullable=False)

    rank = Column(Integer, nullable=True)
    completed = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    first_visited = Column(DateTime, nullable=True)

    country = relationship('DbCountry', back_populates='user_countries')
    user = relationship('DbUser', backref='user_countries')


class DbMovie(DBBaseModel):
    __tablename__ = 'movies'

    title = Column(String(255))
    imdb = Column(String(40), unique=True)
    release_date = Column(DateTime, nullable=True)
    rating_imdb = Column(Float, nullable=True)
    runtime = Column(Integer, nullable=True)
    language = Column(String(40), nullable=True)
    rated = Column(String(11), nullable=True)
    poster_url = Column(String(500), nullable=True)

    user_movies = relationship('DbUserMovie', back_populates='movie')


class DbUserMovie(DBBaseModel):
    __tablename__ = 'user_movies'

    movie_id = Column(Integer, ForeignKey('movies.pk'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.pk'), nullable=False)

    rank = Column(Integer, nullable=True)
    completed = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    movie = relationship('DbMovie', back_populates='user_movies')
    user = relationship('DbUser', backref='user_movies')


class DbTVShow(DBBaseModel):
    __tablename__ = 'tv_shows'

    title = Column(String(254), nullable=False)
    imdb = Column(String(254), unique=True, nullable=True)
    tvmaze = Column(Integer, nullable=True)
    status = Column(String(254), nullable=True)
    poster_url = Column(String(254), nullable=True)

    user_tv_shows = relationship('DbUserTVShow', back_populates='tv_show')
    episodes = relationship('DbTVEpisode', back_populates='tv_show')


class DbUserTVShow(DBBaseModel):
    __tablename__ = 'user_tv_shows'

    tv_show_id = Column(Integer, ForeignKey('tv_shows.pk'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.pk'), nullable=False)

    rank = Column(Integer, nullable=True)
    status = Column(String(254), nullable=True)
    freeze = Column(Integer, default=0)

    tv_show = relationship('DbTVShow', back_populates='user_tv_shows')
    user = relationship('DbUser', backref='user_tv_shows')


class DbTVEpisode(DBBaseModel):
    __tablename__ = 'tv_episodes'

    title = Column(String(254), nullable=False)
    tvmaze = Column(Integer, unique=True, nullable=True)
    tv_show_id = Column(Integer, ForeignKey('tv_shows.pk'), nullable=False)

    airdate = Column(DateTime, nullable=True)
    season = Column(Integer, nullable=True)
    season_number = Column(Integer, nullable=True)

    tv_show = relationship('DbTVShow', back_populates='episodes')
    user_episodes = relationship('DbUserTVEpisode', back_populates='episode')


class DbUserTVEpisode(DBBaseModel):
    __tablename__ = 'user_tv_episodes'

    episode_id = Column(Integer, ForeignKey('tv_episodes.pk'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.pk'), nullable=False)

    watched = Column(Integer, default=0)

    episode = relationship('DbTVEpisode', back_populates='user_episodes')
    user = relationship('DbUser', backref='user_tv_episodes')


class DbVideoGame(DBBaseModel):
    __tablename__ = 'video_games'

    title = Column(String(255))
    igdb = Column(Integer, unique=True, nullable=True)
    poster_url = Column(String(100), nullable=True)
    release_date = Column(DateTime, nullable=True)
    rating = Column(Float, nullable=True)
    time_to_beat = Column(Integer, nullable=True)
    igdb_last_update = Column(DateTime, nullable=True)
    slug = Column(String(255), nullable=True)

    user_games = relationship('DbUserVideoGame', back_populates='game')


class DbUserVideoGame(DBBaseModel):
    __tablename__ = 'user_video_games'

    game_id = Column(Integer, ForeignKey('video_games.pk'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.pk'), nullable=False)

    rank = Column(Integer, nullable=True)
    completed = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    is_100_percent = Column(Boolean, default=False)

    game = relationship('DbVideoGame', back_populates='user_games')
    user = relationship('DbUser', backref='user_video_games')


class DbBook(DBBaseModel):
    __tablename__ = 'books'

    title = Column(String(254), nullable=False)
    isbn = Column(String(20), nullable=True)
    googleid = Column(String(254), nullable=True)
    poster_url = Column(String(254), nullable=True)

    user_books = relationship('DbUserBook', back_populates='book')


class DbUserBook(DBBaseModel):
    __tablename__ = 'user_books'

    book_id = Column(Integer, ForeignKey('books.pk'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.pk'), nullable=False)

    rank = Column(Integer, nullable=True)
    completed = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    book = relationship('DbBook', back_populates='user_books')
    user = relationship('DbUser', backref='user_books')
