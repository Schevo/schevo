"""Entity/extent unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import datetime
import random

from schevo.constant import UNASSIGNED
from schevo import error
from schevo import test
from schevo.test import CreatesSchema, raises
from schevo.transaction import Transaction


class BaseEntityExtent(CreatesSchema):

    body = '''

    from schevo.test import raises

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

        @extentmethod
        def t_multiple_keys_create(extent):
            return T.Multiple_Keys_Create()

        @extentmethod
        def t_multiple_keys_update(extent):
            return T.Multiple_Keys_Update()

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


    class Foo(E.Entity):

        name = f.string()
        user = f.entity('User', required=False)

        _key(name, user)


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


    class Event(E.Entity):
        """An event must have a unique date and datetime, but none are
        required."""

        date = f.date(required=False)
        datetime = f.datetime(required=False)

        _key(date)
        _key(datetime)


    class Multiple_Keys_Create(T.Transaction):

        def _execute(self, db):
            # Whitespace is due to lack of syntax highlighting.
            Batch_Job = db.Batch_Job
            # Create an entity successfully.
            tx = Batch_Job.t.create(name='foo', priority=1)
            result = db.execute(tx)
            # Creating these should fail because of collisions.
            tx = Batch_Job.t.create(name='bar', priority=1)
            try:
                db.execute(tx)
            except schevo.error.KeyCollision, e:
                assert e.extent_name == 'Batch_Job'
                assert e.key_spec == ('priority',)
                assert e.field_values == (1,)
            tx = Batch_Job.t.create(name='foo', priority=2)
            try:
                db.execute(tx)
            except schevo.error.KeyCollision, e:
                assert e.extent_name == 'Batch_Job'
                assert e.key_spec == ('name',)
                assert e.field_values == (u'foo',)
            # Creating this should succeed as no side-effects should be
            # left behind from the previous failure.
            tx = Batch_Job.t.create(name='bar', priority=2)
            result = db.execute(tx)


    class Multiple_Keys_Update(T.Transaction):

        def _execute(self, db):
            Batch_Job = db.Batch_Job
            # Create an entity successfully.
            tx = Batch_Job.t.create(name='foo', priority=1)
            result_foo = db.execute(tx)
            # Create another entity successfully.
            tx = Batch_Job.t.create(name='bar', priority=2)
            result_bar = db.execute(tx)
            # Updating the second one should fail because of collisions.
            tx = result_bar.t.update(name='foo', priority=3)
            try:
                db.execute(tx)
            except schevo.error.KeyCollision, e:
                assert e.extent_name == 'Batch_Job'
                assert e.key_spec == ('name',)
                assert e.field_values == (u'foo',)
            tx = result_bar.t.update(name='baz', priority=1)
            try:
                db.execute(tx)
            except schevo.error.KeyCollision, e:
                assert e.extent_name == 'Batch_Job'
                assert e.key_spec == ('priority',)
                assert e.field_values == (1,)
            # Creating this should succeed as no side-effects should be
            # left behind from the previous failure.
            tx = Batch_Job.t.create(name='baz', priority=3)
            result = db.execute(tx)


    class UserRealmAvatar(T.Transaction):

        def _execute(self, db):
            # Create a user using attribute-setting syntax.
            tx = db.User.t.create()
            tx.name = 'foo'
            user = db.execute(tx)
            # Create a realm using attribute-setting syntax.
            tx = db.Realm.t.create()
            tx.name = 'bar'
            realm = db.execute(tx)
            # Create an avatar using keyword convenience syntax.
            tx = db.Avatar.t.create(
                name='baz',
                user=user,
                realm=realm,
                )
            avatar = db.execute(tx)
            # Return the three.
            return user, realm, avatar

    def t_user_realm_avatar():
        return UserRealmAvatar()


    class LotsOfUsers(T.Transaction):

        def _execute(self, db):
            from random import randint
            def randname():
                name = []
                for x in xrange(randint(5, 15)):
                    name.append(randint(ord('a'), ord('z')))
                return ''.join(chr(c) for c in name)
            for x in xrange(100):
                name = randname()
                if not db.User.find(db.User.f.name == name):
                    name = randname()
                    # Make sure that there is some overlap in 'age' to
                    # trigger faulty key collisions.
                    age = randint(20, 25)
                    tx = db.User.t.create(name=name, age=age)
                    db.execute(tx)

    def t_lots_of_users():
        return LotsOfUsers()
    '''

    def test_key_conflicts_on_create(self):
        extent = db.User
        # Create an entity.
        tx = extent.t.create(name='foo')
        user_foo = db.execute(tx)
        # Attempting to create another user named 'foo' results in a
        # KeyError.
        self.reopen()
        extent = db.User
        tx = extent.t.create(name='foo')
        try:
            db.execute(tx)
        except error.KeyCollision, e:
            assert e.extent_name == 'User'
            assert e.key_spec == ('name',)
            assert e.field_values == (u'foo',)

    def test_no_key_conflicts_on_create_if_necessary(self):
        # Create an entity.
        tx = db.User.t.create(name='foo')
        user_foo = db.execute(tx)
        # Attempting to create-if-necessary another user named 'foo'
        # results in the original user.
        tx = db.User.t.create_if_necessary(name='foo')
        user_foo2 = db.execute(tx)
        assert user_foo == user_foo2
        assert user_foo2.s.rev == 0

    def test_key_conflicts_on_update(self):
        extent = db.User
        # Create an entity.
        tx = extent.t.create(name='foo')
        user_foo = db.execute(tx)
        # Creating another user, then attempting to rename it to 'foo'
        # results in a KeyError.
        self.reopen()
        extent = db.User
        tx = extent.t.create(name='bar')
        user_bar = db.execute(tx)
        tx = user_bar.t.update(name='foo')
        try:
            db.execute(tx)
        except error.KeyCollision, e:
            assert e.extent_name == 'User'
            assert e.key_spec == ('name',)
            assert e.field_values == (u'foo',)

    def test_no_key_conflicts_on_delete(self):
        extent = db.User
        # Create an entity.
        tx = extent.t.create(name='foo')
        user_foo = db.execute(tx)
        # If we delete user_foo, then attempt to recreate another user
        # named 'foo', it should succeed.
        self.reopen()
        extent = db.User
        user_foo = extent[1]
        tx = user_foo.t.delete()
        db.execute(tx)
        self.reopen()
        extent = db.User
        tx = extent.t.create(name='foo')
        user_foo = db.execute(tx)
        assert user_foo.s.oid == 2

    def test_multiple_keys_create(self):
        tx = db.Batch_Job.t.multiple_keys_create()
        db.execute(tx)
        self.reopen()
        assert len(db.Batch_Job) == 2
        assert db.Batch_Job[1].name == 'foo'
        assert db.Batch_Job[1].priority == 1
        assert db.Batch_Job[2].name == 'bar'
        assert db.Batch_Job[2].priority == 2

    def test_multiple_keys_update(self):
        tx = db.Batch_Job.t.multiple_keys_update()
        db.execute(tx)
        self.reopen()
        assert len(db.Batch_Job) == 3
        assert db.Batch_Job[1].name == 'foo'
        assert db.Batch_Job[1].priority == 1
        assert db.Batch_Job[2].name == 'bar'
        assert db.Batch_Job[2].priority == 2
        assert db.Batch_Job[3].name == 'baz'
        assert db.Batch_Job[3].priority == 3

    def test_date_datetime_keys(self):
        dt = datetime.datetime.now()
        d = dt.date()
        t = dt.time()
        # Create and delete events that don't conflict with keys to
        # make sure they are persisted correctly.
        event1 = db.execute(db.Event.t.create(datetime=dt))
        assert event1.datetime == dt
        event2 = db.execute(db.Event.t.create(date=d))
        assert event2.date == d
        db.execute(event1.t.delete())
        db.execute(event2.t.delete())
        event1 = db.execute(db.Event.t.create(date=d))
        assert event1.date == d
        event2 = db.execute(db.Event.t.create(datetime=dt))
        assert event2.datetime == dt

    def test_entity_reference_resolution_create(self):
        user, realm, avatar = self.db.execute(db.t.user_realm_avatar())
        # Test entity reference equality.
        self.reopen()
        avatar = db.Avatar[1]
        user = db.User[1]
        realm = db.Realm[1]
        assert avatar.user == user
        assert avatar.realm == realm

    def test_entity_reference_resolution_update(self):
        user1, realm, avatar = self.db.execute(db.t.user_realm_avatar())
        # Create another user.
        tx = db.User.t.create(name='foo2')
        user2 = db.execute(tx)
        # Update the avatar.
        self.reopen()
        avatar = db.Avatar[1]
        user1 = db.User[1]
        user2 = db.User[2]
        tx = avatar.t.update(user=user2)
        db.execute(tx)
        # Verify that the entity reference got updated.
        self.reopen()
        avatar = db.Avatar[1]
        user1 = db.User[1]
        user2 = db.User[2]
        assert avatar.user != user1
        assert avatar.user == user2

    def test_entity_links_create(self):
        user, realm, avatar = self.db.execute(db.t.user_realm_avatar())
        # No arguments to links().
        self.reopen()
        user = db.User[1]
        realm = db.Realm[1]
        avatar = db.Avatar[1]
        user_links = user.s.links()
        realm_links = realm.s.links()
        assert len(user_links) == 1
        assert len(realm_links) == 1
        assert ('Avatar', 'user') in user_links
        assert ('Avatar', 'realm') in realm_links
        avatar_user = user_links[('Avatar', 'user')]
        assert len(avatar_user) == 1
        assert avatar_user[0] == avatar
        avatar_realm = realm_links[('Avatar', 'realm')]
        assert len(avatar_realm) == 1
        assert avatar_realm[0] == avatar
        # Argument to links.
        user_links = user.s.links('Avatar', 'user')
        assert len(user_links) == 1
        assert user_links[0] == avatar
        realm_links = realm.s.links('Avatar', 'realm')
        assert len(realm_links) == 1
        assert realm_links[0] == avatar
        # Extent name typo.
        try:
            realm.s.links('Ratava', 'realm')
        except error.ExtentDoesNotExist, e:
            assert e.extent_name == 'Ratava'

    def test_entity_links_update(self):
        user1, realm, avatar = self.db.execute(db.t.user_realm_avatar())
        # Create another user.
        self.reopen()
        tx = db.User.t.create(name='foo2')
        user2 = db.execute(tx)
        # Update the avatar.
        self.reopen()
        avatar = db.Avatar[1]
        user2 = db.User[2]
        tx = avatar.t.update(user=user2)
        db.execute(tx)
        # Verify that links got updated.
        self.reopen()
        user1 = db.User[1]
        user2 = db.User[2]
        realm = db.Realm[1]
        avatar = db.Avatar[1]
        links = user1.s.links()
        assert len(links) == 0
        links = user2.s.links()
        assert len(links) == 1
        assert ('Avatar', 'user') in links
        avatar_user = links[('Avatar', 'user')]
        assert len(avatar_user) == 1
        assert avatar_user[0] == avatar

    def test_entity_links_delete(self):
        user, realm, avatar = self.db.execute(db.t.user_realm_avatar())
        tx = avatar.t.delete()
        db.execute(tx)
        # Links should no longer exist.
        self.reopen()
        user = db.User[1]
        realm = db.Realm[1]
        assert len(user.s.links()) == 0
        assert len(realm.s.links()) == 0

    def test_entity_links_filter(self):
        user, realm, avatar = db.execute(db.t.user_realm_avatar())
        # Create two filters.
        user_links_filter = user.s.links_filter('Avatar', 'user')
        realm_links_filter = realm.s.links_filter('Avatar', 'realm')
        # Initially, the results of calling each filter only results
        # in one item each.
        user_links = user_links_filter()
        assert len(user_links) == 1
        assert user_links[0] == avatar
        realm_links = realm_links_filter()
        assert len(realm_links) == 1
        assert realm_links[0] == avatar
        # Create another realm and another avatar for the same user.
        tx = db.Realm.t.create(name='xyz')
        realm2 = db.execute(tx)
        tx = db.Avatar.t.create(name='abc', user=user, realm=realm2)
        avatar2 = db.execute(tx)
        # Calling the user_links_filter again should result in two
        # results this time.
        user_links = user_links_filter()
        assert len(user_links) == 2
        user_links = [(e.s.extent.name, e.s.oid) for e in user_links]
        assert ('Avatar', avatar.s.oid) in user_links
        assert ('Avatar', avatar2.s.oid) in user_links

    def test_entity_links_bad_args(self):
        user, realm, avatar = self.db.execute(db.t.user_realm_avatar())
        self.reopen()
        user = db.User[1]
        args = ('Avatar', 'userr')
        try:
            user.s.links(*args)
        except error.FieldDoesNotExist, e:
            assert e.object_or_name == 'Avatar'
            assert e.field_name == 'userr'
        try:
            user.s.links_filter(*args)
        except error.FieldDoesNotExist, e:
            assert e.object_or_name == 'Avatar'
            assert e.field_name == 'userr'
        args = ('Avatarr', 'user')
        try:
            user.s.links(*args)
        except error.ExtentDoesNotExist, e:
            assert e.extent_name == 'Avatarr'
        try:
            user.s.links_filter(*args)
        except error.ExtentDoesNotExist, e:
            assert e.extent_name == 'Avatarr'

    def test_entity_delete_restrict(self):
        self.db.execute(db.t.user_realm_avatar())
        self.reopen()
        user = db.User[1]
        realm = db.Realm[1]
        avatar = db.Avatar[1]
        user_del_tx = user.t.delete()
        try:
            db.execute(user_del_tx)
        except error.DeleteRestricted, e:
            assert e.restrictions == set([
                (user, avatar, 'user'),
                ])
        realm_del_tx = realm.t.delete()
        try:
            db.execute(realm_del_tx)
        except error.DeleteRestricted, e:
            assert e.restrictions == set([
                (realm, avatar, 'realm'),
                ])
        # After deleting the avatar, deleting user and realm becomes
        # possible.
        db.execute(avatar.t.delete())
        db.execute(user_del_tx)
        db.execute(realm_del_tx)
        self.reopen()
        assert len(db.Avatar) == 0
        assert len(db.Realm) == 0
        assert len(db.User) == 0

    def test_entity_in_extent(self):
        user, realm, avatar = self.db.execute(db.t.user_realm_avatar())
        user_extent = db.User
        realm_extent = db.Realm
        avatar_extent = db.Avatar
        # Entities are 'in' their respective extents.
        assert user in user_extent
        assert realm in realm_extent
        assert avatar in avatar_extent
        # Entities are 'not in' non-respective extents.
        assert user not in realm_extent
        assert user not in avatar_extent
        assert realm not in user_extent
        assert realm not in avatar_extent
        assert avatar not in user_extent
        assert avatar not in realm_extent
        # Entities that are deleted are no longer 'in' their
        # respective extents.
        tx = avatar.t.delete()
        db.execute(tx)
        assert avatar not in avatar_extent

    def test_field_requirements(self):
        tx = db.User.t.create()
        # User was not specified, so transaction shouldn't succeed.
        assert raises(AttributeError, db.execute, tx)
        # Even if the transaction's fields are modified, the entity's
        # field spec should remain enforced.
        tx.f.name.required = False
        assert raises(AttributeError, db.execute, tx)
        # Age should not be required though.
        tx = db.User.t.create()
        tx.name = 'foo'
        result = db.execute(tx)
        assert result.age is UNASSIGNED
        # When updating, restrictions should still be enforced.
        tx = result.t.update(name=UNASSIGNED)
        assert raises(AttributeError, db.execute, tx)
        tx.f.name.required = False
        assert raises(AttributeError, db.execute, tx)

    def test_find(self):
        user, realm, avatar = self.db.execute(db.t.user_realm_avatar())
        extent = db.User
        user1 = db.execute(extent.t.create(name='foo2', age=20))
        user2 = db.execute(extent.t.create(name='bar2', age=20))
        user3 = db.execute(extent.t.create(name='baz2', age=30))
        # Find based on one field.
        results = extent.find(extent.f.age == 20)
        assert len(results) == 2
        assert results[0] == user1 or results[0] == user2
        assert results[1] == user1 or results[1] == user2
        # Find based on two fields.
        results = extent.find((extent.f.age == 20) & (extent.f.name == 'foo2'))
        assert len(results) == 1
        assert results[0] == user1
        # Find based on an entity field.
        results = db.Avatar.find(db.Avatar.f.user == user)
        assert len(results) == 1
        assert results[0] == avatar
        # No args results in everything being found.
        results = extent.find()
        assert len(results) == 4

#     def test_find_bad_field_name(self):
#         extent = db.User
#         try:
#             extent.find(extent.f.some_field == 'some_value')
#         except error.FieldDoesNotExist, e:
#             assert e.object_or_name == 'User'
#             assert e.field_name == 'some_field'

    def test_findone(self):
        extent = db.User
        user1 = db.execute(extent.t.create(name='foo', age=20))
        user2 = db.execute(extent.t.create(name='bar', age=20))
        user3 = db.execute(extent.t.create(name='baz', age=30))
        # Findone using a key.
        result = extent.findone(extent.f.name == 'bar')
        assert result == user2
        # Findone using a unique value but not necessarily a key.
        result = extent.findone(extent.f.age == 30)
        assert result == user3

    def test_findone_found_none(self):
        extent = db.User
        user1 = db.execute(extent.t.create(name='foo', age=20))
        user2 = db.execute(extent.t.create(name='bar', age=20))
        user3 = db.execute(extent.t.create(name='baz', age=30))
        assert extent.findone(extent.f.name == 'abc') is None

    def test_findone_too_many(self):
        extent = db.User
        user1 = db.execute(extent.t.create(name='foo', age=20))
        user2 = db.execute(extent.t.create(name='bar', age=20))
        user3 = db.execute(extent.t.create(name='baz', age=30))
        try:
            extent.findone(extent.f.age == 20)
        except error.FindoneFoundMoreThanOne, e:
            assert e.extent_name == 'User'
#             assert e.criteria == dict(age=20)

    def test_findone_unassigned(self):
        extent = db.User
        user1 = db.execute(extent.t.create(name='foo', age=20))
        user2 = db.execute(extent.t.create(name='bar'))
        user3 = db.execute(extent.t.create(name='baz', age=30))
        result = extent.findone(extent.f.age == UNASSIGNED)
        assert result == user2
        extent = db.Foo
        foo = db.execute(extent.t.create(name='foo'))
        result = extent.findone((extent.f.name == 'foo')
                                & (extent.f.user == UNASSIGNED))
        assert result == foo

    def test_findone_date_datetime(self):
        dt = datetime.datetime.now()
        d = dt.date()
        t = dt.time()
        # Create events that don't conflict with keys to make sure
        # they are found correctly.
        event1 = db.execute(db.Event.t.create(datetime=dt))
        assert event1.datetime == dt
        event2 = db.execute(db.Event.t.create(date=d))
        assert event2.date == d
        result = db.Event.findone(db.Event.f.datetime == dt)
        assert result == event1
        result = db.Event.findone(db.Event.f.date == d)
        assert result == event2

    def test_transaction_error(self):
        ## skip('Temporarily unimportant')
        return
        extent = db.User
        user = db.execute(extent.t.create(name='foo', age=20))
        assert raises(AttributeError, user.t_update, name='bar')

    def test_field_namespace(self):
        extent = db.User
        user = db.execute(extent.t.create(name='foo', age=20))
        assert isinstance(user.f.name, type(user.s.field_map()['name']))
        assert isinstance(user.f.age, type(user.s.field_map()['age']))
        # Make sure entity fields are readonly, including calculated fields.
        assert user.f.name.readonly
        assert user.f.age.readonly
        male = db.execute(db.Gender.t.create(code='M', name='Male'))
        assert male.f.count.readonly

    def test_nonexistent_entity(self):
        try:
            user = db.User[99]
        except error.EntityDoesNotExist, e:
            assert e.extent_name == 'User'
            assert e.oid == 99

    def test_fget_fields(self):
        male = db.execute(db.Gender.t.create(code='M', name='Male'))
        female = db.execute(db.Gender.t.create(code='F', name='Female'))
        # Calls to .count's fget result in 0 people found for each.
        assert male.count == 0
        assert female.count == 0
        db.execute(db.Person.t.create(name='Bob', gender=male))
        db.execute(db.Person.t.create(name='Sue', gender=female))
        db.execute(db.Person.t.create(name='Sally', gender=female))
        # Calls to .count's fget now result in proper counts of people
        # found for each gender.
        assert male.count == 1
        assert female.count == 2
        # sys.field_map should also have the results of fget calls.
        male_field_map = male.s.field_map()
        assert male_field_map['count'].get() == 1
        assert male.f.count.get() == 1

    def test_extent_knows_its_next_oid(self):
        assert db.Gender.next_oid == 1
        assert db.Person.next_oid == 3
        # Property is readonly.
        assert raises(AttributeError, setattr, db.Person, 'next_oid', 2)

    def test_hash(self):
        # Make sure Entity instances behave nicely as dictionary keys.
        foo = db.execute(db.Person.t.create(name='Foo'))
        # Get another foo object based on the same person.
        same_foo = db.Person.findone(db.Person.f.name == 'Foo')
        d = {}
        d[foo] = None
        assert foo in d
        assert same_foo in d
        # Make sure another entity doesn't hash the same.
        bar = db.execute(db.Person.t.create(name='Bar'))
        assert bar not in d
        # Make sure different extents but same oid don't hash the same.
        fred = db.Person.findone(db.Person.f.name == 'Fred Flintstone')
        male = db.execute(db.Gender.t.create(code='M', name='Male'))
        assert fred.s.oid == 1
        assert male.s.oid == 1
        d = {}
        d[fred] = None
        assert male not in d

    def test_extent_by(self):
        # Create several users with random names and ages.
        tx = db.t.lots_of_users()
        db.execute(tx)
        # Get all the user names, sorted by name.
        names = [u.name for u in db.User.by('name')]
        # Make sure they're sorted right.
        assert names == sorted(names)
        # Now get them in reverse order.
        names = [u.name for u in db.User.by('-name')]
        assert names == list(reversed(sorted(names)))
        # Check for same with ages.
        ages = [u.age for u in db.User.by('age')]
        assert ages == sorted(ages)
        ages = [u.age for u in db.User.by('-age')]
        assert ages == list(reversed(sorted(ages)))
        # Check for same with age/name.
        age_names = [(u.age, u.name) for u in db.User.by('age', 'name')]
        assert age_names == sorted(age_names)
        age_names = [(u.age, u.name) for u in db.User.by('-age', '-name')]
        assert age_names == list(reversed(sorted(age_names)))
        # Check for same with name/age.
        name_ages = [(u.name, u.age) for u in db.User.by('name', 'age')]
        assert name_ages == sorted(name_ages)
        name_ages = [(u.name, u.age) for u in db.User.by('-name', '-age')]
        assert name_ages == list(reversed(sorted(name_ages)))

    def test_extent_iter(self):
        # Create several users with random names and ages.
        tx = db.t.lots_of_users()
        db.execute(tx)
        total = len(db.User)
        count = 0
        for user in db.User:
            count += 1
            assert count == user.s.oid
        assert count == total

    def test_entity_equality(self):
        """Entity instances referring to the same entity always have the same
        OID, revision, and field values, and are also equal."""
        realm = db.execute(db.Realm.t.create(name='Foo'))
        assert realm.s.oid == 1
        assert realm.s.rev == 0
        assert realm.name == 'Foo'
        realm2 = db.execute(realm.t.update(name='Bar'))
        assert realm2.s.oid == 1
        assert realm2.s.rev == 1
        assert realm2.name == 'Bar'
        assert realm == realm2
        assert realm.s.rev == 1
        assert realm.name == realm2.name

    def test_extent_sorting(self):
        """When sorting sequences of extent instances, their sort
        order is determined by their name."""
        expected = db.extent_names()
        extents = db.extents()
        random.shuffle(extents)
        extents.sort()
        extent_names = [e.name for e in extents]
        assert extent_names == expected


# class TestEntityExtent1(BaseEntityExtent):

#     include = True

#     format = 1


class TestEntityExtent2(BaseEntityExtent):

    include = True

    format = 2
