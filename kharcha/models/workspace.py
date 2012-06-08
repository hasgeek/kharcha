# -*- coding: utf-8 -*-

from kharcha.models import db, BaseNameMixin

__all__ = ['Workspace']


class Workspace(BaseNameMixin, db.Model):
    """
    Workspaces contain expense reports, budgets and categories. Workspaces
    correspond to organizations in LastUser.
    """
    __tablename__ = 'workspace'
    userid = db.Column(db.Unicode(22), nullable=False, unique=True)
    currency = db.Column(db.Unicode(3), nullable=False)
