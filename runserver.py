#!/usr/bin/env python
from kharcha import app, init_for
from kharcha.models import db
init_for('dev')
db.create_all()
app.run('0.0.0.0', debug=True, port=9000)
