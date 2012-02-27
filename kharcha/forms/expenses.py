# -*- coding: utf-8 -*-

# Expense forms
import flask.ext.wtf as wtf
from baseframe.forms import Form, RichTextField
from coaster import simplify_text
from kharcha.models import Category, Budget

__all__ = ['BudgetForm', 'CategoryForm', 'ExpenseReportForm', 'ExpenseForm']

CURRENCIES = [
    ('INR', 'INR - India Rupee'),
    ('USD', 'USD - US Dollar'),
    ('EUR', 'EUR - Euro'),
    ('GBP', 'GBP - Great Britain Pound')
    ]


class BudgetForm(Form):
    """
    Create or edit a budget.
    """
    title = wtf.TextField(u"Budget title", validators=[wtf.Required()],
        description = u"The name of your project or other budget source")
    description = RichTextField(u"Description",
        description = u"Description of the budget")

    def validate_title(self, field):
        """
        If the title is already in use, refuse to add this one.
        """
        existing = set([simplify_text(b.title) for b in Budget.query.all() if b != self.edit_obj])
        if simplify_text(field.data) in existing:
            raise wtf.ValidationError("You have an existing budget with the same name")


class CategoryForm(Form):
    """
    Create or edit a category.
    """
    title = wtf.TextField(u"Title", validators=[wtf.Required()],
        description = u"The name of the category")

    def validate_title(self, field):
        """
        If the title is already in use, refuse to add this one.
        """
        existing = set([simplify_text(c.title) for c in Category.query.all() if c != self.edit_obj])
        if simplify_text(field.data) in existing:
            raise wtf.ValidationError("You have an existing category with the same name")


def sorted_budgets():
    return Budget.query.order_by('title')


def sorted_categories():
    return Category.query.order_by('title')


class ExpenseReportForm(Form):
    """
    Create or edit an expense report.
    """
    title = wtf.TextField(u"Title", validators=[wtf.Required()],
        description = u"What are these expenses for?")
    budget = wtf.QuerySelectField(u"Budget", validators=[wtf.Optional()],
        query_factory=sorted_budgets, get_label='title', allow_blank=True,
        description=u"The budget source for these expenses")
    currency = wtf.SelectField(u"Currency", validators=[wtf.Required()],
        description=u"Currency for expenses in this report",
        choices=CURRENCIES)
    description = RichTextField(u"Description", validators=[wtf.Optional()],
        description=u"Notes on the expenses")

class ExpenseForm(Form):
    """
    Create or edit an expense line item.
    """
    id = wtf.IntegerField(u"Id", validators=[wtf.Optional()])
    date = wtf.DateField(u"Date", validators=[wtf.Required()])
    category = wtf.QuerySelectField(u"Category", validators=[wtf.Required()],
        query_factory=sorted_categories, get_label='title', allow_blank=True)
    description = wtf.TextField(u"Description", validators=[wtf.Required()])
    amount = wtf.DecimalField(u"Amount", validators=[wtf.Required(), wtf.NumberRange(min=0)])

    def validate_id(self, field):
        # Check if user is authorized to edit this expense.
        pass
