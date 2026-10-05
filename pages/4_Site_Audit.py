import csv
import io
import json

import streamlit as st

from src import flows
from src.facts import load_facts
from src.models import AuditReport
from src.storage import load_json, log_event, save_json
from src.tools.crawler import run_audit
from src.tools.pagespeed import run_pagespeed
from src.ui import control, engine, setup_page

s = setup_page("Site Audit", "🔎")
url = st.text_input("Site URL", s.site_url)
c1, c2 = st.columns(2)
limit = c1.slider("Max pages to crawl", 1, 100, s.crawl_limit)
use_ps = c2.checkbox("Include PageSpeed (mobile) for the home page", value=True)

if st.button("Run audit", type="primary"):
    with st.status("Auditing...", expanded=True) as status:
        st.write("Crawling pages...")
        ps = None
        if use_ps:
            st.write("Running PageSpeed Insights...")
            ps = run_pagespeed(url, api_key=s.pagespeed_api_key)
        report = run_audit(url, limit=limit, pagespeed=ps)
        save_json("audit.json", report.to_dict())
        log_event("audit", f"Audited {url}", pages=len(report.pages), issues=len(report.issues))
        status.update(label=f"Done: {len(report.pages)} page(s), {len(report.issues)} issue(s)", state="complete")

data = load_json("audit.json")
if not data:
    st.info("Run an audit to see results.")
    st.stop()
report = AuditReport.from_dict(data)
st.caption(f"Audit of {report.site_url} at {report.generated_at}")
cols = st.columns(4)
for col, sev in zip(cols, ("critical", "high", "medium", "low")):
    col.metric(sev.title(), sum(1 for i in report.issues if i.severity == sev))
if report.pagespeed:
    st.write("PageSpeed:", report.pagespeed)
st.write("Site checks:", report.site_checks)

tab1, tab2, tab3 = st.tabs(["Issues", "Pages", "Fix plan"])
with tab1:
    sev_filter = st.multiselect("Severity", ["critical", "high", "medium", "low"], default=["critical", "high", "medium", "low"])
    rows = [i.__dict__ for i in report.issues if i.severity in sev_filter]
    st.dataframe(rows)
    buf = io.StringIO()
    if rows:
        w = csv.DictWriter(buf, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    st.download_button("Download issues CSV", buf.getvalue(), "audit_issues.csv", "text/csv")
    st.download_button("Download audit JSON", json.dumps(data, indent=2), "audit.json", "application/json")
with tab2:
    st.dataframe([{k: v for k, v in p.__dict__.items() if k not in ("internal_links",)} for p in report.pages])
with tab3:
    st.markdown(flows.audit_plan_offline(report))
    if st.button("Ask the Auditor agent for a prioritized plan"):
        if control()["kill_switch"]:
            st.error("Kill switch is on.")
        else:
            try:
                with st.spinner("Auditor agent working..."):
                    st.markdown(flows.audit_plan_ai(report, load_facts(), engine()))
            except Exception as e:
                st.error(str(e))
