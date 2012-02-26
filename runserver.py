#!/usr/bin/env python
import os
os.environ['ENVIRONMENT'] = "development"
from kharcha import app
from kharcha.models import db
db.create_all()
app.run('0.0.0.0', debug=True, port=9000)
