#!/usr/bin/env python

from coaster.manage import init_manager

from kharcha.models import db
from kharcha import app


if __name__ == '__main__':
    db.init_app(app)
    manager = init_manager(app, db)
    manager.run()
