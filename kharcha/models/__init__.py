# -*- coding: utf-8 -*-

from flask.ext.sqlalchemy import SQLAlchemy
from kharcha import app
from coaster.sqlalchemy import BaseMixin, BaseNameMixin, BaseScopedNameMixin, BaseScopedIdNameMixin

db = SQLAlchemy(app)

from kharcha.models.user import *
from kharcha.models.workspace import *
from kharcha.models.expenses import *
from kharcha.models.settlements import *
from kharcha.models.attachments import *
