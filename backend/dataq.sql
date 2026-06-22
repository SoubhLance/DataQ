-- ============================================================
-- DATAQ SUPABASE SCHEMA
-- Run this in Supabase SQL Editor (Project > SQL Editor > New Query)
-- Order matters: tables reference each other via foreign keys
-- ============================================================

-- Required for uuid generation
create extension if not exists "pgcrypto";

-- ============================================================
-- 1. PROFILES (extends Supabase auth.users)
-- ============================================================
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  name text,
  avatar_url text,
  created_at timestamptz not null default now()
);

-- Auto-create a profile row whenever someone signs up via Supabase Auth
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, name, avatar_url)
  values (
    new.id,
    new.email,
    new.raw_user_meta_data->>'name',
    new.raw_user_meta_data->>'avatar_url'
  );
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ============================================================
-- 2. DATASETS
-- ============================================================
create table public.datasets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  filename text not null,
  rows int,
  columns int,
  file_type text,
  created_at timestamptz not null default now()
);

create index idx_datasets_user_id on public.datasets(user_id);

-- ============================================================
-- 3. SESSIONS
-- ============================================================
create table public.sessions (
  id uuid primary key default gen_random_uuid(),
  dataset_id uuid not null references public.datasets(id) on delete cascade,
  status text not null default 'active', -- active | completed | abandoned
  created_at timestamptz not null default now(),
  last_accessed timestamptz not null default now()
);

create index idx_sessions_dataset_id on public.sessions(dataset_id);
create index idx_sessions_status on public.sessions(status);

-- ============================================================
-- 4. OPERATIONS HISTORY (powers Undo / Replay / Pipeline Studio / Codegen)
-- ============================================================
create table public.operations (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions(id) on delete cascade,
  step_number int not null,
  operation_type text not null, -- missing_values | duplicates | outliers | encoding | scaling | etc
  parameters jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index idx_operations_session_id on public.operations(session_id);
create index idx_operations_step_number on public.operations(session_id, step_number);

-- ============================================================
-- 5. EXPORTS
-- ============================================================
create table public.exports (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions(id) on delete cascade,
  format text not null, -- csv | excel | json | parquet | python | notebook | yaml
  file_url text not null,
  created_at timestamptz not null default now()
);

create index idx_exports_session_id on public.exports(session_id);

-- ============================================================
-- 6. REPORTS
-- ============================================================
create table public.reports (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions(id) on delete cascade,
  report_url text not null,
  created_at timestamptz not null default now()
);

create index idx_reports_session_id on public.reports(session_id);

-- ============================================================
-- 7. AI CHATS (future)
-- ============================================================
create table public.ai_chats (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  session_id uuid references public.sessions(id) on delete cascade,
  question text not null,
  answer text,
  created_at timestamptz not null default now()
);

create index idx_ai_chats_user_id on public.ai_chats(user_id);
create index idx_ai_chats_session_id on public.ai_chats(session_id);

-- ============================================================
-- 8. SAVED PIPELINES (future)
-- ============================================================
create table public.pipelines (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  name text not null,
  operations jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index idx_pipelines_user_id on public.pipelines(user_id);

-- ============================================================
-- 9. FAVORITE MODELS (future - ML Architect)
-- ============================================================
create table public.favorite_models (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  model_name text not null,
  created_at timestamptz not null default now()
);

create index idx_favorite_models_user_id on public.favorite_models(user_id);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- Supabase enables RLS by default on new tables in many setups,
-- but enable explicitly to be safe, then add policies.
-- ============================================================

alter table public.profiles enable row level security;
alter table public.datasets enable row level security;
alter table public.sessions enable row level security;
alter table public.operations enable row level security;
alter table public.exports enable row level security;
alter table public.reports enable row level security;
alter table public.ai_chats enable row level security;
alter table public.pipelines enable row level security;
alter table public.favorite_models enable row level security;

-- PROFILES: a user can only see/edit their own profile
create policy "Users can view own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id);

-- DATASETS: owned directly by user_id
create policy "Users can view own datasets"
  on public.datasets for select
  using (auth.uid() = user_id);

create policy "Users can insert own datasets"
  on public.datasets for insert
  with check (auth.uid() = user_id);

create policy "Users can update own datasets"
  on public.datasets for update
  using (auth.uid() = user_id);

create policy "Users can delete own datasets"
  on public.datasets for delete
  using (auth.uid() = user_id);

-- SESSIONS: ownership inferred via the parent dataset's user_id
create policy "Users can view own sessions"
  on public.sessions for select
  using (
    exists (
      select 1 from public.datasets d
      where d.id = sessions.dataset_id and d.user_id = auth.uid()
    )
  );

create policy "Users can insert own sessions"
  on public.sessions for insert
  with check (
    exists (
      select 1 from public.datasets d
      where d.id = sessions.dataset_id and d.user_id = auth.uid()
    )
  );

create policy "Users can update own sessions"
  on public.sessions for update
  using (
    exists (
      select 1 from public.datasets d
      where d.id = sessions.dataset_id and d.user_id = auth.uid()
    )
  );

create policy "Users can delete own sessions"
  on public.sessions for delete
  using (
    exists (
      select 1 from public.datasets d
      where d.id = sessions.dataset_id and d.user_id = auth.uid()
    )
  );

-- OPERATIONS: ownership inferred via session -> dataset -> user_id
create policy "Users can view own operations"
  on public.operations for select
  using (
    exists (
      select 1 from public.sessions s
      join public.datasets d on d.id = s.dataset_id
      where s.id = operations.session_id and d.user_id = auth.uid()
    )
  );

create policy "Users can insert own operations"
  on public.operations for insert
  with check (
    exists (
      select 1 from public.sessions s
      join public.datasets d on d.id = s.dataset_id
      where s.id = operations.session_id and d.user_id = auth.uid()
    )
  );

create policy "Users can delete own operations"
  on public.operations for delete
  using (
    exists (
      select 1 from public.sessions s
      join public.datasets d on d.id = s.dataset_id
      where s.id = operations.session_id and d.user_id = auth.uid()
    )
  );

-- EXPORTS: same pattern as operations
create policy "Users can view own exports"
  on public.exports for select
  using (
    exists (
      select 1 from public.sessions s
      join public.datasets d on d.id = s.dataset_id
      where s.id = exports.session_id and d.user_id = auth.uid()
    )
  );

create policy "Users can insert own exports"
  on public.exports for insert
  with check (
    exists (
      select 1 from public.sessions s
      join public.datasets d on d.id = s.dataset_id
      where s.id = exports.session_id and d.user_id = auth.uid()
    )
  );

-- REPORTS: same pattern
create policy "Users can view own reports"
  on public.reports for select
  using (
    exists (
      select 1 from public.sessions s
      join public.datasets d on d.id = s.dataset_id
      where s.id = reports.session_id and d.user_id = auth.uid()
    )
  );

create policy "Users can insert own reports"
  on public.reports for insert
  with check (
    exists (
      select 1 from public.sessions s
      join public.datasets d on d.id = s.dataset_id
      where s.id = reports.session_id and d.user_id = auth.uid()
    )
  );

-- AI_CHATS: owned directly by user_id
create policy "Users can view own ai_chats"
  on public.ai_chats for select
  using (auth.uid() = user_id);

create policy "Users can insert own ai_chats"
  on public.ai_chats for insert
  with check (auth.uid() = user_id);

-- PIPELINES: owned directly by user_id
create policy "Users can view own pipelines"
  on public.pipelines for select
  using (auth.uid() = user_id);

create policy "Users can insert own pipelines"
  on public.pipelines for insert
  with check (auth.uid() = user_id);

create policy "Users can update own pipelines"
  on public.pipelines for update
  using (auth.uid() = user_id);

create policy "Users can delete own pipelines"
  on public.pipelines for delete
  using (auth.uid() = user_id);

-- FAVORITE_MODELS: owned directly by user_id
create policy "Users can view own favorite_models"
  on public.favorite_models for select
  using (auth.uid() = user_id);

create policy "Users can insert own favorite_models"
  on public.favorite_models for insert
  with check (auth.uid() = user_id);

create policy "Users can delete own favorite_models"
  on public.favorite_models for delete
  using (auth.uid() = user_id);

-- ============================================================
-- HELPER: auto-update last_accessed on sessions when touched
-- (call this from your FastAPI backend on each operation, or
-- use this trigger to bump it whenever an operation is inserted)
-- ============================================================
create or replace function public.touch_session_last_accessed()
returns trigger as $$
begin
  update public.sessions
  set last_accessed = now()
  where id = new.session_id;
  return new;
end;
$$ language plpgsql security definer;

create trigger on_operation_insert_touch_session
  after insert on public.operations
  for each row execute procedure public.touch_session_last_accessed();

-- ============================================================
-- STORAGE BUCKETS
-- Run separately, or via Supabase Dashboard > Storage > New Bucket
-- These statements work via the storage schema if you prefer SQL:
-- ============================================================
insert into storage.buckets (id, name, public)
values
  ('uploads', 'uploads', false),
  ('cleaned', 'cleaned', false),
  ('reports', 'reports', false),
  ('exports', 'exports', false)
on conflict (id) do nothing;

-- Storage RLS: only allow authenticated users to access files
-- under a folder path matching their own user id, e.g. uploads/{user_id}/heart.csv
create policy "Users can upload own files"
  on storage.objects for insert
  with check (
    bucket_id in ('uploads','cleaned','reports','exports')
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "Users can view own files"
  on storage.objects for select
  using (
    bucket_id in ('uploads','cleaned','reports','exports')
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "Users can delete own files"
  on storage.objects for delete
  using (
    bucket_id in ('uploads','cleaned','reports','exports')
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- ============================================================
-- DONE
-- After running:
-- 1. Go to Authentication > Providers, enable Google + GitHub OAuth
-- 2. Go to Authentication > URL Configuration, set your redirect URLs
-- 3. Use storage paths like: uploads/{user_id}/{filename} when uploading
--    so the RLS folder-matching policy above works correctly
-- ============================================================