# Ops policy locks (Phase 1 usable path)

Locked for implementation of the usable ops path. Change deliberately if ops disagrees.

## Group numbers

- Allocate **only** when a group is created, via DB sequence / allocator.
- Numbers are **permanent** (no reuse, no renumbering).
- Start from existing sequence (default 1); no historical import in v1.

## Contact person

- Exactly **one** contact per group.
- Contact must be a **member** of the group.
- Prefill from form `Contact Person of Group` when available; staff may change in UI.
- Contact may be recorded as a pending name until that person has an applicant row.

## Minimum data

- Creating/attaching a group requires a saved **applicant** with at least a **display name** (not `N/A` / empty).
- Email/phone may be `N/A`.
- Groups may be created before every roommate has uploaded; other names from `List Others in Group` become **pending roommate references**.

## Review vs manual (v1)

- **Manual** create/attach from application detail (primary).
- Process still creates a **review_item** when matching defers (audit trail).
- Full review-queue resolve UI can come later; process + manual group actions are enough for v1.

## Excel

- Export **all** groups (any status) with their members.
- Columns (v1): group number, status, applicant name, is_contact, email, phone, GPA, property preferences (ranked), application received date.
- Incomplete member fields export as blank/`N/A`.

## Extraction

- Durkin label/tab form; full mapped field set; blanks → `"N/A"`.
- Do **not** persist SSN in v1.
- Filename name is secondary fallback only.
