import json

import requests
import streamlit as st

from src import flows
from src.facts import load_facts
from src.models import AuditReport
from src.storage import load_json
from src.tools.crawler import analyze_html
from src.ui import control, engine, setup_page

setup_page("Local SEO, CRO & Competitors", "📍")
facts = load_facts()
tab1, tab2, tab3 = st.tabs(["Conversion (CRO)", "Local & authority pack", "Competitor gaps"])

with tab1:
    audit = load_json("audit.json")
    report = AuditReport.from_dict(audit) if audit else None
    st.markdown(flows.CRO_FORM_SPEC)
    if report and engine() != "offline" and st.button("Add AI recommendations"):
        try:
            st.markdown(flows.cro_plan(report, facts, engine()).split("## Additional AI recommendations")[-1])
        except Exception as e:
            st.error(str(e))

with tab2:
    st.caption("Drafts only. A human posts and sends everything. Never use fake reviews or paid links.")
    if st.button("Generate pack"):
        try:
            st.session_state["pack"] = flows.local_pack_offline(facts) if engine() == "offline" else flows.local_pack_ai(facts, engine())
        except Exception as e:
            st.error(str(e))
    pack = st.session_state.get("pack")
    if pack:
        for k, v in pack.items():
            st.subheader(k.replace("_", " ").title())
            st.write(v) if isinstance(v, list) else st.code(v, language=None)
        st.download_button("Download pack (JSON)", json.dumps(pack, indent=2, ensure_ascii=False), "local_pack.json")

with tab3:
    st.caption("Paste competitor page URLs (one per line). We compare structure and proof signals; we never copy their text.")
    urls = [u.strip() for u in st.text_area("Competitor URLs", height=100).splitlines() if u.strip().startswith("http")]
    if urls and st.button("Analyze competitors"):
        rows = []
        for u in urls[:8]:
            try:
                r = requests.get(u, timeout=20, headers={"User-Agent": "KunergySEOAutopilot/1.0"})
                p = analyze_html(u, r.text, r.status_code)
                rows.append({"url": u, "title": p.title, "h1": " | ".join(p.h1), "h2s": p.h2_count, "words": p.word_count, "schema": ", ".join(sorted(set(p.jsonld_types))), "has_tel": p.has_tel, "has_whatsapp": p.has_whatsapp, "form_fields": p.max_form_fields})
            except Exception as e:
                rows.append({"url": u, "title": f"ERROR {e}"})
        st.session_state["comp_rows"] = rows
    rows = st.session_state.get("comp_rows")
    if rows:
        st.dataframe(rows)
        if engine() != "offline" and not control()["kill_switch"] and st.button("Ask the Competitor agent for gaps"):
            try:
                st.markdown(flows._ask("competitor", f"Competitor page signals (structure only): {rows}\nOur company facts: {flows.facts_for_prompt(facts)}\nList the 6 biggest gaps/opportunities for our pages (proof, FAQs, schema, CTAs, depth). Do not suggest copying text. Max 250 words.", engine()))
            except Exception as e:
                st.error(str(e))
