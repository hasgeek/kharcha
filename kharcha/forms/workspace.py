# -*- coding: utf-8 -*-

from pytz import common_timezones
from baseframe.forms import Form, RichTextField
import wtforms
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField

from kharcha.forms.expenses import CURRENCIES


class NewWorkspaceForm(Form):
    """
    Create a workspace.
    """
    workspace = wtforms.RadioField(u"Organization", validators=[wtforms.validators.Required("Select an organization")],
        description=u"Select the organization you’d like to create a workspace for")
    currency = wtforms.SelectField(u"Currency", validators=[wtforms.validators.Required("Select a currency")], choices=CURRENCIES,
        description=u"The standard currency for your organization’s accounts. This cannot be changed later")


class WorkspaceForm(Form):
    """
    Manage workspace settings.
    """
    description = RichTextField(u"Usage notes",
        description=u"Notes for your organization members on how to use this expense reporting tool")
    timezone = wtforms.SelectField(u"Timezone", validators=[wtforms.validators.Required("Select a timezone")],
        choices=[(tz, tz) for tz in common_timezones],
        description=u"The primary timezone in which your organization is based")
    access_teams = QuerySelectMultipleField(u"Access Teams",
        validators=[wtforms.validators.Required("You need to select at least one team")], get_label='title',
        description=u"Teams that can submit expense reports")
    review_teams = QuerySelectMultipleField(u"Review Teams",
        validators=[wtforms.validators.Required("You need to select at least one team")], get_label='title',
        description=u"Teams that can review and act on expense reports")
    admin_teams = QuerySelectMultipleField(u"Admin Teams",
        validators=[wtforms.validators.Required("You need to select at least one team")], get_label='title',
        description=u"Teams with administrative access to this workspace. "
            u"Admin access is required to create or edit budgets and categories")

    def validate_admin_teams(self, field):
        if self.edit_obj.owners not in field.data:
            field.data.append(self.edit_obj.owners)
