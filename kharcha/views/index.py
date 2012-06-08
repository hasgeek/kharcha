# -*- coding: utf-8 -*-

from pytz import utc, timezone
from flask import render_template, g
from coaster.views import load_model
from kharcha import app
from kharcha.models import Category, Budget, Workspace
from kharcha.views.workflows import ExpenseReportWorkflow
from kharcha.views.login import lastuser, requires_workspace_member

tz = timezone(app.config['TIMEZONE'])


@app.template_filter('shortdate')
def shortdate(date):
    return utc.localize(date).astimezone(tz).strftime('%b %e')


@app.template_filter('longdate')
def longdate(date):
    return utc.localize(date).astimezone(tz).strftime('%B %e, %Y')


@app.context_processor
def sidebarvars():
    if g.user:
        # TODO: Need more advanced access control
        org_ids = g.user.organizations_memberof_ids()
    else:
        org_ids = []
    workspaces = Workspace.query.filter(Workspace.userid.in_(org_ids)).order_by('title').all()
    if hasattr(g, 'workspace'):
        return {
            'workspaces': workspaces,
            'categories': Category.query.filter_by(workspace=g.workspace).order_by('title').all(),
            'budgets': Budget.query.filter_by(workspace=g.workspace).order_by('title').all(),
            'report_states': ExpenseReportWorkflow.states(),
            'permissions': lastuser.permissions(),
        }
    else:
        return {
            'workspaces': workspaces,
        }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/<workspace>/')
@load_model(Workspace, {'name': 'workspace'}, 'workspace')
@requires_workspace_member
def workspace_view(workspace):
    return render_template('workspace.html', workspace=workspace)
