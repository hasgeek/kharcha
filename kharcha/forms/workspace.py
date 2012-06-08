# -*- coding: utf-8 -*-

from baseframe.forms import Form
import flask.ext.wtf as wtf

from kharcha.forms.expenses import CURRENCIES


class NewWorkspaceForm(Form):
    """
    Create a workspace.
    """
    workspace = wtf.RadioField(u"Organization", validators=[wtf.Required()],
        description=u"Select the organization you’d like to create a workspace for.")
    currency = wtf.SelectField(u"Currency", validators=[wtf.Required()], choices=CURRENCIES,
        description=u"The standard currency for your organization’s accounts.")
