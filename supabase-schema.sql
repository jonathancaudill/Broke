-- Run this in your Supabase SQL editor to set up the documents table for vector search.

create extension if not exists vector;

create table if not exists documents (
  id text primary key,
  content text not null,
  collection text not null,
  section text,
  source text,
  embedding vector(1536)
);

create index if not exists documents_embedding_idx
  on documents using ivfflat (embedding vector_cosine_ops) with (lists = 4);

create index if not exists documents_collection_idx
  on documents (collection);

create or replace function match_documents(
  query_embedding vector(1536),
  match_count int default 5,
  filter_collection text default null
)
returns table (
  id text,
  content text,
  collection text,
  section text,
  source text,
  similarity float
)
language plpgsql as $$
begin
  return query
  select
    d.id,
    d.content,
    d.collection,
    d.section,
    d.source,
    1 - (d.embedding <=> query_embedding) as similarity
  from documents d
  where (filter_collection is null or d.collection = filter_collection)
  order by d.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- Q&A logging table (run in Supabase SQL editor if you already have documents set up).

create table if not exists qa_log (
  id uuid primary key default gen_random_uuid(),
  source text not null check (source in ('chat', 'ask', 'direct-chat')),
  question text not null,
  answer text,
  agent text,
  created_at timestamptz not null default now()
);

create index if not exists qa_log_created_at_idx on qa_log (created_at desc);
create index if not exists qa_log_source_idx on qa_log (source);
