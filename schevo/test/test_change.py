"""Notification / changeset unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.change import CREATE, DELETE, UPDATE, normalize
from schevo.constant import UNASSIGNED
from schevo import error
from schevo.signal import TransactionExecuted
from schevo.test import CreatesSchema, raises
from schevo.transaction import Transaction

try:
    import louie
except ImportError:
    louie = None
else:
    from schevo.change import Distributor


BODY = '''
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


class CreateCreate(T.Transaction):

    def _execute(self, db):
        User = db.User
        user1 = db.execute(User.t.create(name='1'))
        user2 = db.execute(User.t.create(name='2'))
        return (user1, user2)

def t_create_create():
    return CreateCreate()


class CreateDelete(T.Transaction):

    def _execute(self, db):
        user = db.execute(db.User.t.create(name='1'))
        oid = user.s.oid
        db.execute(user.t.delete())
        return oid

def t_create_delete():
    return CreateDelete()


class CreateUpdate(T.Transaction):

    def _execute(self, db):
        user = db.execute(db.User.t.create(name='1'))
        db.execute(user.t.update(name='2'))
        return user

def t_create_update():
    return CreateUpdate()


class UpdateUpdate(T.Transaction):

    user = f.entity('User')

    def _execute(self, db):
        user = self.user
        db.execute(user.t.update(name='2'))
        db.execute(user.t.update(name='3'))
        return user

def t_update_update(user):
    tx = UpdateUpdate()
    tx.user = user
    return tx
'''


class BaseChangeset(CreatesSchema):
    """Upon execution of a transaction, a list of changes that it made
    becomes available regarding Create, Delete, and Update operations
    that occurred in each extent.
    """

    body = BODY

    def test_not_executed(self):
        tx = db.User.t.create()
        # Transaction must be executed before its changes is
        # available.
        try:
            changes = tx._changes
        except error.TransactionNotExecuted, e:
            assert e.transaction == tx

    def test_create(self):
        tx = db.User.t.create(name='foo')
        user = db.execute(tx)
        oid = user.s.oid
        changes = tx.s.changes
        assert list(changes) == [
            (CREATE, 'User', oid),
            ]
        summary = tx.s.summarize()
        assert summary.creates == dict(User=set([oid]))
        assert summary.deletes == dict()
        assert summary.updates == dict()

    def test_delete(self):
        tx = db.User.t.create(name='foo')
        user = db.execute(tx)
        oid = user.s.oid
        tx = user.t.delete()
        db.execute(tx)
        changes = tx.s.changes
        assert list(changes) == [
            (DELETE, 'User', oid),
            ]
        summary = tx.s.summarize()
        assert summary.creates == dict()
        assert summary.deletes == dict(User=set([oid]))
        assert summary.updates == dict()

    def test_update(self):
        tx = db.User.t.create(name='foo')
        user = db.execute(tx)
        oid = user.s.oid
        tx = user.t.update(name='bar')
        db.execute(tx)
        changes = tx.s.changes
        assert list(changes) == [
            (UPDATE, 'User', oid),
            ]
        summary = tx.s.summarize()
        assert summary.creates == dict()
        assert summary.deletes == dict()
        assert summary.updates == dict(User=set([oid]))

    def test_create_create(self):
        tx = db.t.create_create()
        user1, user2 = db.execute(tx)
        changes = tx.s.changes
        assert list(changes) == [
            (CREATE, 'User', user1.s.oid),
            (CREATE, 'User', user2.s.oid),
            ]
        assert list(changes) == list(normalize(changes))
        summary = tx.s.summarize()
        assert summary.creates == dict(
            User=set([user1.s.oid, user2.s.oid]))
        assert summary.deletes == dict()
        assert summary.updates == dict()

    def test_create_delete(self):
        tx = db.t.create_delete()
        oid = db.execute(tx)
        changes = tx.s.changes
        assert list(changes) == [
            (CREATE, 'User', oid),
            (DELETE, 'User', oid),
            ]
        changes = normalize(changes)
        assert list(changes) == []
        summary = tx.s.summarize()
        assert summary.creates == dict()
        assert summary.deletes == dict()
        assert summary.updates == dict()

    def test_create_update(self):
        tx = db.t.create_update()
        user = db.execute(tx)
        changes = tx.s.changes
        assert list(changes) == [
            (CREATE, 'User', user.s.oid),
            (UPDATE, 'User', user.s.oid),
            ]
        changes = normalize(changes)
        assert list(changes) == [
            (CREATE, 'User', user.s.oid),
            ]
        summary = tx.s.summarize()
        assert summary.creates == dict(User=set([user.s.oid]))
        assert summary.deletes == dict()
        assert summary.updates == dict()

    def test_update_update(self):
        user = db.execute(db.User.t.create(name='1'))
        tx = db.t.update_update(user)
        db.execute(tx)
        changes = tx.s.changes
        assert list(changes) == [
            (UPDATE, 'User', user.s.oid),
            (UPDATE, 'User', user.s.oid),
            ]
        changes = normalize(changes)
        assert list(changes) == [
            (UPDATE, 'User', user.s.oid),
            ]
        summary = tx.s.summarize()
        assert summary.creates == dict()
        assert summary.deletes == dict()
        assert summary.updates == dict(User=set([user.s.oid]))


class BaseExecuteNotification(CreatesSchema):
    """The database object, when told to do so, dispatches
    notifications of transaction execution using Louie."""

    body = BODY

    class Subscriber(object):
        """Knows how to properly receive execute notifications."""

        def __init__(self):
            self.received = []

        def __call__(self, transaction):
            self.received.append(transaction)

    if louie is not None:
        def test_notification(self):
            louie.reset()
            User = db.User
            subscriber = self.Subscriber()
            louie.connect(subscriber, TransactionExecuted)
            # Execute a transaction before telling the database to
            # dispatch messages.
            tx = User.t.create(name='foo')
            db.execute(tx)
            assert tx not in subscriber.received
            # Turn on dispatching and execute another.
            db.dispatch = True
            tx = User.t.create(name='bar')
            db.execute(tx)
            assert tx in subscriber.received


if louie is not None:
    class BaseDistributor(CreatesSchema):
        """Given a list of changes made by transaction(s) and a mapping of
        change notification criteria to objects that are interested in
        changes matching each criteria, a Distributor object will notify
        those interested objects of only those changes that they are
        interested in.

        The criteria may be totally general to receive notifications about
        all changes, or may specify a type of change, a type of change and
        an extent name, or a type of change and an extent name and an
        entity OID.

        Listening objects must have a `changes_made(changes)` callable
        attribute in order to receive notifications.
        """

        body = BODY

        class Watcher(object):

            def __init__(self):
                self.received = []

            def __call__(self, change):
                self.received.append(change)

        def setUp(self):
            CreatesSchema.setUp(self)
            louie.reset()
            db.dispatch = True
            dist = self.dist = Distributor(db)

        def test_receive_all(self):
            watcher = self.Watcher()
            self.dist.subscribe(watcher)
            tx = db.User.t.create(name='foo')
            user = db.execute(tx)
            oid = user.s.oid
            self.dist.distribute()
            tx = user.t.delete()
            db.execute(tx)
            self.dist.distribute()
            assert list(watcher.received) == [
                (CREATE, 'User', oid),
                (DELETE, 'User', oid),
                ]

        def test_receive_all_normalized(self):
            watcher = self.Watcher()
            self.dist.subscribe(watcher)
            tx = db.User.t.create(name='foo')
            user = db.execute(tx)
            oid = user.s.oid
            tx = user.t.delete()
            db.execute(tx)
            self.dist.distribute()
            assert list(watcher.received) == [
                ]

        def test_receive_all_unsubscribe(self):
            watcher = self.Watcher()
            self.dist.subscribe(watcher)
            tx = db.User.t.create(name='foo')
            user = db.execute(tx)
            oid = user.s.oid
            self.dist.distribute()
            self.dist.unsubscribe(watcher)
            tx = user.t.delete()
            db.execute(tx)
            self.dist.distribute()
            assert list(watcher.received) == [
                (CREATE, 'User', oid),
                ]

        def test_receive_specific(self):
            watcher = self.Watcher()
            self.dist.subscribe(watcher, DELETE)
            tx = db.User.t.create(name='foo')
            user = db.execute(tx)
            oid = user.s.oid
            self.dist.distribute()
            tx = user.t.delete()
            db.execute(tx)
            self.dist.distribute()
            assert list(watcher.received) == [
                (DELETE, 'User', oid),
                ]

        def test_receive_specific_normalized(self):
            watcher = self.Watcher()
            self.dist.subscribe(watcher, DELETE)
            tx = db.User.t.create(name='foo')
            user = db.execute(tx)
            oid = user.s.oid
            tx = user.t.delete()
            db.execute(tx)
            self.dist.distribute()
            assert list(watcher.received) == [
                ]

        def test_receive_all_autodistribute(self):
            self.dist.auto_distribute = True
            watcher = self.Watcher()
            self.dist.subscribe(watcher)
            tx = db.User.t.create(name='foo')
            user = db.execute(tx)
            oid = user.s.oid
            tx = user.t.delete()
            db.execute(tx)
            assert list(watcher.received) == [
                (CREATE, 'User', oid),
                (DELETE, 'User', oid),
                ]


# class TestChangeset1(BaseChangeset):

#     include = True

#     format = 1


class TestChangeset2(BaseChangeset):

    include = True

    format = 2


# class TestExecuteNotification1(BaseExecuteNotification):

#     include = True

#     format = 1


class TestExecuteNotification2(BaseExecuteNotification):

    include = True

    format = 2


if louie is not None:
#     class TestDistributor1(BaseDistributor):

#         include = True

#         format = 1


    class TestDistributor2(BaseDistributor):

        include = True

        format = 2
