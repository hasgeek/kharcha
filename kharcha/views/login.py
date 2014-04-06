# -*- coding: utf-8 -*-

from flask import Response, redirect, flash, g
from coaster.views import get_next_url

from kharcha import app, lastuser
from kharcha.models import db, Workspace


@app.route('/login')
@lastuser.login_handler
def login():
    return {'scope': 'id email organizations teams'}


@app.route('/logout')
@lastuser.logout_handler
def logout():
    flash(u"You are now logged out", category='info')
    return get_next_url()


@app.route('/login/redirect')
@lastuser.auth_handler
def lastuserauth():
    Workspace.update_from_user(g.user, db.session, make_user_profiles=False, make_org_profiles=False)
    db.session.commit()
    return redirect(get_next_url())


@app.route('/login/notify', methods=['POST'])
@lastuser.notification_handler
def lastusernotify(user):
    Workspace.update_from_user(user, db.session, make_user_profiles=False, make_org_profiles=False)
    db.session.commit()


@lastuser.auth_error_handler
def lastuser_error(error, error_description=None, error_uri=None):
    if error == 'access_denied':
        flash("You denied the request to login", category='error')
        return redirect(get_next_url())
    return Response(u"Error: %s\n"
                    u"Description: %s\n"
                    u"URI: %s" % (error, error_description, error_uri),
                    mimetype="text/plain")
