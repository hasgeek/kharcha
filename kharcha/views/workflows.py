# -*- coding: utf-8 -*-

from flask import g, session
from docflow import (DocumentWorkflow, WorkflowState, WorkflowStateGroup,
    WorkflowPermissionException, WorkflowTransitionException)
from kharcha.models import REPORT_STATUS, ExpenseReport

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

    editable = WorkflowStateGroup([REPORT_STATUS.DRAFT, REPORT_STATUS.REVIEW], title=u"Editable")

    def permissions(self, context=None):
        """
        Permissions available to current user.
        """
        base_permissions = super(ExpenseReportWorkflow, self).permissions(context)
        if self._document.user == g.user:
            base_permissions.append('owner')
        # TODO: Check if the user is a reviewer
        if 'lastuser_userinfo' in session:
            base_permissions.extend(session['lastuser_userinfo']['permissions'])
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

    @draft.transition(withdrawn, 'owner', title=u"Discard")
    def discard_draft(self, context=None):
        """
        Discard expense report.
        """
        pass

    @review.transition(withdrawn, 'owner', title=u"Discard")
    def discard_review(self, context=None):
        """
        Discard expense report.
        """
        pass

    @accepted.transition(closed, 'reviewer', title=u"Close")
    def close(self, context=None):
        """
        Close expense report (indicates payment).
        """
        # TODO: Notify owner of closure.
        pass


# Apply this workflow on ExpenseReport objects
ExpenseReportWorkflow.apply_on(ExpenseReport)
