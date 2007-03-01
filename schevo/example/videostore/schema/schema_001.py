"""Schema for movie rental."""

from schevo.schema import *
schevo.schema.prep(locals())


class SchevoIcon(E.Entity):

    _hidden = True

    name = f.unicode()
    data = f.image()

    _key(name)


def on_open(db):
    """Routine that gets called each time the database is opened."""
    pass


class Actor(E.Entity):

    name = f.unicode()
    
    _key(name)

    def x_movies(self):
        return [casting.movie for casting in self.m.movie_castings()]


class Director(E.Entity):

    name = f.unicode()
    
    _key(name)


class Movie(E.Entity):

    title = f.unicode()
    description = f.memo()
    release_date = f.date()
    director = f.entity('Director')

    _key(title)

    def x_actors(self):
        return [casting.actor for casting in self.m.movie_castings()]


class MovieCasting(E.Entity):

    movie = f.entity('Movie', CASCADE)
    actor = f.entity('Actor')

    _key(movie, actor)

    def __unicode__(self):
        return u'%s :: %s' % (self.movie, self.actor)


    
