# -*- coding: utf-8 -*-

from flask import render_template
from coaster.views import load_model

from kharcha import app, lastuser
from kharcha.models import Workspace


@app.route('/<workspace>/receipts')
@lastuser.requires_login
@load_model(Workspace, {'name': 'workspace'}, 'g.workspace', permission='view')
def receipts(workspace):
    # Gallery of receipts
    return render_template('baseframe/message.html', message="Coming soon")


@app.route('/<workspace>/receipts/new')
@lastuser.requires_login
@load_model(Workspace, {'name': 'workspace'}, 'g.workspace', permission='view')
def receipt_new(workspace):
    return render_template('baseframe/message.html', message="Coming soon")
