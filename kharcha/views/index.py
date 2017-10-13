# -*- coding: utf-8 -*-

from pytz import utc
from flask import render_template, g
from coaster.views import load_model
from kharcha import app, lastuser
from kharcha.models import Category, Budget, Workspace
from kharcha.views.workflows import ExpenseReportWorkflow


@app.template_filter('shortdate')
def shortdate(date):
    if hasattr(g, 'workspace'):
        tz = g.workspace.tz
    else:
        tz = app.config['tz']
    return utc.localize(date).astimezone(tz).strftime('%e %b')


@app.template_filter('longdate')
def longdate(date):
    if hasattr(g, 'workspace'):
        tz = g.workspace.tz
    else:
        tz = app.config['tz']
    return utc.localize(date).astimezone(tz).strftime('%e %B %Y')


@app.context_processor
def sidebarvars():
    if g.user:
        # TODO: Need more advanced access control
        org_ids = g.user.organizations_memberof_ids()
    else:
        org_ids = []

    if org_ids:
        workspaces = Workspace.query.filter(Workspace.userid.in_(org_ids)).order_by('title').all()
    else:
        workspaces = []

    if hasattr(g, 'workspace'):
        return {
            'workspaces': workspaces,
            'categories': Category.query.filter_by(workspace=g.workspace).order_by('title').all(),
            'budgets': Budget.query.filter_by(workspace=g.workspace).order_by('title').all(),
            'report_states': ExpenseReportWorkflow.states(),
        }
    else:
        return {
            'workspaces': workspaces,
        }


@app.route('/')
def index():
    return render_template('index.html.jinja2')


@app.route('/<workspace>/')
@lastuser.requires_login
@load_model(Workspace, {'name': 'workspace'}, 'g.workspace', permission='view')
def workspace_view(workspace):
    return render_template('workspace.html.jinja2', workspace=workspace)
