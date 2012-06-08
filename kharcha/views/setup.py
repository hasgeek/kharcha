# -*- coding: utf-8 -*-

"""
Manage budgets and categories
"""

from flask import flash, url_for, render_template, g
from coaster.views import load_model, load_models
from baseframe.forms import render_form, render_redirect, render_delete_sqla, render_message

from kharcha import app
from kharcha.views.login import lastuser, requires_workspace_member, requires_workspace_owner
from kharcha.models import db, Budget, Category, Workspace
from kharcha.forms import BudgetForm, CategoryForm, NewWorkspaceForm


@app.route('/new', methods=['GET', 'POST'])
@lastuser.requires_login
def workspace_new():
    # Step 1: Get a list of organizations this user owns
    existing = Workspace.query.filter(Workspace.userid.in_(g.user.organizations_owned_ids())).all()
    existing_ids = [e.userid for e in existing]
    # Step 2: Prune list to organizations without a workspace
    new_workspaces = []
    for org in g.user.organizations_owned():
        if org['userid'] not in existing_ids:
            new_workspaces.append((org['userid'], org['title']))
    if not new_workspaces:
        return render_message(
            title=u"No organizations remaining",
            message=u"You do not have any organizations that do not yet have a workspace.")

    # Step 3: Ask user to select organization
    form = NewWorkspaceForm()
    form.workspace.choices = new_workspaces
    if form.validate_on_submit():
        # Step 4: Make a workspace
        org = [org for org in g.user.organizations_owned() if org['userid'] == form.workspace.data][0]
        workspace = Workspace(name=org['name'], title=org['title'], userid=org['userid'],
            currency=form.currency.data)
        db.session.add(workspace)
        db.session.commit()
        flash("Created new workspace for %s" % workspace.title, "success")
        return render_redirect(url_for('workspace_view', workspace=workspace.name), code=303)
    return render_form(form=form, title="Create a new organization workspace", submit="Create",
        formid="workspace_new", cancel_url=url_for('index'), ajax=False)


@app.route('/<workspace>/budgets/')
@load_model(Workspace, {'name': 'workspace'}, 'workspace')
@requires_workspace_member
def budget_list(workspace):
    return render_template('budgets.html')


@app.route('/<workspace>/budgets/new', methods=['GET', 'POST'])
@load_model(Workspace, {'name': 'workspace'}, 'workspace')
@requires_workspace_owner
def budget_new(workspace):
    form = BudgetForm()
    if form.validate_on_submit():
        budget = Budget(workspace=workspace)
        form.populate_obj(budget)
        budget.make_name()
        db.session.add(budget)
        db.session.commit()
        flash("Created new budget '%s'." % budget.title, "success")
        return render_redirect(url_for('budget', workspace=workspace.name, budget=budget.name), code=303)
    return render_form(form=form, title=u"Create new budget",
        formid="budget_new", submit=u"Create",
        cancel_url=url_for('budget_list', workspace=workspace.name), ajax=True)


@app.route('/<workspace>/budgets/<budget>/edit', methods=['GET', 'POST'])
@load_models(
    (Workspace, {'name': 'workspace'}, 'workspace'),
    (Budget, {'name': 'budget', 'workspace': 'workspace'}, 'budget')
    )
@requires_workspace_owner
def budget_edit(workspace, budget):
    form = BudgetForm(obj=budget)
    if form.validate_on_submit():
        form.populate_obj(budget)
        budget.make_name()
        db.session.commit()
        flash("Edited budget '%s'" % budget.title, "success")
        return render_redirect(url_for('budget', workspace=workspace.name, budget=budget.name), code=303)
    return render_form(form=form, title=u"Edit budget",
        formid='budget_edit', submit=u"Save",
        cancel_url=url_for('budget', workspace=workspace.name, budget=budget.name), ajax=True)


@app.route('/<workspace>/budgets/<budget>/delete', methods=['GET', 'POST'])
@load_models(
    (Workspace, {'name': 'workspace'}, 'workspace'),
    (Budget, {'name': 'budget', 'workspace': 'workspace'}, 'budget')
    )
@requires_workspace_owner
def budget_delete(workspace, budget):
    return render_delete_sqla(budget, db, title=u"Confirm delete",
        message=u"Delete budget '%s'?" % budget.title,
        success=u"You have deleted budget '%s'." % budget.title,
        next=url_for('budget_list', workspace=workspace.name))


@app.route('/<workspace>/categories/')
@load_model(Workspace, {'name': 'workspace'}, 'workspace')
@requires_workspace_member
def category_list(workspace):
    return render_template('categories.html')


@app.route('/<workspace>/categories/new', methods=['GET', 'POST'])
@load_model(Workspace, {'name': 'workspace'}, 'workspace')
@requires_workspace_owner
def category_new(workspace):
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(workspace=workspace)
        form.populate_obj(category)
        category.make_name()
        db.session.add(category)
        db.session.commit()
        flash("Created new category '%s'." % category.title, "success")
        return render_redirect(url_for('category', workspace=workspace.name, category=category.name), code=303)
    return render_form(form=form, title=u"Create new category",
        formid="category_new", submit=u"Create",
        cancel_url=url_for('category_list', workspace=workspace.name), ajax=True)


@app.route('/<workspace>/categories/<category>')
@load_models(
    (Workspace, {'name': 'workspace'}, 'workspace'),
    (Category, {'name': 'category', 'workspace': 'workspace'}, 'category')
    )
@requires_workspace_member
def category(workspace, category):
    return render_template('category.html', category=category)


@app.route('/<workspace>/categories/<category>/edit', methods=['GET', 'POST'])
@load_models(
    (Workspace, {'name': 'workspace'}, 'workspace'),
    (Category, {'name': 'category', 'workspace': 'workspace'}, 'category')
    )
@requires_workspace_owner
def category_edit(workspace, category):
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        form.populate_obj(category)
        category.make_name()
        db.session.commit()
        flash("Edited category '%s'" % category.title, "success")
        return render_redirect(url_for('category', workspace=workspace.name, category=category.name), code=303)
    return render_form(form=form, title=u"Edit category",
        formid='category_edit', submit=u"Save",
        cancel_url=url_for('category', workspace=workspace.name, category=category.name), ajax=True)


@app.route('/<workspace>/categories/<category>/delete', methods=['GET', 'POST'])
@load_models(
    (Workspace, {'name': 'workspace'}, 'workspace'),
    (Category, {'name': 'category', 'workspace': 'workspace'}, 'category')
    )
@requires_workspace_owner
def category_delete(workspace, category):
    return render_delete_sqla(category, db, title=u"Confirm delete",
        message=u"Delete category '%s'?" % category.title,
        success=u"You have deleted category '%s'." % category.title,
        next=url_for('category_list', workspace=workspace.name))
