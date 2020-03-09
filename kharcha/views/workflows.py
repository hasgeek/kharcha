# -*- coding: utf-8 -*-

from __future__ import absolute_import

from datetime import datetime
from flask import g
from kharcha.docflow import DocumentWorkflow, WorkflowState, WorkflowStateGroup
from kharcha.models import REPORT_STATUS, ExpenseReport
from kharcha.forms import ReviewForm


class ExpenseReportWorkflow(DocumentWorkflow):
    """
    Workflow for expense reports.
    """

    state_attr = 'status'

    draft = WorkflowState(REPORT_STATUS.DRAFT, title="Draft")
    pending = WorkflowState(REPORT_STATUS.PENDING, title="Pending review")
    review = WorkflowState(REPORT_STATUS.REVIEW, title="Returned for review")
    accepted = WorkflowState(REPORT_STATUS.ACCEPTED, title="Accepted")
    rejected = WorkflowState(REPORT_STATUS.REJECTED, title="Rejected")
    withdrawn = WorkflowState(REPORT_STATUS.WITHDRAWN, title="Withdrawn")
    closed = WorkflowState(REPORT_STATUS.CLOSED, title="Closed")

    #: States in which an owner can edit
    editable = WorkflowStateGroup([draft, review], title="Editable")
    #: States in which a reviewer can view
    reviewable = WorkflowStateGroup([pending, review, accepted, rejected, closed],
                                    title="Reviewable")

    @draft.transition(pending, 'owner', title="Submit", category="primary",
        description="Submit this expense report to a reviewer? You cannot "
        "edit this report after it has been submitted.",
        view='report_submit')
    def submit(self):
        """
        Submit the report.
        """
        # Update timestamp
        self.document.datetime = datetime.utcnow()
        # TODO: Notify reviewers

    @review.transition(pending, 'owner', title="Submit", category="primary",
        description="Resubmit this expense report to a reviewer? You cannot "
        "edit this report after it has been submitted.",
        view='report_resubmit')
    def resubmit(self):
        """
        Resubmit the report.
        """
        # Update timestamp
        self.document.datetime = datetime.utcnow()
        # TODO: Notify reviewers

    @pending.transition(accepted, 'review', title="Accept", category="primary",
        description="Accept this expense report and queue it for reimbursements?",
        view='report_accept')
    def accept(self, reviewer):
        """
        Accept the expense report and mark for payout to owner.
        """
        # TODO: Notify owner of acceptance
        self.document.reviewer = reviewer

    @pending.transition(review, 'review', title="Return for review", category="warning",
        description="Return this expense report to the submitter for review?",
        view='report_return', form=ReviewForm)
    def return_for_review(self, reviewer, notes):
        """
        Return report to owner for review.
        """
        # TODO: Notify owner
        self.document.reviewer = reviewer
        self.document.notes = notes

    @pending.transition(rejected, 'review', title="Reject", category="danger",
        description="Reject this expense report? Rejected reports are archived but cannot be processed again.",
        view='report_reject', form=ReviewForm)
    def reject(self, reviewer, notes):
        """
        Reject expense report.
        """
        # TODO: Notify owner
        self.document.reviewer = reviewer
        self.document.notes = notes

    @review.transition(withdrawn, 'owner', title="Withdraw", category="danger",
        description="Withdraw this expense report? Withdrawn reports are archived but cannot be processed again.",
        view='report_withdraw')
    def withdraw(self):
        """
        Withdraw the expense report.
        """
        pass

    @accepted.transition(closed, 'review', title="Close", category="success",
        description="Mark this expense report as reimbursed? "
            "This will archive the report, after which it cannot be processed again.",
        view='report_close')
    def close(self):
        """
        Close expense report (indicates reimbursement).
        """
        # TODO: Notify owner of closure.
        pass

# Apply this workflow on ExpenseReport objects
ExpenseReportWorkflow.apply_on(ExpenseReport)
