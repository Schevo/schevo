"""Object decoration unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo import label
from schevo import test
from schevo import transaction


class TestDecoration(test.CreatesSchema):

    body = '''

    class AlphaAlpha(E.Entity):
        """Referred to by other classes, and can also optionally refer to
        self."""

        beta = f.integer()
        alpha_alpha = f.entity('AlphaAlpha', required=False)

        _key(beta)

        _hidden = True

        def __unicode__(self):
            return u'beta %i' % self.beta


    class AlphaBravo(E.Entity):
        """Has a reference to an AlphaAlpha, such that when that
        AlphaAlpha is deleted, this AlphaBravo will also be deleted."""

        alpha_alpha = f.entity('AlphaAlpha', on_delete=CASCADE)


    class Avatar(E.Entity):

        realm = f.entity('Realm')
        user = f.entity('User')
        name = f.unicode()

        _key(user, realm, name)

        def __unicode__(self):
            return u'%s (%s in %s)' % (self.name, self.user, self.realm)


    class Batch_Job(E.Entity):

        name = f.unicode()
        priority = f.integer(label='Pri.')

        _key(name)
        _key(priority)

        @extentmethod
        def t_multiple_keys_create(extent):
            return T.Multiple_Keys_Create()

        @extentmethod
        def t_multiple_keys_update(extent):
            return T.Multiple_Keys_Update()

        def __unicode__(self):
            return u'%s :: %i' % (self.name, self.priority)


    class Realm(E.Entity):

        name = f.unicode()

        _key(name)

        class _Create(T.Create):

            def _undo(self):
                return None


    class User(E.Entity):

        name = f.unicode()
        age = f.integer(required=False)

        _key(name)

        _index(age)
        _index(age, name)
        _index(name, age)

        @extentmethod
        def t_create_foo_and_bar(extent):
            return T.Create_Foo_And_Bar()

        @extentmethod
        def t_create_name_only(extent):
            tx = E.User._Create()
            del tx.f.age
            return tx

        @extentmethod
        def t_trigger_key_collision(extent):
            return T.Trigger_Key_Collision()


    class Account(E.Entity):
        """Bank account."""

        owner = f.entity('Person')
        name = f.unicode()
        balance = f.money()
        overdraft_protection = f.boolean(default=False) # XXX
        suspended = f.boolean(default=False) # XXX

        _key(owner, name)

        def t_suspend(self):
            """Suspend this account."""
            tx = T.Suspend()
            tx.account = self
            tx.f.account.readonly = True
            return tx

        @with_label('Transfer Funds From This Account')
        def t_transfer(self):
            """Transfer funds from this account."""
            tx = T.Transfer()
            tx.from_account = self
            tx.f.from_account.readonly = True
            tx._label = 'Transfer Funds From %s' % self
            return tx

        _sample_unittest = [
            (('Fred Flintstone', ), 'Personal', 204.52, False, False),
            (('Fred Flintstone', ), 'Business', 29142.75, True, False),
            (('Betty Rubble', ), 'Family', 291.00, False, True),
            (('Betty Rubble', ), 'Savings', 2816.50, False, False),
            ]


    class Gender(E.Entity):
        """Gender of a person."""

        code = f.unicode()
        name = f.unicode()
        @f.integer()
        def count(self):
            return self.sys.count('Person', 'gender')

        _key(code)
        _key(name)


    class Person(E.Entity):
        """Bank account owner."""

        name = f.unicode()
        gender = f.entity('Gender', required=False)

        _key(name)

        _plural = 'People'

        _sample_unittest = [
            ('Fred Flintstone', UNASSIGNED),
            ('Betty Rubble', UNASSIGNED),
            ]


    class Suspend(T.Transaction):
        """Suspend an account."""

        account = f.entity('Account')

        def _execute(self, db):
            tx = self.account.t.update(suspended=True)
            db.execute(tx)


    class Transfer(T.Transaction):
        """Transfer money from one account to another."""

        from_account = f.entity('Account')
        to_account = f.entity('Account')
        amount = f.money(min_value=0.00)

        def _execute(self, db):
            from_account = self.from_account
            to_account = self.to_account
            amount = self.amount
            has_overdraft_protection = from_account.overdraft_protection
            new_balance = from_account.balance - amount
            # Validate.
            if from_account.suspended or to_account.suspended:
                raise Exception('An account is suspended.')
            if not has_overdraft_protection and new_balance < 0.00:
                raise Exception('Insufficient funds.')
            # Transfer.
            tx_withdraw = from_account.t.update()
            tx_withdraw.balance -= amount
            tx_deposit = to_account.t.update()
            tx_deposit.balance += amount
            db.execute(tx_withdraw, tx_deposit)


    class LoopSegment(E.Entity):
        """A loop segment must always have a 'next' field.

        If it is UNASSIGNED during a create operation, then the segment
        itself will be the value.
        """

        next = f.entity('LoopSegment')

        _key(next)

        _hide('t_create', 't_update')
        _hide('t_update')                   # Dupes are ignored.

        class _CreateLoop(T.Transaction):
            """Create a loop of multiple segments.  Result of execution is
            the first segment made."""

            count = f.integer()

            def _execute(self, db):
                db.LoopSegment.relax_index('next')
                segments = []
                # Create segments.
                for x in xrange(self.count):
                    tx = db.LoopSegment.t.create()
                    segments.append(db.execute(tx, strict=False))
                # Link them together in a loop.
                for x in xrange(self.count - 1):
                    this = segments[x]
                    next = segments[x + 1]
                    tx = this.t.update()
                    tx.next = next
                    db.execute(tx)
                this = segments[-1]
                next = segments[0]
                tx = this.t.update()
                tx.next = next
                db.execute(tx)
                db.LoopSegment.enforce_index('next')
                # Return the first one created.
                return segments[0]

        @extentmethod
        def t_create_loop(extent):
            return E.LoopSegment._CreateLoop()

        class _DirtyCreateLoop(T.Transaction):
            """Create a loop of multiple segments.  Intentionally fails."""

            count = f.integer()

            def _execute(self, db):
                db.LoopSegment.relax_index('next')
                segments = []
                # Create segments.
                for x in xrange(self.count):
                    tx = db.LoopSegment.t.create()
                    segments.append(db.execute(tx, strict=False))
                # This should fail:
                try:
                    db.LoopSegment.enforce_index('next')
                except error.KeyCollision:
                    raise
                else:
                    raise Exception('Key collision not detected!')

        @extentmethod
        def t_dirty_create_loop(extent):
            return E.LoopSegment._DirtyCreateLoop()


    class Create_Foo_And_Bar(T.Transaction):

        def _execute(self, db):
            User = db.User
            # Successful transaction.
            tx = User.t.create(name='foo')
            db.execute(tx)
            # Failing transaction.
            tx = User.t.create(name='bar')
            db.execute(tx)


    def t_subtransactions():
        return T.Subtransactions()

    class Subtransactions(T.Transaction):
        """We do not do anything meaningful here."""
        pass
    '''

    def test_label_from_name(self):
        lfn = label.label_from_name
        assert lfn('something') == 'Something'
        assert lfn('Something') == 'Something'
        assert lfn('some_other_thing') == 'Some Other Thing'
        assert lfn('Some_Other_Thing') == 'Some Other Thing'
        assert lfn('has_WiFi') == 'Has WiFi'
        assert lfn('Has_WiFi') == 'Has WiFi'
        assert lfn('withoutAnUnderscore') == 'Without An Underscore'
        assert lfn('WithoutAnUnderscore') == 'Without An Underscore'
        assert lfn('hasWiFi') == 'Has Wi Fi'
        assert lfn('HasWiFi') == 'Has Wi Fi'
        assert lfn('_something') == 'Something'
        assert lfn('_Something') == 'Something'
        assert lfn('something_') == 'Something'
        assert lfn('Something_') == 'Something'
        assert lfn('__something') == 'Something'
        assert lfn('__Something') == 'Something'
        assert lfn('something__') == 'Something'
        assert lfn('Something__') == 'Something'
        assert lfn('__some_other____thing') == 'Some Other Thing'
        assert lfn('_Some__Other_Thing___') == 'Some Other Thing'
        assert lfn('_SomeOtherThing') == 'Some Other Thing'
        assert lfn('a') == 'A'
        assert lfn('a_') == 'A'
        assert lfn('_a') == 'A'
        assert lfn('a__') == 'A'
        assert lfn('__a') == 'A'
        assert lfn('__a__') == 'A'
        assert lfn('a_dog') == 'A Dog'
        assert lfn('a__dog') == 'A Dog'
        assert lfn('is_a_b_c_dog') == 'Is A B C Dog'

    def test_database_decoration(self):
        # This label is assigned automatically.
        assert label.label(db) == 'Schevo Database'
        # It can be easily overridden.
        db.label = 'Custom Label'
        assert label.label(db) == 'Custom Label'

    def test_extent_decoration(self):
        # These labels were assigned automatically.
        assert label.label(db.Avatar) == 'Avatar'
        assert label.label(db.Batch_Job) == 'Batch Job'
        assert label.label(db.Realm) == 'Realm'
        assert label.label(db.User) == 'User'
        assert label.label(db.Person) == 'Person'
        assert label.plural(db.Avatar) == 'Avatars'
        assert label.plural(db.Batch_Job) == 'Batch Jobs'
        assert label.plural(db.Realm) == 'Realms'
        assert label.plural(db.User) == 'Users'
        # These labels were assigned manually.
        assert label.plural(db.Person) == 'People'
        # The docstring for an extent is set to the docstring for the
        # entity.
        assert db.Person.__doc__ == 'Bank account owner.'
        # An extent may optionally be hidden from typical user
        # interfaces.
        assert db.AlphaAlpha.hidden
        assert not db.AlphaBravo.hidden

    def test_entity_decoration(self):
        # Default label based on name.
        user = db.execute(db.User.t.create(name='foo'))
        assert label.label(user) == 'foo'
        # Custom label.
        realm = db.execute(db.Realm.t.create(name='bar'))
        avatar = db.execute(db.Avatar.t.create(
            name='baz', user=user, realm=realm))
        assert label.label(avatar) == u'baz (foo in bar)'

    def test_field_decoration(self):
        # Fields on transactions have labels.
        tx = db.Avatar.t.create()
        # These labels were assigned automatically.
        assert label.label(tx.f.realm) == 'Realm'
        assert label.label(tx.f.user) == 'User'
        assert label.label(tx.f.name) == 'Name'
        # Batch_Job.priority has a custom label.
        tx = db.Batch_Job.t.create()
        assert label.label(tx.f.priority) == 'Pri.'
        # Resulting entity instances' fields have labels.
        tx.name = 'foo'
        tx.priority = 1
        batch_job = db.execute(tx)
        assert label.label(batch_job.f.name) == 'Name'
        assert label.label(batch_job.f.priority) == 'Pri.'

    def test_transaction_decoration(self):
        # Canonical transactions have default labels.
        tx = db.Realm.t.create(name='foo')
        assert label.label(tx) == 'Create'
        realm = db.execute(tx)
        assert label.label(realm.t.delete()) == 'Delete'
        assert label.label(realm.t.update()) == 'Update'
        # Custom transactions have default labels generated from their
        # class name.
        tx = db.User.t.create_foo_and_bar()
        assert label.label(tx) == 'Create Foo And Bar'
        # Transaction instances can have custom labels assigned upon
        # creation by transaction methods, among other means.
        tx = db.Account[1].t.transfer()
        assert label.label(tx) == 'Transfer Funds From Personal'
        
    def test_transaction_method_decoration(self):
        # Extents for entity classes that are not customized only have
        # a transaction method for the canonical Create transaction.
        t = db.Realm.t
        assert sorted(list(t)) == ['create']
        assert label.label(t.create) == 'Create'
        # Entity instances for entity classes that are not customized
        # only have transaction methods for canonical Delete and
        # Update transactions.
        realm = db.execute(t.create(name='foo'))
        t = realm.t
        L = sorted(t)
        assert L == ['delete', 'update']
        assert label.label(t.delete) == 'Delete'
        assert label.label(t.update) == 'Update'
        # Transaction methods that aren't labeled are automatically
        # labeled.  Test for labels of custom extent transaction
        # methods.
        t = db.Batch_Job.t
        assert 'multiple_keys_create' in list(t)
        assert label.label(t.multiple_keys_create) == 'Multiple Keys Create'
        # Test for labels of custom entity transaction methods.
        t = db.Account[1].t
        assert 'suspend' in list(t)
        assert 'transfer' in list(t)
        assert label.label(t.suspend) == 'Suspend'
        assert label.label(t.transfer) == 'Transfer Funds From This Account'
        # Test for labels of database-level transaction functions.
        t = db.t
        assert list(t) == ['subtransactions']
        assert label.label(t.subtransactions) == 'Subtransactions'

    def test_transaction_method_hiding(self):
        # Make sure that a LoopSegment's create and update
        # transactions are hidden, since they are marked with
        # _hide('t_txname').
        #
        # First check the extent.
        assert sorted(list(db.LoopSegment.t)) == [
            'create_loop', 'dirty_create_loop']
        # Create is still available, even though it's hidden.
        assert isinstance(db.LoopSegment.t.create(), transaction.Create)
        # Create a loop of one segment and verify that 'update' is
        # hidden.
        tx = db.LoopSegment.t.create_loop()
        tx.count = 1
        segment = db.execute(tx)
        assert sorted(list(segment.t)) == ['delete']
        assert isinstance(segment.t.update(), transaction.Update)

    def test_builtin_decoration(self):
        assert label.label('some string') == 'some string'


# Copyright (C) 2001-2006 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# 709 East Jackson Road
# Saint Louis, MO  63119-4241
# http://orbtech.com/
#
# This toolkit is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This toolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
