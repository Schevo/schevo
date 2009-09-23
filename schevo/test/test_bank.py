"""Bank account tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import CreatesSchema, raises


class BaseBank(CreatesSchema):

    body = '''

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
    '''

    def test_suspend(self):
        fred = db.Person.findone(name='Fred Flintstone')
        personal = db.Account.findone(owner=fred, name='Personal')
        assert personal.suspended == False
        tx = personal.t.suspend()
        db.execute(tx)
        assert personal.suspended == True

    def test_transfer_success(self):
        fred = db.Person.findone(name='Fred Flintstone')
        business = db.Account.findone(owner=fred, name='Business')
        personal = db.Account.findone(owner=fred, name='Personal')
        # Transfer from business to personal.
        tx = business.t.transfer()
        assert tx.from_account == business
        tx.to_account = personal
        tx.amount = 100.00
        db.execute(tx)
        assert business.balance == 29042.75
        assert personal.balance == 304.52
        # Overdraft protection should work.
        tx = business.t.transfer()
        tx.to_account = personal
        tx.amount = 30000.00
        db.execute(tx)
        assert business.balance == 29042.75 - 30000.00
        assert personal.balance == 304.52 + 30000.00

    def test_transfer_insufficient_funds(self):
        fred = db.Person.findone(name='Fred Flintstone')
        business = db.Account.findone(owner=fred, name='Business')
        personal = db.Account.findone(owner=fred, name='Personal')
        # Attempt transfer from personal to business.
        tx = personal.t.transfer()
        tx.to_account = business
        tx.amount = 205.00
        assert raises(Exception, db.execute, tx)

    def test_transfer_account_suspended(self):
        betty = db.Person.findone(name='Betty Rubble')
        family = db.Account.findone(owner=betty, name='Family')
        savings = db.Account.findone(owner=betty, name='Savings')
        # Attempt transfer from family to savings.
        tx = family.t.transfer()
        tx.to_account = savings
        tx.amount = 0.01
        assert raises(Exception, db.execute, tx)
        # Attempt transfer from savings to family.
        tx = savings.t.transfer()
        tx.to_account = family
        tx.amount = 0.01
        assert raises(Exception, db.execute, tx)


# class TestBank1(BaseBank):

#     include = True

#     format = 1


class TestBank2(BaseBank):

    include = True

    format = 2
