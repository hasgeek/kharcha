"""Team model changes

Revision ID: 342f7d42966
Revises: 269666e6a991
Create Date: 2014-04-07 03:23:38.993621

"""

# revision identifiers, used by Alembic.
revision = '342f7d42966'
down_revision = '269666e6a991'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('users_teams', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.add_column('users_teams', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.alter_column('users_teams', 'created_at', server_default=None)
    op.alter_column('users_teams', 'updated_at', server_default=None)
    op.alter_column('users_teams', 'team_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('users_teams', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.create_primary_key('users_teams_pkey', 'users_teams', ['user_id', 'team_id'])

def downgrade():
    op.drop_index('users_teams_pkey', 'users_teams')
    op.alter_column('users_teams', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('users_teams', 'team_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_column('users_teams', 'updated_at')
    op.drop_column('users_teams', 'created_at')
