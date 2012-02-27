# -*- coding: utf-8 -*-

import os
from pytz import utc, timezone
from flask import render_template
from kharcha import app
from kharcha.models import Category, Budget
from kharcha.views.workflows import ExpenseReportWorkflow
from kharcha.views.login import lastuser

tz = timezone(app.config['TIMEZONE'])

@app.template_filter('shortdate')
def shortdate(date):
    return utc.localize(date).astimezone(tz).strftime('%b %e')


@app.template_filter('longdate')
def longdate(date):
    return utc.localize(date).astimezone(tz).strftime('%B %e, %Y')


@app.context_processor
def sidebarvars():
    return {
        'categories': Category.query.order_by('title').all(),
        'budgets': Budget.query.order_by('title').all(),
        'report_states': ExpenseReportWorkflow.states(),
        'permissions': lastuser.permissions(),
    }

@app.route('/')
def index():
    return render_template('index.html')
