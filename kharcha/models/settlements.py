# -*- coding: utf-8 -*-

from kharcha.models import db, BaseMixin
from kharcha.models.user import User
from kharcha.models.workspace import Workspace

__all__ = ['Payment']


class Payment(BaseMixin, db.Model):
    __tablename__ = 'payment'
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), nullable=False)
    workspace = db.relation(Workspace, backref=db.backref('payments', cascade='all, delete-orphan'))
    #: User who made the payment
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship(User, primaryjoin=user_id == User.id,
        backref=db.backref('payouts', cascade='all, delete-orphan'))
    #: User-reported date when payment was made
    date = db.Column(db.Date, nullable=False)
    #: Currency for payment
    currency = db.Column(db.Unicode(3), nullable=False, default=u'INR')
    #: Amount of payment
    amount = db.Column(db.Numeric(10, 2), default=0, nullable=False)
