"""schevo.expression unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import CreatesSchema, raises


class BaseExpression(CreatesSchema):

    body = """
        class FoodCombo(E.Entity):

            carrots = f.integer()
            apples = f.integer()
            broccoli = f.integer()

        class PetCombo(E.Entity):

            cats = f.integer()
            dogs = f.integer()
        """

    def test_single_extent_field_equality_criteria(self):
        expected = {
            db.FoodCombo.f.carrots: 1,
            db.FoodCombo.f.apples: 2,
            db.FoodCombo.f.broccoli: 3,
            }
        criteria = (
            (db.FoodCombo.f.carrots == 1)
            & (db.FoodCombo.f.apples == 2)
            & (db.FoodCombo.f.broccoli == 3)
            )
        assert criteria.single_extent_field_equality_criteria() == expected
        criteria = (
            ((db.FoodCombo.f.carrots == 1)
             & (db.FoodCombo.f.apples == 2))
            & (db.FoodCombo.f.broccoli == 3)
            )
        assert criteria.single_extent_field_equality_criteria() == expected
        criteria = (
            (db.FoodCombo.f.carrots == 1)
            & ((db.FoodCombo.f.apples == 2)
               & (db.FoodCombo.f.broccoli == 3))
            )
        assert criteria.single_extent_field_equality_criteria() == expected

    def test_not_single_extent_field_equality_criteria(self):
        criteria = (
            (db.FoodCombo.f.carrots == 1)
            & (db.FoodCombo.f.apples != 2)
            & (db.FoodCombo.f.broccoli < 3)
            )
        assert raises(
            ValueError, criteria.single_extent_field_equality_criteria)
        criteria = (
            (db.FoodCombo.f.carrots == 1)
            & (db.PetCombo.f.cats == 2)
            )
        assert raises(
            ValueError, criteria.single_extent_field_equality_criteria)


# class TestExpression1(BaseExpression):

#     include = True

#     format = 1


class TestExpression2(BaseExpression):

    include = True

    format = 2
