# Student Housing Application Processing System

## Project Overview

The Student Housing Application Processing System is an internal operations platform that converts student housing application documents into clean, structured, and reviewable group records.

The system accepts Microsoft Word (`.docx`) applications containing applicant information, requested houses, roommate names, contact information, GPA, and related details. It extracts and validates the submitted information, identifies whether the applicant belongs to an existing roommate group, assigns permanent sequential group numbers, and generates a consistently formatted Excel workbook for staff use.

The project is intended to replace a repetitive, error-prone manual workflow while preserving human control over ambiguous matches and conflicting application data.

## Problem Statement

Student applications do not necessarily arrive together or in a predictable order. Members of the same roommate group may submit their applications days apart, use slightly different versions of one another's names, list house preferences differently, or provide incomplete information.

A reliable system must therefore do more than extract fields from a document. It must:

- Recognize applicants who have already been recorded.
- Match late-arriving applicants to previously created roommate groups.
- Preserve the original group number when additional roommates arrive.
- Distinguish genuinely new groups from incomplete existing groups.
- Identify the correct contact person for each group.
- Flag uncertain or conflicting information for employee review.
- Produce an orderly Excel workbook without treating Excel as the source of truth.

## Primary Goals

The system will:

1. Accept and archive housing application documents.
2. Extract applicant, roommate, property preference, and contact information.
3. Normalize and validate extracted values.
4. Detect duplicate files and duplicate applicant records.
5. Match each applicant to the correct roommate group.
6. Assign permanent, chronological group numbers to new groups.
7. Preserve group membership when applications arrive out of order.
8. Maintain a confirmed contact person for every group.
9. Generate a formatted Excel workbook with grouped applicants and bold contact names.
10. Route uncertain decisions to a human review queue.
11. Maintain an audit history of automated and manual decisions.

## Non-Goals

The initial system will not:

- Allow an LLM to independently create or modify authoritative records.
- Automatically merge people based only on similar names.
- Renumber existing groups when a late application is received.
- Use Excel as the primary database.
- Make leasing, approval, pricing, or property-assignment decisions.
- Remove human review from ambiguous identity or group matches.

## Core Operating Principle

The database is the authoritative source of truth. Word documents are source inputs, and Excel workbooks are generated outputs.

Deterministic Python logic controls validation, identity resolution, group numbering, database writes, and exports. An LLM may assist with interpreting inconsistent document language and producing structured extraction results, but it does not assign group numbers, approve matches, or write directly to the database.

## High-Level Workflow

1. An employee uploads or imports a `.docx` application.
2. The system calculates a file hash and checks for duplicate submissions.
3. Python extracts document paragraphs, tables, labels, and formatting.
4. Deterministic parsers extract known fields.
5. An LLM may structure missing or inconsistently formatted information.
6. Pydantic validation checks types, formats, required values, and internal consistency.
7. Applicant identity resolution searches for existing people using email, phone, name, and supporting evidence.
8. The group matcher compares the applicant and their listed roommates against existing groups and pending roommate references.
9. The system either:
   - Attaches the applicant to an existing group.
   - Creates a new group with the next sequential number.
   - Sends the application to the review queue.
10. Confirmed records are saved in a database transaction.
11. The current Excel workbook is regenerated from database records.
12. The original document, processing result, and decision history are archived.

## Group Numbering Rules

A group receives its permanent group number when the system first confidently recognizes that group.

Group numbers reflect the order in which groups first enter the system, not the order in which every member submits an application. Once assigned, a group number is never automatically changed.

Example:

- Sarah submits on Monday and becomes Group 1.
- Jake submits an unrelated application on Tuesday and becomes Group 2.
- Mike submits on Thursday and lists Sarah as a roommate.
- Mike is added to Group 1; Group 2 remains unchanged.

New group numbers must be allocated atomically by the database to prevent duplicates during simultaneous processing. Ambiguous applications do not receive a new group number until an employee confirms that they represent a new group.

## Matching Philosophy

Matching decisions use the strongest available evidence in descending order:

1. Exact normalized email address.
2. Exact normalized phone number.
3. Existing applicant identity and group membership.
4. Email or phone matches in pending roommate references.
5. Multiple exact roommate-name overlaps.
6. Contact-person agreement.
7. Compatible group size and property preferences.
8. Fuzzy name similarity as supporting evidence only.

Conflicting exact identifiers, competing group memberships, or inconsistent contact-person claims require human review.

The system will retain unmatched roommate names as pending references. When those roommates later submit applications, the references become evidence for attaching them to the correct existing group.

## Contact-Person Rules

Each group has one confirmed contact person. Contact status is stored explicitly in the database and is not inferred from Excel formatting.

The preferred decision order is:

1. An explicitly identified contact person in the application.
2. The group's existing confirmed contact person.
3. A manual employee selection.
4. The first applicant received, if the business enables this fallback.

Conflicting contact-person claims create a review item rather than silently replacing the existing contact.

In the Excel export, the confirmed contact person's name cell is formatted in bold.

## Major System Components

### Document Ingestion

Receives `.docx` files, records metadata, calculates hashes, stores the original documents, and initiates processing.

### Document Extraction

Reads Word paragraphs, tables, field labels, formatting, and known application structures using `python-docx`.

### Structured Data Extraction

Combines deterministic field mappings with optional LLM-assisted extraction. All LLM responses must follow a strict schema and represent missing information as null rather than inventing values.

### Validation and Normalization

Normalizes names, email addresses, phone numbers, GPA values, property names, dates, and roommate references. It also detects incomplete or contradictory records.

### Applicant Identity Resolution

Finds an existing applicant or creates a new canonical applicant record. Names alone are never treated as globally unique identifiers.

### Group Matching

Scores candidate groups using applicant identities, roommate overlap, contact-person evidence, expected group size, and property preferences. It produces an automatic match, a likely-new-group result, or a review requirement.

### Review Queue

Allows employees to correct extracted values, attach an application to an existing group, create a new group, resolve contact conflicts, or mark duplicate submissions.

### Excel Export

Generates a clean workbook with one row per applicant, consecutive roommate rows, repeated group numbers, bold contact names, property preferences, filters, frozen headers, and visual group separation.

### Audit System

Records group creation, applicant attachment, manual corrections, contact changes, matching decisions, document processing, and export activity.

## Proposed Technology Stack

- **Language:** Python 3.12+
- **API:** FastAPI
- **Database:** PostgreSQL in production; SQLite for early local development
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Validation:** Pydantic
- **DOCX parsing:** `python-docx`
- **Excel generation:** `openpyxl`
- **Fuzzy comparison:** RapidFuzz
- **Phone normalization:** `phonenumbers`
- **Review interface:** Streamlit for the first internal release
- **Testing:** Pytest
- **LLM integration:** Provider-agnostic structured-output adapter

## Core Data Domains

The system will maintain records for:

- Application files
- Applicants
- Roommate groups
- Group memberships
- Pending roommate references
- Properties
- Group property preferences
- Review items
- Audit events
- Excel export history

Detailed schemas, relationships, indexes, and constraints will be defined in a dedicated database design document.

## Excel Output Requirements

The generated workbook should include, at minimum:

- Group number
- Applicant name
- Contact-person status
- Phone number
- Email address
- GPA
- Requested properties in preference order
- Expected or confirmed group size
- Application received date
- Group status
- Review notes or missing information

Rows must be sorted by group number, with the contact person first within each group. Group numbers should be repeated on every row to preserve filtering and sorting behavior. Merged cells should not be used.

## Security and Data Handling

The system processes student personally identifiable information and must be treated as an internal restricted-access application.

Required safeguards include:

- Role-based employee access
- Encryption in transit and at rest
- Secure storage of original applications
- Database backups
- Audit logging
- Minimal exposure of student data to third-party services
- Approved data-processing terms before external LLM use
- Redaction or synthetic data for development and automated tests
- Configurable retention and deletion policies

## Reliability Requirements

The system must:

- Process the same file idempotently.
- Prevent duplicate group numbers.
- Preserve original source values alongside normalized values.
- Perform related database changes within transactions.
- Never silently overwrite conflicting information.
- Recover cleanly from extraction, model, database, and export failures.
- Track parser, prompt, and model versions used for each application.
- Support reprocessing without destroying previously confirmed decisions.

## Initial Delivery Phases

### Phase 1: Deterministic MVP

- Manual DOCX upload
- Original-file archival
- Duplicate-file detection
- Deterministic field extraction
- SQLite database
- Manual group selection and correction
- Permanent sequential group numbering
- Excel generation with grouped rows and bold contact names

### Phase 2: Intelligent Matching

- PostgreSQL migration
- Applicant identity resolution
- Pending roommate references
- Candidate group scoring
- Human review queue
- LLM-assisted structured extraction
- Property alias resolution

### Phase 3: Operational Hardening

- Authentication and employee roles
- Background document processing
- Comprehensive audit interface
- Automated backups
- Error reporting and operational metrics
- Historical spreadsheet import
- Regression tests built from sanitized application cases

### Phase 4: Integrations

- Email inbox ingestion
- Barefoot CRM synchronization
- Applicant status workflows
- Property availability integration
- Employee alerts and processing summaries

## Success Criteria

The first production-ready release should demonstrate that:

- Staff can process applications without manually transcribing every field.
- Late roommate applications reliably join the correct existing group.
- Existing group numbers remain stable.
- No duplicate group numbers can be created.
- Ambiguous cases are surfaced with understandable evidence.
- Contact-person formatting is consistently correct.
- The database and Excel output remain synchronized.
- Every automated and manual decision can be audited.
- Historical test cases produce repeatable matching outcomes.

## Documentation Roadmap

This overview establishes the system's purpose and boundaries. The remaining technical design should be documented separately so each area can evolve without turning one file into a small novel.

Recommended follow-up documents:

1. `REQUIREMENTS.md`
2. `SYSTEM_ARCHITECTURE.md`
3. `DATABASE_SCHEMA.md`
4. `DOCX_EXTRACTION_PIPELINE.md`
5. `IDENTITY_AND_GROUP_MATCHING.md`
6. `LLM_INTEGRATION.md`
7. `EXCEL_EXPORT_SPEC.md`
8. `REVIEW_DASHBOARD.md`
9. `SECURITY_AND_PRIVACY.md`
10. `TESTING_STRATEGY.md`
11. `IMPLEMENTATION_ROADMAP.md`

## Current Project Status

The project is in architecture and documentation planning. No implementation decisions beyond the principles and proposed stack in this document should be considered irreversible. The immediate objective is to finish the build-ready documentation set, establish representative sanitized test cases, and then implement the deterministic MVP before adding automated LLM-assisted matching.
