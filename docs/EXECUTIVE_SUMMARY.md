# Comprehensive Executive Summary & System Rebuild Blueprint

> **System Name:** Brand Intel Platform (`brand-intel-vercel` / `ideaform-brands`)  
> **Domain:** Commercial Retail Leasing, Brand BD Sourcing & Site Selection (India Market)  
> **Purpose:** Detailed architectural specification, module breakdown, connector inventory, and component swap roadmap for system rebuild.

---

## Table of Contents
1. [System Mission & Executive Overview](#1-system-mission--executive-overview)
2. [High-Level Technical Architecture](#2-high-level-technical-architecture)
3. [Provider, Connector & Integration Inventory](#3-provider-connector--integration-inventory)
4. [Deep-Dive Module Specifications](#4-deep-dive-module-specifications)
   - [Module 1: Executive & Expansion Research](#module-1-executive--expansion-research)
   - [Module 2: Expansion News Monitor & Cron Alerts](#module-2-expansion-news-monitor--cron-alerts)
   - [Module 3: Requirement Mandate Inbox & Open-Web Sourcing](#module-3-requirement-mandate-inbox--open-web-sourcing)
   - [Module 4: Property-to-Brand Requirement Matcher](#module-4-property-to-brand-requirement-matcher)
   - [Module 5: Catchment & Micro-Market Analysis](#module-5-catchment--micro-market-analysis)
   - [Module 6: Multi-Channel Outreach Copy Composer](#module-6-multi-channel-outreach-copy-composer)
   - [Module 7: CRM & Contact Database Store](#module-7-crm--contact-database-store)
   - [Module 8: Local Deal Logger](#module-8-local-deal-logger)
5. [Database Architecture & Schema Specs](#5-database-architecture--schema-specs)
6. [Component Swap & Rebuild Blueprint](#6-component-swap--rebuild-blueprint)
7. [Step-by-Step System Reconstruction Guide](#7-step-by-step-system-reconstruction-guide)

---

## 1. System Mission & Executive Overview

Commercial retail leasing brokers, property developers, and brand business development (BD) leads in India operate in an opaque, highly fragmented market. Information regarding who makes leasing decisions within brands, which brands are expanding into specific cities, what space requirements brands have, and what micro-market demographics look like is spread across news portals, social media posts, and private networks.

The **Brand Intel Platform** serves as an operational hub that unifies:
- **People Discovery**: Automated extraction of C-suite executives, India master operators/franchisees, and BD/real estate expansion directors for any target brand.
- **Market Signal Tracking**: Automated scanning and classification of retail expansion news announcements to catch leasing leads early.
- **Demand Capture**: Parsing unstructured mandate posts (from WhatsApp groups, LinkedIn, or web searches) into structured, queryable database records.
- **Site Selection & Matching**: Scoring specific retail properties against brand requirements and providing custom pitch angles.
- **Micro-Market Catchment Analysis**: Quantitative POI (Points of Interest) extraction and AI-driven trade area profiling around any address using OpenStreetMap data.
- **Outreach Automation**: Generating high-converting WhatsApp pitches, emails, and 6-section formal leasing proposals.

---

## 2. High-Level Technical Architecture

The existing repository is built as a serverless Next.js 16 (App Router) web application deployed on Vercel, utilizing external free-tier SaaS APIs for search, AI, database, geocoding, and email notification.

### Data Flow Diagram

```mermaid
flowchart TD
    User([User / Browser]) <--> UI["Next.js App Router UI"]

    subgraph ServerlessAPI["Serverless API Routes (/app/api)"]
        ResearchRoute["/api/research"]
        MonitorRoute["/api/monitor"]
        CronRoute["/api/cron"]
        RequirementsRoute["/api/requirements/*"]
        MatchRoute["/api/match"]
        CatchmentRoute["/api/catchment"]
        ComposeRoute["/api/compose"]
        ContactsRoute["/api/contacts"]
    end

    UI <--> ServerlessAPI

    subgraph External["External Connectors & Providers"]
        Tavily["Tavily Search API<br/>api.tavily.com"]
        Groq["Groq LLM API<br/>llama-3.3-70b-versatile"]
        GoogleNews["Google News RSS<br/>news.google.com"]
        Nominatim["OSM Nominatim / Komoot Photon<br/>Geocoding"]
        Overpass["Overpass API<br/>OSM POI Retrieval"]
        Supabase[("Supabase PostgreSQL<br/>Contacts & Mandates")]
        Resend["Resend Email API<br/>Daily Digest Alert"]
    end

    ResearchRoute -->|Search Queries| Tavily
    ResearchRoute -->|Extract JSON| Groq
    ResearchRoute -->|Upsert Contacts| Supabase

    MonitorRoute -->|Fetch News XML| GoogleNews
    MonitorRoute -->|Classify HOT/WARM| Groq

    CronRoute -->|Daily Scan| MonitorRoute
    CronRoute -->|Send Alert Email| Resend

    RequirementsRoute -->|Open-Web Search| Tavily
    RequirementsRoute -->|Parse Raw Text| Groq
    RequirementsRoute -->|CRUD Operations| Supabase

    MatchRoute -->|Score Fit & Objections| Groq

    CatchmentRoute -->|Address to Lat/Lon| Nominatim
    CatchmentRoute -->|Lat/Lon to POIs| Overpass
    CatchmentRoute -->|Analyze Mix & Gaps| Groq

    ComposeRoute -->|Generate Copy & Proposal| Groq

    ContactsRoute <-->|RPC merge_contacts| Supabase

---

## 3. Provider, Connector & Integration Inventory

The current system relies on seven external services/connectors. Rebuilding the platform requires understanding each connector's API details, credentials, and data payloads:

### Connector 1: Tavily Search API
- **Endpoint**: `https://api.tavily.com/search`
- **Method**: `POST` (`Content-Type: application/json`)
- **Authentication**: `api_key` payload parameter (`TAVILY_API_KEY`)
- **Usage**:
  - `app/api/research/route.ts`: Runs 6 parallel queries per brand lookup (`max_results: 6`).
  - `app/api/requirements/search/route.ts`: Runs 5 open-web search queries for mandate discovery (`search_depth: "advanced"`, `include_raw_content: true`).
- **Data Extracted**: Page URL, Title, Snippet Content, and Raw Webpage Content.

### Connector 2: Groq LLM API
- **Endpoint**: `https://api.groq.com/openai/v1/chat/completions`
- **Method**: `POST` (`Authorization: Bearer GROQ_API_KEY`)
- **Model**: `llama-3.3-70b-versatile`
- **Settings**: `temperature: 0.1`–`0.4`, `response_format: { type: "json_object" }`
- **Usage**: Used in all AI tasks for structured JSON extraction, Jaccard Jaccard-augmented news classification, property match scoring, trade area analysis, and copy generation.

### Connector 3: Supabase (PostgreSQL Database)
- **Endpoint**: `NEXT_PUBLIC_SUPABASE_URL`
- **Authentication**: `SUPABASE_SERVICE_ROLE_KEY` (Server-side admin access)
- **SDK**: `@supabase/supabase-js` v2.111.0
- **Tables**: `contacts`, `companies`, `requirements`, `sourced_contacts`
- **Stored Procedures (RPCs)**: `merge_contacts(payload)`, `merge_company(payload)`

### Connector 4: Nominatim & Komoot Photon Geocoders
- **Endpoints**:
  - Nominatim: `https://nominatim.openstreetmap.org/search`
  - Photon: `https://photon.komoot.io/api/`
- **Method**: `GET` (Requires custom `User-Agent` header)
- **Usage**: Geocodes address strings (e.g. "100 Feet Road, Indiranagar, Bengaluru") into exact coordinates (`lat`, `lon`). Includes fallback array strategy with India region priority (`countrycodes=in`).

### Connector 5: OpenStreetMap Overpass API
- **Endpoints**: `https://overpass-api.de/api/interpreter`, `https://lz4.overpass-api.de/api/interpreter`
- **Method**: `POST` (`Content-Type: application/x-www-form-urlencoded`)
- **Usage**: Queries nodes/ways/relations (`nwr`) within radius $R$ (300m–1500m) for tags `[shop]` and `[amenity~"cafe|restaurant|fast_food|bar|cinema|bank|food_court"]`. Returns up to 400 commercial POIs.

### Connector 6: Google News RSS
- **Endpoint**: `https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en`
- **Method**: `GET`
- **Usage**: Fetches news articles matching brand expansion terms over a specified day window. No API key required.

### Connector 7: Resend Email API
- **Endpoint**: `https://api.resend.com/emails`
- **Method**: `POST` (`Authorization: Bearer RESEND_API_KEY`)
- **Usage**: Sends daily automated HTML email digests of `HOT` expansion news signals to `ALERT_EMAIL`.

---

## 4. Deep-Dive Module Specifications

### Module 1: Executive & Expansion Research
- **Frontend Page**: [app/page.tsx](file:///d:/ideaform-brands/app/page.tsx)
- **API Endpoint**: [app/api/research/route.ts](file:///d:/ideaform-brands/app/api/research/route.ts)
- **Execution Workflow**:
  1. User enters brand name (e.g., "Zudio").
  2. Server fires 6 parallel Tavily search requests:
     - `${brand} founder CEO managing director leadership team`
     - `${brand} head of business development retail expansion linkedin`
     - `${brand} real estate leasing head store development linkedin`
     - `${brand} India head country head franchise licensee partner`
     - `${brand} new store opening expansion press release`
     - `${brand} vice president director expansion property acquisition`
  3. Server combines search snippets (capped at 28,000 characters) and sends to Groq with `EXTRACT_PROMPT`.
  4. Groq returns structured JSON separating `leadership` (CEOs, Founders, Directors) from `expansion_team` (Leasing, Real Estate, BD heads).
  5. The API handler passes results to `lib/contacts.ts`, which cleans junk strings, normalizes LinkedIn URLs, and automatically persists newly discovered contacts into Supabase.

### Module 2: Expansion News Monitor & Cron Alerts
- **Frontend Page**: [app/monitor/page.tsx](file:///d:/ideaform-brands/app/monitor/page.tsx)
- **API Endpoints**: [app/api/monitor/route.ts](file:///d:/ideaform-brands/app/api/monitor/route.ts), [app/api/cron/route.ts](file:///d:/ideaform-brands/app/api/cron/route.ts)
- **Core Logic**: [lib/scan.ts](file:///d:/ideaform-brands/lib/scan.ts)
- **Execution Workflow**:
  1. System pulls watchlist brands from [lib/brands.ts](file:///d:/ideaform-brands/lib/brands.ts).
  2. `fetchBrandNews()` queries Google News RSS for each brand using expansion terms (`opens`, `expansion`, `flagship`, `leasing`, `store`).
  3. `dedupe()` uses **Jaccard word-set similarity ($\ge 0.55$)** to eliminate identical stories reported across multiple media outlets.
  4. Groq classifies stories into `HOT` (actively opening/funding stores), `WARM` (general growth signals), or `INFO` (irrelevant).
  5. Daily cron at `03:30 UTC` invokes `/api/cron` via `CRON_SECRET` authentication, generating an HTML digest email via Resend if HOT/WARM signals exist.

### Module 3: Requirement Mandate Inbox & Open-Web Sourcing
- **Frontend Page**: [app/requirements/page.tsx](file:///d:/ideaform-brands/app/requirements/page.tsx)
- **API Endpoints**:
  - `POST /api/requirements/parse`: Uses Groq to parse pasted raw text (from WhatsApp or LinkedIn posts) into structured JSON fields.
  - `POST /api/requirements/search`: Uses Tavily to query the open web for mandate posts by city/category and parses demand records with Groq.
  - `GET/POST/PATCH/DELETE /api/requirements`: Handles Supabase persistence for active mandates.
- **Extracted Attributes**: Brand Name, Category (Fashion, F&B, Jewellery, etc.), Broker vs Brand Direct Post, Cities, States, Min/Max Size (sqft), Rent/Capex terms, Property Types, Poster Contact Info, Priority (`HOT`/`WARM`/`INFO`).

### Module 4: Property-to-Brand Requirement Matcher
- **Frontend Page**: [app/match/page.tsx](file:///d:/ideaform-brands/app/match/page.tsx)
- **API Endpoint**: [app/api/match/route.ts](file:///d:/ideaform-brands/app/api/match/route.ts)
- **Execution Workflow**:
  1. Accepts property details (location, carpet area, frontage, rent) + requirement posts.
  2. Groq evaluates property characteristics against each brand mandate.
  3. Returns ranked array of matches containing:
     - `score`: Numeric rating 0–100.
     - `verdict`: `STRONG` ($\ge 75$), `POSSIBLE` ($50–74$), `WEAK` ($< 50$).
     - `reason`: Brief explanation of fit/mismatch.
     - `pitch_angle`: Specific value proposition hook for this brand.
     - `concerns`: Expected objections (e.g. insufficient frontage, wrong city/size).

### Module 5: Catchment & Micro-Market Analysis
- **Frontend Page**: [app/catchment/page.tsx](file:///d:/ideaform-brands/app/catchment/page.tsx)
- **API Endpoint**: [app/api/catchment/route.ts](file:///d:/ideaform-brands/app/api/catchment/route.ts)
- **Execution Workflow**:
  1. Address input is converted to (`lat`, `lon`) via `geocode()` (Nominatim / Photon).
  2. Overpass API fetches commercial POIs within radius (300m–1500m).
  3. `detectBrand()` Regex identifies recognized Indian national retail brands (e.g., Tanishq, Starbucks, Zudio, Croma, McDonald's).
  4. Groq synthesizes trade area dynamics:
     - `overview`: 3-4 sentence narrative on catchment profile.
     - `anchors`: Major retail anchors present.
     - `category_mix`: Count breakdown across retail categories.
     - `gaps`: Missing retail categories representing entrant opportunities.
     - `best_fit`: Recommended brand categories with justifications.
  5. Renders interactive Leaflet map with custom POI markers.

### Module 6: Multi-Channel Outreach Copy Composer
- **Frontend Page**: [app/compose/page.tsx](file:///d:/ideaform-brands/app/compose/page.tsx)
- **API Endpoint**: [app/api/compose/route.ts](file:///d:/ideaform-brands/app/api/compose/route.ts)
- **Execution Workflow**:
  1. Accepts property details, target retail category, and optional specific brand name.
  2. Groq generates four distinct outreach formats tuned to Indian leasing terms:
     - `whatsapp`: Under 100 words, direct hook, no generic greetings, soft call-to-action.
     - `email_subject`: Under 9 words, highly specific.
     - `email`: 120-180 words, scannable, call-to-action asking for site visit.
     - `proposal`: 300-400 words structured into 6 sections: LOCATION, THE PROPERTY, WHY IT WORKS FOR YOU, CATCHMENT & NEIGHBOURS, COMMERCIALS, NEXT STEP.
     - `hook_line`: High-converting single opening line.

### Module 7: CRM & Contact Database Store
- **Frontend Pages**: [app/contacts/page.tsx](file:///d:/ideaform-brands/app/contacts/page.tsx), [app/sourced/page.tsx](file:///d:/ideaform-brands/app/sourced/page.tsx)
- **API Endpoints**: [app/api/contacts/route.ts](file:///d:/ideaform-brands/app/api/contacts/route.ts), [app/api/sourced/route.ts](file:///d:/ideaform-brands/app/api/sourced/route.ts)
- **Core Helpers**: [lib/contacts.ts](file:///d:/ideaform-brands/lib/contacts.ts)
- **Features**:
  - Full-text search and filtering by company, tier, outreach status (`new`, `contacted`, `replied`, `meeting`, `dead`), research mode.
  - One-click CSV export (`toCSV()`).
  - WhatsApp text summary generator (`toWhatsApp()`).

### Module 8: Local Deal Logger
- **Frontend Page**: [app/deals/page.tsx](file:///d:/ideaform-brands/app/deals/page.tsx)
- **Storage**: Browser `localStorage` (client-side persistence).
- **Features**: Local deal tracking (property, brand, carpet area, rent, stage) with CSV export.

---

## 5. Database Architecture & Schema Specs

Execute these SQL definitions in PostgreSQL / Supabase to initialize the database layer:

```sql
-- 1. CONTACTS TABLE
CREATE TABLE IF NOT EXISTS contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_name TEXT NOT NULL,
  full_name TEXT NOT NULL,
  designation TEXT,
  department TEXT,
  responsibilities TEXT,
  email TEXT,
  email_confidence TEXT CHECK (email_confidence IN ('verified', 'pattern', 'unknown')),
  phone TEXT,
  linkedin_url TEXT,
  profile_url TEXT,
  source_url TEXT,
  tier TEXT CHECK (tier IN ('leadership', 'expansion', 'talent', 'other')),
  research_mode TEXT CHECK (research_mode IN ('expansion', 'hiring')),
  influences_expansion BOOLEAN,
  hiring_authority TEXT,
  status TEXT DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'replied', 'meeting', 'dead')),
  notes TEXT,
  tags TEXT[] DEFAULT '{}',
  last_contacted TIMESTAMPTZ,
  first_seen TIMESTAMPTZ DEFAULT now(),
  last_seen TIMESTAMPTZ DEFAULT now(),
  dedupe_key TEXT GENERATED ALWAYS AS (lower(trim(full_name)) || '::' || lower(trim(company_name))) STORED UNIQUE
);

-- 2. REQUIREMENTS MANDATES TABLE
CREATE TABLE IF NOT EXISTS requirements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand TEXT,
  category TEXT,
  is_broker_post BOOLEAN DEFAULT false,
  cities TEXT[] DEFAULT '{}',
  states TEXT[] DEFAULT '{}',
  size_min INT,
  size_max INT,
  capex TEXT,
  property_types TEXT[] DEFAULT '{}',
  poster_name TEXT,
  poster_title TEXT,
  email TEXT,
  phone TEXT,
  source_url TEXT,
  priority TEXT DEFAULT 'WARM' CHECK (priority IN ('HOT', 'WARM', 'INFO')),
  status TEXT DEFAULT 'open' CHECK (status IN ('open', 'matching', 'closed')),
  notes TEXT,
  raw_text TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 3. SOURCED CONTACTS TABLE (MANUAL / WHATSAPP HARVEST)
CREATE TABLE IF NOT EXISTS sourced_contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name TEXT NOT NULL,
  company_name TEXT,
  designation TEXT,
  phones TEXT[] DEFAULT '{}',
  emails TEXT[] DEFAULT '{}',
  category TEXT DEFAULT 'other',
  status TEXT DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'replied', 'meeting', 'dead')),
  notes TEXT,
  tags TEXT[] DEFAULT '{}',
  source TEXT DEFAULT 'manual',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  dedupe_key TEXT GENERATED ALWAYS AS (lower(trim(full_name)) || '::' || lower(trim(coalesce(company_name, '')))) STORED UNIQUE
);

-- 4. NON-DESTRUCTIVE CONTACT MERGE RPC FUNCTION
CREATE OR REPLACE FUNCTION merge_contacts(payload JSONB)
RETURNS SETOF contacts AS $$
DECLARE
  elem JSONB;
  rec contacts;
BEGIN
  FOR elem IN SELECT * FROM jsonb_array_elements(payload) LOOP
    INSERT INTO contacts (
      company_name, full_name, designation, department, responsibilities,
      email, email_confidence, phone, linkedin_url, profile_url, source_url,
      tier, research_mode, influences_expansion, hiring_authority
    ) VALUES (
      elem->>'company_name', elem->>'full_name', elem->>'designation', elem->>'department', elem->>'responsibilities',
      elem->>'email', elem->>'email_confidence', elem->>'phone', elem->>'linkedin_url', elem->>'profile_url', elem->>'source_url',
      elem->>'tier', elem->>'research_mode', (elem->>'influences_expansion')::boolean, elem->>'hiring_authority'
    )
    ON CONFLICT (dedupe_key) DO UPDATE SET
      designation = coalesce(excluded.designation, contacts.designation),
      department = coalesce(excluded.department, contacts.department),
      responsibilities = coalesce(excluded.responsibilities, contacts.responsibilities),
      email = coalesce(excluded.email, contacts.email),
      email_confidence = coalesce(excluded.email_confidence, contacts.email_confidence),
      phone = coalesce(excluded.phone, contacts.phone),
      linkedin_url = coalesce(excluded.linkedin_url, contacts.linkedin_url),
      profile_url = coalesce(excluded.profile_url, contacts.profile_url),
      source_url = coalesce(excluded.source_url, contacts.source_url),
      tier = coalesce(excluded.tier, contacts.tier),
      research_mode = coalesce(excluded.research_mode, contacts.research_mode),
      influences_expansion = coalesce(excluded.influences_expansion, contacts.influences_expansion),
      last_seen = now()
    RETURNING * INTO rec;
    RETURN NEXT rec;
  END LOOP;
  RETURN;
END;
$$ LANGUAGE plpgsql;
```

---

## 6. Component Swap & Rebuild Blueprint

When rebuilding this platform with custom infrastructure or enterprise vendors, use this blueprint:

```
+-------------------------------------------------------------------------------------------------------------------------+
|                                              COMPONENT SWAP SPECIFICATION                                               |
+--------------------------+----------------------------------+-----------------------------------------------------------+
| Existing Component       | Interface Standard Needed        | Alternative Technologies & Migration Steps                |
+--------------------------+----------------------------------+-----------------------------------------------------------+
| Tavily Search API        | Input: String Query              | 1. Custom Playwright Scraper: Search Google/DuckDuckGo    |
|                          | Output: Array<{ url, content }>  | 2. SearXNG: Self-hosted meta-search instance              |
|                          |                                  | 3. Serper API / SerpAPI: Direct Google Search API wrapper |
+--------------------------+----------------------------------+-----------------------------------------------------------+
| Groq LLM API             | Input: System + User Prompts     | 1. OpenAI (GPT-4o / GPT-4o-mini): Direct drop-in via API  |
| (Llama 3.3 70B)          | Output: Valid JSON Object        | 2. Anthropic (Claude 3.5 Sonnet): Excellent JSON & context|
|                          |                                  | 3. Self-Hosted Ollama / vLLM (Qwen2.5 / DeepSeek-R1):     |
|                          |                                  |    Run local inference server for zero API costs          |
+--------------------------+----------------------------------+-----------------------------------------------------------+
| Supabase PostgreSQL      | PostgreSQL Connection or REST    | 1. Self-hosted PostgreSQL DB + Drizzle / Prisma ORM       |
|                          | client with RPC support          | 2. AWS RDS PostgreSQL / PlanetScale / CockroachDB         |
+--------------------------+----------------------------------+-----------------------------------------------------------+
| Nominatim / Overpass     | Input: Address / Coordinates     | 1. Google Places API & Geocoding API: Enterprise grade    |
|                          | Output: Lat/Lon & Commercial POIs| 2. Mapbox Geocoding & Tile Service                        |
|                          |                                  | 3. Radar.io Places API / Foursquare Places API            |
+--------------------------+----------------------------------+-----------------------------------------------------------+
| Resend Email API         | Input: To, Subject, HTML Body    | 1. SendGrid / Postmark / Mailgun API                      |
|                          |                                  | 2. AWS SES: Highly cost-effective bulk/alert email        |
+--------------------------+----------------------------------+-----------------------------------------------------------+
```

---

## 7. Step-by-Step System Reconstruction Guide

If you are beginning your rebuild today, follow this sequential implementation order:

1. **Database Layer Initialization**:
   - Create your target relational database (PostgreSQL recommended).
   - Apply table definitions for `contacts`, `requirements`, and `sourced_contacts`.
   - Implement deduplication constraints (`full_name + company_name`) and non-destructive upsert functions.

2. **Search & Intelligence Connector Setup**:
   - Establish your search service abstraction layer (e.g. `searchWeb(query: string)` wrapper function).
   - Implement your LLM client wrapper configured with JSON response enforcement (`response_format: { type: "json_object" }`).

3. **Core Research Pipeline (Module 1)**:
   - Wire search + LLM extraction pipeline for brand leadership.
   - Connect output directly to your contact persistence function.

4. **Demand & Mandate Parser (Module 3)**:
   - Build raw text requirement extractor UI + API handler.
   - Add open-web requirement search crawler.

5. **Geospatial & Catchment Engine (Module 5)**:
   - Integrate address geocoder.
   - Build POI radius query service and retail category classifier.

6. **Outreach & Matching Engines (Modules 4 & 6)**:
   - Create prompt templates for property-to-mandate match scoring.
   - Build WhatsApp/Email/Proposal text generator.

7. **News Signals & Automated Alerting (Module 2)**:
   - Implement RSS feed scanner with Jaccard deduplication logic.
   - Attach cron scheduler and email notification service.
