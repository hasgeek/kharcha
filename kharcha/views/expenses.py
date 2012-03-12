# -*- coding: utf-8 -*-

"""
Manage expense reports
"""

import csv
import StringIO
from flask import g, flash, url_for, render_template, request, redirect, abort, Response
from werkzeug.datastructures import MultiDict
from coaster import format_currency as coaster_format_currency
from coaster.views import load_model
from baseframe.forms import render_form, render_redirect, render_delete_sqla, ConfirmDeleteForm

from kharcha import app
from kharcha.forms import ExpenseReportForm, ExpenseForm
from kharcha.views.login import lastuser
from kharcha.views.workflows import ExpenseReportWorkflow
from kharcha.models import db, ExpenseReport, Expense, Budget


@app.template_filter('format_currency')
def format_currency(value):
    return coaster_format_currency(value, decimals=2)


def available_reports(user=None):
    if user is None:
        user = g.user
    query = ExpenseReport.query.order_by('datetime')
    if 'reviewer' in lastuser.permissions():
        # Get all reports owned by this user and in states where the user can review them
        query = ExpenseReport.query.filter(db.or_(
            ExpenseReport.user == user,
            ExpenseReport.status.in_(ExpenseReportWorkflow.reviewable.values)))
    else:
        query = ExpenseReport.query.filter_by(user=user)
    return query


@app.route('/budgets/<name>')
def budget(name):
    budget = Budget.query.filter_by(name=name).first_or_404()
    unsorted_reports = available_reports().filter_by(budget=budget).all()
    if unsorted_reports:
        noreports = False
    else:
        noreports = True
    reports = ExpenseReportWorkflow.sort_documents(unsorted_reports)
    return render_template('budget.html', budget=budget, reports=reports, noreports=noreports)


@app.route('/reports/')
@lastuser.requires_login
def reports():
    # Sort reports by status
    reports = ExpenseReportWorkflow.sort_documents(available_reports().all())
    return render_template('reports.html', reports=reports, reportspage=True)


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
    if form and report is None:
        newreport = True
    else:
        newreport = False
    return render_template('reportnew.html',
        form=form, report=report, workflow=workflow, newreport=newreport)


@app.route('/reports/new', methods=['GET', 'POST'])
@lastuser.requires_login
def report_new():
    form = ExpenseReportForm(prefix='report')
    return report_edit_internal(form)


@app.route('/reports/<int:id>', methods=['GET', 'POST'])
@lastuser.requires_login
@load_model(ExpenseReport, {'id': 'id'}, 'report')
def report(report):
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
@load_model(ExpenseReport, {'id': 'id'}, 'report')
def report_expensetable(report):
    workflow = report.workflow()
    if not workflow.can_view():
        abort(403)
    return render_template('expensetable.html',
        report=report, workflow=workflow)


@app.route('/reports/<int:id>/csv')
@lastuser.requires_login
@load_model(ExpenseReport, {'id': 'id'}, 'report')
def report_csv(report):
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
@load_model(ExpenseReport, {'id': 'id'}, 'report')
def report_edit(report):
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
        flash("Edited report '%s'." % report.title, 'success')
        return render_redirect(url_for('report', id=report.id), code=303)
    return render_form(form=form, title=u"Edit expense report",
        formid="report_edit", submit=u"Save",
        cancel_url=url_for('report', id=report.id))


@app.route('/reports/<int:id>/delete', methods=['GET', 'POST'])
@lastuser.requires_login
@load_model(ExpenseReport, {'id': 'id'}, 'report')
def report_delete(report):
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
@load_model([(ExpenseReport, {'id': 'rid'}, 'report'),
             (Expense, {'report': 'report', 'id': 'eid'}, 'expense')
             ])
def expense_delete(report, expense):
    #report = ExpenseReport.query.get_or_404(rid)
    workflow = report.workflow()
    if not workflow.can_view():
        abort(403)
    if not workflow.can_edit():
        abort(403)
    #expense = Expense.query.filter_by(report=report, id=eid).first_or_404()
    form = ConfirmDeleteForm()
    if form.validate_on_submit():
        if 'delete' in request.form:
            db.session.delete(expense)
            db.session.commit()
            report.update_total()
            db.session.commit()
        return redirect(url_for('report', id=report.id), code=303)
    return render_template('baseframe/delete.html', form=form, title=u"Confirm delete",
        message=u"Delete expense item '%s' for %s %s?" % (
            expense.description, report.currency, format_currency(expense.amount)))


@app.route('/reports/<int:id>/submit', methods=['POST'])
@lastuser.requires_login
@load_model(ExpenseReport, {'id': 'id'}, 'report', workflow=True)
def report_submit(wf):
    if wf.document.expenses == []:
        flash(u"This expense report does not list any expenses.", 'error')
        return redirect(url_for('report', id=wf.document.id), code=303)
    wf.submit()
    db.session.commit()
    flash(u"Expense report '%s' has been submitted." % wf.document.title, 'success')
    return redirect(url_for('report', id=wf.document.id), code=303)


@app.route('/reports/<int:id>/resubmit', methods=['POST'])
@lastuser.requires_login
@load_model(ExpenseReport, {'id': 'id'}, 'report', workflow=True)
def report_resubmit(wf):
    if wf.document.expenses == []:
        flash(u"This expense report does not list any expenses.", 'error')
        return redirect(url_for('report', id=wf.document.id), code=303)
    wf.resubmit()
    db.session.commit()
    flash(u"Expense report '%s' has been submitted." % wf.document.title, 'success')
    return redirect(url_for('report', id=wf.document.id), code=303)


@app.route('/reports/<int:id>/accept', methods=['POST'])
@lastuser.requires_login
@load_model(ExpenseReport, {'id': 'id'}, 'report', workflow=True)
def report_accept(wf):
    wf.accept()
    db.session.commit()
    flash(u"Expense report '%s' has been accepted." % wf.document.title, 'success')
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/return_for_review', methods=['POST'])
@lastuser.requires_login
@load_model(ExpenseReport, {'id': 'id'}, 'report', workflow=True)
def report_return(wf):
    wf.return_for_review()
    db.session.commit()
    flash(u"Expense report '%s' has been returned for review." % wf.document.title,
        'success')
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/reject', methods=['POST'])
@lastuser.requires_login
@load_model(ExpenseReport, {'id': 'id'}, 'report', workflow=True)
def report_reject(wf):
    wf.reject()
    db.session.commit()
    flash(u"Expense report '%s' has been rejected." % wf.document.title, 'success')
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/withdraw', methods=['POST'])
@lastuser.requires_login
@load_model(ExpenseReport, {'id': 'id'}, 'report', workflow=True)
def report_withdraw(wf):
    wf.withdraw()
    db.session.commit()
    flash(u"Expense report '%s' has been withdrawn." % wf.document.title, 'success')
    return redirect(url_for('reports'), code=303)


@app.route('/reports/<int:id>/close', methods=['POST'])
@lastuser.requires_login
@load_model(ExpenseReport, {'id': 'id'}, 'report', workflow=True)
def report_close(wf):
    wf.close()
    db.session.commit()
    flash(u"Expense report '%s' has been closed." % wf.document.title, 'success')
    return redirect(url_for('reports'), code=303)
