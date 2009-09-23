"""extent.find() unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import CreatesSchema, raises


class BaseFind(CreatesSchema):

    body = """
        class Sightings(E.Entity):

            date = f.date()
            people = f.integer()
            aliens = f.integer()

            _key(date)
            _index(people)
            _index(aliens)

            _sample_unittest = [
                ('2009-01-01', 5, 1),
                ('2009-01-02', 5, 2),
                ('2009-01-03', 6, 2),
                ('2009-01-04', 5, 2),
                ('2009-01-05', 3, 2),
                ('2009-01-06', 6, 3),
                ('2009-01-07', 7, 1),
                ('2009-01-08', 7, 4),
                ('2009-01-09', 1, 5),
                ]
        """

    def test_count_complex_criteria(self):
        f = db.Sightings.f
        count = db.Sightings.count
        # <
        assert count(f.date < '2008-12-31') == 0
        assert count(f.date < '2009-01-01') == 0
        assert count(f.date < '2009-01-03') == 2
        assert count(f.date < '2009-01-10') == 9
        # <=
        assert count(f.date <= '2008-12-31') == 0
        assert count(f.date <= '2009-01-02') == 2
        assert count(f.date <= '2009-01-09') == 9
        # ==
        assert count(f.date == '2009-01-05') == 1
        # >=
        assert count(f.date >= '2009-01-10') == 0
        assert count(f.date >= '2009-01-08') == 2
        assert count(f.date >= '2008-12-31') == 9
        # >
        assert count(f.date > '2009-01-10') == 0
        assert count(f.date > '2009-01-09') == 0
        assert count(f.date > '2009-01-07') == 2
        assert count(f.date > '2008-12-31') == 9
        # < & ==
        assert count((f.date < '2009-01-04') & (f.people == 5)) == 2
        # >= | <=
        assert count((f.date >= '2009-01-08') | (f.people <= 3)) == 3
        # !=
        assert count(f.people != 5) == 6


# class TestFind1(BaseFind):

#     include = True

#     format = 1


class TestFind2(BaseFind):

    include = True

    format = 2
