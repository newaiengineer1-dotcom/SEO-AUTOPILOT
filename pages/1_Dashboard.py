import streamlit as st

from src.storage import load_json, read_logs
from src.ui import setup_page

setup_page("Dashboard", "📊")
audit = load_json("audit.json")
drafts = load_json("drafts.json", []) or []
patch = load_json("last_patch_summary.json")

if audit:
    sev = {k: sum(1 for i in audit["issues"] if i["severity"] == k) for k in ("critical", "high", "medium", "low")}
    cols = st.columns(5)
    for col, (k, v) in zip(cols, sev.items()):
        col.metric(k.title(), v)
    cols[4].metric("Pages crawled", len(audit["pages"]))
    ps = audit.get("pagespeed")
    if ps and not ps.get("error"):
        st.subheader("PageSpeed (mobile)")
        c = st.columns(4)
        c[0].metric("Performance", ps.get("performance"))
        c[1].metric("SEO", ps.get("seo"))
        c[2].metric("Accessibility", ps.get("accessibility"))
        c[3].metric("LCP (s)", round((ps.get("lcp_ms") or 0) / 1000, 1))
else:
    st.info("No audit yet. Open **Site Audit** and run one.")

c1, c2 = st.columns(2)
c1.metric("Drafts", len(drafts))
c1.metric("Drafts with AI text", sum(1 for d in drafts if d.get("source") == "ai"))
if patch:
    c2.subheader("Last patch")
    c2.json(patch)

st.subheader("30-day checklist")
for item in [
    "Search Console + GA4 + Bing Webmaster verified; conversions defined (form, call, WhatsApp)",
    "Google Business Profile claimed (Dubai + Lahore)",
    "facts.yaml filled with real proof (projects, certifications, brands, WhatsApp)",
    "Audit run; low-risk PR merged",
    "Service pages drafted, edited by a human, QA-clean, merged",
    "Sitemap submitted; new URLs requested for indexing",
    "3-5 real case studies + testimonials published",
    "Quote form shortened; thank-you page + conversion event live",
    "First weekly report reviewed",
]:
    st.checkbox(item, key=f"chk_{item[:20]}")

st.subheader("Recent activity")
logs = read_logs(8)
st.dataframe(logs) if logs else st.caption("No activity yet.")
