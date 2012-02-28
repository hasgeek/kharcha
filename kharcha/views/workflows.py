# -*- coding: utf-8 -*-

from flask import g
from docflow import DocumentWorkflow, WorkflowState, WorkflowStateGroup
from kharcha.models import REPORT_STATUS, ExpenseReport
from kharcha.views.login import lastuser


class ExpenseReportWorkflow(DocumentWorkflow):
    """
    Workflow for expense reports.
    """

    state_attr = 'status'

    draft = WorkflowState(REPORT_STATUS.DRAFT, title=u"Draft")
    pending = WorkflowState(REPORT_STATUS.PENDING, title=u"Pending")
    review = WorkflowState(REPORT_STATUS.REVIEW, title=u"Returned for review")
    accepted = WorkflowState(REPORT_STATUS.ACCEPTED, title=u"Accepted")
    rejected = WorkflowState(REPORT_STATUS.REJECTED, title=u"Rejected")
    withdrawn = WorkflowState(REPORT_STATUS.WITHDRAWN, title=u"Withdrawn")
    closed = WorkflowState(REPORT_STATUS.CLOSED, title=u"Closed")

    #: States in which an owner can edit
    editable = WorkflowStateGroup([draft, review], title=u"Editable")
    #: States in which a reviewer can view
    reviewable = WorkflowStateGroup([pending, accepted, rejected, closed],
                                    title=u"Reviewable")

    # The context parameter is mandated by docflow but not required in Flask
    # apps because Flask provides direct access to thread-local context
    # variables such as `request` and `g`. We accept the parameter and pass
    # it around, but don't bother to read it.
    def permissions(self, context=None):
        """
        Permissions available to current user.
        """
        base_permissions = super(ExpenseReportWorkflow,
                                 self).permissions(context)
        if self._document.user == g.user:
            base_permissions.append('owner')
        base_permissions.extend(lastuser.permissions())
        return base_permissions

    @draft.transition(pending, 'owner', title=u"Submit")
    def submit(self, context=None):
        """
        Publish the review.
        """
        # TODO: Notify reviewers
        pass

    @review.transition(pending, 'owner', title=u"Submit")
    def resubmit(self, context=None):
        """
        Publish the review.
        """
        # TODO: Notify reviewers
        pass

    @pending.transition(accepted, 'reviewer', title=u"Accept")
    def accept(self, context=None):
        """
        Accept the expense report and mark for payout to owner.
        """
        # TODO: Notify owner of acceptance
        pass

    @pending.transition(review, 'reviewer', title=u"Return for review")
    def return_for_review(self, context=None):
        """
        Return report to owner for review.
        """
        # TODO: Notify owner
        pass

    @pending.transition(rejected, 'reviewer', title=u"Reject")
    def reject(self, context=None):
        """
        Reject expense report.
        """
        # TODO: Notify owner
        pass

    @review.transition(withdrawn, 'owner', title=u"Withdraw")
    def withdraw(self, context=None):
        """
        Withdraw the expense report.
        """
        pass

    @accepted.transition(closed, 'reviewer', title=u"Close")
    def close(self, context=None):
        """
        Close expense report (indicates payment).
        """
        # TODO: Notify owner of closure.
        pass

    def can_view(self):
        """
        Can the current user view this?
        """
        permissions = self.permissions()
        if 'owner' in permissions:
            return True
        if 'reviewer' in permissions and self.reviewable():
            return True
        return False

    def can_edit(self):
        """
        Can the current user edit this?
        """
        return 'owner' in self.permissions() and self.editable()

# Apply this workflow on ExpenseReport objects
ExpenseReportWorkflow.apply_on(ExpenseReport)
