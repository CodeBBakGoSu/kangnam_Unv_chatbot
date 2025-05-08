-- 과목명 정규화 테이블 생성
create table course_names (
    id bigint primary key generated always as identity,
    original_name text not null unique,    -- unique constraint 추가
    normalized_name text not null,         -- 정규화된 과목명 (예: "데이터수집과처리")
    short_name text not null,              -- 축약명 (예: "데수처")
    embedding vector(768),                 -- 정규화된 과목명의 임베딩
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 과목명 검색 함수
create or replace function match_course_name(
    query_embedding vector(768),
    match_threshold float default 0.5,
    match_count int default 5
)
returns table (
    original_name text,
    normalized_name text,
    short_name text,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        course_names.original_name,
        course_names.normalized_name,
        course_names.short_name,
        1 - (course_names.embedding <=> query_embedding) as similarity
    from course_names
    where 1 - (course_names.embedding <=> query_embedding) > match_threshold
    order by similarity desc
    limit match_count;
end;
$$;

-- 테이블이 이미 존재하는 경우를 위한 ALTER TABLE 문
-- 이 부분은 테이블이 이미 존재할 때 실행하세요
/*
ALTER TABLE course_names
ADD CONSTRAINT course_names_original_name_key UNIQUE (original_name);
*/ 