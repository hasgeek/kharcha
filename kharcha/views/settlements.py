# -*- coding: utf-8 -*-

from flask import render_template
from coaster.views import load_model

from kharcha import app
from kharcha.models import Workspace
from kharcha.views.login import requires_workspace_member


@app.route('/<workspace>/settlements/')
@load_model(Workspace, {'name': 'workspace'}, 'workspace')
@requires_workspace_member
def settlements(workspace):
    return render_template('baseframe/message.html', message="Coming soon")
