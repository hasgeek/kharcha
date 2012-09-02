# -*- coding: utf-8 -*-

from pytz import timezone
from werkzeug import cached_property
from kharcha.models import db, BaseNameMixin, Team

__all__ = ['Workspace']


workspace_admin_teams = db.Table('workspace_admin_teams', db.Model.metadata,
    db.Column('workspace_id', db.Integer, db.ForeignKey('workspace.id')),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'))
    )

workspace_review_teams = db.Table('workspace_review_teams', db.Model.metadata,
    db.Column('workspace_id', db.Integer, db.ForeignKey('workspace.id')),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'))
    )

workspace_access_teams = db.Table('workspace_access_teams', db.Model.metadata,
    db.Column('workspace_id', db.Integer, db.ForeignKey('workspace.id')),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'))
    )


class Workspace(BaseNameMixin, db.Model):
    """
    Workspaces contain expense reports, budgets and categories. Workspaces
    correspond to organizations in LastUser.
    """
    __tablename__ = 'workspace'
    userid = db.Column(db.Unicode(22), nullable=False, unique=True)
    currency = db.Column(db.Unicode(3), nullable=False)
    timezone = db.Column(db.Unicode(32), nullable=False)
    description = db.Column(db.UnicodeText, nullable=False, default=u'')

    admin_teams = db.relationship('Team', secondary=workspace_admin_teams, backref='workspaces_admin')
    review_teams = db.relationship('Team', secondary=workspace_review_teams, backref='workspaces_reviewer')
    access_teams = db.relationship('Team', secondary=workspace_access_teams, backref='workspaces_access')

    def __init__(self, *args, **kwargs):
        super(Workspace, self).__init__(*args, **kwargs)

        # Add owners to admin and review teams automatically
        if self.owners and self.owners not in self.admin_teams:
            self.admin_teams.insert(0, self.owners)
        if self.owners and self.owners not in self.review_teams:
            self.review_teams.append(self.owners)

    @cached_property
    def tz(self):
        return timezone(self.timezone)

    @cached_property
    def owners(self):
        return Team.query.filter_by(orgid=self.userid, owners=True).first()

    def permissions(self, user, inherited=None):
        perms = super(Workspace, self).permissions(user, inherited)
        # No access without explicit tests
        perms.discard('view')
        perms.discard('edit')
        perms.discard('delete')

        if user:
            userteams = set(user.teams)
            if len(userteams & set(self.admin_teams)) > 0 or self.userid in user.organizations_owned_ids():
                # The user is in a team that has admin access
                perms.add('edit')
                perms.add('delete')
                perms.add('admin')
                perms.add('view')
                perms.add('new-report')
                perms.add('new-budget')
                perms.add('new-category')
            if len(userteams & set(self.review_teams)) > 0:
                # The user is in a team that has review access
                perms.add('review')
                perms.add('view')
            if len(userteams & set(self.access_teams)) > 0:
                # The user is in a team that has view/submit access
                perms.add('view')
                perms.add('new-report')
        return perms
