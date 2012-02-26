# -*- coding: utf-8 -*-

"""
Manage expense reports
"""

from flask import g, flash, url_for, render_template, Markup, request, redirect
from werkzeug.datastructures import MultiDict
from coaster import format_currency as coaster_format_currency
from baseframe.forms import render_form, render_redirect, render_delete_sqla, ConfirmDeleteForm

from kharcha import app
from kharcha.forms import ExpenseReportForm, ExpenseForm
from kharcha.views.login import lastuser
from kharcha.views.workflows import (ExpenseReportWorkflow,
    WorkflowPermissionException, WorkflowTransitionException)
from kharcha.models import db, User, ExpenseReport, Expense, Category


@app.template_filter('format_currency')
def format_currency(value):
    return coaster_format_currency(value, decimals=2)


@app.route('/reports/')
def reports():
    # Sort reports by status
    reports = ExpenseReportWorkflow.sort_documents(ExpenseReport.query.order_by('updated_at').all())
    return render_template('reports.html', reports=reports)


@app.route('/reports/new', methods=['GET', 'POST'])
@lastuser.requires_login
def report_new():
    form = ExpenseReportForm()
    if form.validate_on_submit():
        report = ExpenseReport()
        form.populate_obj(report)
        report.user = g.user
        db.session.add(report)
        db.session.commit()
        flash("Created new report '%s'." % report.title, "success")
        return render_redirect(url_for('report', id=report.id), code=303)
    return render_form(form=form, title=u"Submit an expense report",
        formid="report_new", submit=Markup(u'Add details &raquo;'),
        cancel_url=url_for('reports'), ajax=True)


@app.route('/reports/<int:id>', methods=['GET', 'POST'])
@lastuser.requires_login
def report(id):
    # TODO: Allow reviewers to view
    report = ExpenseReport.query.get_or_404(id)
    if report.user != g.user:
        abort(403)
    workflow = report.workflow()
    expenseform = ExpenseForm()
    expenseform.report = report
    if expenseform.validate_on_submit():
        if expenseform.id.data:
            expense = Expense.query.get(expenseform.id.data)
        else:
            expense = Expense()
            # Find the highest sequence number for exxpenses in this report.
            # If None, assume 0, then add 1 to get the next sequence number
            expense.seq = db.session.query(
                db.func.max(Expense.seq).label('seq')).filter_by(
                    report_id=report.id).first().seq or 0 + 1
            db.session.add(expense)
        expenseform.populate_obj(expense)
        report.expenses.append(expense)
        db.session.commit()
        report.update_total()
        db.session.commit()
        if request.is_xhr:
            # Return with a blank form
            return render_template("expense.html", report=report, expenseform=ExpenseForm(MultiDict()))
        else:
            return redirect(url_for('report', id=id), code=303)
    if request.is_xhr:
        return render_template("expense.html", report=report, expenseform=expenseform)
    return render_template('report.html',
        report = report,
        workflow = workflow,
        transitions = workflow.transitions(),
        expenseform = expenseform)


@app.route('/reports/<int:id>/expensetable')
@lastuser.requires_login
def report_expensetable(id):
    # TODO: Allow reviewers to view
    report = ExpenseReport.query.get_or_404(id)
    if report.user != g.user:
        abort(403)
    return render_template('expensetable.html',
        report = report,
        workflow = report.workflow())


@app.route('/reports/<int:id>/edit', methods=['GET', 'POST'])
@lastuser.requires_login
def report_edit(id):
    report = ExpenseReport.query.get_or_404(id)
    if report.user != g.user:
        abort(403)
    wf = report.workflow()
    if not wf.editable():
        return render_template('baseframe/message.html', message=u"You cannot edit this report at this time.")
    # All okay. Allow editing
    form = ExpenseReportForm(obj=report)
    if form.validate_on_submit():
        form.populate_obj(report)
        db.session.commit()
        flash("Edited report '%s'." % report.title, "success")
        return render_redirect(url_for('report', id=report.id), code=303)
    return render_form(form=form, title=u"Edit expense report",
        formid="report_edit", submit=u"Save",
        cancel_url=url_for('report', id=report.id))


@app.route('/reports/<int:id>/delete', methods=['GET', 'POST'])
@lastuser.requires_login
def report_delete(id):
    report = ExpenseReport.query.get_or_404(id)
    if report.user != g.user:
        abort(403)
    wf = report.workflow()
    if not wf.draft():
        # Only drafts can be deleted
        return render_template('baseframe/message.html', message=u"Only draft expense reports can be deleted.")
    # Confirm delete
    return render_delete_sqla(report, db, title=u"Confirm delete",
        message=u"Delete expense report '%s'?" % report.title,
        success=u"You have deleted report '%s'." % report.title,
        next=url_for('reports'))


@app.route('/reports/<int:rid>/<int:eid>/delete', methods=['GET', 'POST'])
@lastuser.requires_login
def expense_delete(rid, eid):
    report = ExpenseReport.query.get_or_404(rid)
    if report.user != g.user:
        abort(403)
    workflow = report.workflow()
    if not workflow.editable():
        abort(403)
    expense = Expense.query.filter_by(report=report, id=eid).first_or_404()
    form = ConfirmDeleteForm()
    if form.validate_on_submit():
        if 'delete' in request.form:
            db.session.delete(expense)
            db.session.commit()
            report.update_total()
            db.session.commit()
            return redirect(url_for('report', id=rid), code=303)
    return render_template('baseframe/delete.html', form=form, title=u"Confirm delete",
        message=u"Delete expense item '%s' for %s %s?" % (
            expense.description, report.currency, format_currency(expense.amount)))


@app.route('/reports/<int:id>/submit', methods=['POST'])
@lastuser.requires_login
def report_submit(id):
    report = ExpenseReport.query.get_or_404(id)
    if report.user != g.user:
        abort(403)
    wf = report.workflow()
    try:
        wf.submit()
    except (WorkflowPermissionException, WorkflowTransitionException):
        abort(403)
    db.session.commit()
    flash("Expense report '%s' has been submitted." % report.title, "success")
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/accept', methods=['POST'])
@lastuser.requires_login
def report_accept(id):
    report = ExpenseReport.query.get_or_404(id)
    if report.user != g.user:
        abort(403)
    wf = report.workflow()
    try:
        wf.accept()
    except (WorkflowPermissionException, WorkflowTransitionException):
        abort(403)
    db.session.commit()
    flash("Expense report '%s' has been accepted." % report.title, "success")
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/return', methods=['POST'])
@lastuser.requires_login
def report_return(id):
    report = ExpenseReport.query.get_or_404(id)
    if report.user != g.user:
        abort(403)
    wf = report.workflow()
    try:
        wf.return_for_review()
    except (WorkflowPermissionException, WorkflowTransitionException):
        abort(403)
    db.session.commit()
    flash("Expense report '%s' has been returned for review." % report.title, "success")
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/reject', methods=['POST'])
@lastuser.requires_login
def report_reject(id):
    report = ExpenseReport.query.get_or_404(id)
    if report.user != g.user:
        abort(403)
    wf = report.workflow()
    try:
        wf.reject()
    except (WorkflowPermissionException, WorkflowTransitionException):
        abort(403)
    db.session.commit()
    flash("Expense report '%s' has been rejected." % report.title, "success")
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/discard', methods=['POST'])
@lastuser.requires_login
def report_discard(id):
    report = ExpenseReport.query.get_or_404(id)
    if report.user != g.user:
        abort(403)
    wf = report.workflow()
    try:
        if wf.draft():
            wf.discard_draft()
        else:
            wf.discard_review()
    except (WorkflowPermissionException, WorkflowTransitionException):
        abort(403)
    db.session.commit()
    flash("Expense report '%s' has been withdrawn." % report.title, "success")
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/close', methods=['POST'])
@lastuser.requires_login
def report_close(id):
    report = ExpenseReport.query.get_or_404(id)
    if report.user != g.user:
        abort(403)
    wf = report.workflow()
    try:
        wf.close()
    except (WorkflowPermissionException, WorkflowTransitionException):
        abort(403)
    db.session.commit()
    flash("Expense report '%s' has been closed." % report.title, "success")
    return redirect(url_for('reports'), code=303)