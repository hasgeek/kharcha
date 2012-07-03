# -*- coding: utf-8 -*-

from decimal import Decimal
from datetime import datetime
from flask import url_for
from kharcha.models import db, BaseMixin, BaseScopedNameMixin, BaseScopedIdNameMixin
from kharcha.models.user import User
from kharcha.models.workspace import Workspace

__all__ = ['REPORT_STATUS', 'Budget', 'Category', 'ExpenseReport', 'Expense']


# --- Constants ---------------------------------------------------------------

class REPORT_STATUS:
    DRAFT     = 0
    PENDING   = 1
    REVIEW    = 2
    ACCEPTED  = 3
    REJECTED  = 4
    WITHDRAWN = 5
    CLOSED    = 6


# --- Models ------------------------------------------------------------------

class Budget(BaseScopedNameMixin, db.Model):
    """
    Budget to which expense reports can be assigned.
    """
    __tablename__ = 'budget'
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), nullable=False)
    workspace = db.relation(Workspace, backref=db.backref('budgets', cascade='all, delete-orphan'))
    parent = db.synonym('workspace')
    #: Description of the budget. HTML field.
    description = db.Column(db.Text, nullable=False, default=u'')
    __table_args__ = (db.UniqueConstraint('name', 'workspace_id'),)


class Category(BaseScopedNameMixin, db.Model):
    """
    Expense categories.
    """
    __tablename__ = 'category'
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), nullable=False)
    workspace = db.relation(Workspace, backref=db.backref('categories', cascade='all, delete-orphan'))
    parent = db.synonym('workspace')
    __table_args__ = (db.UniqueConstraint('name', 'workspace_id'),)


class ExpenseReport(BaseScopedIdNameMixin, db.Model):
    """
    Collection of expenses.
    """
    __tablename__ = 'expense_report'
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), nullable=False)
    workspace = db.relation(Workspace, backref=db.backref('reports', cascade='all, delete-orphan'))
    parent = db.synonym('workspace')
    #: User who submitted the report
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship(User, primaryjoin=user_id == User.id,
        backref=db.backref('expensereports', cascade='all, delete-orphan'))
    #: Date of report submission
    datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    #: Budget to which this report is assigned
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=True)
    budget = db.relationship(Budget, primaryjoin=budget_id == Budget.id)
    #: Currency for expenses in this report
    currency = db.Column(db.Unicode(3), nullable=False, default=u'INR')
    #: Optional description of expenses
    description = db.Column(db.Text, nullable=False, default=u'')
    #: Total value in the report's currency
    total_value = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.0'))
    #: Total value in the organization's preferred currency
    total_converted = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.0'))
    #: Reviewer
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewer = db.relationship(User, primaryjoin=reviewer_id == User.id,
        backref=db.backref('reviewed_reports', cascade='all'))  # No delete-orphan
    #: Reviewer notes
    notes = db.Column(db.Text, nullable=False, default=u'')  # HTML notes
    #: Status
    status = db.Column(db.Integer, nullable=False, default=REPORT_STATUS.DRAFT)

    __table_args__ = (db.UniqueConstraint('url_id', 'workspace_id'),)

    def update_total(self):
        self.total_value = sum([e.amount for e in self.expenses])
        #self.total_value = db.session.query(
        #    db.func.sum(Expense.amount).label('sum')).filter_by(
        #        report_id = self.id).first().sum

    def update_sequence_numbers(self):
        # self.expenses is ordered by seq. See the relation defined at Expense.report
        for i, expense in enumerate(self.expenses):
            # Only edit the object if its sequence position has changed
            if expense.seq != i + 1:
                expense.seq = i + 1


class Expense(BaseMixin, db.Model):
    """
    Expense line item.
    """
    __tablename__ = 'expense'
    #: Id of report in which this expense is recorded
    report_id = db.Column(db.Integer, db.ForeignKey('expense_report.id'), nullable=False)
    #: Sequence number for sorting
    seq = db.Column(db.Integer, nullable=False, default=0)
    #: Date of expense
    date = db.Column(db.Date, nullable=False)
    #: Category of expense
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship(Category, primaryjoin=category_id == Category.id)
    #: Description
    description = db.Column(db.Unicode(250), nullable=False)
    #: Amount of expense
    amount = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    #: Report in which this expense is recorded
    report = db.relationship(ExpenseReport, primaryjoin=report_id == ExpenseReport.id,
        backref=db.backref('expenses', cascade='all, delete-orphan', order_by=seq))
