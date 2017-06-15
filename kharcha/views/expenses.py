# -*- coding: utf-8 -*-

"""
Manage expense reports
"""

import csv
import StringIO
from flask import g, flash, url_for, render_template, request, redirect, Response
from werkzeug.datastructures import MultiDict
from coaster.utils import format_currency as coaster_format_currency
from coaster.views import load_model, load_models
from baseframe.forms import render_form, render_redirect, render_delete_sqla, ConfirmDeleteForm

from kharcha import app, lastuser
from kharcha.forms import ExpenseReportForm, ExpenseForm
from kharcha.views.workflows import ExpenseReportWorkflow
from kharcha.models import db, Workspace, ExpenseReport, Expense, Budget


@app.template_filter('format_currency')
def format_currency(value):
    return coaster_format_currency(value, decimals=2)


def available_reports(workspace, user=None, all=False):
    if user is None:
        user = g.user
    query = ExpenseReport.query.filter_by(workspace=workspace).order_by('datetime')
    # FIXME+TODO: Replace with per-workspace permissions
    if all and 'review' in g.permissions:
        # Get all reports owned by this user and in states where the user can review them
        query = query.filter(db.or_(
            ExpenseReport.user == user,
            ExpenseReport.status.in_(ExpenseReportWorkflow.reviewable.values)))
    else:
        query = query.filter_by(user=user)
    return query


@app.route('/<workspace>/budgets/<budget>')
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (Budget, {'name': 'budget', 'workspace': 'workspace'}, 'budget'),
    permission='view'
    )
def budget(workspace, budget):
    unsorted_reports = available_reports(workspace).filter_by(budget=budget).all()
    if unsorted_reports:
        noreports = False
    else:
        noreports = True
    reports = ExpenseReportWorkflow.sort_documents(unsorted_reports)
    return render_template('budget.html', budget=budget, reports=reports, noreports=noreports)


@app.route('/<workspace>/reports/')
@lastuser.requires_login
@load_model(Workspace, {'name': 'workspace'}, 'g.workspace', permission='view')
def reports(workspace):
    # Sort reports by status
    reports = ExpenseReportWorkflow.sort_documents(available_reports(workspace).all())
    return render_template('reports.html', reports=reports)


@app.route('/<workspace>/reports/all')
@lastuser.requires_login
@load_model(Workspace, {'name': 'workspace'}, 'g.workspace', permission='view')
def reports_all(workspace):
    # Sort reports by status
    reports = ExpenseReportWorkflow.sort_documents(available_reports(workspace, all=True).all())
    return render_template('reports.html', reports=reports)


def report_edit_internal(workspace, form, report=None, workflow=None):
    if form.validate_on_submit():
        if report is None:
            report = ExpenseReport(workspace=workspace)
            report.user = g.user
            db.session.add(report)
        form.populate_obj(report)
        report.make_name()
        db.session.commit()
        return redirect(url_for('report', workspace=workspace.name, report=report.url_name), code=303)
    # TODO: Ajax handling here (but then again, is it required?)
    return render_template('reportnew.html',
        workspace=workspace, form=form, report=report, workflow=workflow)


@app.route('/<workspace>/reports/new', methods=['GET', 'POST'])
@lastuser.requires_login
@load_model(Workspace, {'name': 'workspace'}, 'g.workspace', permission='new-report')
def report_new(workspace):
    form = ExpenseReportForm(prefix='report')
    return report_edit_internal(workspace, form)


@app.route('/<workspace>/reports/<report>', methods=['GET', 'POST'])
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (ExpenseReport, {'url_name': 'report', 'workspace': 'workspace'}, 'report'),
    permission='view'
    )
def report(workspace, report):
    workflow = report.workflow()
    expenseform = ExpenseForm()
    expenseform.report = report
    if expenseform.validate_on_submit():
        if expenseform.id.data:
            expense = Expense.query.get(expenseform.id.data)
        else:
            expense = Expense()
            # FIXME: Replace this with SQLAlchemy's sequence ordering extension

            # Find the highest sequence number for expenses in this report.
            # If None, assume 0, then add 1 to get the next sequence number
            expense.seq = (db.session.query(
                db.func.max(Expense.seq).label('seq')).filter_by(
                    report_id=report.id).first().seq or 0) + 1
        expenseform.populate_obj(expense)
        report.expenses.append(expense)
        db.session.flush()
        report.update_total()
        db.session.commit()
        if request.is_xhr:
            # Return with a blank form
            return render_template("expense.html", report=report, expenseform=ExpenseForm(MultiDict()))
        else:
            return redirect(url_for('report', workspace=workspace.name, report=report.url_name), code=303)
    if request.is_xhr:
        return render_template("expense.html", report=report, expenseform=expenseform)
    return render_template('report.html',
        report=report,
        workflow=workflow,
        transitions=workflow.transitions(),
        expenseform=expenseform)


@app.route('/<workspace>/reports/<report>/expensetable')
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (ExpenseReport, {'url_name': 'report', 'workspace': 'workspace'}, 'report'),
    permission='view'
    )
def report_expensetable(workspace, report):
    workflow = report.workflow()
    return render_template('expensetable.html',
        report=report, workflow=workflow)


@app.route('/<workspace>/reports/<report>/csv')
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (ExpenseReport, {'url_name': 'report', 'workspace': 'workspace'}, 'report'),
    permission='view'
    )
def report_csv(workspace, report):
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
        headers={'Content-Disposition': 'attachment; filename="%s.csv"' % report.url_name,
                 'Cache-Control': 'no-store',
                 'Pragma': 'no-cache'})
    return response


@app.route('/<workspace>/reports/<report>/edit', methods=['GET', 'POST'])
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (ExpenseReport, {'url_name': 'report', 'workspace': 'workspace'}, 'report'),
    permission='edit'
    )
def report_edit(workspace, report):
    workflow = report.workflow()
    form = ExpenseReportForm(obj=report)
    return report_edit_internal(workspace, form, report, workflow)

    # All okay. Allow editing
    if form.validate_on_submit():
        form.populate_obj(report)
        db.session.commit()
        flash("Edited report '%s'." % report.title, 'success')
        return render_redirect(url_for('report', workspace=workspace.name, report=report.url_name), code=303)
    return render_form(form=form, title=u"Edit expense report",
        formid="report_edit", submit=u"Save",
        cancel_url=url_for('report', workspace=workspace.name, report=report.url_name))


@app.route('/<workspace>/reports/<report>/delete', methods=['GET', 'POST'])
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (ExpenseReport, {'url_name': 'report', 'workspace': 'workspace'}, 'report'),
    permission='delete'
    )
def report_delete(workspace, report):
    # Confirm delete
    return render_delete_sqla(report, db, title=u"Confirm delete",
        message=u"Delete expense report '%s'?" % report.title,
        success=u"You have deleted report '%s'." % report.title,
        next=url_for('reports', workspace=workspace.name))


@app.route('/<workspace>/reports/<report>/<expense>/delete', methods=['GET', 'POST'])
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (ExpenseReport, {'url_name': 'report', 'workspace': 'workspace'}, 'report'),
    (Expense, {'report': 'report', 'id': 'expense'}, 'expense'),
    permission='delete'
    )
def expense_delete(workspace, report, expense):
    form = ConfirmDeleteForm()
    if form.validate_on_submit():
        if 'delete' in request.form:
            db.session.delete(expense)
            db.session.commit()
            report.update_total()
            report.update_sequence_numbers()
            db.session.commit()
        return redirect(url_for('report', workspace=workspace.name, report=report.url_name), code=303)
    return render_template('baseframe/delete.html', form=form, title=u"Confirm delete",
        message=u"Delete expense item '%s' for %s %s?" % (
            expense.description, report.currency, format_currency(expense.amount)))


@app.route('/<workspace>/reports/<report>/submit', methods=['POST'])
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (ExpenseReport, {'url_name': 'report', 'workspace': 'workspace'}, 'report'),
    permission='edit'
    )
def report_submit(workspace, report):
    wf = report.workflow()
    if wf.document.expenses == []:
        flash(u"This expense report does not list any expenses.", 'error')
        return redirect(url_for('report', workspace=workspace.name, report=report.url_name), code=303)
    wf.submit()
    db.session.commit()
    flash(u"Your expense report has been submitted.", 'success')
    return redirect(url_for('report', workspace=workspace.name, report=report.url_name), code=303)


@app.route('/<workspace>/reports/<report>/resubmit', methods=['POST'])
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (ExpenseReport, {'url_name': 'report', 'workspace': 'workspace'}, 'report'),
    permission='edit'
    )
def report_resubmit(workspace, report):
    wf = report.workflow()
    if wf.document.expenses == []:
        flash(u"This expense report does not list any expenses.", 'error')
        return redirect(url_for('report', workspace=workspace.name, report=report.url_name), code=303)
    wf.resubmit()
    db.session.commit()
    flash(u"Your expense report has been submitted.", 'success')
    return redirect(url_for('report', workspace=workspace.name, report=report.url_name), code=303)


@app.route('/<workspace>/reports/<report>/accept', methods=['POST'])
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (ExpenseReport, {'url_name': 'report', 'workspace': 'workspace'}, 'report'),
    permission='review'
    )
def report_accept(workspace, report):
    wf = report.workflow()
    wf.accept(reviewer=g.user)
    db.session.commit()
    flash(u"Expense report '%s' has been accepted." % report.title, 'success')
    return redirect(url_for('reports_all', workspace=workspace.name), code=303)


@app.route('/<workspace>/reports/<report>/return_for_review', methods=['POST'])
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (ExpenseReport, {'url_name': 'report', 'workspace': 'workspace'}, 'report'),
    permission='review'
    )
def report_return(workspace, report):
    wf = report.workflow()
    wf.return_for_review(reviewer=g.user, notes=u'')  # TODO: Form for notes
    db.session.commit()
    flash(u"Expense report '%s' has been returned for review." % report.title,
        'success')
    return redirect(url_for('reports_all', workspace=workspace.name), code=303)


@app.route('/<workspace>/reports/<report>/reject', methods=['POST'])
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (ExpenseReport, {'url_name': 'report', 'workspace': 'workspace'}, 'report'),
    permission='review'
    )
def report_reject(workspace, report):
    wf = report.workflow()
    wf.reject(reviewer=g.user, notes=u'')  # TODO: Form for notes
    db.session.commit()
    flash(u"Expense report '%s' has been rejected." % report.title, 'success')
    return redirect(url_for('reports_all', workspace=workspace.name), code=303)


@app.route('/<workspace>/reports/<report>/withdraw', methods=['POST'])
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (ExpenseReport, {'url_name': 'report', 'workspace': 'workspace'}, 'report'),
    permission='withdraw'
    )
def report_withdraw(workspace, report):
    wf = report.workflow()
    wf.withdraw()
    db.session.commit()
    flash(u"Expense report '%s' has been withdrawn." % report.title, 'success')
    return redirect(url_for('reports', workspace=workspace.name), code=303)


@app.route('/<workspace>/reports/<report>/close', methods=['POST'])
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (ExpenseReport, {'url_name': 'report', 'workspace': 'workspace'}, 'report'),
    permission='review'
    )
def report_close(workspace, report):
    wf = report.workflow()
    wf.close()
    db.session.commit()
    flash(u"Expense report '%s' has been closed." % report.title, 'success')
    return redirect(url_for('reports_all', workspace=workspace.name), code=303)
