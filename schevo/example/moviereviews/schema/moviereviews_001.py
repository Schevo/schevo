"""Schema for MovieReviews."""

from schevo.schema import *
schevo.schema.prep(locals())


class SchevoIcon(E.Entity):

    _hidden = True

    name = f.string()
    data = f.image()

    _key(name)


class Actor(E.Entity):

    name = f.string()

    _key(name)

    def x_movies(self):
        return [casting.movie
                for casting in self.m.movie_castings()]


class Director(E.Entity):

    name = f.string()

    _key(name)


class Movie(E.Entity):

    title = f.string()
    release_date = f.date()
    director = f.entity('Director')
    description = f.string(multiline=True, required=False)

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


E.Actor._sample = [
    ('Keanu Reeves', ),
    ('Winona Ryder', ),
    ]

E.Director._sample = [
    ('Richard Linklater', ),
    ('Stephen Herek', ),
    ('Tim Burton', ),
    ]

E.Movie._sample = [
    ('A Scanner Darkly', '2006-07-28', ('Richard Linklater', ),
        DEFAULT),
    ("Bill & Ted's Excellent Adventure", '1989-02-17',
        ('Stephen Herek', ), DEFAULT),
    ('Edward Scissorhands', '1990-12-14', ('Tim Burton', ),
        DEFAULT),
    ]

E.MovieCasting._sample = [
    (('A Scanner Darkly', ), ('Keanu Reeves', )),
    (('A Scanner Darkly', ), ('Winona Ryder', )),
    (("Bill & Ted's Excellent Adventure", ), ('Keanu Reeves', )),
    (('Edward Scissorhands', ), ('Winona Ryder', )),
    ]
