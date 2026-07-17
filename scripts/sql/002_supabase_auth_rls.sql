-- ============================================================================
-- Staff auth profiles + RLS (defense-in-depth for Supabase Auth)
--
-- Preferred apply path:  uv run alembic upgrade head
-- Manual apply: paste into Supabase SQL Editor after 001_supabase_schema.sql,
-- then:  uv run alembic stamp 0003_staff_auth
--
-- Notes:
-- - FastAPI uses a privileged DATABASE_URL and bypasses RLS.
-- - RLS protects direct access via anon/authenticated Supabase keys.
-- - Create staff users in Supabase Dashboard (Auth → Users). Disable public sign-ups.
-- ============================================================================

CREATE TABLE IF NOT EXISTS staff_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users (id) ON DELETE CASCADE,
    email VARCHAR(320) NOT NULL,
    display_name VARCHAR(256) NULL,
    role VARCHAR(64) NOT NULL DEFAULT 'operations',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_staff_profiles_email ON staff_profiles (email);
CREATE INDEX IF NOT EXISTS ix_staff_profiles_is_active ON staff_profiles (is_active);

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
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_staff_user();

-- Backfill profiles for users created before this script ran
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
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------

ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE applicants ENABLE ROW LEVEL SECURITY;
ALTER TABLE groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE group_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_roommate_references ENABLE ROW LEVEL SECURITY;
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE group_property_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE outbox_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE excel_exports ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS staff_all ON applications;
DROP POLICY IF EXISTS staff_all ON applicants;
DROP POLICY IF EXISTS staff_all ON groups;
DROP POLICY IF EXISTS staff_all ON group_members;
DROP POLICY IF EXISTS staff_all ON pending_roommate_references;
DROP POLICY IF EXISTS staff_all ON properties;
DROP POLICY IF EXISTS staff_all ON group_property_preferences;
DROP POLICY IF EXISTS staff_all ON review_items;
DROP POLICY IF EXISTS staff_all ON audit_events;
DROP POLICY IF EXISTS staff_all ON outbox_events;
DROP POLICY IF EXISTS staff_all ON excel_exports;
DROP POLICY IF EXISTS staff_read_own ON staff_profiles;

CREATE POLICY staff_all ON applications
  FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  );

CREATE POLICY staff_all ON applicants
  FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  );

CREATE POLICY staff_all ON groups
  FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  );

CREATE POLICY staff_all ON group_members
  FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  );

CREATE POLICY staff_all ON pending_roommate_references
  FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  );

CREATE POLICY staff_all ON properties
  FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  );

CREATE POLICY staff_all ON group_property_preferences
  FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  );

CREATE POLICY staff_all ON review_items
  FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  );

CREATE POLICY staff_all ON audit_events
  FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  );

CREATE POLICY staff_all ON outbox_events
  FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  );

CREATE POLICY staff_all ON excel_exports
  FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.staff_profiles p
      WHERE p.id = auth.uid() AND p.is_active
    )
  );

-- Staff may read their own profile; role/is_active changes stay server/Dashboard only
CREATE POLICY staff_read_own ON staff_profiles
  FOR SELECT
  TO authenticated
  USING (id = auth.uid());
