# Credit Institute Guarantee Management System — Complete Implementation Plan

---

## Review of Original Documents — Gaps & Flaws Found

### Critical Missing Business Concepts
1. **Beneficiary Entity** — A guarantee is issued TO a beneficiary ON BEHALF OF a client. Your ER diagram has no beneficiary.
2. **Guarantee Types** — No structured model for types (Bid Bond, Performance Bond, Advance Payment, Retention, Customs, Good Execution).
3. **Guarantee Lifecycle States** — No defined states or allowed transitions. Need: Draft → Under Review → Approved → Issued → Active → Expired/Cancelled/Claimed.
4. **Fee/Commission Calculation** — No formula, no calculation model, no payment tracking.
5. **Payment Tracking** — No model for deposits, commissions, refunds.
6. **Expiry & Renewal** — No auto-notification or renewal workflow.
7. **Guarantee Letter** — The actual issued document/letter entity is not modeled.
8. **Claims** — Not in scope now, but architecture must support it (the `CLAIMED` state must exist).
9. **Credit Framework** — No credit scoring/evaluation system. Need a dynamic weighted scorecard that evaluates customer financial data + collateral to determine credit limits, with automated checks in the workflow and Director override capability.

### Missing Technical Components
1. **Client Portal** — Your docs only mention admin. Clients need a self-service portal (submit requests, track status, download documents, see fee statements).
2. **REST API** — Needed for portal and future integrations (DRF).
3. **Notification System** — No app for expiry alerts, approval notifications, status updates.
4. **Async Task Processing** — Celery for document generation, scheduled expiry checks, notifications.

### Requirements Document Flaws
1. No non-functional requirements (performance, availability, scalability).
2. Requirement 10 says SQLite for testing — **dangerous** if using PostgreSQL-specific features. Use PostgreSQL everywhere.
3. Missing file upload restrictions (size/type limits).
4. Missing data validation rules for financial amounts (decimal precision).
5. Missing backup/disaster recovery requirements.

---

## Technology Stack

| Layer | Technology | Version/Notes |
|---|---|---|
| Framework | Django 5.2 LTS | Long-term support |
| Admin UI | `django-unfold-rtl` 2.0.5 | RTL fork of django-unfold for Persian |
| Database | PostgreSQL 16+ | Used in all environments including dev/test |
| State Machine | `django-fsm-2` | Maintained fork, supports Django 5.x and 6.0 |
| Async Tasks | Celery 5.x + Redis | Task queue and message broker |
| REST API | Django REST Framework 3.15+ | For client portal and future integrations |
| PDF Generation | WeasyPrint 64+ | RTL improvements landed in v64; use with `django-weasyprint` |
| DOCX Generation | `python-docx-template` (docxtpl) | Jinja2-based Word templates; RTL via template document settings |
| Auth | `django-allauth` | Multi-backend auth for both admin and portal |
| Caching | Redis | Shared with Celery broker |
| Testing | pytest-django + factory-boy | PostgreSQL for test DB too |

---

## Corrected & Complete ER Diagram

This is the full entity-relationship map including all entities missing from the original design documents.

```
┌─────────────────────────────────────────────────────────────────────┐
│  ACCOUNTS APP                                                       │
│                                                                     │
│  User (extends AbstractUser)                                        │
│  ├── role: enum(ANALYST, ACCOUNTANT, DIRECTOR, CLIENT_USER)         │
│  ├── national_code: char(10)                                        │
│  ├── phone: char(11)                                                │
│  └── is_staff / is_portal_user                                      │
│                                                                     │
│  Role / Permission (Django groups + object-level via django-guardian)│
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  CLIENTS APP                                                        │
│                                                                     │
│  Client (abstract: no)                                              │
│  ├── client_type: enum(LEGAL, REAL)                                 │
│  ├── client_code: char, unique, auto-generated                      │
│  ├── credit_limit: Decimal(20,0)  [Rials, no decimals needed]       │
│  ├── used_credit: Decimal(20,0)  [computed / cached]                │
│  ├── is_active: bool                                                │
│  ├── portal_user: FK → User (nullable, for portal login)            │
│  ├── created_by, updated_by: FK → User                              │
│  └── timestamps                                                     │
│                                                                     │
│  LegalPersonProfile (OneToOne → Client)                             │
│  ├── company_name, registration_number, national_id                 │
│  ├── economic_code, registration_date                               │
│  └── ceo_name, ceo_national_code                                    │
│                                                                     │
│  RealPersonProfile (OneToOne → Client)                              │
│  ├── first_name, last_name, father_name                             │
│  ├── national_code, birth_date, gender                              │
│  └── id_number (shenasnameh)                                        │
│                                                                     │
│  ClientContact                                                      │
│  ├── client: FK → Client                                            │
│  ├── contact_type: enum(PHONE, EMAIL, FAX, ADDRESS)                 │
│  ├── value, is_primary                                              │
│  └── timestamps                                                     │
│                                                                     │
│  ClientDocument                                                     │
│  ├── client: FK → Client                                            │
│  ├── doc_type: enum(NATIONAL_CARD, REGISTRATION_CERT, ...)          │
│  ├── file: FileField (validated size/type)                          │
│  ├── uploaded_by: FK → User                                         │
│  └── timestamps                                                     │
│                                                                     │
│  ClientBankAccount                                                  │
│  ├── client: FK → Client                                            │
│  ├── bank_name, branch, account_number, sheba, card_number          │
│  └── is_primary, timestamps                                         │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  GUARANTEES APP                                                     │
│                                                                     │
│  GuaranteeType (predefined, admin-editable)                         │
│  ├── code: char, unique (BID, PERFORMANCE, ADVANCE, RETENTION,     │
│  │         CUSTOMS, GOOD_EXECUTION)                                 │
│  ├── name_fa: char (Persian name)                                   │
│  ├── default_commission_rate: Decimal(5,4)  [e.g. 0.0150 = 1.5%]   │
│  ├── default_deposit_ratio: Decimal(5,4)                            │
│  ├── typical_duration_months: int                                   │
│  ├── requires_collateral: bool                                      │
│  └── is_active, timestamps                                          │
│                                                                     │
│  *** Beneficiary ***  [MISSING FROM ORIGINAL]                       │
│  ├── name: char                                                     │
│  ├── beneficiary_type: enum(GOVERNMENT, PRIVATE, BANK, OTHER)       │
│  ├── national_id / registration_number                              │
│  ├── address, phone, contact_person                                 │
│  └── is_active, timestamps                                          │
│                                                                     │
│  Guarantee                                                          │
│  ├── guarantee_number: char, unique, auto-generated                 │
│  ├── client: FK → Client                                            │
│  ├── beneficiary: FK → Beneficiary                                  │
│  ├── guarantee_type: FK → GuaranteeType                             │
│  ├── state: FSMField (DRAFT → UNDER_REVIEW → APPROVED →            │
│  │          ISSUED → ACTIVE → EXPIRED | CANCELLED | CLAIMED)        │
│  ├── framework_status: enum(PENDING, PASS, BLOCKED, OVERRIDDEN)     │
│  ├── credit_evaluation: FK → CreditEvaluation (nullable)            │
│  ├── amount: Decimal(20,0)                                          │
│  ├── currency: char(3) default='IRR'                                │
│  ├── issue_date, effective_date, expiry_date                        │
│  ├── purpose / description: text                                    │
│  ├── deposit_amount: Decimal(20,0)                                  │
│  ├── commission_rate: Decimal(5,4)                                  │
│  ├── commission_amount: Decimal(20,0)                               │
│  ├── contract: FK → Contract (nullable, set after contract created) │
│  ├── parent_guarantee: FK → self (nullable, for renewals)           │
│  ├── renewal_count: int default=0                                   │
│  ├── created_by, reviewed_by, approved_by: FK → User                │
│  ├── rejection_reason: text (nullable)                              │
│  └── timestamps                                                     │
│                                                                     │
│  *** GuaranteeStateTransition (via django-fsm-log) ***              │
│  ├── guarantee: FK → Guarantee                                      │
│  ├── source_state, target_state                                     │
│  ├── transitioned_by: FK → User                                     │
│  ├── comment: text                                                  │
│  └── timestamp                                                      │
│                                                                     │
│  *** GuaranteeLetter ***  [MISSING FROM ORIGINAL]                   │
│  ├── guarantee: OneToOne → Guarantee                                │
│  ├── letter_number: char, unique                                    │
│  ├── letter_date: date                                              │
│  ├── template_used: char                                            │
│  ├── generated_pdf: FileField                                       │
│  ├── generated_docx: FileField                                      │
│  ├── is_signed: bool                                                │
│  ├── signed_by: FK → User                                           │
│  └── timestamps                                                     │
│                                                                     │
│  *** FeeSchedule ***  [MISSING FROM ORIGINAL]                       │
│  ├── guarantee: FK → Guarantee                                      │
│  ├── fee_type: enum(COMMISSION, STAMP_DUTY, SERVICE_FEE, RENEWAL)   │
│  ├── amount: Decimal(20,0)                                          │
│  ├── calculation_basis: text (human-readable formula record)        │
│  ├── due_date: date                                                 │
│  ├── is_paid: bool                                                  │
│  └── timestamps                                                     │
│                                                                     │
│  *** Payment ***  [MISSING FROM ORIGINAL]                           │
│  ├── client: FK → Client                                            │
│  ├── guarantee: FK → Guarantee (nullable)                           │
│  ├── fee_schedule: FK → FeeSchedule (nullable)                      │
│  ├── payment_type: enum(DEPOSIT, COMMISSION, REFUND, RENEWAL_FEE)   │
│  ├── amount: Decimal(20,0)                                          │
│  ├── payment_method: enum(BANK_TRANSFER, CHECK, CASH, ONLINE)       │
│  ├── reference_number: char                                         │
│  ├── payment_date: date                                             │
│  ├── verified_by: FK → User (nullable)                              │
│  ├── is_verified: bool                                              │
│  └── timestamps                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  CREDIT FRAMEWORK APP  [NEW]                                        │
│                                                                     │
│  ScorecardCategory                                                  │
│  ├── name_fa, description, ordering                                 │
│  (e.g., "Financial Ratios", "Collateral Quality", "Business History")│
│                                                                     │
│  ScorecardFactor                                                    │
│  ├── category: FK → ScorecardCategory                               │
│  ├── name_fa, code: char                                            │
│  ├── weight: Decimal (all weights sum to 100)                       │
│  ├── value_type: enum(NUMERIC, PERCENTAGE, ENUM, BOOLEAN)           │
│  ├── min_value, max_value                                           │
│  ├── is_active, timestamps                                          │
│  (e.g., "Debt-to-Equity" weight=15, "Collateral Coverage %" weight=25)│
│                                                                     │
│  ScorecardFactorOption (for ENUM-type factors)                      │
│  ├── factor: FK → ScorecardFactor                                   │
│  ├── label_fa, score                                                │
│  (e.g., Collateral Type: Real Estate=100, Bank Deposit=90, Check=60)│
│                                                                     │
│  CreditTier                                                         │
│  ├── name_fa: char                                                  │
│  ├── min_score, max_score: Decimal                                  │
│  ├── max_credit_limit: Decimal(20,0)                                │
│  ├── max_single_guarantee_pct: Decimal                              │
│  ├── description, is_active                                         │
│  (e.g., "Tier A" score 80-100 → max 50B Rials)                     │
│                                                                     │
│  CreditEvaluation                                                   │
│  ├── client: FK → Client                                            │
│  ├── guarantee: FK → Guarantee (nullable)                           │
│  ├── evaluated_by: FK → User                                        │
│  ├── evaluation_date: datetime                                      │
│  ├── total_score: Decimal                                           │
│  ├── assigned_tier: FK → CreditTier                                 │
│  ├── recommended_credit_limit: Decimal(20,0)                        │
│  ├── status: enum(PASS, FAIL, OVERRIDDEN)                           │
│  ├── is_active: bool (latest evaluation per client)                 │
│  └── timestamps                                                     │
│                                                                     │
│  CreditEvaluationDetail                                             │
│  ├── evaluation: FK → CreditEvaluation                              │
│  ├── factor: FK → ScorecardFactor                                   │
│  ├── raw_value, normalized_score (0-100), weighted_score            │
│  └── notes                                                          │
│                                                                     │
│  DirectorOverride                                                   │
│  ├── evaluation: FK → CreditEvaluation                              │
│  ├── guarantee: FK → Guarantee                                      │
│  ├── overridden_by: FK → User                                       │
│  ├── override_reason: text (required)                               │
│  ├── original_tier: FK → CreditTier                                 │
│  ├── granted_credit_limit: Decimal(20,0)                            │
│  ├── override_date, expiry_date (nullable, time-bound)              │
│  └── timestamps                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  COLLATERALS APP                                                    │
│                                                                     │
│  Collateral                                                         │
│  ├── client: FK → Client                                            │
│  ├── collateral_type: enum(REAL_ESTATE, BANK_DEPOSIT, CHECK,        │
│  │    PROMISSORY_NOTE, STOCK, EQUIPMENT, OTHER)                     │
│  ├── description, estimated_value: Decimal(20,0)                    │
│  ├── appraised_value: Decimal(20,0) (nullable)                      │
│  ├── appraisal_date: date (nullable)                                │
│  ├── status: enum(AVAILABLE, PLEDGED, RELEASED, SEIZED)             │
│  └── timestamps, created_by                                         │
│                                                                     │
│  GuaranteeCollateral  (M2M through table)                           │
│  ├── guarantee: FK → Guarantee                                      │
│  ├── collateral: FK → Collateral                                    │
│  ├── pledged_amount: Decimal(20,0) [portion of collateral pledged]  │
│  ├── pledged_date, released_date (nullable)                         │
│  └── timestamps                                                     │
│                                                                     │
│  CollateralDocument                                                 │
│  ├── collateral: FK → Collateral                                    │
│  ├── doc_type, file, uploaded_by                                    │
│  └── timestamps                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  CONTRACTS APP                                                      │
│                                                                     │
│  Contract                                                           │
│  ├── contract_number: char, unique                                  │
│  ├── client: FK → Client                                            │
│  ├── contract_type: enum(GUARANTEE_ISSUANCE, FRAMEWORK, AMENDMENT)  │
│  ├── start_date, end_date                                           │
│  ├── total_value: Decimal(20,0)                                     │
│  ├── status: enum(DRAFT, ACTIVE, COMPLETED, TERMINATED)             │
│  ├── signed_date, signed_by_client, signed_by_director              │
│  └── timestamps, created_by                                         │
│                                                                     │
│  ContractDocument                                                   │
│  ├── contract: FK → Contract                                        │
│  ├── doc_type: enum(ORIGINAL, AMENDMENT, APPENDIX)                  │
│  ├── file, version                                                  │
│  └── timestamps                                                     │
│                                                                     │
│  DocumentTemplate                                                   │
│  ├── name, code: char, unique                                       │
│  ├── template_type: enum(GUARANTEE_LETTER, CONTRACT, RECEIPT, ...)  │
│  ├── format: enum(HTML, DOCX)                                       │
│  ├── file: FileField (for DOCX) / template_content: text (for HTML) │
│  ├── variables_schema: JSONField (documents expected context vars)   │
│  ├── is_active: bool                                                │
│  └── timestamps                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  NOTIFICATIONS APP  [NEW]                                           │
│                                                                     │
│  NotificationTemplate                                               │
│  ├── code: char, unique (e.g. GUARANTEE_EXPIRY_30D)                 │
│  ├── channel: enum(IN_APP, SMS, EMAIL)                              │
│  ├── subject_template, body_template: text (Jinja2)                 │
│  └── is_active                                                      │
│                                                                     │
│  Notification                                                       │
│  ├── recipient: FK → User                                           │
│  ├── template: FK → NotificationTemplate (nullable)                 │
│  ├── title, body: text                                              │
│  ├── channel: enum(IN_APP, SMS, EMAIL)                              │
│  ├── related_content_type: FK → ContentType                         │
│  ├── related_object_id: PositiveIntegerField                        │
│  ├── related_object: GenericForeignKey                              │
│  ├── is_read: bool                                                  │
│  ├── read_at: datetime (nullable)                                   │
│  └── created_at                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  AUDIT APP                                                          │
│                                                                     │
│  AuditLog (via django-auditlog or custom)                           │
│  ├── content_type, object_id, object_repr                           │
│  ├── action: enum(CREATE, UPDATE, DELETE)                           │
│  ├── changes: JSONField                                             │
│  ├── actor: FK → User                                               │
│  ├── remote_addr: GenericIPAddressField                             │
│  └── timestamp                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  ANALYTICS APP                                                      │
│                                                                     │
│  No persistent models — uses DB views, aggregation queries,         │
│  and Unfold dashboard components. Optionally:                       │
│                                                                     │
│  DashboardSnapshot (for caching expensive aggregations)             │
│  ├── report_type: char                                              │
│  ├── data: JSONField                                                │
│  ├── generated_at: datetime                                         │
│  └── parameters: JSONField                                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  PORTAL APP  [NEW — separate from admin]                            │
│                                                                     │
│  GuaranteeRequest                                                   │
│  ├── client: FK → Client                                            │
│  ├── submitted_by: FK → User (portal user)                          │
│  ├── guarantee_type: FK → GuaranteeType                             │
│  ├── beneficiary_name, beneficiary_info: text                       │
│  ├── requested_amount: Decimal(20,0)                                │
│  ├── purpose: text                                                  │
│  ├── requested_duration_months: int                                 │
│  ├── status: enum(SUBMITTED, UNDER_REVIEW, CONVERTED, REJECTED)    │
│  ├── converted_to_guarantee: FK → Guarantee (nullable)              │
│  ├── reviewer_notes: text                                           │
│  └── timestamps                                                     │
└─────────────────────────────────────────────────────────────────────┘

RELATIONSHIPS SUMMARY:
  Client 1──* Guarantee
  Client 1──* Collateral
  Client 1──* Contract
  Client 1──* Payment
  Client 1──1 LegalPersonProfile (if LEGAL)
  Client 1──1 RealPersonProfile (if REAL)
  Client 1──* ClientContact
  Client 1──* ClientDocument
  Client 1──* ClientBankAccount
  Client 1──0..1 User (portal_user)
  Client 1──* CreditEvaluation
  Guarantee *──1 GuaranteeType
  Guarantee *──1 Beneficiary
  Guarantee 1──1 GuaranteeLetter
  Guarantee 1──* FeeSchedule
  Guarantee 1──* Payment
  Guarantee *──* Collateral (through GuaranteeCollateral)
  Guarantee *──0..1 Contract
  Guarantee *──0..1 Guarantee (parent, for renewals)
  Guarantee *──0..1 CreditEvaluation
  CreditEvaluation 1──* CreditEvaluationDetail
  CreditEvaluation *──1 CreditTier
  CreditEvaluationDetail *──1 ScorecardFactor
  DirectorOverride *──1 CreditEvaluation
  DirectorOverride *──0..1 Guarantee
  Contract 1──* ContractDocument
  Collateral 1──* CollateralDocument
  User 1──* Notification
  GuaranteeRequest *──1 Client
  GuaranteeRequest *──0..1 Guarantee
```

---

## Project Directory Structure

```
credit_fund/
├── manage.py
├── pyproject.toml                    # uv / poetry project definition
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── config/                           # Project-level settings
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
├── apps/
│   ├── __init__.py
│   ├── core/                         # Abstract base models, utilities
│   ├── accounts/
│   ├── clients/
│   ├── guarantees/
│   ├── creditframework/              # Credit scoring engine [NEW]
│   ├── collaterals/
│   ├── contracts/
│   ├── notifications/
│   ├── audit/
│   ├── analytics/
│   └── portal/                       # Client-facing portal + DRF API
├── templates/
│   ├── admin/                        # Unfold overrides
│   ├── portal/                       # Client portal templates
│   ├── documents/                    # HTML templates for PDF generation
│   ├── notifications/                # Email/SMS templates
│   └── base.html
├── static/
│   ├── css/
│   ├── js/
│   └── fonts/                        # Persian fonts (Vazirmatn)
├── media/                            # Uploaded files (gitignored)
├── document_templates/               # .docx template files
├── locale/
│   └── fa/                           # Persian translations
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .env.example
└── tests/
    ├── conftest.py
    ├── factories.py
    └── (mirrors apps/ structure)
```

---

## Guarantee Workflow (Sequential Approval + Credit Framework Check)

```
[DRAFT] --Analyst submits--> [UNDER_REVIEW]
                                  |
                         ┌────────┴────────┐
                         │  CREDIT CHECK    │
                         │  (automatic)     │
                         │                  │
                         │  Evaluate client  │
                         │  scorecard:      │
                         │  - financial data│
                         │  - collateral    │
                         │    type & value  │
                         │  - business hist │
                         └────────┬────────┘
                                  |
                    ┌─────────────┼──────────────┐
                    |             |               |
                  PASS         FAIL          FAIL + Director
                    |             |            Override (with
                    |         BLOCKED          logged reason)
                    |          (cannot           |
                    |          approve)           |
                    |             |               |
                    |      Director can           |
                    |      override ──────────────┘
                    |
           Director approves
                    |
               [APPROVED]
                    |
          Accountant verifies
           fees paid & issues
                    |
               [ISSUED]
                    |
              auto-activate
                    |
               [ACTIVE]
               /      \
      auto-expire    cancel
          |            |
     [EXPIRED]   [CANCELLED]
          |
     can renew -> new [DRAFT] linked to parent

  At any point: Director returns -> back to [DRAFT]
```

**Credit Framework Check Details:**
- Runs automatically when guarantee enters UNDER_REVIEW
- System evaluates client's weighted scorecard (financial ratios, collateral coverage, business history)
- Each factor scored and weighted → total score → mapped to Credit Tier
- If total guarantee exposure exceeds tier's max credit limit → **BLOCKED**
- If single guarantee amount exceeds tier's max_single_guarantee_pct → **BLOCKED**
- Director can override any block with a mandatory reason (logged and audited)
- Override can be time-bound (expiry_date) or permanent
- All evaluations and overrides stored for audit trail

Future: ACTIVE → [CLAIMED] (claims workflow)

---

## Phase-by-Phase Implementation Plan

**Apps (11 total):** core, accounts, clients, guarantees, creditframework, collaterals, contracts, notifications, audit, analytics, portal

---

### PHASE 1: Project Scaffolding, Core App, Accounts App

**Goal:** Bootable Django project with authentication, custom User model, role-based access, and Unfold admin working with RTL.

**What to build:**

1. **Project initialization**
   - `django-admin startproject config .` inside `credit_fund/`
   - Split settings into `config/settings/{base,dev,prod}.py`
   - `base.py`: `DATABASES` pointing to PostgreSQL (never SQLite), `AUTH_USER_MODEL = 'accounts.User'`, installed apps, middleware, `LANGUAGE_CODE = 'fa'`, `USE_L10N = True`, `USE_TZ = True`, `TIME_ZONE = 'Asia/Tehran'`
   - `dev.py`: `DEBUG=True`, `django-debug-toolbar`, console email backend
   - `prod.py`: security settings, proper email backend, `SECURE_SSL_REDIRECT`, etc.
   - Celery configuration in `config/celery.py` with autodiscover
   - Redis as `CACHES` backend and Celery broker

2. **Core app** (`apps/core/`)
   - `models.py` — abstract base models:
     ```python
     class TimeStampedModel(models.Model):
         created_at = models.DateTimeField(auto_now_add=True)
         updated_at = models.DateTimeField(auto_now=True)
         class Meta:
             abstract = True

     class UserTrackingModel(TimeStampedModel):
         created_by = models.ForeignKey(settings.AUTH_USER_MODEL, ..., related_name='+')
         updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, ..., related_name='+', null=True)
         class Meta:
             abstract = True
     ```
   - `mixins.py` — admin mixins: `UserTrackingAdminMixin` that auto-sets `created_by`/`updated_by` from `request.user` in `save_model()`
   - `validators.py` — Iranian national code validator, phone number validator, SHEBA validator, file size/type validators (max 10MB, allowed: pdf/jpg/png/docx)
   - `utils.py` — unique code generators (guarantee number, client code, contract number patterns)
   - `templatetags/` — Persian number conversion, Jalali date display

3. **Accounts app** (`apps/accounts/`)
   - **Models:**
     - `User(AbstractUser)` with fields: `role` (TextChoices: ANALYST, ACCOUNTANT, DIRECTOR, CLIENT_USER), `national_code`, `phone`, `is_portal_user`
   - **Admin:** Unfold-based `UserAdmin` with fieldset tabs, list filters by role
   - **Management command:** `create_default_groups` that creates Django Groups (Analysts, Accountants, Directors) with appropriate permissions
   - **Middleware:** `CurrentUserMiddleware` that stores `request.user` in thread-local for audit tracking

4. **Unfold RTL configuration**
   - Install `django-unfold-rtl` instead of `django-unfold`
   - Configure in `base.py` under `UNFOLD` dict: site title (Persian), navigation sidebar grouping by app, colors
   - Load Vazirmatn font for Persian typography
   - Verify RTL layout works

5. **Docker Compose** (for development)
   - `docker-compose.yml` with services: `db` (postgres:16), `redis` (redis:7), `web` (Django), `celery_worker`, `celery_beat`

**Key design decisions:**
- Custom User model from day one (cannot change later without pain)
- `django-unfold-rtl` over plain `django-unfold` to avoid CSS hacks for Persian
- PostgreSQL in dev/test/prod — no SQLite anywhere
- All apps under `apps/` directory with `apps.core` AppConfig label adjustments
- Thread-local middleware for `created_by` tracking in abstract models

**Dependencies:** None (Phase 1 is the foundation).

**Files to create:**
- `config/settings/base.py`, `config/settings/dev.py`, `config/settings/prod.py`
- `config/celery.py`, `config/urls.py`
- `apps/core/models.py`, `apps/core/validators.py`, `apps/core/mixins.py`, `apps/core/utils.py`
- `apps/accounts/models.py`, `apps/accounts/admin.py`, `apps/accounts/management/commands/create_default_groups.py`
- `docker/docker-compose.yml`, `docker/Dockerfile`

---

### PHASE 2: Client Management

**Goal:** Full client CRUD for Legal and Real person types, with documents, contacts, bank accounts, and credit limit tracking.

**What to build:**

1. **Client models** (`apps/clients/models.py`)
   - `Client(UserTrackingModel)` — core fields: `client_type` (LEGAL/REAL), `client_code` (auto-generated, e.g., `CL-1403-0001`), `credit_limit`, `used_credit`, `is_active`, `portal_user` FK
   - `LegalPersonProfile(TimeStampedModel)` — OneToOneField to Client, company-specific fields
   - `RealPersonProfile(TimeStampedModel)` — OneToOneField to Client, individual-specific fields
   - `ClientContact(TimeStampedModel)` — multi-type contacts
   - `ClientDocument(UserTrackingModel)` — file uploads with type classification, uses core validators
   - `ClientBankAccount(TimeStampedModel)` — SHEBA-validated bank info
   - Add `available_credit` as a `@property` on Client: `credit_limit - used_credit`

2. **Admin classes** (`apps/clients/admin.py`)
   - `ClientAdmin` with Unfold styling:
     - Conditional inlines: show `LegalPersonProfileInline` or `RealPersonProfileInline` based on `client_type` (use Unfold's conditional fields feature)
     - Tab-based inlines: Contacts | Bank Accounts | Documents | Guarantees (read-only reverse)
     - List display: client_code, name, type, credit_limit, available_credit, is_active
     - Filters: client_type, is_active, credit range
     - Search: client_code, name, national_code
     - Custom action: "Export to Excel"
   - `ClientDocumentAdmin` — with file preview

3. **Signals**
   - `post_save` on Client: auto-create the appropriate profile (Legal or Real) based on client_type

4. **Services** (`apps/clients/services.py`)
   - `ClientService.generate_client_code()` — generates sequential codes with Jalali year prefix
   - `ClientService.update_used_credit(client)` — recalculates from active guarantees
   - `ClientService.check_credit_availability(client, amount)` — returns bool + remaining

**Key design decisions:**
- One `Client` model with type-discriminated OneToOne profiles rather than multi-table inheritance. This avoids join overhead for common queries and keeps the guarantee FK simple (`guarantee.client` always works regardless of type).
- `used_credit` is a denormalized field updated via signals/service methods when guarantees change state. This avoids expensive aggregation on every page load. A Celery task runs nightly to reconcile.
- File uploads validated at model level (max 10MB, allowed types), stored under `media/clients/{client_code}/`.

**Dependencies:** Phase 1 (core base models, validators, User model).

---

### PHASE 3: Guarantee Processing (Types, Workflow, Fees, Payments)

**Goal:** The heart of the system. Guarantee lifecycle from creation through issuance, with fee calculation and payment tracking.

**What to build:**

1. **Guarantee type model** (`apps/guarantees/models.py`)
   - `GuaranteeType` — predefined via data migration (not fixture). Fields: `code`, `name_fa`, `default_commission_rate`, `default_deposit_ratio`, `typical_duration_months`, `requires_collateral`, `is_active`
   - Data migration seeds: BID_BOND, PERFORMANCE_BOND, ADVANCE_PAYMENT, RETENTION, CUSTOMS, GOOD_EXECUTION

2. **Beneficiary model**
   - `Beneficiary(TimeStampedModel)` — reusable entity. A client may issue guarantees to the same beneficiary multiple times.

3. **Guarantee model with FSM**
   - `Guarantee(UserTrackingModel)` with `state = FSMField(default='draft')`
   - State transitions (using `django-fsm-2` decorators):
     ```
     @transition(field=state, source='draft', target='under_review',
                 permission='guarantees.can_submit_guarantee')
     def submit_for_review(self, by_user):
         self.reviewed_by = None  # reset

     @transition(field=state, source='under_review', target='approved',
                 permission='guarantees.can_approve_guarantee',
                 conditions=[lambda g: g.framework_status != 'blocked'])
     def approve(self, by_user):
         self.approved_by = by_user

     @transition(field=state, source='under_review', target='draft',
                 permission='guarantees.can_approve_guarantee')
     def return_for_revision(self, by_user, reason):
         self.rejection_reason = reason

     @transition(field=state, source='approved', target='issued',
                 permission='guarantees.can_issue_guarantee',
                 conditions=[lambda g: g.fees_paid])
     def issue(self, by_user):
         # Triggers: create FeeSchedule, update client.used_credit
         pass

     @transition(field=state, source='issued', target='active')
     def activate(self):
         pass  # Auto after effective_date

     @transition(field=state, source=['active', 'issued'], target='expired')
     def expire(self):
         pass  # Called by Celery beat

     @transition(field=state, source=['active', 'issued'], target='cancelled',
                 permission='guarantees.can_cancel_guarantee')
     def cancel(self, by_user, reason):
         self.rejection_reason = reason

     # FUTURE: claimed state
     # @transition(field=state, source='active', target='claimed')
     # def claim(self, by_user): ...
     ```
   - Workflow mapping to roles:
     - **Analyst**: creates (draft), submits for review (draft → under_review)
     - **Director**: approves (under_review → approved) or returns for revision
     - **Accountant**: issues (approved → issued) after verifying deposits/fees paid

4. **FeeSchedule model**
   - Created automatically when guarantee is issued. Service method calculates:
     - Commission = `amount * commission_rate * (duration_months / 12)`
     - Deposit = `amount * deposit_ratio`
     - Optional: stamp duty, service fee

5. **Payment model**
   - Tracks all financial movements. Verified by Accountant role.
   - A guarantee cannot transition to `issued` unless required fees are paid (checked in transition condition via `conditions=[lambda g: g.fees_paid]`).

6. **Admin classes**
   - `GuaranteeAdmin`:
     - FSM transition buttons as Unfold actions (custom template override for state-change buttons in change_form)
     - Color-coded state display in list view
     - Framework status badge (green PASS / red BLOCKED / yellow OVERRIDDEN)
     - Tabbed inlines: Fees | Payments | Collaterals | State History | Letter | Credit Evaluation
     - Filters: state, guarantee_type, client, framework_status, date ranges
     - Auto-populate `commission_rate` and `deposit_ratio` from GuaranteeType defaults (via JS in admin or `get_changeform_initial_data`)
   - `BeneficiaryAdmin` with autocomplete for use in Guarantee form
   - `PaymentAdmin` with verification action

7. **Services** (`apps/guarantees/services.py`)
   - `GuaranteeService.calculate_fees(guarantee)` — returns dict of fee amounts
   - `GuaranteeService.create_fee_schedule(guarantee)` — creates FeeSchedule records
   - `GuaranteeService.check_issuance_readiness(guarantee)` — validates all prerequisites
   - `GuaranteeService.renew_guarantee(guarantee)` — creates child guarantee linked to parent, copies relevant data, increments renewal_count
   - `GuaranteeService.process_expiry(guarantee)` — called by Celery for auto-expiry

8. **Celery tasks** (`apps/guarantees/tasks.py`)
   - `check_expiring_guarantees` — runs daily, finds guarantees expiring in 30/15/7/1 days, creates notifications
   - `process_expired_guarantees` — runs daily, transitions past-expiry guarantees to expired state
   - `reconcile_client_credits` — runs nightly, recalculates all client used_credit values

**Key design decisions:**
- `django-fsm-2` over custom state machine: it provides field-level state, transition decorators with permission checks, and conditions. Pair with `django-fsm-log` for automatic transition audit trail.
- Fee calculation lives in a service layer, not in the model's save method. This keeps models clean and makes testing straightforward.
- Payments are a separate model from FeeSchedule. A FeeSchedule record says "this fee is owed"; a Payment record says "this money was received". They link via FK. This separation supports partial payments and overpayments.
- The `claimed` state is defined in the FSM choices but the transition method is commented out. The model already has the state in its choices enum, so adding the transition later requires no migration.
- The `approve()` transition has a condition: `framework_status != 'blocked'`. This makes the Credit Framework an integral gate in the workflow.

**Dependencies:** Phase 1 (User, base models), Phase 2 (Client model for FK).

---

### PHASE 3B: Credit Framework (Scoring Engine + Director Override)

**Goal:** Dynamic weighted scorecard system that evaluates client creditworthiness, gates the guarantee workflow, and allows Director overrides.

**What to build:**

1. **Models** (`apps/creditframework/models.py`)
   - `ScorecardCategory` — groups of factors (e.g., "Financial Ratios", "Collateral Quality", "Business History"). Ordered, admin-editable.
   - `ScorecardFactor` — individual scoring criteria within a category. Fields: `code`, `name_fa`, `weight` (Decimal, all weights across factors should sum to 100), `value_type` (NUMERIC/PERCENTAGE/ENUM/BOOLEAN), `min_value`, `max_value`, scoring brackets. Director can add/modify/delete factors through admin.
   - `ScorecardFactorOption` — for ENUM-type factors (e.g., collateral type: Real Estate=100pts, Bank Deposit=90pts, Check=60pts, Promissory Note=40pts).
   - `CreditTier` — score-to-limit mapping. Fields: `name_fa`, `min_score`, `max_score`, `max_credit_limit`, `max_single_guarantee_pct` (e.g., no single guarantee > 40% of total limit). Director configures tiers.
   - `CreditEvaluation` — a snapshot of a client's evaluation at a point in time. Fields: `client`, `guarantee` (nullable — can evaluate client generally or for a specific guarantee), `total_score`, `assigned_tier`, `recommended_credit_limit`, `status` (PASS/FAIL/OVERRIDDEN), `is_active`.
   - `CreditEvaluationDetail` — per-factor scores for an evaluation. Fields: `factor`, `raw_value`, `normalized_score` (0-100), `weighted_score` (normalized * weight/100).
   - `DirectorOverride` — when Director overrules a FAIL. Fields: `evaluation`, `guarantee`, `overridden_by`, `override_reason` (required text), `original_tier`, `granted_credit_limit`, `override_date`, `expiry_date` (optional, for time-bound overrides).

2. **Services** (`apps/creditframework/services.py`)
   - `CreditEvaluationService.evaluate_client(client, guarantee=None)` — runs all active scorecard factors, calculates weighted scores, determines tier, returns CreditEvaluation
   - `CreditEvaluationService.check_guarantee_eligibility(guarantee)` — evaluates whether this guarantee fits within client's tier limits. Returns `{eligible: bool, evaluation: CreditEvaluation, violations: list[str]}`
   - `CreditEvaluationService.apply_director_override(evaluation, guarantee, director_user, reason, granted_limit=None, expiry_date=None)` — creates DirectorOverride, updates evaluation status to OVERRIDDEN
   - `CreditEvaluationService.get_effective_credit_limit(client)` — returns the active limit considering latest evaluation + any active overrides

3. **Workflow integration (modify Phase 3's FSM)**
   - In `Guarantee.submit_for_review()` transition: auto-trigger `check_guarantee_eligibility()`
   - If FAIL: guarantee gets `framework_status = BLOCKED`. The `approve()` transition's condition checks `framework_status != BLOCKED` — Director cannot approve a blocked guarantee through the normal flow.
   - Director override flow: Director clicks "Override Framework" action in admin → fills reason form → `apply_director_override()` called → `framework_status` set to `OVERRIDDEN` → `approve()` transition now allowed.
   - Fields added to Guarantee model: `framework_status` (PENDING/PASS/BLOCKED/OVERRIDDEN), `credit_evaluation` FK→CreditEvaluation (nullable)

4. **Admin classes**
   - `ScorecardCategoryAdmin` — drag-to-reorder (Unfold sortable)
   - `ScorecardFactorAdmin` — inline factor options for ENUM type, weight validation (warning if total != 100)
   - `CreditTierAdmin` — tier configuration with visual score range display
   - `CreditEvaluationAdmin` — read-only evaluation history with detail inlines, filter by client/status/date
   - `DirectorOverrideAdmin` — read-only audit log of all overrides
   - On `GuaranteeAdmin`: show framework status badge (green PASS / red BLOCKED / yellow OVERRIDDEN), evaluation summary panel, "Override Framework" action button (visible only to Directors, only when BLOCKED)

5. **Evaluation display**
   - When Analyst opens a guarantee in UNDER_REVIEW, they see a scorecard summary panel showing: each factor's raw value, score, weight, and the total. If BLOCKED, the specific violations are listed (e.g., "Total exposure 15B exceeds Tier B max of 10B", "Collateral coverage 80% below required 100%").
   - Director sees the same + the override button.

6. **Celery tasks**
   - `check_expired_overrides` — runs daily, finds DirectorOverrides past their expiry_date, re-evaluates affected clients

**Key design decisions:**
- Evaluation is a **snapshot** — it captures the scores at evaluation time. If factors/weights change later, old evaluations remain valid historical records. New evaluations use current rules.
- Weights are Decimals summing to 100 (enforced by admin validation, soft warning not hard block to allow in-progress editing).
- DirectorOverride has an optional `expiry_date` for time-bound overrides. A Celery task checks daily for expired overrides and re-evaluates affected clients.
- The framework is fully dynamic — Directors can add new factors, adjust weights, and modify tiers without code changes. This is a rule engine, not hardcoded logic.
- `framework_status` on Guarantee is the gate. The FSM `approve()` condition checks this field, making the framework an integral part of the workflow, not a bypass-able warning.

**Dependencies:** Phase 2 (Client), Phase 3 (Guarantee model — adds fields to it).

---

### PHASE 4: Collateral Management

**Goal:** Track collaterals owned by clients, pledge them against guarantees, manage lifecycle.

**What to build:**

1. **Models** (`apps/collaterals/models.py`)
   - `Collateral(UserTrackingModel)` — type, values, status (AVAILABLE/PLEDGED/RELEASED/SEIZED)
   - `GuaranteeCollateral` — M2M through table with pledged_amount and dates
   - `CollateralDocument(UserTrackingModel)` — supporting documents

2. **Admin classes**
   - `CollateralAdmin` with status indicators, value display, linked guarantees inline
   - Custom validation: total pledged amount across all guarantees cannot exceed appraised_value

3. **Services**
   - `CollateralService.pledge(collateral, guarantee, amount)` — validates availability, creates through record, updates status
   - `CollateralService.release(guarantee_collateral)` — called when guarantee expires/cancels
   - `CollateralService.get_available_value(collateral)` — appraised minus total pledged

4. **Signals**
   - When guarantee transitions to expired/cancelled, auto-release linked collaterals via `post_transition` signal from django-fsm

**Key design decisions:**
- Collateral belongs to Client, not Guarantee. One collateral can back multiple guarantees (with partial amounts). This models real-world usage where a property might secure several guarantees.
- The through table (`GuaranteeCollateral`) with `pledged_amount` enables partial pledging.

**Dependencies:** Phase 2 (Client), Phase 3 (Guarantee model for M2M).

---

### PHASE 5: Contracts & Document Generation

**Goal:** Contract management and automated document generation in both PDF and DOCX formats with Persian/RTL support.

**What to build:**

1. **Contract models** (`apps/contracts/models.py`)
   - `Contract(UserTrackingModel)` — links to client, has status FSM (simpler: DRAFT → ACTIVE → COMPLETED)
   - `ContractDocument(TimeStampedModel)` — versioned document attachments
   - `DocumentTemplate(TimeStampedModel)` — stores both HTML templates and .docx template files with variable schemas

2. **Document generation engine** (`apps/contracts/document_generator.py`)
   - `PDFGenerator` class:
     - Loads HTML template from `DocumentTemplate` or filesystem
     - Renders with Django template engine (context from guarantee/client/contract)
     - Converts to PDF via WeasyPrint
     - CSS includes: `direction: rtl`, Vazirmatn font-face, proper page size (A4)
   - `DOCXGenerator` class:
     - Loads `.docx` template from `DocumentTemplate.file`
     - Renders via `python-docx-template` with Jinja2 context
     - RTL handled by the template file itself (created RTL in Word)
   - `DocumentService` facade:
     - `generate_guarantee_letter(guarantee, format='pdf')` — creates GuaranteeLetter record
     - `generate_contract(contract, format='pdf')`
     - `generate_fee_statement(client, date_range, format='pdf')`

3. **Admin integration**
   - "Generate Letter" action button on GuaranteeAdmin (only visible when state=issued)
   - "Generate Contract" action on ContractAdmin
   - Inline preview of generated documents
   - `DocumentTemplateAdmin` — with variable schema documentation

4. **Celery tasks**
   - `generate_document_async(template_id, context, format)` — for heavy generation workloads

5. **Guarantee Letter flow**
   - When guarantee transitions to `issued`, auto-generate GuaranteeLetter (via post_transition signal or in the `issue()` method)
   - Store both PDF and DOCX versions
   - Letter number auto-generated with pattern

**Key design decisions:**
- Two-engine approach (WeasyPrint for PDF, docxtpl for DOCX) because each format has distinct advantages. PDF for official distribution, DOCX for cases where the recipient needs to edit.
- Templates stored in DB (`DocumentTemplate`) rather than filesystem so admin users can manage them. HTML templates as text fields, DOCX templates as file uploads.
- WeasyPrint RTL: use CSS `direction: rtl; unicode-bidi: embed;` on body, with `@font-face` for Vazirmatn. Test with mixed Persian/English content (numbers, dates).
- DOCX RTL: the base template `.docx` file must be created with RTL paragraph direction in Word. `python-docx-template` preserves the formatting; it only fills in the Jinja2 variables.

**Note:** Phases 4 and 5 can be developed in parallel once Phase 3B is complete.

**Dependencies:** Phase 2 (Client), Phase 3 (Guarantee, FeeSchedule for context data).

---

### PHASE 6: Client Portal (Separate Django App + DRF API)

**Goal:** Self-service web portal where clients can submit guarantee requests, track status, view active guarantees, download documents, and see fee statements.

**What to build:**

1. **DRF API** (`apps/portal/api/`)
   - **Serializers:**
     - `GuaranteeRequestSerializer` (create/list)
     - `GuaranteeListSerializer` (read-only, client's guarantees)
     - `GuaranteeDetailSerializer` (read-only, full detail)
     - `FeeStatementSerializer`
     - `PaymentListSerializer`
     - `ClientProfileSerializer` (read/update own profile)
     - `DocumentDownloadSerializer`
   - **ViewSets:**
     - `GuaranteeRequestViewSet` — create new requests, list own requests, upload supporting docs
     - `GuaranteeViewSet` (read-only) — list/retrieve own guarantees with state, fees, collaterals
     - `PaymentViewSet` (read-only) — own payment history
     - `DocumentViewSet` — download own guarantee letters, contracts
     - `NotificationViewSet` — list/mark-read own notifications
     - `DashboardView` — aggregated stats for the client (active guarantees count, total exposure, pending fees)
   - **Permissions:**
     - `IsPortalUser` — checks `user.is_portal_user` and `user.role == CLIENT_USER`
     - `IsOwnerOfClient` — ensures user can only access their linked client's data
   - **Authentication:**
     - Session auth for portal web UI
     - Token auth (DRF TokenAuthentication or SimpleJWT) for future mobile/integration

2. **GuaranteeRequest model** (`apps/portal/models.py`)
   - Submitted by portal user, reviewed by Analyst in admin
   - When approved, Analyst converts to a real Guarantee (service method: `convert_request_to_guarantee`)
   - Status tracked separately from Guarantee status

3. **Portal web frontend** (`apps/portal/views.py` + `templates/portal/`)
   - Server-side rendered with Django templates (not SPA — keeps complexity low)
   - Pages:
     - Login / password reset
     - Dashboard (summary cards)
     - My Guarantees (list + detail + timeline)
     - New Request (multi-step form)
     - My Payments / Fee Statements
     - Documents (download center)
     - Notifications
     - Profile
   - RTL layout using a simple CSS framework (Tailwind with RTL plugin, or Bootstrap 5 RTL)
   - Separate `portal/base.html` template — no dependency on Unfold admin templates

4. **URL routing**
   - Admin: `/admin/` (Unfold)
   - Portal: `/portal/` (separate URL namespace)
   - API: `/api/v1/` (DRF router)

5. **Admin-side for GuaranteeRequest**
   - `GuaranteeRequestAdmin` in admin panel for Analysts to review incoming requests
   - Action: "Convert to Guarantee" — opens pre-filled guarantee creation form

**Key design decisions:**
- Server-side rendered portal (not React/Vue SPA) for initial release. The DRF API exists alongside it for future mobile app or SPA migration. This drastically reduces frontend complexity.
- `GuaranteeRequest` is a separate model from `Guarantee`. A request is a "wish" from the client; a Guarantee is an official record managed by staff. The conversion is explicit, not automatic. This prevents clients from polluting the guarantee table with incomplete data.
- Portal users have a separate role (`CLIENT_USER`) and are linked to a Client record. All portal queries are scoped via `get_queryset()` filtering: `Guarantee.objects.filter(client__portal_user=request.user)`.
- API versioning via URL prefix (`/api/v1/`) from day one.

**Dependencies:** Phase 1 (User with CLIENT_USER role), Phase 2 (Client with portal_user FK), Phase 3 (Guarantee for read views), Phase 5 (Documents for download).

---

### PHASE 7: Analytics Dashboard, Notifications, Reporting

**Goal:** Operational dashboard for staff, automated notifications, and reporting capabilities.

**What to build:**

1. **Notifications app** (`apps/notifications/`)
   - **Models:** `NotificationTemplate`, `Notification` (as in ER diagram above)
   - **Service:** `NotificationService`
     - `send_notification(user, template_code, context, channel='IN_APP')`
     - `send_bulk_notification(users, template_code, context)`
     - `mark_as_read(notification_id, user)`
   - **Celery tasks:**
     - `send_email_notification` — async email dispatch
     - `send_sms_notification` — async SMS (pluggable backend, start with logging, integrate Kavenegar/Melipayamak later)
     - `check_and_send_expiry_notifications` — scheduled daily
     - `send_approval_notification` — triggered on state transitions
   - **Signal handlers:** connect to `django-fsm-2`'s `post_transition` signal:
     - Guarantee submitted → notify Director
     - Guarantee approved → notify Accountant
     - Guarantee issued → notify Client (portal user)
     - Guarantee expiring → notify Analyst + Client
     - Framework BLOCKED → notify Director (needs override decision)
   - **Admin:** `NotificationAdmin` (read-only log), `NotificationTemplateAdmin` (editable)
   - **Unfold integration:** notification bell icon in admin header (custom template override)

2. **Analytics dashboard** (`apps/analytics/`)
   - **Unfold dashboard page** (custom admin view at `/admin/`):
     - KPI cards: Total active guarantees, Total exposure (sum of amounts), Expiring this month, Pending approvals, Blocked by framework
     - Charts (using Unfold's chart components or Chart.js):
       - Guarantees by type (pie/donut)
       - Monthly issuance trend (bar)
       - Credit utilization by top 10 clients (horizontal bar)
       - State distribution (funnel or stacked bar)
       - Framework pass/fail/override ratio
     - Recent activity feed (last 20 state transitions)
     - Expiry calendar (next 30 days)
   - **Dashboard data services** (`apps/analytics/services.py`):
     - All queries use Django ORM aggregations: `annotate`, `aggregate`, `Count`, `Sum`, `F`, `Q`
     - Optional: cache expensive queries in `DashboardSnapshot` for performance
   - **Report generation:**
     - "Guarantee Register" — full list export with filters (Excel via `openpyxl`)
     - "Client Exposure Report" — per-client summary
     - "Expiry Report" — upcoming expirations
     - "Fee Collection Report" — outstanding vs collected
     - "Credit Framework Report" — evaluation history, override frequency, tier distribution
     - Export formats: Excel (.xlsx) and PDF

3. **Audit app finalization** (`apps/audit/`)
   - Integrate `django-auditlog` for automatic model change tracking
   - Register all critical models: Guarantee, Client, Collateral, Contract, Payment, CreditEvaluation, DirectorOverride
   - Admin view for audit log browsing with filters

**Key design decisions:**
- Notifications use Django's `ContentType` framework (GenericForeignKey) so any model can be the "related object" of a notification. This is flexible without creating FKs to every model.
- SMS integration uses an abstract backend pattern: `BaseSMSBackend` with `send(phone, message)`. Ship with `LoggingSMSBackend` for dev; implement `KavenegarBackend` when ready. Configured via `settings.SMS_BACKEND`.
- Dashboard queries should not hit the DB on every page load for all users. Use Django's cache framework with 5-minute TTL for aggregate stats. The `DashboardSnapshot` model is a fallback for very expensive reports.
- Use Unfold's built-in dashboard customization (the `UNFOLD["DASHBOARD_CALLBACK"]` setting) rather than building a separate dashboard app.

**Dependencies:** Phase 1-6 (needs data from all models to report on).

---

### PHASE 8: Testing, Optimization & Deployment

**Goal:** Comprehensive test coverage, performance tuning, and production-ready deployment.

**What to build:**

1. **Testing**
   - **Factory setup** (`tests/factories.py`):
     - `UserFactory`, `ClientFactory`, `LegalPersonProfileFactory`, `RealPersonProfileFactory`
     - `GuaranteeTypeFactory`, `BeneficiaryFactory`, `GuaranteeFactory`
     - `CollateralFactory`, `ContractFactory`, `PaymentFactory`
     - `ScorecardFactorFactory`, `CreditTierFactory`, `CreditEvaluationFactory`
     - Use `factory-boy` with `faker` (Persian locale: `fa_IR`)
   - **Unit tests per app:**
     - `apps/core/` — validator tests, utility function tests
     - `apps/accounts/` — user creation, role assignment, permission checks
     - `apps/clients/` — client CRUD, credit calculation, profile creation signals
     - `apps/guarantees/` — FSM transitions (valid and invalid), fee calculation, payment verification, renewal logic
     - `apps/creditframework/` — scorecard evaluation, tier assignment, director override, expired override handling, framework blocking guarantee approval
     - `apps/collaterals/` — pledging, releasing, over-pledge prevention
     - `apps/contracts/` — document generation (mock WeasyPrint/docxtpl in unit tests)
     - `apps/portal/` — API endpoint tests, permission scoping (client A cannot see client B's data)
     - `apps/notifications/` — notification creation, template rendering
   - **Integration tests:**
     - Full guarantee lifecycle: create client → evaluate credit → create guarantee → submit → framework check → approve → issue → verify fees → expire
     - Framework block flow: create guarantee exceeding tier → submit → BLOCKED → Director override → approve
     - Portal request flow: client submits request → analyst reviews → converts to guarantee
   - **Test database:** PostgreSQL (same as prod). Configure in `config/settings/test.py` (inherits from `dev.py`, overrides DB name)
   - **pytest configuration** in `pyproject.toml`:
     ```
     [tool.pytest.ini_options]
     DJANGO_SETTINGS_MODULE = "config.settings.dev"
     python_files = ["tests.py", "test_*.py"]
     ```

2. **Performance optimization**
   - Add `select_related` and `prefetch_related` to all admin querysets and API viewsets
   - Database indexes: composite index on `(client_id, state)` for Guarantee, index on `expiry_date`, index on `state`, index on `framework_status`
   - `django-cachalot` or manual queryset caching for dashboard
   - Connection pooling via `django-db-connection-pool` or `pgbouncer`

3. **Security hardening**
   - `django-axes` for brute-force login protection
   - Rate limiting on API endpoints (`django-ratelimit` or DRF throttling)
   - CSP headers via `django-csp`
   - File upload scanning (ClamAV integration or at minimum strict type validation)
   - All financial amount fields: `DecimalField(max_digits=20, decimal_places=0)` for Rials (no sub-unit)

4. **Deployment configuration**
   - `Dockerfile` (multi-stage: build static assets, then slim Python runtime)
   - `docker-compose.prod.yml`: Django (gunicorn), Celery worker, Celery beat, PostgreSQL, Redis, Nginx
   - Nginx config: serve static/media, proxy to gunicorn, handle SSL termination
   - Backup strategy: `pg_dump` cron job to offsite storage (daily full, hourly WAL archiving)
   - Environment variables via `.env` (never committed): `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `EMAIL_*`, `SMS_*`

5. **Monitoring**
   - `django-health-check` for readiness/liveness probes
   - Sentry for error tracking
   - Structured logging via `django-structlog`

**Key design decisions:**
- All tests use PostgreSQL — never SQLite. This catches type coercion bugs, ensures `JSONField` works identically, and validates any raw SQL or PostgreSQL-specific features.
- Financial amounts use `DecimalField(max_digits=20, decimal_places=0)` because Iranian Rial has no sub-units. This avoids floating-point errors entirely. The max_digits=20 supports amounts up to 99,999,999,999,999,999,999 Rials (more than enough).
- Deployment targets Docker from the start. Even if the initial deploy is on a single VM, containerization makes it reproducible and eases future scaling.

**Dependencies:** All previous phases.

---

## Cross-Cutting Concerns Summary

| Concern | Approach |
|---|---|
| **RTL/Persian** | `django-unfold-rtl` for admin, CSS `direction: rtl` for portal, Vazirmatn font, `django.utils.translation` with `fa` locale, Jalali date display via `jdatetime` |
| **Audit Trail** | `django-auditlog` for model changes + `django-fsm-log` for state transitions + custom `UserTrackingModel` for created_by/updated_by |
| **Permissions** | Django's built-in permission system + Groups (Analysts/Accountants/Directors) + `django-fsm-2` transition permissions + DRF permissions for portal |
| **File Handling** | Core validators (10MB max, pdf/jpg/png/docx), organized media storage (`media/{app}/{entity_code}/`), serve via Nginx in prod |
| **Financial Precision** | `DecimalField(max_digits=20, decimal_places=0)` for Rials, `Decimal` type in all Python calculations, never `float` |
| **Async Processing** | Celery for: document generation, notifications, scheduled expiry checks, credit reconciliation, expired override checks |
| **Credit Framework** | Dynamic weighted scorecard, configurable by Director, gates guarantee approval, Director override with audit trail |
| **Future Claims** | `CLAIMED` state exists in FSM choices, transition method is stubbed but commented out, `Claim` model placeholder noted in code comments |

---

## Dependency Graph Between Phases

```
Phase 1 (Foundation)
  └── Phase 2 (Clients)
        └── Phase 3 (Guarantees) ←── core business logic
              └── Phase 3B (Credit Framework) ←── gates the workflow
                    ├── Phase 4 (Collaterals)  ── can parallelize
                    └── Phase 5 (Contracts & Documents)
                          └── Phase 6 (Client Portal)
                                └── Phase 7 (Analytics & Notifications)
                                      └── Phase 8 (Testing & Deployment)
```

Phase 3B modifies the Guarantee model (adds `framework_status` and `credit_evaluation` FK), so it must complete before Phases 4/5 to avoid migration conflicts. Phases 4 and 5 can be developed in parallel. Phase 8 testing should begin alongside Phase 3 (write tests as you build each phase) but the full test suite and deployment hardening happen last.

---

## Estimated Effort

| Phase | Effort | Cumulative |
|---|---|---|
| Phase 1: Foundation | 1 week | 1 week |
| Phase 2: Clients | 1 week | 2 weeks |
| Phase 3: Guarantees | 2 weeks | 4 weeks |
| Phase 3B: Credit Framework | 1.5 weeks | 5.5 weeks |
| Phase 4: Collaterals | 0.5 weeks | 6 weeks |
| Phase 5: Contracts/Docs | 1.5 weeks | 7.5 weeks |
| Phase 6: Client Portal | 2 weeks | 9.5 weeks |
| Phase 7: Analytics/Notifications | 1.5 weeks | 11 weeks |
| Phase 8: Testing/Deploy | 1.5 weeks | 12.5 weeks |

These assume a single experienced Django developer working full-time. Reduce by 30-40% with two developers (Phases 4/5 can parallelize, and portal/analytics can parallelize).

---

## Critical Files for Implementation

These are the files whose design decisions cascade most broadly and should be implemented with the most care:

- `config/settings/base.py` — all project-wide configuration including AUTH_USER_MODEL, UNFOLD config, Celery, database, and installed apps. Mistakes here are expensive to fix later.
- `apps/core/models.py` — the `TimeStampedModel` and `UserTrackingModel` abstract base classes that every other model inherits from. Their field definitions propagate to every table.
- `apps/accounts/models.py` — the custom `User` model. Must be defined before first migration and cannot be swapped later.
- `apps/guarantees/models.py` — the `Guarantee` model with FSM field, the `GuaranteeType` seed data, `Beneficiary`, `FeeSchedule`, and `Payment` models. This is the system's core domain.
- `apps/guarantees/services.py` — fee calculation logic, issuance readiness checks, renewal workflow, and credit limit updates. Business rules live here, not in models or views.
- `apps/creditframework/models.py` — the scorecard, tier, evaluation, and override models. The dynamic rule engine structure.
- `apps/creditframework/services.py` — evaluation logic, eligibility checks, override application. The credit framework's brain.

---

## Verification Plan

After each phase, verify by:
1. `python manage.py makemigrations --check` (no missing migrations)
2. `python manage.py check --deploy` (Django system checks)
3. `pytest` (all tests pass against PostgreSQL)
4. Manual verification in admin panel (create/edit/delete entities, test RTL layout)
5. For Phase 3: walk through complete guarantee lifecycle in admin
6. For Phase 3B: configure scorecard factors and tiers → create guarantee → verify framework blocks/passes correctly → test Director override
7. For Phase 6: test portal as client user (submit request, track, download)
8. For Phase 7: verify notifications fire on state transitions, dashboard shows correct aggregates
