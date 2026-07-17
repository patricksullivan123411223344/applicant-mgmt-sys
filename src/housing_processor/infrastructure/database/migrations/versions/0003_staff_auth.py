"""Add staff_profiles + Postgres RLS for Supabase Auth.

Revision ID: 0003_staff_auth
Revises: 0002_postgres_domains
Create Date: 2026-07-17
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_staff_auth"
down_revision: Union[str, None] = "0002_postgres_domains"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DOMAIN_TABLES = (
    "applications",
    "applicants",
    "groups",
    "group_members",
    "pending_roommate_references",
    "properties",
    "group_property_preferences",
    "review_items",
    "audit_events",
    "outbox_events",
    "excel_exports",
    "staff_profiles",
)


def _auth_users_exists(bind: sa.Connection) -> bool:
    result = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'auth' AND table_name = 'users'
            """
        )
    )
    return result.first() is not None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.create_table(
        "staff_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=256), nullable=True),
        sa.Column("role", sa.String(length=64), nullable=False, server_default="operations"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_staff_profiles_email", "staff_profiles", ["email"])
    op.create_index("ix_staff_profiles_is_active", "staff_profiles", ["is_active"])

    if dialect != "postgresql":
        return

    if _auth_users_exists(bind):
        op.execute(
            sa.text(
                """
                ALTER TABLE staff_profiles
                ADD CONSTRAINT staff_profiles_id_fkey
                FOREIGN KEY (id) REFERENCES auth.users (id) ON DELETE CASCADE
                """
            )
        )
        op.execute(
            sa.text(
                """
                CREATE OR REPLACE FUNCTION public.handle_new_staff_user()
                RETURNS TRIGGER
                LANGUAGE plpgsql
                SECURITY DEFINER
                SET search_path = public
                AS $$
                BEGIN
                  INSERT INTO public.staff_profiles (
                    id, email, display_name, role, is_active, created_at, updated_at
                  )
                  VALUES (
                    NEW.id,
                    COALESCE(NEW.email, ''),
                    NULL,
                    'operations',
                    TRUE,
                    NOW(),
                    NOW()
                  )
                  ON CONFLICT (id) DO UPDATE
                    SET email = EXCLUDED.email,
                        updated_at = NOW();
                  RETURN NEW;
                END;
                $$
                """
            )
        )
        op.execute(sa.text("DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users"))
        op.execute(
            sa.text(
                """
                CREATE TRIGGER on_auth_user_created
                  AFTER INSERT ON auth.users
                  FOR EACH ROW
                  EXECUTE FUNCTION public.handle_new_staff_user()
                """
            )
        )
        op.execute(
            sa.text(
                """
                INSERT INTO public.staff_profiles (
                  id, email, display_name, role, is_active, created_at, updated_at
                )
                SELECT
                  u.id,
                  COALESCE(u.email, ''),
                  NULL,
                  'operations',
                  TRUE,
                  NOW(),
                  NOW()
                FROM auth.users u
                ON CONFLICT (id) DO NOTHING
                """
            )
        )

    active_staff = """
        EXISTS (
          SELECT 1 FROM public.staff_profiles p
          WHERE p.id = auth.uid() AND p.is_active
        )
    """
    for table in _DOMAIN_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"DROP POLICY IF EXISTS staff_all ON {table}"))
        if table == "staff_profiles":
            op.execute(sa.text("DROP POLICY IF EXISTS staff_read_own ON staff_profiles"))
            op.execute(
                sa.text(
                    """
                    CREATE POLICY staff_read_own ON staff_profiles
                      FOR SELECT
                      TO authenticated
                      USING (id = auth.uid())
                    """
                )
            )
        else:
            op.execute(
                sa.text(
                    f"""
                    CREATE POLICY staff_all ON {table}
                      FOR ALL
                      TO authenticated
                      USING ({active_staff})
                      WITH CHECK ({active_staff})
                    """
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        for table in _DOMAIN_TABLES:
            if table == "staff_profiles":
                op.execute(sa.text("DROP POLICY IF EXISTS staff_read_own ON staff_profiles"))
            else:
                op.execute(sa.text(f"DROP POLICY IF EXISTS staff_all ON {table}"))
            op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))

        if _auth_users_exists(bind):
            op.execute(sa.text("DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users"))
            op.execute(sa.text("DROP FUNCTION IF EXISTS public.handle_new_staff_user()"))
            op.execute(
                sa.text(
                    "ALTER TABLE staff_profiles DROP CONSTRAINT IF EXISTS staff_profiles_id_fkey"
                )
            )

    op.drop_index("ix_staff_profiles_is_active", table_name="staff_profiles")
    op.drop_index("ix_staff_profiles_email", table_name="staff_profiles")
    op.drop_table("staff_profiles")
