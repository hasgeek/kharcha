#!/usr/bin/env python
from kharcha import app
from kharcha.models import db
db.create_all()
app.run('0.0.0.0', port=9000)
