# Housing Processor — Master Overview

**Last updated:** July 21, 2026  
**Audience:** anyone who needs to understand what this system is, what it does today, and where it’s going — without reading the code.

---

## In one sentence

This is an **internal tool for housing staff** that turns student housing Word applications into organized roommate-group records (and, later, Excel reports) — with a database as the single source of truth.

---

## Why it exists

Today, student housing applications often arrive as Microsoft Word (`.docx`) files at different times. Roommate names are messy, preferences vary, and staff spend a lot of time copying information into spreadsheets.

This system is meant to:

1. **Receive and keep** the original Word files safely  
2. **Extract** applicant, roommate, contact, and property preference details  
3. **Group** people into roommate groups with stable group numbers  
4. **Flag** anything unclear for a human to decide  
5. **Export** a clean Excel workbook for day-to-day operations  

Students do **not** use this product. It is for **operations / housing staff** only.

---

## The big idea (non-negotiable)

| Thing | Role |
| --- | --- |
| **Database** | The official record — what the business trusts |
| **Word documents** | Inputs only — kept as archives, not edited as the master list |
| **Excel workbooks** | Reports generated *from* the database — never the master list |

Automation may help read a document or suggest a match. It should **not** silently invent group numbers or overwrite conflicting data without staff review when something is ambiguous.

---

## Where the app stands today

Think of the current product as a **working scaffold**: the doors, rooms, and wiring are in place, but several rooms are still empty.

### What staff can do now

- **Sign up / sign in** with email and password (when connected to Supabase)  
- **Browse** the ops screens without being forced to a login page first  
- **Upload** a housing application Word file from the Dashboard  
- **See uploaded applications** on the Applications page  
- **Browse Groups** (list and detail) — these stay empty until real grouping is built  
- Have the system **start processing** an application (via a staff/developer action); it currently ends in **“needs review”** because automatic extraction and matching are not finished yet  

### What is not ready for daily use yet

| Capability | Status in plain English |
| --- | --- |
| Reading fields out of Word (name, email, roommates, houses, GPA, etc.) | Placeholder — text can be read, but structured mapping is not done |
| Automatically putting people into roommate groups | Not built — unclear cases always go to “needs review” |
| Creating or editing groups in the UI | Not built |
| A real review queue (decide match / fix data) | Not built |
| Generating and downloading Excel for ops | Not wired end-to-end |
| Email inbox ingest, CRM sync, student portal | Future work |

**Bottom line:** staff can already get files into the system and see them listed. They **cannot yet** rely on the system to extract fields, assign group numbers, resolve reviews, or produce the Excel workbook. Closing that gap is the path from “scaffold” to “daily tool.”

---

## What you see on screen

The staff website and the behind-the-scenes service run together (typically at `http://127.0.0.1:8000/` when running locally).

| Screen | What it’s for |
| --- | --- |
| **Dashboard** | Check that the system is up; upload a `.docx` application |
| **Groups** | Browse roommate groups (filter by group number) |
| **Group detail** | See members of one group (contact person, email, phone) |
| **Applications** | See every uploaded file: name, status, when it arrived |
| **Sign in / Sign up** | Create an account or log in with email and password |

The top bar always offers **Dashboard**, **Groups**, **Applications**, a **group number** search, and either **Log in / Sign up** or your email plus **Log out**.

---

## The staff journey (today vs intended)

### Today’s realistic journey

```text
1. Open the site
2. Sign in (or sign up) if you need to upload or load lists
3. Upload a Word application on the Dashboard
4. Confirm it appears under Applications
5. Processing (when run) marks it “needs review”
6. Groups stay empty until grouping features are built
```

### The intended full journey (once Phase 1 is complete)

```text
Word application arrives
        ↓
Staff uploads it (or email ingest, later)
        ↓
System stores the file and creates an application record
        ↓
System extracts applicant + roommate + preference details
        ↓
System tries to match to an existing roommate group
        ↓
Clear match → attach to that group
Ambiguous / new → staff review → create or attach group
        ↓
Group numbers are permanent and sequential
        ↓
Staff exports Excel from the database whenever needed
```

---

## How information moves (plain English)

1. **Someone uploads a Word file.**  
2. The system checks whether that exact file was already uploaded (duplicate detection).  
3. The original file is **archived**; a row is written in the **database** saying an application was received.  
4. When processing runs, the system tries to understand the document and decide on a group.  
5. Today that decision almost always becomes **“a human needs to look at this.”**  
6. Later, staff will resolve those cases, groups will fill in, and Excel will be generated from the database — not by retyping Word into a spreadsheet.

---

## Accounts and access

- Staff create an account with **email and password** (Sign up) or use an existing one (Log in).  
- After login, the site **remembers you** as you move between pages.  
- Looking around without logging in is allowed; **loading lists or uploading** requires being signed in.  
- Only **active staff accounts** can use the protected features.  
- This is **not** a public student portal.

---

## What’s underneath (only as much as you need)

You do not need this to use the product, but it helps when talking to developers:

- A **staff website** (simple web pages)  
- A **service** that accepts uploads, talks to the database, and enforces login  
- A **database** (cloud Postgres via Supabase, or a local file for offline experiments)  
- **Login** handled by Supabase Auth  
- Libraries that can read Word and (later) write Excel  

The important product rule stays the same regardless of tools: **database first; Word in; Excel out.**

---

## Roadmap in plain language

Work is organized so the system becomes useful for daily ops **before** fancy matching or AI.

1. **Reliable reading of Word applications** into structured fields  
2. **Saving applicants** and creating real “needs review” items when something is unclear  
3. **Manual group tools** — create a group or attach someone to an existing one (with permanent group numbers)  
4. **Excel export** that staff can download from live database data  
5. **Smarter matching** (and optional AI assist) only after the above is trustworthy  

Later phases may add email intake, CRM connections, richer review screens, and operational hardening (backups, metrics, etc.).

---

## How to talk about status with others

| Phrase | Meaning |
| --- | --- |
| “We can ingest applications” | Upload + store + list works |
| “We’re not live for matching yet” | Groups and auto-assignment are not production-ready |
| “Review is a placeholder” | Processing stops at “needs review”; there is no full review workspace |
| “Excel is next after extraction and groups” | Export depends on having real data in the database |
| “Scaffold, not finished ops tool” | Foundation is real; Phase 1 product outcomes are still open |

---

## Related documents

| Document | Who it’s for |
| --- | --- |
| This file (`MASTER_OVERVIEW.md`) | Everyone — shared understanding |
| [`README.md`](README.md) | Developers — how to install and run |
| `cursor-docs/` (local only) | Detailed design notes for builders; not required for business readers |

---

## Closing

**Housing Processor** is being built so housing staff can stop treating Word and Excel as the system of record.  

**Today:** sign-in, upload, and application listing are real; processing stops at human review; grouping and Excel are still ahead.  

**Next:** make extraction and group workflows trustworthy enough that Excel can be regenerated from the database on demand — then the tool becomes something operations can rely on every day.
