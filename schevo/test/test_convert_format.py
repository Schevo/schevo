"""Database format conversion tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.backend import backends
from schevo.placeholder import Placeholder
from schevo.test import CreatesSchema


# class TestFormat1Format2ConversionSimple(CreatesSchema):
#     """Very simple test of the format 1 to format 2 converter."""

#     format = 1

#     body = '''
#         class Foo(E.Entity):

#             name = f.string()

#             _key(name)

#             _sample_unittest = [
#                 (u'Foo 1', ),
#                 (u'Foo 2', ),
#                 ]

#         class Bar(E.Entity):

#             id = f.integer()
#             foo = f.entity('Foo')

#             _key(id)
#             _index(foo)

#             _sample_unittest = [
#                 (1, (u'Foo 1', ), ),
#                 (2, (u'Foo 2', ), ),
#                 (3, (u'Foo 1', ), ),
#                 (4, (u'Foo 2', ), ),
#                 ]
#         '''

#     def test(self):
#         self.internal_structure_format_1(db)
#         self.reopen(format=2)
#         self.internal_structure_format_2(db)

#     def internal_structure_format_1(self, db):
#         schevo = db._root['SCHEVO']
#         assert schevo['format'] == 1
#         extent_name_id = schevo['extent_name_id']
#         extents = schevo['extents']
#         Foo_extent_id = extent_name_id['Foo']
#         Bar_extent_id = extent_name_id['Bar']
#         Foo_extent = extents[Foo_extent_id]
#         Bar_extent = extents[Bar_extent_id]
#         Foo_field_name_id = Foo_extent['field_name_id']
#         Bar_field_name_id = Bar_extent['field_name_id']
#         Foo_name_field_id = Foo_field_name_id['name']
#         Bar_id_field_id = Bar_field_name_id['id']
#         Bar_foo_field_id = Bar_field_name_id['foo']
#         Foo_entities = Foo_extent['entities']
#         Bar_entities = Bar_extent['entities']
#         Foo_1 = Foo_entities[1]
#         Foo_2 = Foo_entities[2]
#         Bar_1 = Bar_entities[1]
#         Bar_2 = Bar_entities[2]
#         Bar_3 = Bar_entities[3]
#         Bar_4 = Bar_entities[4]
#         assert Foo_1['fields'][Foo_name_field_id] == u'Foo 1'
#         assert Foo_2['fields'][Foo_name_field_id] == u'Foo 2'
#         assert Bar_1['fields'][Bar_id_field_id] == 1
#         assert Bar_2['fields'][Bar_id_field_id] == 2
#         assert Bar_3['fields'][Bar_id_field_id] == 3
#         assert Bar_4['fields'][Bar_id_field_id] == 4
#         assert Bar_1['fields'][Bar_foo_field_id] == (Foo_extent_id, 1)
#         assert Bar_2['fields'][Bar_foo_field_id] == (Foo_extent_id, 2)
#         assert Bar_3['fields'][Bar_foo_field_id] == (Foo_extent_id, 1)
#         assert Bar_4['fields'][Bar_foo_field_id] == (Foo_extent_id, 2)
#         Bar_foo_index_unique, Bar_foo_index_tree = Bar_extent['indices'][
#             (Bar_foo_field_id, )]
#         assert set(Bar_foo_index_tree.keys()) == set([
#             (Foo_extent_id, 1),
#             (Foo_extent_id, 2),
#             ])
#         assert set(Bar_foo_index_tree[(Foo_extent_id, 1)].keys()) == set([1, 3])
#         assert set(Bar_foo_index_tree[(Foo_extent_id, 2)].keys()) == set([2, 4])

#     def internal_structure_format_2(self, db):
#         schevo = db._root['SCHEVO']
#         assert schevo['format'] == 2
#         extent_name_id = schevo['extent_name_id']
#         extents = schevo['extents']
#         Foo_extent_id = extent_name_id['Foo']
#         Bar_extent_id = extent_name_id['Bar']
#         Foo_extent = extents[Foo_extent_id]
#         Bar_extent = extents[Bar_extent_id]
#         Foo_field_name_id = Foo_extent['field_name_id']
#         Bar_field_name_id = Bar_extent['field_name_id']
#         Foo_name_field_id = Foo_field_name_id['name']
#         Bar_id_field_id = Bar_field_name_id['id']
#         Bar_foo_field_id = Bar_field_name_id['foo']
#         Foo_entities = Foo_extent['entities']
#         Bar_entities = Bar_extent['entities']
#         Foo_1 = Foo_entities[1]
#         Foo_2 = Foo_entities[2]
#         Bar_1 = Bar_entities[1]
#         Bar_2 = Bar_entities[2]
#         Bar_3 = Bar_entities[3]
#         Bar_4 = Bar_entities[4]
#         assert Foo_1['fields'][Foo_name_field_id] == u'Foo 1'
#         assert Foo_2['fields'][Foo_name_field_id] == u'Foo 2'
#         assert Bar_1['fields'][Bar_id_field_id] == 1
#         assert Bar_2['fields'][Bar_id_field_id] == 2
#         assert Bar_3['fields'][Bar_id_field_id] == 3
#         assert Bar_4['fields'][Bar_id_field_id] == 4
#         assert Bar_1['fields'][Bar_foo_field_id] == Placeholder(db.Foo[1])
#         assert Bar_2['fields'][Bar_foo_field_id] == Placeholder(db.Foo[2])
#         assert Bar_3['fields'][Bar_foo_field_id] == Placeholder(db.Foo[1])
#         assert Bar_4['fields'][Bar_foo_field_id] == Placeholder(db.Foo[2])
#         assert Bar_1['related_entities'][Bar_foo_field_id] == frozenset([
#             Placeholder(db.Foo[1])])
#         assert Bar_2['related_entities'][Bar_foo_field_id] == frozenset([
#             Placeholder(db.Foo[2])])
#         assert Bar_3['related_entities'][Bar_foo_field_id] == frozenset([
#             Placeholder(db.Foo[1])])
#         assert Bar_4['related_entities'][Bar_foo_field_id] == frozenset([
#             Placeholder(db.Foo[2])])
#         Bar_foo_index_unique, Bar_foo_index_tree = Bar_extent['indices'][
#             (Bar_foo_field_id, )]
#         assert set(Bar_foo_index_tree.keys()) == set([
#             Placeholder(db.Foo[1]),
#             Placeholder(db.Foo[2]),
#             ])
#         assert set(Bar_foo_index_tree[Placeholder(db.Foo[1])].keys()) == set(
#             [1, 3])
#         assert set(Bar_foo_index_tree[Placeholder(db.Foo[2])].keys()) == set(
#             [2, 4])


# class TestFormat1Format2ConversionComplex(CreatesSchema):
#     """More complex test of the format 1 to format 2 converter."""

#     format = 1

#     body = '''
#         class Foo(E.Entity):

#             name = f.string()

#             _key(name)

#             _sample_unittest = [
#                 (u'Foo 1', ),
#                 (u'Foo 2', ),
#                 ]

#         class Gee(E.Entity):

#             name = f.string()

#             _key(name)

#             _sample_unittest = [
#                 (u'Gee 1', ),
#                 (u'Gee 2', ),
#                 ]

#         class Bar(E.Entity):

#             id = f.integer()
#             foo = f.entity('Foo')
#             gee = f.entity('Gee')

#             _key(id)
#             _index(foo, gee)

#             _sample_unittest = [
#                 (1, (u'Foo 1', ), (u'Gee 1', ), ),
#                 (2, (u'Foo 2', ), (u'Gee 1', ), ),
#                 (3, (u'Foo 1', ), (u'Gee 1', ), ),
#                 (4, (u'Foo 2', ), (u'Gee 2', ), ),
#                 ]
#         '''

#     def test(self):
#         self.check_using_public_api()
#         self.reopen(format=2)
#         self.check_using_public_api()

#     def check_using_public_api(self):
#         foo1 = db.Foo[1]
#         foo2 = db.Foo[2]
#         gee1 = db.Gee[1]
#         gee2 = db.Gee[2]
#         bar1 = db.Bar[1]
#         bar2 = db.Bar[2]
#         bar3 = db.Bar[3]
#         bar4 = db.Bar[4]
#         assert bar1.foo == foo1
#         assert bar1.gee == gee1
#         assert bar2.foo == foo2
#         assert bar2.gee == gee1
#         assert bar3.foo == foo1
#         assert bar3.gee == gee1
#         assert bar4.foo == foo2
#         assert bar4.gee == gee2
