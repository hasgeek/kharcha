# -*- coding: utf-8 -*-

from flask.ext.lastuser.sqlalchemy import UserBase, TeamBase
from kharcha.models import db

__all__ = ['User', 'Team']


class User(UserBase, db.Model):
    pass


class Team(TeamBase, db.Model):
    pass
