-- Per-table row count and MD5 over every row (text form). Run with PGTZ=UTC; compare with diff --strip-trailing-cr.
select 'certifications', count(*), md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from certifications t
union all select 'contact_links', count(*), md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from contact_links t
union all select 'educations', count(*), md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from educations t
union all select 'experiences', count(*), md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from experiences t
union all select 'profiles', count(*), md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from profiles t
union all select 'projects', count(*), md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from projects t
union all select 'skills', count(*), md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from skills t
union all select 'alembic_version', count(*), md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from alembic_version t;
