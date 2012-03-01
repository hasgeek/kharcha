# -*- coding: utf-8 -*-

"""
Manage expense reports
"""

import csv
import StringIO
from flask import g, flash, url_for, render_template, request, redirect, abort, Response
from werkzeug.datastructures import MultiDict
from coaster import format_currency as coaster_format_currency
from baseframe.forms import render_form, render_redirect, render_delete_sqla, ConfirmDeleteForm

from kharcha import app
from kharcha.forms import ExpenseReportForm, ExpenseForm
from kharcha.views.login import lastuser
from kharcha.views.workflows import ExpenseReportWorkflow
from docflow import WorkflowPermissionException, WorkflowTransitionException
from kharcha.models import db, ExpenseReport, Expense


@app.template_filter('format_currency')
def format_currency(value):
    return coaster_format_currency(value, decimals=2)


@app.route('/reports/')
@lastuser.requires_login
def reports():
    # Sort reports by status
    query = ExpenseReport.query.order_by('updated_at')
    if 'reviewer' in lastuser.permissions():
        # Get all reports owned by this user and in states where the user can review them
        query = ExpenseReport.query.filter(db.or_(
            ExpenseReport.user == g.user,
            ExpenseReport.status.in_(ExpenseReportWorkflow.reviewable.value)))
    else:
        query = ExpenseReport.query.filter_by(user=g.user)
    reports = ExpenseReportWorkflow.sort_documents(query.order_by('updated_at').all())
    return render_template('reports.html', reports=reports)


def report_edit_internal(form, report=None, workflow=None):
    if form.validate_on_submit():
        if report is None:
            report = ExpenseReport()
            report.user = g.user
            db.session.add(report)
        form.populate_obj(report)
        db.session.commit()
        return redirect(url_for('report', id=report.id), code=303)
    # TODO: Ajax handling here (but then again, is it required?)
    return render_template('reportnew.html',
        form=form, report=report, workflow=workflow)


@app.route('/reports/new', methods=['GET', 'POST'])
@lastuser.requires_login
def report_new():
    form = ExpenseReportForm(prefix='report')
    return report_edit_internal(form)


@app.route('/reports/<int:id>', methods=['GET', 'POST'])
@lastuser.requires_login
def report(id):
    report = ExpenseReport.query.get_or_404(id)
    workflow = report.workflow()
    if not workflow.can_view():
        abort(403)
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
        report=report,
        workflow=workflow,
        transitions=workflow.transitions(),
        expenseform=expenseform)


@app.route('/reports/<int:id>/expensetable')
@lastuser.requires_login
def report_expensetable(id):
    report = ExpenseReport.query.get_or_404(id)
    workflow = report.workflow()
    if not workflow.can_view():
        abort(403)
    return render_template('expensetable.html',
        report=report, workflow=workflow)


@app.route('/reports/<int:id>/csv')
@lastuser.requires_login
def report_csv(id):
    report = ExpenseReport.query.get_or_404(id)
    workflow = report.workflow()
    if not workflow.can_view():
        abort(403)
    outfile = StringIO.StringIO()
    out = csv.writer(outfile)
    out.writerow(['Date', 'Category', 'Description', 'Amount'])
    for expense in report.expenses:
        out.writerow([expense.date.strftime('%Y-%m-%d'),
                      expense.category.title.encode('utf-8'),
                      expense.description.encode('utf-8'),
                      '%.2f' % expense.amount])
    response = Response(outfile.getvalue(),
        content_type='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename="%d.csv"' % report.id,
                 'Cache-Control': 'no-store',
                 'Pragma': 'no-cache'})
    return response


@app.route('/reports/<int:id>/edit', methods=['GET', 'POST'])
@lastuser.requires_login
def report_edit(id):
    report = ExpenseReport.query.get_or_404(id)
    workflow = report.workflow()
    if not workflow.can_view():
        abort(403)
    if not workflow.can_edit():
        return render_template('baseframe/message.html',
            message=u"You cannot edit this report at this time.")
    form = ExpenseReportForm(obj=report)
    return report_edit_internal(form, report, workflow)

    # All okay. Allow editing
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
    workflow = report.workflow()
    if not workflow.can_view():
        abort(403)
    if not workflow.draft():
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
    workflow = report.workflow()
    if workflow.can_view():
        abort(403)
    if not workflow.can_edit():
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
    wf = report.workflow()
    try:
        wf.submit()
    except (WorkflowPermissionException, WorkflowTransitionException):
        abort(403)
    db.session.commit()
    flash("Expense report '%s' has been submitted." % report.title, "success")
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/resubmit', methods=['POST'])
@lastuser.requires_login
def report_resubmit(id):
    report = ExpenseReport.query.get_or_404(id)
    wf = report.workflow()
    try:
        wf.resubmit()
    except (WorkflowPermissionException, WorkflowTransitionException):
        abort(403)
    db.session.commit()
    flash("Expense report '%s' has been submitted." % report.title, "success")
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/accept', methods=['POST'])
@lastuser.requires_login
def report_accept(id):
    report = ExpenseReport.query.get_or_404(id)
    wf = report.workflow()
    try:
        wf.accept()
    except (WorkflowPermissionException, WorkflowTransitionException):
        abort(403)
    db.session.commit()
    flash("Expense report '%s' has been accepted." % report.title, "success")
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/return_for_review', methods=['POST'])
@lastuser.requires_login
def report_return(id):
    report = ExpenseReport.query.get_or_404(id)
    wf = report.workflow()
    try:
        wf.return_for_review()
    except (WorkflowPermissionException, WorkflowTransitionException):
        abort(403)
    db.session.commit()
    flash("Expense report '%s' has been returned for review." % report.title,
        "success")
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/reject', methods=['POST'])
@lastuser.requires_login
def report_reject(id):
    report = ExpenseReport.query.get_or_404(id)
    wf = report.workflow()
    try:
        wf.reject()
    except (WorkflowPermissionException, WorkflowTransitionException):
        abort(403)
    db.session.commit()
    flash("Expense report '%s' has been rejected." % report.title, "success")
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/withdraw', methods=['POST'])
@lastuser.requires_login
def report_withdraw(id):
    report = ExpenseReport.query.get_or_404(id)
    wf = report.workflow()
    try:
        wf.withdraw()
    except (WorkflowPermissionException, WorkflowTransitionException):
        abort(403)
    db.session.commit()
    flash("Expense report '%s' has been withdrawn." % report.title, "success")
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/close', methods=['POST'])
@lastuser.requires_login
def report_close(id):
    report = ExpenseReport.query.get_or_404(id)
    wf = report.workflow()
    try:
        wf.close()
    except (WorkflowPermissionException, WorkflowTransitionException):
        abort(403)
    db.session.commit()
    flash("Expense report '%s' has been closed." % report.title, "success")
    return redirect(url_for('reports'), code=303)
