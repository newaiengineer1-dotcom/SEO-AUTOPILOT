import streamlit as st

from src.facts import load_facts
from src.flows import draft_pages
from src.keywords import default_page_plan, plan_from_rows
from src.models import PageDraft
from src.storage import load_json, log_event, save_json
from src.tools import facts_guard
from src.ui import control, engine, setup_page

setup_page("Content Queue", "✍️")
facts = load_facts()
saved = load_json("plan.json")
plan = [p for p in (plan_from_rows(saved) if saved else default_page_plan()) if p.enabled]
st.caption("Drafts use ONLY facts.yaml. Any `[NEEDS CLIENT FACT: ...]` must be replaced by you before the QA gate lets a page through.")

chosen = st.multiselect("Pages to draft", [p.slug for p in plan], default=[p.slug for p in plan[2:5]])
st.write(f"Engine: **{engine()}** " + ("(scaffold only, no AI)" if engine() == "offline" else ""))
if st.button("Generate drafts", type="primary", disabled=not chosen):
    if control()["kill_switch"]:
        st.error("Kill switch is on.")
    else:
        prog = st.progress(0.0)
        try:
            new = draft_pages([p for p in plan if p.slug in chosen], facts, engine(), lambda i, n, slug: prog.progress(i / n, text=slug))
            by = {d["slug"]: d for d in (load_json("drafts.json", []) or [])}
            by.update({d.slug: d.__dict__ for d in new})
            save_json("drafts.json", list(by.values()))
            log_event("drafts", f"Generated {len(new)} draft(s)", engine=engine())
            st.success(f"{len(new)} draft(s) saved.")
        except Exception as e:
            st.error(f"Drafting failed: {e}")

drafts = [PageDraft(**d) for d in (load_json("drafts.json", []) or [])]
if not drafts:
    st.info("No drafts yet.")
for d in drafts:
    issues = facts_guard.check_draft(d, facts)
    badge = "✅ ready" if not issues else f"❌ {len(issues)} blocker(s)"
    with st.expander(f"{d.slug}  ·  {badge}  ·  source: {d.source}"):
        for i in issues:
            st.error(f"{i.code}: {i.message}")
        intro = st.text_area("Intro", d.intro, key=f"intro_{d.slug}", height=120)
        secs = []
        for n, sec in enumerate(d.sections):
            h2 = st.text_input(f"Section {n + 1} heading", sec["h2"], key=f"h2_{d.slug}_{n}")
            body = st.text_area(f"Section {n + 1} text", sec["body"], key=f"b_{d.slug}_{n}", height=130)
            secs.append({"h2": h2, "body": body})
        faqs = []
        for n, f in enumerate(d.faq):
            q = st.text_input(f"FAQ {n + 1} question", f["q"], key=f"q_{d.slug}_{n}")
            a = st.text_area(f"FAQ {n + 1} answer", f["a"], key=f"a_{d.slug}_{n}", height=80)
            faqs.append({"q": q, "a": a})
        c1, c2 = st.columns(2)
        if c1.button("Save edits", key=f"save_{d.slug}"):
            d.intro, d.sections, d.faq = intro, secs, faqs
            d.source = "ai" if d.source == "ai" else "edited"
            all_d = {x["slug"]: x for x in (load_json("drafts.json", []) or [])}
            all_d[d.slug] = d.__dict__
            save_json("drafts.json", list(all_d.values()))
            st.success("Saved. Re-open to refresh the blocker list.")
        if c2.button("Delete draft", key=f"del_{d.slug}"):
            save_json("drafts.json", [x for x in (load_json("drafts.json", []) or []) if x["slug"] != d.slug])
            st.rerun()
