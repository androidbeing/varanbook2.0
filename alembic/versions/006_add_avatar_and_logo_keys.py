"""Add avatar_key to users and logo_key to tenants for S3-backed profile pictures.

- users.avatar_key  : S3 object key for a user's profile picture (member or admin)
- tenants.logo_key  : S3 object key for the matrimonial centre's branding logo

Revision ID: 006
Revises:     005
Create Date: 2026-03-02
"""

from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add profile-picture column to every user (member, admin, super_admin)
    op.add_column(
        "users",
        sa.Column(
            "avatar_key",
            sa.String(512),
            nullable=True,
            comment="S3 object key for profile picture",
        ),
    )

    # Add branding-logo column to tenant
    op.add_column(
        "tenants",
        sa.Column(
            "logo_key",
            sa.String(512),
            nullable=True,
            comment="S3 object key for tenant logo",
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "logo_key")
    op.drop_column("users", "avatar_key")
