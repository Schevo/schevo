"""Field metadata changing tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import CreatesSchema

from schevo.field import not_expensive, not_fget, not_hidden


class BaseFieldMetadataChanged(CreatesSchema):

    body = '''
    class Foo(E.Entity):

        bar = f.string()

        class _Update(T.Update):

            def h_bar(self):
                self.f.bar.readonly = True

            def _setup(self):
                self.f.bar.required = False
    '''

    def test_metadata_not_changed_initially(self):
        tx = db.Foo.t.create()
        assert tx.f.bar.metadata_changed == False
        tx.bar = 'baz'
        foo = db.execute(tx)
        tx = foo.t.update()
        assert tx.f.bar.required == False
        assert tx.f.bar.metadata_changed == False

    def test_metadata_changed_during_change_handler(self):
        tx = db.Foo.t.create(bar='baz')
        foo = db.execute(tx)
        tx = foo.t.update()
        assert tx.f.bar.metadata_changed == False
        tx.f.bar.readonly = False
        assert tx.f.bar.metadata_changed == True
        tx.f.bar.reset_metadata_changed()
        assert tx.f.bar.metadata_changed == False
        tx.bar = 'frob'
        assert tx.f.bar.readonly == True
        assert tx.f.bar.metadata_changed == True
        tx.f.bar.reset_metadata_changed()
        assert tx.f.bar.metadata_changed == False


# class TestFieldMetadataChanged1(BaseFieldMetadataChanged):

#     include = True

#     format = 1


class TestFieldMetadataChanged2(BaseFieldMetadataChanged):

    include = True

    format = 2
