from alembic import op
import sqlalchemy as sa
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('email', sa.String(255), nullable=False), sa.Column('password_hash', sa.String(255), nullable=False), sa.Column('role', sa.String(20), nullable=False), sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_table('companies', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('inn', sa.String(12), nullable=False), sa.Column('name', sa.String(255), nullable=False), sa.Column('okved', sa.String(20), nullable=False), sa.Column('revenue', sa.Numeric(14,2), nullable=False), sa.Column('debt', sa.Numeric(14,2), nullable=False), sa.Column('overdue_days', sa.Integer(), nullable=False))
    op.create_index('ix_companies_inn', 'companies', ['inn'], unique=True)
    op.create_table('applications', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('client_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False), sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False), sa.Column('product', sa.String(30), nullable=False), sa.Column('amount', sa.Numeric(14,2), nullable=False), sa.Column('term_months', sa.Integer(), nullable=False), sa.Column('status', sa.String(30), nullable=False), sa.Column('purpose', sa.Text(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=False), sa.Column('updated_at', sa.DateTime(), nullable=False))
    op.create_table('status_history', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('application_id', sa.Integer(), sa.ForeignKey('applications.id'), nullable=False), sa.Column('from_status', sa.String(30), nullable=True), sa.Column('to_status', sa.String(30), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=False))
    op.create_table('audit_logs', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True), sa.Column('action', sa.String(100), nullable=False), sa.Column('entity_type', sa.String(50), nullable=False), sa.Column('entity_id', sa.Integer(), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=False))

def downgrade():
    for table in ['audit_logs','status_history','applications','companies','users']:
        op.drop_table(table)
