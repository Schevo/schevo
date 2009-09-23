"""Transaction unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import CreatesSchema, raises
from schevo.constant import UNASSIGNED
from schevo import error
from schevo import field
from schevo.label import label
from schevo.placeholder import Placeholder
from schevo import transaction

class BaseTransaction(CreatesSchema):

    body = '''

    from schevo.test import raises

    class Account(E.Entity):
        """Bank account."""

        owner = f.entity('Person')
        name = f.string()
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

        code = f.string()
        name = f.string()
        @f.integer()
        def count(self):
            return self.s.count('Person', 'gender')

        _key(code)
        _key(name)


    class Person(E.Entity):
        """Bank account owner."""

        name = f.string()
        gender = f.entity('Gender', required=False)

        _key(name)

        _plural = 'People'

        _sample_unittest = [
            ('Fred Flintstone', UNASSIGNED),
            ('Betty Rubble', UNASSIGNED),
            ]

        class _Create(T.Create):

            def x_current_name_len(self):
                return len(self.name)


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


    class Avatar(E.Entity):

        realm = f.entity('Realm')
        user = f.entity('User')
        name = f.string()

        _key(user, realm, name)

        def __unicode__(self):
            return u'%s (%s in %s)' % (self.name, self.user, self.realm)


    class Batch_Job(E.Entity):

        name = f.string()
        priority = f.integer(label='Pri.')

        _key(name)
        _key(priority)

        def __unicode__(self):
            return u'%s :: %i' % (self.name, self.priority)


    class Realm(E.Entity):

        name = f.string()

        _key(name)

        class _Create(T.Create):

            def _undo(self):
                return None


    class User(E.Entity):

        name = f.string()
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


    class Create_Foo_And_Bar(T.Transaction):

        def _execute(self, db):
            User = db.User
            # Successful transaction.
            tx = User.t.create(name='foo')
            db.execute(tx)
            # Failing transaction.
            tx = User.t.create(name='bar')
            db.execute(tx)


    class Trigger_Key_Collision(T.Transaction):

        def _execute(self, db):
            User = db.User
            # Successful transaction.
            tx = User.t.create(name='foo')
            db.execute(tx)
            # Failing transaction.
            tx = User.t.create(name='foo')
            db.execute(tx)


    class Subtransactions(T.Transaction):
        """The top-level transaction of a series of subtransactions.

        The sequence of execution is as follows:

        - create user 1
        - subtransaction as list
          - create user 2
          - create user 3
        - subtransaction as list -> handled failure
          - create user 4
          - update user 2
          - delete user 3
          - create user -> unhandled failure
        - subtransaction 1 as instance
          - create user 5
          - create user 6
        - subtransaction 2 as instance -> handled failure
          - create user 7
          - update user 5
          - delete user 6
          - create user -> unhandled failure
        - subtransaction 3 as instance
          - sub-subtransaction as list
            - create user 8
            - create user 9
          - sub-subtransaction as list -> handled failure
            - create user 10
            - update user 8
            - delete user 9
            - create user -> unhandled failure
        - subtransaction 4 as instance -> handled failure
          - sub-subtransaction as list
            - create user 11
            - update user 2
            - delete user 3
          - sub-subtransaction as list -> unhandled failure
            - create user 12
            - create user -> unhandled failure
        - create user 13

        The result is that eight users with the following OIDs should
        exist in the User extent, all with revision 0: 1, 2, 3, 5, 6, 8,
        9, 13
        """

        def _execute(self, db):
            User = db.User
            txc1 = User.t.create(name='1')
            db.execute(txc1)
            assert len(User) == 1
            txc2 = User.t.create(name='2')
            txc3 = User.t.create(name='3')
            user2, user3 = db.execute(txc2, txc3)
            assert len(User) == 3
            txc4 = User.t.create(name='4')
            txu2 = user2.t.update(name='2b')
            txd3 = user3.t.delete()
            txcfail = User.t.create(name='1') # Key collision.
            try:
                db.execute(txc4, txu2, txd3, txcfail)
            except schevo.error.KeyCollision, e:
                assert e.extent_name == 'User'
                assert e.key_spec == ('name',)
                assert e.field_values == (u'1',)
            assert len(User) == 3
            txs1 = T.Subtransaction1()
            db.execute(txs1)
            txs2 = T.Subtransaction2()
            try:
                db.execute(txs2)
            except schevo.error.KeyCollision, e:
                assert e.extent_name == 'User'
                assert e.key_spec == ('name',)
                assert e.field_values == (u'1',)
            txs3 = T.Subtransaction3()
            db.execute(txs3)
            txs4 = T.Subtransaction4()
            try:
                db.execute(txs4)
            except schevo.error.KeyCollision, e:
                assert e.extent_name == 'User'
                assert e.key_spec == ('name',)
                assert e.field_values == (u'1',)
            txc13 = User.t.create(name='13')
            db.execute(txc13)


    def t_subtransactions():
        return T.Subtransactions()


    class Subtransaction1(T.Transaction):

        def _execute(self, db):
            User = db.User
            txc5 = User.t.create(name='5')
            db.execute(txc5)
            txc6 = User.t.create(name='6')
            db.execute(txc6)


    class Subtransaction2(T.Transaction):

        def _execute(self, db):
            User = db.User
            txc7 = User.t.create(name='7')
            db.execute(txc7)
            txu5 = User[5].t.update(name='5b')
            db.execute(txu5)
            txd6 = User[6].t.delete()
            db.execute(txd6)
            txcfail = User.t.create(name='1') # Key collision.
            db.execute(txcfail)             # Allow exception to pass through.


    class Subtransaction3(T.Transaction):

        def _execute(self, db):
            User = db.User
            txc8 = User.t.create(name='8')
            txc9 = User.t.create(name='9')
            user8, user9 = db.execute(txc8, txc9)
            txc10 = User.t.create(name='10')
            txu8 = user8.t.update(name='8b')
            txd9 = user9.t.delete()
            txcfail = User.t.create(name='1') # Key collision.
            try:
                db.execute(txc10, txu8, txd9, txcfail)
            except schevo.error.KeyCollision, e:
                assert e.extent_name == 'User'
                assert e.key_spec == ('name',)
                assert e.field_values == (u'1',)


    class Subtransaction4(T.Transaction):

        def _execute(self, db):
            User = db.User
            txc11 = User.t.create(name='11')
            txu2 = User[2].t.update(name='2b')
            txd3 = User[3].t.delete()
            db.execute(txc11, txu2, txd3)
            txc12 = User.t.create(name='12')
            txcfail = User.t.create(name='1') # Key collision.
            db.execute(txc12, txcfail)      # Allow exception to pass through.


    class LoopSegment(E.Entity):
        """A loop segment must always have a 'next' field.

        If it is UNASSIGNED during a create operation, then the segment
        itself will be the value.
        """

        next = f.entity('LoopSegment')

        _key(next)

        _hide('t_create', 't_update')
        _hide('t_update')                   # Dupes are ignored.

        @extentmethod
        def t_create(extent):
            tx = E.LoopSegment._Create()
            tx.f.next.required = False
            return tx

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
                except schevo.error.KeyCollision:
                    raise
                else:
                    raise Exception('Key collision not detected!')

        @extentmethod
        def t_dirty_create_loop(extent):
            return E.LoopSegment._DirtyCreateLoop()


    class Cog(E.Entity):
        """A cog with sprockets."""

        name = f.string()

        _key(name)

        class _Create(T.Create):
            """A cog is usually created with five sprockets."""

            def _after_execute(self, db, cog):
                sprockets = db.extent('Sprocket')
                try:
                    for x in xrange(5):
                        db.execute(sprockets.t.create(cog=cog))
                except:
                    # If sprockets couldn't be created, don't worry.
                    pass


    class Sprocket(E.Entity):
        """A sprocket for a cog."""

        cog = f.entity('Cog')

        class _Create(T.Create):
            """A sprocket is only created if the name of the cog is
            not 'Spacely'."""

            def _after_execute(self, db, sprocket):
                if sprocket.cog.name == 'Spacely':
                    raise Exception('Antitrust error.')


    class ProblemGender(E.Entity):
        """Gender of a person, with a problematic _Create transaction."""

        code = f.string()
        name = f.string()
        @f.integer()
        def count(self):
            return self.s.count('Person', 'gender')

        _key(code)
        _key(name)

        class _Create(T.Create):

            # Bogus fields here, to trigger potential problems.
            count = f.string()
            foo = f.integer()

        class _Update(T.Update):

            # Bogus fields here, to trigger potential problems.
            count = f.string()
            foo = f.integer()


    class Folder(E.Entity):
        """Folder that could have a parent."""

        name = f.string(error_message=u'Please enter the name of the folder.')
        parent = f.entity('Folder', required=False)

        _key(name, parent)

        def __unicode__(self):
            name = self.name
            parent = self.parent
            while parent and parent != self:
                name = parent.name + u'/' + name
                parent = parent.parent
            return name


    class FooWithCalc(E.Entity):

        name = f.string()

        _key(name)

        class _Create(T.Create):

            @f.integer()
            def bar(self):
                return 42

        class _Update(T.Update):

            @f.string()
            def baz(self):
                return u'BAZ'


    def t_base_transaction():
        return T.Transaction()
    '''

    def test_not_implemented(self):
        # The base transaction must be subclassed and provided with
        # its own _execute method, it should never be used directly
        # like we do here.
        tx = db.t.base_transaction()
        assert raises(NotImplementedError, db.execute, tx)

    def test_create_simple(self):
        # No users to start out with.
        assert len(db.User) == 0
        # Get a create transaction.
        tx = db.User.t.create()
        # All fields are UNASSIGNED by default in this case.
        assert tx.name is UNASSIGNED
        assert tx.f.name.get() is UNASSIGNED
        # Only one field exists in the transaction.
        assert tx.s.field_map().keys() == ['name', 'age']
        # Set a field and execute the transaction against the db.
        tx.name = 'foo'
        result = db.execute(tx)
        # The result should be a new User entity.
        assert isinstance(result, db.User.EntityClass)
        assert result.s.oid == 1
        assert result.s.rev == 0
        assert result.name == 'foo'
        assert len(db.User) == 1
        assert db.User[1].name == 'foo'
        assert db.User[1] == result

    def test_create_copy(self):
        # Create a user to copy from.
        user = db.execute(db.User.t.create(name='Joe', age=42))
        # Copy the user by passing in the user's entity as a
        # positional argument, and setting keyword arguments for field
        # value overrides.
        user2 = db.execute(db.User.t.create(user, name='Bob'))
        assert user2.age == 42
        assert user2.name == 'Bob'
        # Any object with attributes that match the transaction's
        # fields may be used.
        class Foo(object):
            name = 'Tim'
            age = 50
        # Demonstration of populating fields based on a class.
        user3 = db.execute(db.User.t.create(Foo))
        assert user3.name == 'Tim'
        assert user3.age == 50
        # Demonstration of populating fields based on an instance.
        foo = Foo()
        foo.name = 'John'
        user4 = db.execute(db.User.t.create_if_necessary(foo))
        assert user4.name == 'John'
        assert user4.age == 50
        # Pass in multiple positional arguments.
        class Bar(object):
            name = 'Tim'
            # This field is ignored; the transaction doesn't have an
            # 'other' field.
            other = 'Does not matter'
        bar2 = Bar()
        bar2.name = 'Jim'
        bar3 = Bar()
        bar3.name = 'James'
        user5 = db.execute(db.User.t.create(Foo, user2, bar2, bar3))
        assert user5.name == 'James'    # Obtained from bar3
        assert user5.age == 42          # Obtained from Foo
        # Demonstration of populating an entity field.
        male = db.execute(db.Gender.t.create(code='M', name='Male'))
        john = db.execute(db.Person.t.create(name='John Doe', gender=male))
        other = db.execute(db.Person.t.create(john, name='Other Doe'))
        assert other.gender.name == 'Male'
        # Person from one db with same gender in other db.
        self.reopen()
        other = db.execute(db.Person.t.create(john, name='Other Foo'))
        assert other.s.db != john.s.db
        assert other.gender.name == 'Male'
        # Person from one db WITHOUT same gender in other db.
        self.reopen()
        for person in db.Person:
            if person.gender is not UNASSIGNED:
                # Need to delete these people first otherwise deleting
                # the gender will fail.
                db.execute(person.t.delete())
        gender = db.Gender.findone(code='M')
        db.execute(gender.t.delete())
        try:
            db.Person.t.create(john, name='Other Guy')
        except error.DatabaseMismatch, e:
            assert e.field_name == 'gender'
            assert e.field_value == None

    def test_create_with_fget(self):
        tx = db.Gender.t.create()
        # Transaction has a field for the fget field, but it's hidden.
        assert tx.s.field_map().keys() == ['code', 'name', 'count']
        assert tx.f.count.hidden == True
        # Transaction still executes properly.
        tx.code = 'M'
        tx.name = 'Male'
        result = db.execute(tx)
        assert result.code == 'M'
        assert result.name == 'Male'
        assert result.count == 0

    def test_update_simple(self):
        # Create something that we can update.
        tx = db.User.t.create(name='foo')
        result1 = db.execute(tx)
        # Get an update transaction from the resulting entity instance.
        tx = result1.t.update()
        # It should have the same field values as the entity itself.
        assert tx.s.field_map().keys() == ['name', 'age']
        assert tx.name == 'foo'
        # Change 'name' and execute.
        tx.name = 'bar'
        result2 = db.execute(tx)
##         # Make sure the fields that changed were flagged as such.
##         assert result2.f.name.changed
##         assert not result2.f.age.changed
        # The result should be the same User entity, except have a new
        # rev and a new name.
        assert isinstance(result2, db.User.EntityClass)
        assert result2.s.oid == 1
        assert result2.s.rev == 1
        assert result2.name == 'bar'
        assert len(db.User) == 1
        assert db.User[1].name == 'bar'
        assert db.User[1] == result2
        # The second result may not be the same Python object as the
        # first result, but they should be equal.
        assert result1.s.rev == 1
        assert result1.name == 'bar'
        assert result1 == result2

    def test_update_cannot_skip_revisions(self):
        tx = db.User.t.create(name='foo')
        user = db.execute(tx)
        tx1 = user.t.update(name='bar')
        tx2 = user.t.update(name='baz')
        db.execute(tx1)
        try:
            db.execute(tx2)
        except error.TransactionExpired, e:
            assert e.transaction == tx2
            assert e.original_rev == 0
            assert e.current_rev == 1

    def test_update_with_fget(self):
        tx = db.Gender.t.create()
        tx.code = 'M'
        tx.name = 'Male'
        result = db.execute(tx)
        tx = result.t.update()
        # Transaction has fget fields, but they are hidden.
        assert tx.s.field_map().keys() == ['code', 'name', 'count']
        assert tx.f.count.hidden == True
        # Transaction still executes properly.
        tx.code = 'F'
        tx.name = 'Female'
        result = db.execute(tx)
        assert result.code == 'F'
        assert result.name == 'Female'
        assert result.count == 0

    def test_update_entities(self):
        male = db.execute(db.Gender.t.create(code='M', name='Male'))
        female = db.execute(db.Gender.t.create(code='F', name='Female'))
        p = db.execute(db.Person.t.create(gender=male, name='Some person'))
        assert p.gender == male
        self.internal_update_entities_1(expected=male)
        db.execute(p.t.update(gender=female))
        assert p.gender == female
        self.internal_update_entities_1(expected=female)

    def internal_update_entities_1(self, expected):
        raise NotImplementedError()

    def test_delete_simple(self):
        # Create something that we can delete.
        tx = db.User.t.create(name='foo')
        result1 = db.execute(tx)
        # Get a delete transaction from the resulting entity instance.
        tx = result1.t.delete()
        # It should have the same field values as the entity itself.
        assert tx.s.field_map().keys() == ['name', 'age']
        assert tx.name == 'foo'
        # Fields should be readonly.
        assert raises(AttributeError, setattr, tx, 'name', 'bar')
        # Execute it.
        result2 = db.execute(tx)
        # The result should be None since the entity instance no
        # longer exists in the backing store.
        assert result2 is None
        # The extent should be updated accordingly.
        assert len(db.User) == 0
        # The first result should no longer be valid.
        try:
            name = result1.name
        except error.EntityDoesNotExist, e:
            assert e.extent_name == 'User'
            assert e.oid == result1.s.oid
        # Creating a new entity should result in a new OID.
        tx = db.User.t.create(name='baz')
        result = db.execute(tx)
        assert result.s.oid == 2

    def test_delete_restrict(self):
        folder1 = db.execute(db.Folder.t.create(name='folder1'))
        folder2 = db.execute(db.Folder.t.create(name='folder2',
                                                parent=folder1))
        # Deleting the folder should fail.
        try:
            db.execute(folder1.t.delete())
        except error.DeleteRestricted, e:
            assert e.restrictions == set([
                (folder1, folder2, 'parent'),
                ])
        assert folder1 in db.Folder
        assert folder2 in db.Folder

    def test_delete_self_reference(self):
        # Create a folder that references itself.
        folder1 = db.execute(db.Folder.t.create(name='folder1'))
        db.execute(folder1.t.update(parent=folder1))
        # Deleting the folder should succeed since its only incoming
        # reference is itself.
        db.execute(folder1.t.delete())
        assert folder1 not in db.Folder

    def test_delete_cascade(self):
        ## skip('Delete cascade will be reimplemented.')
        return
        # Create some things to potentially delete.
        user_foo = db.execute(db.User.t.create(name='foo'))
        user_bar = db.execute(db.User.t.create(name='bar'))
        realm_foo = db.execute(db.Realm.t.create(name='foo'))
        realm_bar = db.execute(db.Realm.t.create(name='bar'))
        a_foofoo = db.execute(db.Avatar.t.create(
            name='foofoo', user=user_foo, realm=realm_foo))
        a_foobar = db.execute(db.Avatar.t.create(
            name='foobar', user=user_foo, realm=realm_bar))
        a_barfoo = db.execute(db.Avatar.t.create(
            name='barfoo', user=user_bar, realm=realm_foo))
        a_barbar = db.execute(db.Avatar.t.create(
            name='barbar', user=user_bar, realm=realm_bar))
        # Delete cascade of user_foo should result in a_foofoo and
        # a_foobar being deleted as well.
        tx = user_foo.t.delete_cascade()
        db.execute(tx)
        assert user_foo not in db.User
        assert a_foofoo not in db.Avatar
        assert a_foobar not in db.Avatar
        # Delete cascade of realm_bar should result in a_barbar being
        # deleted as well.
        tx = realm_bar.t.delete_cascade()
        db.execute(tx)
        assert realm_bar not in db.Realm
        assert a_barbar not in db.Avatar
        # Everything else should still exist.
        assert user_bar in db.User
        assert realm_foo in db.Realm
        assert a_barfoo in db.Avatar

    def test_delete_cascade_circular(self):
        ## skip('Delete cascade will be reimplemented.')
        return
        # Create some folders that are circularly-referenced.
        folder1 = db.execute(db.Folder.t.create(name='folder1'))
        folder2 = db.execute(db.Folder.t.create(name='folder2',
                                                parent=folder1))
        folder3 = db.execute(db.Folder.t.create(name='folder3',
                                                parent=folder2))
        db.execute(folder1.t.update(parent=folder3))
        # Deleting any of them should result in all three being
        # deleted.
        tx = folder2.t.delete_cascade()
        db.execute(tx)
        assert folder1 not in db.Folder
        assert folder2 not in db.Folder
        assert folder3 not in db.Folder

    def test_delete_with_fget(self):
        tx = db.Gender.t.create()
        tx.code = 'M'
        tx.name = 'Male'
        result = db.execute(tx)
        tx = result.t.delete()
        # Transaction has fget fields, but they are hidden.
        assert tx.s.field_map().keys() == ['code', 'name', 'count']
        assert tx.f.count.hidden == True
        # Transaction still executes properly.
        db.execute(tx)
        assert result not in db.Gender

    def test_delete_cannot_skip_revisions(self):
        tx = db.User.t.create(name='foo')
        user = db.execute(tx)
        tx1 = user.t.update(name='bar')
        tx2 = user.t.delete()
        db.execute(tx1)
        assert raises(error.TransactionExpired, db.execute, tx2)

    def test_clone_simple(self):
        # Create a user that we will then clone.
        tx = db.User.t.create(name='User 1', age=123)
        user1 = db.execute(tx)
        # Make sure the label for the 'clone' transaction method is
        # correct.
        assert label(user1.t.clone) == 'Clone'
        # Create a 'clone' transaction based on the user.
        tx = user1.t.clone()
        # Make sure the label for the actual transaction is correct.
        assert label(tx) == 'Clone'
        # The values of the cloned transaction should match the entity
        # being cloned.
        assert tx.name == user1.name
        assert tx.age == user1.age
        # Executing the transaction without modification will result
        # in a key collision, since a user with the name 'User 1'
        # already exists.
        try:
            db.execute(tx)
        except error.KeyCollision, e:
            assert e.extent_name == 'User'
            assert e.key_spec == ('name',)
            assert e.field_values == (u'User 1',)
        # Modify the transaction to change the name, then execute.
        tx.name = 'User 2'
        user2 = db.execute(tx)
        assert user2 != user1
        assert user2.name != user1.name
        assert user2.age == user1.age
        # One may also specify keyword arguments when calling the
        # 'clone' transaction method.
        tx = user1.t.clone(name='User 5')
        user5 = db.execute(tx)
        assert user5.name == 'User 5'

    def test_nested_commit(self):
        assert len(db.User) == 0
        # Execute a transaction that fails.
        tx = db.User.t.create_foo_and_bar()
        db.execute(tx)
        # Two users should have been created.
        assert len(db.User) == 2
        assert db.User[1].name == 'foo'
        assert db.User[2].name == 'bar'

    def test_nested_rollback(self):
        assert len(db.User) == 0
        # Execute a transaction that fails.
        tx = db.User.t.trigger_key_collision()
        try:
            db.execute(tx)
        except error.KeyCollision, e:
            assert e.extent_name == 'User'
            assert e.key_spec == ('name',)
            assert e.field_values == (u'foo',)
        # The successful subtransaction should be rolled back.
        assert len(db.User) == 0

    def test_execute_only_once(self):
        """Transaction instances may be stored for later reference by
        the database and have additional state information added to
        them.  For this reason, transactions can only be executed
        once."""
        # Execute a transaction once, successfully.
        tx = db.User.t.create(name='foo')
        result = db.execute(tx)
        # Executing the transaction again is not allowed.
        try:
            db.execute(tx)
        except error.TransactionAlreadyExecuted, e:
            assert e.transaction == tx
        assert len(db.User) == 1

    def test_sys_executed(self):
        """You can tell if a transaction has been executed yet by
        checking its sys.executed flag."""
        tx = db.User.t.create(name='foo')
        assert not tx.s.executed
        db.execute(tx)
        assert tx.s.executed

    def test_subtransactions(self):
        tx = db.t.subtransactions()
        db.execute(tx)
        # The result is that eight users with the following OIDs
        # should exist in the User extent, all with revision 0: 1, 2,
        # 3, 5, 6, 8, 9, 13
        oids = [1, 2, 3, 5, 6, 8, 9, 13]
        assert len(db.User) == len(oids)
        for oid in oids:
            user = db.User[oid]
            assert user.name == str(oid)
            assert user.s.rev == 0

    def test_only_one_top_level(self):
        # Cannot pass more than one top-level transaction.
        tx1 = db.User.t.create(name='1')
        tx2 = db.User.t.create(name='2')
        assert raises(RuntimeError, db.execute, tx1, tx2)
        # Must pass at least one top-level transaction.
        assert raises(RuntimeError, db.execute)

    def test_failing_transaction_subclass(self):
        # Creating a cog should result in also creating five
        # sprockets.
        tx = db.Cog.t.create(name='Cogswell')
        cog = db.execute(tx)
        assert cog.s.count('Sprocket', 'cog') == 5
        # However, creating a cog with a name of 'Spacely' should
        # result in only a cog being created, and no sprockets.
        len_cogs = len(db.Cog)
        len_sprockets = len(db.Sprocket)
        tx = db.Cog.t.create(name='Spacely')
        cog = db.execute(tx)
        assert len(db.Cog) == len_cogs + 1
        assert len(db.Sprocket) == len_sprockets

    def test_undo(self):
        # Execute a complex transaction, keeping track of before and
        # after stats.
        before_len = len(db.User)
        tx = db.t.subtransactions()
        # Prior to execution, a transaction cannot be undone.
        try:
            tx._undo()
        except error.TransactionNotExecuted, e:
            assert e.transaction == tx
        # Continue with execution, storing the undo.
        db.execute(tx)
        after_len = len(db.User)
        undo_tx = tx._undo()
        # Execute the undo transaction and verify its side effects.
        db.execute(undo_tx)
        assert len(db.User) == before_len
        # Inverting an undo transaction works as expected.
        undo_undo_tx = undo_tx._undo()
        db.execute(undo_undo_tx)
        assert len(db.User) == after_len
        # And so forth...
        undo_undo_undo_tx = undo_undo_tx._undo()
        db.execute(undo_undo_undo_tx)
        assert len(db.User) == before_len

    def test_undo_unavailable(self):
        # Some transactions cannot be undone, if their _undo method
        # returns None.
        tx = db.Realm.t.create(name='xyz')
        realm = db.execute(tx)
        assert tx._undo() is None

    def test_f_delattr(self):
        # The create_name_only transaction method for the User extent
        # deletes the .age field from the transaction's .f namespace.
        tx = db.User.t.create_name_only()
        assert tx.s.field_map().keys() == ['name']
        tx.name = 'foo'
        # 'age' isn't required, so the transaction will execute just
        # fine.
        user = db.execute(tx)
        assert user.name == 'foo'
        assert user.age is UNASSIGNED
        # If we were to delete the .name field from a Create
        # transaction though, it will fail upon execution since .name
        # is required.
        tx = db.User.t.create()
        del tx.f.name
        assert tx.s.field_map().keys() == ['age']
        tx.age = 5
        assert raises(AttributeError, db.execute, tx)

# These test_f_... tests attempt to make changes to the f namespace
# directly, but we have so much metaclass magic that you can't really
# do that any more.  So these tests will need to be changed to go
# about things some other way.

##     def test_f_setattr(self):
##         # Attempting to add an existing field to an .f namespace
##         # results in an AttributeError.
##         tx = db.User.t.create()
##         f = field.Field(None, None)
##         assert raises(AttributeError, setattr, tx.f, 'age', f)
##         # Removing an existing field and adding a different field in
##         # its place succeeds.  The field's `instance` and `attribute`
##         # are synced to the transaction and the field name regardless
##         # of what is passed to the field constructor.
##         del tx.f.age
##         tx.f.age = f
##         assert f._instance is tx
##         assert f._attribute == 'age'
##         # The value assigned to an attribute must be a field instance.
##         del tx.f.age
##         assert raises(ValueError, setattr, tx.f, 'age', 5)
##         # Field assignment ordering is kept.
##         tx = db.User.t.create()
##         fname = tx.f.name
##         fage = tx.f.age
##         del tx.f.name
##         del tx.f.age
##         tx.f.age = fage
##         tx.f.name = fname
##         assert tx.s.field_map().keys() == ['age', 'name']

##     def test_f_setattr_extra(self):
##         # Because some subclasses of standard transactions extend the
##         # field namespace to accommodate custom behavior, extra fields
##         # are ignored when creating an entity.
##         tx = db.User.t.create()
##         tx.f.extra = field.Field(None, None)
##         tx.name = 'foo'
##         tx.age = 12
##         tx.extra = 1.23
##         assert tx.extra == 1.23
##         user = db.execute(tx)
##         assert user.name == 'foo'
##         assert user.age == 12
##         assert raises(AttributeError, getattr, user, 'extra')
##         # Make sure extra fields on update are ignored as well.
##         tx = user.t.update()
##         tx.f.extra = field.Field(None, None)
##         # Make sure the field has a label.
##         assert label(tx.f.extra) == 'Extra'
##         tx.name = 'bar'
##         tx.age = 15
##         tx.extra = 2.34
##         assert tx.extra == 2.34
##         db.execute(tx)
##         assert user.name == 'bar'
##         assert user.age == 15
##         assert raises(AttributeError, getattr, user, 'extra')
##         # If labels are already given, don't apply one automatically.
##         tx = user.t.update()
##         f = field.Field(None, None)
##         f.label = 'Extar'
##         tx.f.extra = f
##         assert label(tx.f.extra) == 'Extar'

##     def test_f_setattr_fielddef(self):
##         # Add another field using field constructor.
##         f = db.schema.f
##         tx = db.User.t.create()
##         tx.f.extra = f.field()
##         # Make sure the field has a label.
##         assert label(tx.f.extra) == 'Extra'
##         assert isinstance(tx.f.extra, field.Field)
##         # If labels are already given, don't apply one automatically.
##         del tx.f.extra
##         tx.f.extra = f.field(label='Extar')
##         assert label(tx.f.extra) == 'Extar'

    def test_outermost_transaction_is_strict(self):
        # Even if strict is set to False when executing an outermost
        # transaction, it will still be executed strictly.
        tx = db.User.t.create()
        assert raises(AttributeError, db.execute, tx, strict=False)

    def test_cannot_relax_outside_transaction(self):
        assert raises(RuntimeError, db.LoopSegment.relax_index, 'next')

    def test_relaxed_index(self):
        # Create a loop of three segments using a transaction that
        # relaxes a unique index.
        tx = db.LoopSegment.t.create_loop()
        tx.count = 3
        first = db.execute(tx)
        assert first.next.next.next == first

    def test_relaxed_index_collision(self):
        # Create a loop of three segments using a transaction that
        # relaxes a unique index.
        tx = db.LoopSegment.t.create_loop()
        tx.count = 3
        first = db.execute(tx)
        assert first.next.next.next == first
        # Now do something that causes a key collision.
        tx = db.LoopSegment.t.dirty_create_loop()
        tx.count = 3
        try:
            db.execute(tx)
        except error.KeyCollision, e:
            assert e.extent_name == 'LoopSegment'
            assert e.key_spec == ('next',)
            assert e.field_values == (UNASSIGNED,)
        # Make sure stuff was cleaned up.
        assert len(db.LoopSegment) == 3
        # Make sure we can still do things successfully.
        tx = db.LoopSegment.t.create_loop()
        tx.count = 3
        first = db.execute(tx)
        assert first.next.next.next == first
        assert len(db.LoopSegment) == 6

    def test_parent_delete_before_execute(self):
        # Create user and realm.
        user = db.execute(db.User.t.create(name='foo'))
        realm = db.execute(db.Realm.t.create(name='bar'))
        # Create a 'create' transaction that references them.
        tx = db.Avatar.t.create(user=user, realm=realm, name='avi')
        # Delete the user.
        db.execute(user.t.delete())
        # Check that the proper exception is raised due to the missing
        # entity.
        try:
            db.execute(tx)
        except error.EntityDoesNotExist, e:
            assert e.extent_name == 'User'
            assert e.field_name == 'user'
        # Perform the same check with regard to update transactions.
        user = db.execute(db.User.t.create(name='foo'))
        user2 = db.execute(db.User.t.create(name='baz'))
        avatar = db.execute(db.Avatar.t.create(
            name='xyz', user=user, realm=realm))
        tx = avatar.t.update(user=user2)
        db.execute(user2.t.delete())
        try:
            db.execute(tx)
        except error.EntityDoesNotExist, e:
            assert e.extent_name == 'User'
            assert e.field_name == 'user'

    def test_calc_fields_in_create_or_update(self):
        # Calculated fields within a custom transaction should be ignored.
        foo = db.execute(db.FooWithCalc.t.create(name='Foo'))
        assert foo.name == 'Foo'
        db.execute(foo.t.update(name='Bar'))
        assert foo.name == 'Bar'

    def test_extra_fields(self):
        # A normal Gender create does not normally have fget fields in
        # the transaction, but in ProblemGender we've inserted them as
        # fields of different types.
        tx = db.ProblemGender.t.create()
        assert sorted(tx.s.field_map().keys()) == [
            'code', 'count', 'foo', 'name']
        # When executing the transaction, the superclass T.Create
        # should ignore .count since it was an fget field.
        tx.code = 'X'
        tx.name = 'xyz'
        tx.count = 'foo'
        tx.foo = 5
        pgender = db.execute(tx)
        # Accessing the count directly should result in a calculated
        # value.
        assert pgender.count == 0
        # Peek in the database to make sure that it didn't get stored
        # in the database as a string though, since in cases where the
        # type of the calculated field is an entity field
        assert db._entity_field(
            'ProblemGender', pgender.s.oid, 'count') != 'foo'
        assert raises(KeyError, db._entity_field, 'ProblemGender',
                      pgender.s.oid, 'foo')
        # Same thing for updates.
        tx = pgender.t.update()
        tx.count = 'bar'
        tx.foo = 10
        pgender = db.execute(tx)
        assert pgender.count == 0
        assert db._entity_field(
            'ProblemGender', pgender.s.oid, 'count') != 'foo'
        assert raises(KeyError, db._entity_field, 'ProblemGender',
                      pgender.s.oid, 'foo')

    def test_delete_update_count_links(self):
        """Standard delete and update transactions have .s.count and
        .s.links properties corresponding to the transaction's entity."""
        exe = db.execute
        realm = exe(db.Realm.t.create(name='Foo'))
        user = exe(db.User.t.create(name='Bar'))
        avatar = exe(db.Avatar.t.create(realm=realm, user=user, name='Baz'))
        delete = realm.t.delete()
        assert delete.s.count() == realm.s.count()
        update = realm.t.update()
        assert update.s.count() == realm.s.count()

    def test_callable_wrapper(self):
        exe = db.execute
        assert len(db.User) == 0
        def fn1(db):
            exe(db.User.t.create(name='foo'))
        tx = transaction.CallableWrapper(fn1)
        exe(tx)
        assert len(db.User) == 1
        # It can also be used as a decorator.
        @transaction.CallableWrapper
        def fn2(db):
            exe(db.User.t.create(name='bar'))
        exe(fn2)
        assert len(db.User) == 2

    def test_x_namespace(self):
        tx = db.Person.t.create()
        tx.name = 'Sam'
        assert list(tx.x) == ['current_name_len']
        assert tx.x.current_name_len() == 3
        tx.x.arbitrary = 6
        assert sorted(tx.x) == ['arbitrary', 'current_name_len']
        assert tx.x.arbitrary == 6


# class TestTransaction1(BaseTransaction):

#     include = True

#     format = 1

#     def internal_update_entities_1(self, expected):
#         person_entity = db.Person.findone(name='Some person')
#         root = db._root
#         schevo = root['SCHEVO']
#         extent_name_id = schevo['extent_name_id']
#         extents = schevo['extents']
#         Gender_extent_id = extent_name_id['Gender']
#         Person_extent_id = extent_name_id['Person']
#         Gender_extent = extents[Gender_extent_id]
#         Person_extent = extents[Person_extent_id]
#         Gender_field_name_id = Gender_extent['field_name_id']
#         Person_field_name_id = Person_extent['field_name_id']
#         # Check for p.gender having correct field values.
#         p = Person_extent['entities'][person_entity.s.oid]
#         p_fields = p['fields']
#         Person_gender_field_id = Person_field_name_id['gender']
#         p_gender = p_fields[Person_gender_field_id]
#         assert p_gender == (Gender_extent_id, expected.s.oid)


class TestTransaction2(BaseTransaction):

    include = True

    format = 2

    def internal_update_entities_1(self, expected):
        person_entity = db.Person.findone(name='Some person')
        root = db._root
        schevo = root['SCHEVO']
        extent_name_id = schevo['extent_name_id']
        extents = schevo['extents']
        Gender_extent_id = extent_name_id['Gender']
        Person_extent_id = extent_name_id['Person']
        Gender_extent = extents[Gender_extent_id]
        Person_extent = extents[Person_extent_id]
        Gender_field_name_id = Gender_extent['field_name_id']
        Person_field_name_id = Person_extent['field_name_id']
        # Check for p.gender having correct related entity structures.
        p = Person_extent['entities'][person_entity.s.oid]
        p_related_entities = p['related_entities']
        Person_gender_field_id = Person_field_name_id['gender']
        p_related_genders = p_related_entities[Person_gender_field_id]
        expected_p_related_genders = frozenset([Placeholder(expected)])
        assert p_related_genders == expected_p_related_genders
