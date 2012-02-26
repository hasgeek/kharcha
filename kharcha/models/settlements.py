# -*- coding: utf-8 -*-

from kharcha.models import db, BaseMixin, BaseNameMixin
from kharcha.models.user import User

__all__ = ['Payment']

class Payment(db.Model, BaseMixin):
    __tablename__ = 'payment'
    pass
