# -*- coding: utf-8 -*-

"""
Manage budgets and categories
"""

from flask import flash, url_for, render_template, g, Markup, request
from coaster.views import load_model, load_models
from baseframe.forms import render_form, render_redirect, render_delete_sqla, render_message

from kharcha import app, lastuser
from kharcha.models import db, Team, Budget, Category, Workspace
from kharcha.forms import BudgetForm, CategoryForm, NewWorkspaceForm, WorkspaceForm


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
            title=u"No organizations found",
            message=Markup(u"You do not have any organizations that do not already have a workspace. "
                u'Would you like to <a href="%s">create a new organization</a>?' %
                    lastuser.endpoint_url('/organizations/new')))
    eligible_workspaces = []
    for orgid, title in new_workspaces:
        if Team.query.filter_by(orgid=orgid).first() is not None:
            eligible_workspaces.append((orgid, title))
    if not eligible_workspaces:
        return render_message(
            title=u"No organizations available",
            message=Markup(u"To create a workspace for an organization, you must first allow this app to "
                u"access the list of teams in your organization. "
                u'<a href="%s">Do that here</a>.' % lastuser.endpoint_url('/apps/' + lastuser.client_id)))

    # Step 3: Ask user to select organization
    form = NewWorkspaceForm()
    form.workspace.choices = eligible_workspaces
    if request.method == 'GET':
        form.workspace.data = new_workspaces[0][0]
    if form.validate_on_submit():
        # Step 4: Make a workspace
        org = [org for org in g.user.organizations_owned() if org['userid'] == form.workspace.data][0]
        workspace = Workspace(name=org['name'], title=org['title'], userid=org['userid'],
            currency=form.currency.data, timezone=app.config.get('TIMEZONE', ''))
        db.session.add(workspace)
        db.session.commit()
        flash(u"Created a workspace for %s" % workspace.title, "success")
        return render_redirect(url_for('workspace_edit', workspace=workspace.name), code=303)
    return render_form(form=form, title="Create a workspace for your organization...", submit="Next",
        formid="workspace_new", cancel_url=url_for('index'), ajax=False)


@app.route('/<workspace>/edit', methods=['GET', 'POST'])
@lastuser.requires_login
@load_model(Workspace, {'name': 'workspace'}, 'g.workspace', permission='edit')
def workspace_edit(workspace):
    form = WorkspaceForm(obj=workspace)
    form.admin_teams.query = Team.query.filter_by(orgid=workspace.userid).order_by(Team.title)
    form.review_teams.query = form.admin_teams.query
    form.access_teams.query = form.admin_teams.query
    if form.validate_on_submit():
        form.populate_obj(workspace)
        db.session.commit()
        flash(u"Edited workspace settings.", 'success')
        return render_redirect(url_for('workspace_view', workspace=workspace.name), code=303)

    return render_form(form=form, title=u"Edit workspace settings", submit="Save",
        formid="workspace_edit", cancel_url=url_for('workspace_view', workspace=workspace.name), ajax=True)


@app.route('/<workspace>/delete', methods=['GET', 'POST'])
@lastuser.requires_login
@load_model(Workspace, {'name': 'workspace'}, 'g.workspace', permission='delete')
def workspace_delete(workspace):
    # Only allow workspaces to be deleted if they have no expense reports
    if workspace.reports:
        return render_message(
            title=u"Cannot delete this workspace",
            message=u"This workspace cannot be deleted because it contains expense reports.")
    return render_delete_sqla(workspace, db, title=u"Confirm delete",
        message=u"Delete workspace '%s'?" % workspace.title,
        success=u"You have deleted workspace '%s'." % workspace.title,
        next=url_for('index'))


@app.route('/<workspace>/budgets/')
@lastuser.requires_login
@load_model(Workspace, {'name': 'workspace'}, 'g.workspace', permission='view')
def budget_list(workspace):
    return render_template('budgets.html')


@app.route('/<workspace>/budgets/new', methods=['GET', 'POST'])
@lastuser.requires_login
@load_model(Workspace, {'name': 'workspace'}, 'g.workspace', permission='new-budget')
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
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (Budget, {'name': 'budget', 'workspace': 'workspace'}, 'budget'),
    permission='edit'
    )
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
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (Budget, {'name': 'budget', 'workspace': 'workspace'}, 'budget'),
    permission='delete'
    )
def budget_delete(workspace, budget):
    return render_delete_sqla(budget, db, title=u"Confirm delete",
        message=u"Delete budget '%s'?" % budget.title,
        success=u"You have deleted budget '%s'." % budget.title,
        next=url_for('budget_list', workspace=workspace.name))


@app.route('/<workspace>/categories/')
@lastuser.requires_login
@load_model(Workspace, {'name': 'workspace'}, 'g.workspace', permission='view')
def category_list(workspace):
    return render_template('categories.html')


@app.route('/<workspace>/categories/new', methods=['GET', 'POST'])
@lastuser.requires_login
@load_model(Workspace, {'name': 'workspace'}, 'g.workspace', permission='new-category')
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
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (Category, {'name': 'category', 'workspace': 'workspace'}, 'category'),
    permission='view'
    )
def category(workspace, category):
    return render_template('category.html', category=category)


@app.route('/<workspace>/categories/<category>/edit', methods=['GET', 'POST'])
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (Category, {'name': 'category', 'workspace': 'workspace'}, 'category'),
    permission='edit'
    )
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
@lastuser.requires_login
@load_models(
    (Workspace, {'name': 'workspace'}, 'g.workspace'),
    (Category, {'name': 'category', 'workspace': 'workspace'}, 'category'),
    permission='delete'
    )
def category_delete(workspace, category):
    return render_delete_sqla(category, db, title=u"Confirm delete",
        message=u"Delete category '%s'?" % category.title,
        success=u"You have deleted category '%s'." % category.title,
        next=url_for('category_list', workspace=workspace.name))
