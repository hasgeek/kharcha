# -*- coding: utf-8 -*-

from flask import render_template
from coaster.views import load_model

from kharcha import app, lastuser
from kharcha.models import Workspace


@app.route('/<workspace>/settlements/')
@lastuser.requires_login
@load_model(Workspace, {'name': 'workspace'}, 'g.workspace', permission='view')
def settlements(workspace):
    return render_template('baseframe/message.html', message="Coming soon")
