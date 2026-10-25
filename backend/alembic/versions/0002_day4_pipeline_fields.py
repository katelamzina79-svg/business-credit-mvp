"""Add scoring and decision output fields for the Day 4 pipeline."""
from alembic import op
import sqlalchemy as sa

revision = "0002_day4_pipeline_fields"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("applications", sa.Column("score", sa.Integer(), nullable=True))
    op.add_column("applications", sa.Column("risk_level", sa.String(length=20), nullable=True))
    op.add_column("applications", sa.Column("score_factors", sa.JSON(), nullable=True))
    op.add_column("applications", sa.Column("decision_recommendation", sa.String(length=30), nullable=True))
    op.add_column("applications", sa.Column("decision_reasons", sa.JSON(), nullable=True))
    op.add_column("applications", sa.Column("bki_overdue_days", sa.Integer(), nullable=True))
    op.add_column("applications", sa.Column("recommended_amount", sa.Numeric(14, 2), nullable=True))
    op.add_column("applications", sa.Column("external_checks", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("applications", "external_checks")
    op.drop_column("applications", "recommended_amount")
    op.drop_column("applications", "bki_overdue_days")
    op.drop_column("applications", "decision_reasons")
    op.drop_column("applications", "decision_recommendation")
    op.drop_column("applications", "score_factors")
    op.drop_column("applications", "risk_level")
    op.drop_column("applications", "score")
