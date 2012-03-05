# -*- coding: utf-8 -*-

"""
Manage budgets and categories
"""

from flask import flash, url_for, render_template
from baseframe.forms import render_form, render_redirect, render_delete_sqla

from kharcha import app
from kharcha.views.login import lastuser
from kharcha.models import db, Budget, Category
from kharcha.forms import BudgetForm, CategoryForm


@app.route('/budgets/')
def budget_list():
    return render_template('budgets.html')


@app.route('/budgets/new', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
def budget_new():
    form = BudgetForm()
    if form.validate_on_submit():
        budget = Budget()
        form.populate_obj(budget)
        budget.make_name()
        db.session.add(budget)
        db.session.commit()
        flash("Created new budget '%s'." % budget.title, "success")
        return render_redirect(url_for('budget', name=budget.name), code=303)
    return render_form(form=form, title=u"Create new budget",
        formid="budget_new", submit=u"Create",
        cancel_url=url_for('budget_list'), ajax=True)


@app.route('/budgets/<name>')
def budget(name):
    budget = Budget.query.filter_by(name=name).first_or_404()
    return render_template('budget.html', budget=budget)


@app.route('/budgets/<name>/edit', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
def budget_edit(name):
    budget = Budget.query.filter_by(name=name).first_or_404()
    form = BudgetForm(obj=budget)
    if form.validate_on_submit():
        form.populate_obj(budget)
        budget.make_name()
        db.session.commit()
        flash("Edited budget '%s'" % budget.title, "success")
        return render_redirect(url_for('budget', name=budget.name), code=303)
    return render_form(form=form, title=u"Edit budget",
        formid='budget_edit', submit=u"Save",
        cancel_url=url_for('budget', name=budget.name), ajax=True)


@app.route('/budgets/<name>/delete', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
def budget_delete(name):
    budget = Budget.query.filter_by(name=name).first_or_404()
    return render_delete_sqla(budget, db, title=u"Confirm delete",
        message=u"Delete budget '%s'?" % budget.title,
        success=u"You have deleted budget '%s'." % budget.title,
        next=url_for('budget_list'))


@app.route('/categories/')
def category_list():
    return render_template('categories.html')


@app.route('/categories/new', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
def category_new():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category()
        form.populate_obj(category)
        category.make_name()
        db.session.add(category)
        db.session.commit()
        flash("Created new category '%s'." % category.title, "success")
        return render_redirect(url_for('category', name=category.name), code=303)
    return render_form(form=form, title=u"Create new category",
        formid="category_new", submit=u"Create",
        cancel_url=url_for('category_list'), ajax=True)


@app.route('/categories/<name>')
def category(name):
    category = Category.query.filter_by(name=name).first_or_404()
    return render_template('category.html', category=category)


@app.route('/categories/<name>/edit', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
def category_edit(name):
    category = Category.query.filter_by(name=name).first_or_404()
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        form.populate_obj(category)
        category.make_name()
        db.session.commit()
        flash("Edited category '%s'" % category.title, "success")
        return render_redirect(url_for('category', name=category.name), code=303)
    return render_form(form=form, title=u"Edit category",
        formid='category_edit', submit=u"Save",
        cancel_url=url_for('category', name=category.name), ajax=True)


@app.route('/categories/<name>/delete', methods=['GET', 'POST'])
@lastuser.requires_permission('siteadmin')
def category_delete(name):
    category = Category.query.filter_by(name=name).first_or_404()
    return render_delete_sqla(category, db, title=u"Confirm delete",
        message=u"Delete category '%s'?" % category.title,
        success=u"You have deleted category '%s'." % category.title,
        next=url_for('category_list'))
