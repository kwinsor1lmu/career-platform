# Personal Resume and Career Platform Design

**Status:** Draft for user review  
**Date:** 2026-09-15

## 1. Summary

Build a database-driven personal resume website that combines a polished,
recruiter-friendly resume with a substantive professional presence for peers.
The first release is single-user and focused on the core resume, while its
boundaries and data model leave a deliberate path toward a broader career
platform.

The first release will not include a content-management dashboard. Resume
content will be maintained as version-controlled files and published through
the normal repository and deployment workflow. The runtime database is part of
the foundation for structured data, future features, and eventual platform
growth; it is not an excuse to build an editor before one is needed.

## 2. Goals

### 2.1 First-release goals

- Present a clear, polished public resume.
- Let recruiters and hiring managers quickly understand qualifications,
  experience, and how to make contact.
- Give peers enough substantive context to understand professional expertise.
- Store resume information in a structured, queryable model rather than
  embedding all content directly in page templates.
- Support reliable Git-based authoring, review, and publication.
- Preserve private drafts and personal notes without exposing them publicly.
- Keep the application and persistence boundaries suitable for later expansion.

### 2.2 Explicitly deferred

The first release will not attempt to provide:

- A multi-user public platform.
- A browser-based admin editor.
- Projects or portfolio case studies.
- Articles, talks, or other professional writing.
- Recommendations or testimonials.
- A full career-goals or milestone journal.
- Recruiter-specific accounts or gated resume areas.
- Social networking, messaging, payments, or job matching.

These are future possibilities, not first-release acceptance criteria.

## 3. Users and access model

### 3.1 Public visitors

Unauthenticated visitors can view the published resume and public contact
links. The experience should prioritize fast scanning while still providing
enough detail for peers who want to understand the person's work.

### 3.2 Content owner

The initial content owner authors and reviews content through Git. There is no
runtime authoring interface in the first release.

### 3.3 Visibility rules

Every content record that could later be authored or edited should have an
explicit publication state or visibility value. The initial public site may
query only published public records. Draft and private records must not be
included in public responses, generated pages, indexes, feeds, metadata, or
search results.

The model must distinguish at least:

- `draft`: not published and available only to the authoring workflow.
- `private`: intentionally retained for the owner and never public.
- `published`: eligible for the public site.

The implementation may use an equivalent representation, but visibility
filtering must be centralized rather than reimplemented inconsistently in
individual pages.

## 4. Initial content model

The initial domain consists of one professional profile and its resume
sections:

- **Profile:** name, headline, summary, optional location, and presentation
  metadata.
- **Experience entries:** employer, role/title, dates, location or work mode,
  description, responsibilities, and achievements.
- **Education entries:** institution, credential, field of study, dates, and
  supporting description.
- **Skills:** skill name, optional category, proficiency/presentation metadata,
  and display order.
- **Certifications:** issuer, credential name, issue and expiration dates when
  relevant, credential identifier, and verification URL when available.
- **Contact links:** email or contact route plus external professional links.
- **Presentation metadata:** ordering, featured state where useful, slugs or
  stable identifiers, and visibility/publication state.

Records should use stable identifiers and explicit ordering rather than relying
on insertion order. Dates should support incomplete ranges such as
“present” and unknown start or end dates. The schema should avoid storing
rendered HTML as the primary representation; formatted content should remain
safe to render and portable across future presentation surfaces.

Although the first release is single-user, the ownership boundary should be
represented in a way that can later associate content with an account or
profile without changing every content table. The design must not introduce
multi-user workflows, invitations, or account management prematurely.

## 5. Content workflow and publication

Resume source content will live in the repository in a structured,
human-editable format. A deployment build or ingestion step will validate the
content and make the approved version available to the application and
database.

The workflow is:

1. Edit structured resume content in a Git branch.
2. Validate required fields, data types, ordering, dates, links, and visibility
   values.
3. Review and merge the change through the repository workflow.
4. Deploy the approved version.
5. Publish only records marked as public and published.

The ingestion process must fail clearly on invalid content rather than silently
dropping records or substituting success-shaped defaults. A deployment must
not expose draft or private content if ingestion or publication metadata is
incomplete.

Git history supplies the initial audit trail. Database migrations and content
ingestion must be separate concerns so that a content update does not require
an unsafe schema change.

## 6. Application architecture

Use a conventional full-stack web application with these boundaries:

- **Presentation layer:** responsive public resume pages and navigation.
- **Read/query layer:** retrieves only records permitted for the public
  surface, with consistent ordering and visibility filtering.
- **Domain/data layer:** typed models and persistence operations for profile,
  resume sections, ownership, ordering, and publication state.
- **Ingestion/validation layer:** converts version-controlled source content into
  validated structured records.
- **Database layer:** managed SQL persistence with migrations and backups.

The initial public surface should be server-renderable or statically
cacheable where practical, with progressive enhancement rather than requiring
client-side JavaScript for core resume access. Public pages should have stable
URLs, meaningful metadata, and accessible semantic structure.

The design should use portable application components and standard SQL
interfaces. Cloud-native services may be added only where they solve a clear
operational need; the first release should not depend on a large collection of
provider-specific services.

## 7. Deployment and operations

The initial target is cloud infrastructure, with the provider left open until
implementation planning. The deployment must separate:

- Application/runtime deployment
- Managed SQL database
- Secrets and configuration
- Public/static asset delivery

The production baseline should include:

- Environment-specific configuration with no secrets in Git.
- Automated database migrations that are reviewable and repeatable.
- Database backups and a documented restore approach.
- Health and error visibility sufficient to detect failed deployments or
  unavailable dependencies.
- HTTPS and secure handling of any future authenticated authoring path.

The design should remain deployable on more than one major cloud provider
without rewriting the domain or persistence layers.

## 8. Security and privacy

- Public queries must enforce publication and visibility constraints at the
  data-access boundary.
- Private notes and drafts must not be sent to the browser, embedded in
  client bundles, rendered into page source, or exposed through metadata.
- Secrets, credentials, and private source content must not be committed.
- External links and imported content must be validated and rendered safely.
- Future authentication and authorization must be designed around explicit
  ownership and least privilege; no anonymous write path is permitted.
- Logs and error reports must avoid recording private note content or secrets.

## 9. Error handling

Invalid source content, failed ingestion, missing required configuration, and
database failures are deployment or operational errors and must be surfaced
with actionable diagnostics. The public site may use a user-safe error page,
but it must not silently publish partial or stale content without an explicit
and documented policy.

For read failures, the application should distinguish an unavailable
dependency from an empty valid profile. Monitoring and logs should preserve
that distinction.

## 10. Accessibility, responsiveness, and discoverability

The public resume must:

- Work on mobile, tablet, and desktop layouts.
- Use semantic headings, landmarks, lists, and links.
- Support keyboard navigation and visible focus.
- Maintain readable contrast and typography.
- Provide meaningful document titles and descriptions.
- Expose structured professional information in an SEO-friendly way without
  exposing private records.
- Treat the resume as usable content, not only as a visual composition.

## 11. Testing and acceptance criteria

The implementation plan must include tests at the smallest useful boundaries:

- Content validation rejects malformed, incomplete, contradictory, or invalid
  visibility data.
- Public queries exclude drafts and private records.
- Ordering and date-range behavior are deterministic.
- Ingestion is repeatable and does not duplicate records unexpectedly.
- A representative public page renders the complete published core resume.
- Private content is absent from HTML, metadata, API responses, and search
  results.
- Responsive and accessibility checks cover the primary public navigation and
  resume sections.
- Migration and deployment checks fail visibly when required configuration or
  dependencies are unavailable.

The first release is successful when a visitor can reach the public resume,
understand the person's qualifications and professional focus quickly, inspect
the complete core resume, and follow contact links, while repository-based
updates can be validated and deployed without exposing private content.

## 12. Growth path

The architecture should make these later additions incremental:

- Projects and case studies related to experience or skills.
- Professional writing and publications.
- Recommendations and testimonials with consent and moderation state.
- Career goals, milestones, and personal timeline entries.
- A private browser-based editor with preview and publication controls.
- Multiple users and profiles with explicit ownership and authorization.
- Selective sharing or recruiter-specific access.

These additions should reuse the existing visibility, ownership, stable
identifier, ordering, validation, and publication concepts rather than create
parallel conventions.

## 13. Decisions still intentionally open for implementation planning

The following choices are deliberately not fixed by this product spec:

- Cloud provider and exact managed services.
- Programming language and web framework.
- SQL database vendor/version.
- Exact source-content serialization format.
- Visual brand, typography, and detailed page layout.
- Whether ingestion occurs at build time, deploy time, or through a controlled
  release command.

Implementation planning should choose defaults based on repository conventions,
operational simplicity, portability, and the smallest reliable first release.
