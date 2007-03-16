"""Schema for VideoStore."""

from schevo.schema import *
schevo.schema.prep(locals())


class SchevoIcon(E.Entity):

    _hidden = True

    name = f.unicode()
    data = f.image()

    _key(name)


class Actor(E.Entity):

    name = f.unicode()
    
    _key(name)

    def x_movies(self):
        return [casting.movie 
                for casting in self.m.movie_castings()]


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
        return [casting.actor 
                for casting in self.m.movie_castings()]

    def __unicode__(self):
        return u'%s (%i)' % (self.title, self.release_date.year)


class MovieCasting(E.Entity):

    movie = f.entity('Movie', CASCADE)
    actor = f.entity('Actor')

    _key(movie, actor)
