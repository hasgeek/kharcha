# -*- coding: utf-8 -*-

# The imports in this file are order-sensitive

from pytz import timezone
from flask import Flask
from flask.ext.lastuser import Lastuser
from flask.ext.lastuser.sqlalchemy import UserManager
from baseframe import baseframe, assets, Version
import coaster.app
from ._version import __version__

version = Version(__version__)
app = Flask(__name__, instance_relative_config=True)
lastuser = Lastuser()

from . import models, views
from .models import db

assets['kharcha.css'][version] = 'css/app.css'


# Configure the app
def init_for(env):
    coaster.app.init_app(app, env)
    baseframe.init_app(app, requires=['baseframe', 'jquery.expander', 'kharcha'])
    app.config.get('NETWORKBAR_LINKS', []).append({
        'name': u'kharcha',
        'title': u'Expenses',
        'url': None
        })
    lastuser.init_app(app)
    lastuser.init_usermanager(UserManager(models.db, models.User, models.Team))
    app.config['tz'] = timezone(app.config['TIMEZONE'])
