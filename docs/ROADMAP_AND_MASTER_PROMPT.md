# Kunergy SEO Autopilot: Master Prompt, 30-Day Roadmap & Website Optimization Plan

Site reviewed: https://www.kunergy.com (reviewed 3 Oct 2026)

---

## Part 1. What I found on kunergy.com

I could read the page text only. The audit agent must verify meta tags, schema, alt text and speed.

| # | Finding | Why it hurts leads / ranking |
|---|---------|------------------------------|
| 1 | **Everything is on one URL**. Navigation is anchors (`#about`, `#solutions`...) | Google can rank one page for only a few topics. You offer 13 services in 2 countries but have no page for any of them. |
| 2 | Page title is just **"Kunergy"**. H1 is "WELCOME TO KUNERGY" | No keywords like *solar*, *Dubai*, *Lahore* in the two strongest on-page signals. |
| 3 | **No proof**: no projects, case studies, testimonials, certifications, kW installed, brands | Solar is a high-trust, high-ticket purchase. Buyers and Google's E-E-A-T both look for proof. |
| 4 | Typos: "Commerical", "Kunegy Solar Energy System..." (legal name), "Electrical Vehicles" | Hurts credibility. People search "electric vehicle charging", so the wording misses queries. |
| 5 | Two markets (UAE, Pakistan) share one page | Needs separate UAE and Pakistan pages with local signals. |
| 6 | Quote form has 9 fields and no qualifying questions. No visible WhatsApp or click-to-call button | Too much friction for mobile users. Sales gets no data to prioritize leads. |
| 7 | Images appear to have **no alt text**. File names have spaces (`png logo.png`, `...48 (1).png`). Three full-width hero images | Accessibility, image search and load speed (LCP) suffer. |
| 8 | No blog or guides. Footer says © 2024 | Misses all the "cost of solar", "payback" and "net metering" searches that bring buyers in. |

---

## Part 2. THE MASTER PROMPT (copy everything inside the block)

Paste it into Claude Code, Cursor, or a fresh Claude chat. Tell it to work **phase by phase**.

~~~~text
# ROLE
You are a combined team: Senior Product Architect, Python Engineer, Streamlit UX Engineer,
AI Systems Engineer (CrewAI + Groq), Technical SEO Engineer, QA Engineer and DevOps Engineer.
Build "Kunergy SEO Autopilot": a multi-agent system with a Streamlit control panel that audits,
plans, builds, QA-checks and (after human approval) deploys SEO and lead-generation improvements
to https://www.kunergy.com.

# BUSINESS CONTEXT
- Company: Kunergy, "Energy for Life". Founded 2014. One-stop renewable energy and technical services.
- Entities:
  1) Kunergy Solar Energy System Installations Co. L.L.C. - 0301, Bayan Business Center, DIP 1, Dubai, UAE.
     +971 50 4254087, info@kunergy.com
  2) Kunergy International Pvt. Ltd. - E-7-1-B, Al Noor Town, Lahore Cantt, Pakistan.
     +92 300 1950006 | +92 332 1335540, info@kunergy.com
- Services:
  Solar PV EPC (residential, commercial, industrial, utility), Solar + BESS, solar street lights,
  electrical fitting contracting, HVAC/ventilation/air filtration, electromechanical installation,
  EV charging (residential, commercial, industrial), solar O&M, building electrical and AC maintenance,
  EV charger maintenance, solar feasibility study, engineering design, project management.
- Current site: single-page static site with anchor navigation, weak title/H1, no service pages,
  no proof (projects, testimonials, certifications), long quote form, no WhatsApp or click-to-call, no blog.
- PRIMARY GOAL: more qualified quote requests (leads) from UAE and Pakistan.
- SECONDARY GOALS: rank for service + location keywords, win local map results, build trust, keep the site fast.

# TECH STACK
- Python 3.11 (confirm against CrewAI's supported range), crewai, crewai-tools, streamlit, pydantic v2,
  httpx, beautifulsoup4, lxml, PyGithub or GitPython, python-dotenv, tenacity, pytest, ruff,
  google-api-python-client (Search Console and GA4 read access, optional).
- LLM: Groq via CrewAI's LLM class. Model from env var GROQ_MODEL
  (default "groq/llama-3.3-70b-versatile"; verify the current model IDs at console.groq.com).
  Example:
    from crewai import LLM
    llm = LLM(model=os.getenv("GROQ_MODEL"), api_key=os.getenv("GROQ_API_KEY"), temperature=0.3)
- Handle Groq rate limits (HTTP 429): exponential backoff, Crew max_rpm, chunk long inputs, use a smaller
  model for cheap tasks (classification, alt text) and a larger one for writing.
- DO NOT scrape Google search results (against Google's terms). For keyword data use official APIs
  (Search Console, PageSpeed Insights) or CSV exports the user uploads (Keyword Planner, GSC).
- Streamlit Community Cloud has an EPHEMERAL filesystem. Persist state in the GitHub repo (JSON/YAML)
  or an external DB, never only on local disk.

# REPOSITORIES
1) kunergy-seo-autopilot  (the app, this project)
2) kunergy-website        (the site source; ask me for the URL and hosting provider)
Agents must NEVER push to main of the website repo. They create a branch seo/YYYY-MM-DD-topic and open
a Pull Request with a changelog. A human merges. CI deploys on merge.
Use a fine-grained GitHub token limited to the website repo (contents + pull requests only).

# PROJECT STRUCTURE
kunergy-seo-autopilot/
  app.py                      # Streamlit entry
  pages/ 1_Dashboard.py 2_Connections.py 3_Site_Audit.py 4_Keyword_Map.py
         5_Content_Queue.py 6_Approvals.py 7_Run_Logs.py 8_Reports.py
  src/
    config.py                 # pydantic settings, reads env / st.secrets
    llm.py                    # Groq LLM factory + retry
    agents.py  tasks.py  flows.py
    tools/ crawler.py pagespeed.py html_patcher.py schema_builder.py sitemap.py
           github_ops.py gsc.py link_checker.py facts_guard.py
    models.py                 # pydantic models for every artifact
  data/ facts.yaml  keyword_map.json  audit/  drafts/
  tests/
  .github/workflows/ci.yml
  requirements.txt  .env.example  README.md

# facts.yaml (SOURCE OF TRUTH FOR ALL CLAIMS)
Holds the real company facts: years of experience, completed projects, kW installed, certifications,
licences, partner brands, testimonials (with permission), service areas, addresses, phones.
Writers may use ONLY facts in this file. If a needed fact is missing, insert [NEEDS CLIENT FACT: ...]
and list it in the Approvals page. NEVER invent statistics, testimonials, certifications, awards,
prices, savings figures or regulations.

# AGENTS (CrewAI)
1. Site Auditor - crawls the site and checks title, meta description, H1-H3, canonical, alt text,
   internal links, broken links, schema, robots/sitemap, mobile, PageSpeed/Core Web Vitals,
   typos, NAP consistency. Output: AuditReport (severity, URL, fix).
2. Keyword & Intent Strategist - clusters keywords by intent (service + city + country, "cost",
   "net metering", "EV charger installation", etc.) from uploaded CSV/GSC data and maps ONE primary keyword
   to ONE page. Separate UAE and Pakistan. Output: keyword_map.json.
3. Competitor Analyst - given competitor URLs I supply, compares page structure, offers, proof,
   FAQs. Output: gap list (no copying of competitor text).
4. Content Writer - drafts service pages, location pages, case studies, FAQs and blog posts from approved
   briefs, strictly from facts.yaml. Natural language, no keyword stuffing, unique text per page.
5. On-Page & Schema Engineer - edits HTML safely: title, meta, headings, alt text, internal links,
   canonical, hreflang (en-AE / en-PK), JSON-LD (Organization, LocalBusiness x2, Service, FAQPage,
   BreadcrumbList), sitemap.xml, robots.txt, OpenGraph.
6. CRO / Lead-Gen Specialist - sticky WhatsApp + click-to-call, shorter quote form with qualifiers
   (property type, monthly electricity bill, city, timeline), thank-you page for conversion tracking,
   trust blocks, CTA placement, optional savings-estimator spec.
7. Local & Authority Agent - drafts Google Business Profile posts/descriptions/Q&A, citation list,
   review-request templates, outreach emails. DRAFTS ONLY; a human sends everything.
8. QA & Compliance Reviewer (gatekeeper) - blocks a PR if: HTML invalid, links broken, Lighthouse
   below thresholds (Perf >= 85 mobile, SEO >= 95, A11y >= 90), a claim is not in facts.yaml, text is
   duplicated across pages, or content looks like keyword stuffing, doorway pages, or unreviewed scaled AI
   content (Google spam policies).
9. Release Manager - branch, commit, PR with changelog and rollback steps, post-deploy smoke test,
   ping Search Console URL inspection list for me to submit.
10. Reporter - weekly KPI report from GSC/GA4 (clicks, impressions, position for mapped keywords,
    leads, conversion rate, CWV) with recommended next actions.

# WORKFLOW (CrewAI Flow with human gates)
Audit -> Keyword Map -> PLAN (human approves) -> Build drafts -> QA -> PR (human approves/merges)
-> Deploy -> Monitor -> Report -> loop.
Auto-merge is allowed ONLY for an allow-list of low-risk changes (alt text, typo fixes, sitemap lastmod).
Anything touching claims, pricing, legal text, or new pages always needs human approval.
Default mode = DRY RUN (writes diffs, does not open PRs) with a visible toggle and a kill switch.

# STREAMLIT UX REQUIREMENTS
- Clean sidebar, st.status/progress for long runs, st.cache_data for crawls, session_state for runs.
- Connections page tests Groq, GitHub, GSC, PageSpeed keys with clear success/failure messages.
- Approvals page shows side-by-side diffs, the QA verdict, [NEEDS CLIENT FACT] items, Approve / Reject / Comment.
- Run Logs: every agent action, tokens used, errors, timestamps. Download buttons for CSV/JSON.
- Friendly error states, no stack traces to the user, mobile-friendly layout.

# SECURITY
Secrets only in env or st.secrets; .env in .gitignore; ship .env.example. Validate and sanitize all
HTML before writing. Restrict file writes to the website repo working tree. Log all outbound calls.

# QA & TESTING
pytest unit tests (HTML patcher golden files, schema validity, sitemap, facts_guard), mocked-LLM
integration test of the full flow, ruff lint, GitHub Actions CI (lint + tests + html validation +
Lighthouse CI on the PR preview).

# DEPLOYMENT
Deploy the app on Streamlit Community Cloud from the GitHub repo (pinned requirements.txt, secrets set in
the dashboard). Provide a step-by-step README and a first-run checklist.

# HOW TO WORK
Phase 0: Restate the plan, list assumptions, ask me up to 5 questions (hosting, repo access, GSC access,
facts for facts.yaml, competitor URLs). Phase 1: skeleton + config + LLM + tests green. Phase 2: Auditor +
crawler + Audit page. Phase 3: Keyword + Content agents + queue. Phase 4: Patcher/Schema/CRO + QA gate.
Phase 5: GitHub PR flow + Approvals page. Phase 6: Reporter + CI + deploy. After each phase:
show the file tree, full code, how to run it, tests and results, and what is next.
Never claim something works without running the tests. Write complete files, not snippets.

# ACCEPTANCE CRITERIA
- One command starts the app. Full flow runs end-to-end in dry-run mode on the live site.
- Audit report produced; keyword map produced; at least 5 service pages drafted from facts.yaml.
- No PR can be merged by the system itself except allow-listed low-risk changes.
- All tests and CI pass. README lets a non-developer deploy it.
~~~~

---

## Part 3. Step-by-step 30-day roadmap

**Expectation setting:** nobody can honestly guarantee page-1 rankings in 30 days. In month 1 you can realistically get: a measurable site, a fixed foundation, 10 to 15 indexed pages, a stronger Google Business Profile, a better quote form, and early impressions on long-tail searches. Rankings for competitive terms such as "solar installation Dubai" usually take 3 to 6+ months. If you need leads sooner, run a small **Google Ads search campaign** in parallel while SEO matures.

### Week 1: Measure and fix the foundation
| Day | Task |
|-----|------|
| 1 | Set up Google Search Console (domain property), GA4 and Bing Webmaster Tools. Set up GTM. |
| 1 | Define conversions: form submit, WhatsApp click, phone click. Test each one. |
| 2 | Claim/verify **Google Business Profile** for Dubai and Lahore. Add services, hours, photos. (Google requires a real, staffed location. Check the rules for the Bayan Business Center address.) |
| 2 | Fix quick wins by hand: title tag, meta description, H1, typos ("Commercial", "Electric Vehicle", legal name), © year, `tel:` and `mailto:` links. |
| 3 | Confirm HTTPS, one canonical version (www or non-www), and add `robots.txt` and `sitemap.xml`. Submit the sitemap. |
| 4 to 5 | Keyword research using Keyword Planner and GSC. Build the keyword map (Part 4). |
| 6 to 7 | Collect real proof into `facts.yaml`: projects, kW installed, photos, testimonials, certifications, brands. Create the two repos and the Phase 1 to 2 app skeleton from the master prompt. |

### Week 2: Restructure the site (one page per service and market)
- Split the site into real pages (list in Part 4). Keep the current design if you like it.
- Each page gets: unique title and meta, one H1, 600 to 1,000 words of useful copy, FAQ, project photos, one clear CTA, and internal links to related services.
- Add JSON-LD schema (Organization, LocalBusiness for each entity, Service, FAQPage).
- Compress images to WebP, add alt text, lazy-load, and reduce the hero sliders to one image.
- Agents draft; **you review every page** for accuracy before merging.
- Submit the new URLs in GSC (URL Inspection → Request indexing).

### Week 3: Trust, conversion and local
- Publish 3 to 5 **real** case studies (location, system size, challenge, result, photo).
- Add a testimonials section (with permission), certifications, and partner or brand logos you actually hold.
- Replace the quote form: name, phone/WhatsApp, email, city, property type, monthly bill, service, optional message. Add a thank-you page that fires the conversion event.
- Add a sticky WhatsApp and call button on mobile.
- Google Business Profile: weekly posts, services list, Q&A, project photos. Start asking past customers for reviews with a short, honest request template.
- Create or clean up listings on relevant UAE and Pakistan business directories and keep name, address and phone identical everywhere.

### Week 4: Content, authority, iterate
- Publish 4 helpful articles (human-edited, with real data). Ideas: solar panel cost and payback in the UAE, how commercial solar saves money, what a BESS is and when it pays off, EV charger installation guide, solar net metering in Pakistan (verify the current rules before publishing). Ask the agent to include only facts you can cite.
- Add internal links from articles to service pages.
- Earn 5 to 10 legitimate links: partner and supplier pages, industry associations, local press, LinkedIn articles, chambers of commerce. No bought links.
- Review GSC: queries with impressions but low clicks → rewrite title and meta. Pages with no impressions → check indexing.
- Run a PageSpeed pass and fix the slowest items.
- Produce the Month 1 report and plan Month 2 to 3.

### Month 2 to 3 preview
More location and industry pages (e.g., warehouses, villas, farms, factories), a projects gallery, video, Arabic and Urdu versions if your audience searches in them, and a monthly content calendar.

---

## Part 4. Website optimization recommendations

### 4.1 New page structure
```
/                                  Home (brand + all services, two market entry points)
/uae/                              UAE hub
  /uae/solar-installation-dubai/
  /uae/commercial-industrial-solar/
  /uae/residential-solar/
  /uae/solar-battery-storage-bess/
  /uae/ev-charging-solutions/
  /uae/solar-om-maintenance/
/pakistan/                         Pakistan hub
  /pakistan/solar-installation-lahore/
  /pakistan/commercial-industrial-solar/
  /pakistan/solar-net-metering-support/   (only if you truly offer it)
/services/electrical-contracting/
/services/hvac-ventilation-air-filtration/
/services/solar-feasibility-engineering-consultancy/
/projects/   /about/   /blog/   /contact/
```
Use `en-AE` and `en-PK` hreflang only on pages that are true regional equivalents.

### 4.2 Starter keyword map (verify volumes in Keyword Planner first)
| Page | Primary keyword idea |
|------|----------------------|
| UAE solar | solar panel installation Dubai; solar company UAE |
| UAE commercial | commercial solar EPC UAE; industrial rooftop solar UAE |
| BESS | solar battery storage Dubai |
| EV | EV charger installation Dubai / UAE |
| O&M | solar O&M services UAE |
| PK solar | solar panel installation Lahore; solar EPC Pakistan |
| PK commercial | commercial solar Pakistan; industrial solar Lahore |

### 4.3 Example on-page tags (adapt after keyword research)
- Title: `Solar Panel Installation Dubai & UAE | Kunergy Solar` (keep under about 60 characters)
- Meta: `Kunergy designs, supplies and installs solar PV and battery systems for homes, businesses and industry across the UAE. Get a free quote today.`
- H1: `Solar Panel Installation in Dubai & the UAE`

### 4.4 Priority fix list
| Priority | Action |
|----------|--------|
| **Critical** | Real service pages; keyword-rich title/H1; Search Console + GA4 + conversion tracking; Google Business Profile; WhatsApp and call buttons; shorter form |
| **Critical** | Real proof (projects, testimonials, certifications) |
| **High** | LocalBusiness and Service schema for both entities; sitemap/robots; canonical; compress images + alt text; fix typos and legal name |
| **High** | 4+ helpful articles; internal linking; FAQ sections |
| **Medium** | Reviews program, citations, backlinks; video; Arabic/Urdu; savings calculator |

### 4.5 Schema starter (Dubai entity, fill from facts.yaml)
```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Kunergy Solar Energy System Installations Co. L.L.C.",
  "url": "https://www.kunergy.com/uae/",
  "telephone": "+971504254087",
  "email": "info@kunergy.com",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "0301, Bayan Business Center, DIP 1",
    "addressLocality": "Dubai",
    "addressCountry": "AE"
  },
  "sameAs": [
    "https://pk.linkedin.com/company/Kunergy",
    "https://www.facebook.com/kunergy/",
    "https://www.instagram.com/kunergy/"
  ]
}
```
Do not add ratings or review markup unless the reviews are real and visible on the page.

---

## Part 5. How the agents "automatically update" the website, safely

1. **Agents propose, humans approve.** Each run opens a Pull Request from a `seo/...` branch with a diff, a changelog and a QA report.
2. **Auto-merge only the safe list**: alt text, typo fixes, sitemap dates. Never auto-merge claims, prices, legal text or new pages.
3. **CI deploys on merge** (GitHub Pages, Netlify, Cloudflare Pages or Vercel, depending on your host). Roll back by reverting the PR.
4. **Facts guard**: every number or claim must exist in `facts.yaml`, or the QA agent blocks it.
5. **Avoid spam patterns**: Google penalizes mass-produced unreviewed AI pages, doorway pages, keyword stuffing and fake reviews. The QA agent checks for these.
6. **Weekly loop**: Reporter reads Search Console → proposes title/meta tests, new content and fixes → you approve → agents ship.

## Part 6. KPIs to track weekly
Leads (form + WhatsApp + calls), lead conversion rate, cost per lead (if running ads), GSC clicks/impressions/average position for mapped keywords, indexed pages, Google Business Profile calls and direction requests, Core Web Vitals, number of reviews, referring domains.

## Part 7. Quick start (developer)
```bash
git clone <your repo> kunergy-seo-autopilot && cd kunergy-seo-autopilot
python -m venv .venv && source .venv/bin/activate
pip install crewai streamlit pydantic httpx beautifulsoup4 lxml PyGithub python-dotenv tenacity pytest ruff
cp .env.example .env   # add GROQ_API_KEY, GROQ_MODEL, GITHUB_TOKEN
streamlit run app.py
```
Deploy: push to GitHub → share.streamlit.io → New app → select repo and `app.py` → add secrets under Settings → Secrets.
