from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "workouts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("exercise", sa.String(120), nullable=False),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_workouts_user_performed", "workouts", ["user_id", "performed_at"]
    )
    op.create_table(
        "nutrition_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("calories", sa.Integer(), nullable=False),
        sa.Column("protein_g", sa.Float(), nullable=False),
        sa.Column("carbs_g", sa.Float(), nullable=False),
        sa.Column("fat_g", sa.Float(), nullable=False),
        sa.Column("notes", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_nutrition_user_date", "nutrition_entries", ["user_id", "date"])
    op.create_table(
        "weekly_summaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("workout_count", sa.Integer(), nullable=False),
        sa.Column("total_volume_kg", sa.Float(), nullable=False),
        sa.Column("avg_calories", sa.Float(), nullable=False),
        sa.Column("avg_protein_g", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "week_start", name="uq_summary_user_week"),
    )
    op.create_index(
        "ix_summary_user_week", "weekly_summaries", ["user_id", "week_start"]
    )


def downgrade():
    op.drop_index("ix_summary_user_week", table_name="weekly_summaries")
    op.drop_table("weekly_summaries")
    op.drop_index("ix_nutrition_user_date", table_name="nutrition_entries")
    op.drop_table("nutrition_entries")
    op.drop_index("ix_workouts_user_performed", table_name="workouts")
    op.drop_table("workouts")
    op.drop_table("users")
