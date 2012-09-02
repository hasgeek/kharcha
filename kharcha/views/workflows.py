# -*- coding: utf-8 -*-

from datetime import datetime
from flask import g
from coaster.docflow import DocumentWorkflow, WorkflowState, WorkflowStateGroup
from kharcha.models import REPORT_STATUS, ExpenseReport
from kharcha.forms import ReviewForm


class ExpenseReportWorkflow(DocumentWorkflow):
    """
    Workflow for expense reports.
    """

    state_attr = 'status'

    draft = WorkflowState(REPORT_STATUS.DRAFT, title=u"Draft")
    pending = WorkflowState(REPORT_STATUS.PENDING, title=u"Pending review")
    review = WorkflowState(REPORT_STATUS.REVIEW, title=u"Returned for review")
    accepted = WorkflowState(REPORT_STATUS.ACCEPTED, title=u"Accepted")
    rejected = WorkflowState(REPORT_STATUS.REJECTED, title=u"Rejected")
    withdrawn = WorkflowState(REPORT_STATUS.WITHDRAWN, title=u"Withdrawn")
    closed = WorkflowState(REPORT_STATUS.CLOSED, title=u"Closed")

    #: States in which an owner can edit
    editable = WorkflowStateGroup([draft, review], title=u"Editable")
    #: States in which a reviewer can view
    reviewable = WorkflowStateGroup([pending, review, accepted, rejected, closed],
                                    title=u"Reviewable")

    def permissions(self, user=None):
        """
        Permissions available to current user.
        """
        base_permissions = super(ExpenseReportWorkflow,
                                 self).permissions()
        if user is None:
            user = g.user
        base_permissions.extend(self.document.permissions(user))
        return base_permissions

    @draft.transition(pending, 'owner', title=u"Submit", category="primary",
        description=u"Submit this expense report to a reviewer? You cannot "
        "edit this report after it has been submitted.",
        view='report_submit')
    def submit(self):
        """
        Submit the report.
        """
        # Update timestamp
        self.document.datetime = datetime.utcnow()
        # TODO: Notify reviewers

    @review.transition(pending, 'owner', title=u"Submit", category="primary",
        description=u"Resubmit this expense report to a reviewer? You cannot "
        "edit this report after it has been submitted.",
        view='report_resubmit')
    def resubmit(self):
        """
        Resubmit the report.
        """
        # Update timestamp
        self.document.datetime = datetime.utcnow()
        # TODO: Notify reviewers

    @pending.transition(accepted, 'review', title=u"Accept", category="primary",
        description=u"Accept this expense report and queue it for reimbursements?",
        view='report_accept')
    def accept(self, reviewer):
        """
        Accept the expense report and mark for payout to owner.
        """
        # TODO: Notify owner of acceptance
        self.document.reviewer = reviewer

    @pending.transition(review, 'review', title=u"Return for review", category="warning",
        description=u"Return this expense report to the submitter for review?",
        view='report_return', form=ReviewForm)
    def return_for_review(self, reviewer, notes):
        """
        Return report to owner for review.
        """
        # TODO: Notify owner
        self.document.reviewer = reviewer
        self.document.notes = notes

    @pending.transition(rejected, 'review', title=u"Reject", category="danger",
        description=u"Reject this expense report? Rejected reports are archived but cannot be processed again.",
        view='report_reject', form=ReviewForm)
    def reject(self, reviewer, notes):
        """
        Reject expense report.
        """
        # TODO: Notify owner
        self.document.reviewer = reviewer
        self.document.notes = notes

    @review.transition(withdrawn, 'owner', title=u"Withdraw", category="danger",
        description=u"Withdraw this expense report? Withdrawn reports are archived but cannot be processed again.",
        view='report_withdraw')
    def withdraw(self):
        """
        Withdraw the expense report.
        """
        pass

    @accepted.transition(closed, 'review', title=u"Close", category="success",
        description=u"Mark this expense report as reimbursed? "
            u"This will archive the report, after which it cannot be processed again.",
        view='report_close')
    def close(self):
        """
        Close expense report (indicates reimbursement).
        """
        # TODO: Notify owner of closure.
        pass

# Apply this workflow on ExpenseReport objects
ExpenseReportWorkflow.apply_on(ExpenseReport)
