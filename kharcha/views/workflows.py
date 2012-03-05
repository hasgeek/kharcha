# -*- coding: utf-8 -*-

from datetime import datetime
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

    def permissions(self):
        """
        Permissions available to current user.
        """
        base_permissions = super(ExpenseReportWorkflow,
                                 self).permissions()
        if self.document.user == g.user:
            base_permissions.append('owner')
        base_permissions.extend(lastuser.permissions())
        return base_permissions

    @draft.transition(pending, 'owner', title=u"Submit", category="primary",
        description=u"Submit this expense report to a reviewer.",
        view='report_submit')
    def submit(self):
        """
        Submit the report.
        """
        # Update timestamp
        self.document.datetime = datetime.utcnow()
        # TODO: Notify reviewers

    @review.transition(pending, 'owner', title=u"Submit", category="primary",
        description=u"Resubmit this expense report to a reviewer.",
        view='report_resubmit')
    def resubmit(self):
        """
        Resubmit the report.
        """
        # Update timestamp
        self.document.datetime = datetime.utcnow()
        # TODO: Notify reviewers

    @pending.transition(accepted, 'reviewer', title=u"Accept", category="primary",
        description=u"Accept this expense report and queue it for reimbursements.",
        view='report_accept')
    def accept(self):
        """
        Accept the expense report and mark for payout to owner.
        """
        # TODO: Notify owner of acceptance
        pass

    @pending.transition(review, 'reviewer', title=u"Return for review", category="warning",
        description=u"Return this expense report to the submitter for review.",
        view='report_return')
    def return_for_review(self):
        """
        Return report to owner for review.
        """
        # TODO: Notify owner
        pass

    @pending.transition(rejected, 'reviewer', title=u"Reject", category="danger",
        description=u"Reject this expense report.",
        view='report_reject')
    def reject(self):
        """
        Reject expense report.
        """
        # TODO: Notify owner
        pass

    @review.transition(withdrawn, 'owner', title=u"Withdraw", category="danger",
        description=u"Withdraw this expense report.",
        view='report_withdraw')
    def withdraw(self):
        """
        Withdraw the expense report.
        """
        pass

    @accepted.transition(closed, 'reviewer', title=u"Close", category="success",
        description=u"Mark this expense report as reimbursed.",
        view='report_close')
    def close(self):
        """
        Close expense report (indicates reimbursement).
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
