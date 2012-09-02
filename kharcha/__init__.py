# -*- coding: utf-8 -*-

# The imports in this file are order-sensitive

from pytz import timezone
from flask import Flask
from flask.ext.assets import Environment, Bundle
from flask.ext.lastuser import Lastuser
from flask.ext.lastuser.sqlalchemy import UserManager
from baseframe import baseframe, baseframe_js, baseframe_css, expander_js
import coaster.app

app = Flask(__name__, instance_relative_config=True)
lastuser = Lastuser()

import kharcha.models
import kharcha.views

app.register_blueprint(baseframe)

assets = Environment(app)
js = Bundle(baseframe_js, expander_js,
    filters='jsmin', output='js/packed.js')
css = Bundle(baseframe_css, 'css/app.css',
    filters='cssmin', output='css/packed.css')
assets.register('js_all', js)
assets.register('css_all', css)


# Configure the app
def init_for(env):
    coaster.app.init_app(app, env)
    lastuser.init_app(app)
    lastuser.init_usermanager(UserManager(kharcha.models.db, kharcha.models.User, kharcha.models.Team))
    app.config['tz'] = timezone(app.config['TIMEZONE'])
