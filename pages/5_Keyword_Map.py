import streamlit as st

from src.keywords import default_page_plan, match_queries_to_pages, plan_from_rows
from src.storage import load_json, save_json
from src.tools.gsc import analyze, load_gsc_csv
from src.ui import setup_page

setup_page("Keyword Map", "🗺️")
st.caption("One primary keyword per page, separate UAE / Pakistan pages. Verify search volumes in Google Keyword Planner before committing.")

saved = load_json("plan.json")
plan = plan_from_rows(saved) if saved else default_page_plan()
rows = [{**p.__dict__, "secondary_keywords": ", ".join(p.secondary_keywords)} for p in plan]
edited = st.data_editor(rows, num_rows="dynamic", key="plan_editor")
c1, c2 = st.columns(2)
if c1.button("Save plan", type="primary"):
    new_plan = plan_from_rows(edited)
    save_json("plan.json", [{**p.__dict__} for p in new_plan])
    st.success(f"Saved {len(new_plan)} pages.")
if c2.button("Reset to default plan"):
    save_json("plan.json", [p.__dict__ for p in default_page_plan()])
    st.rerun()

st.subheader("Use real Search Console data")
up = st.file_uploader("Search Console export (Queries.csv)", type=["csv"])
if up:
    rows_gsc = load_gsc_csv(up.getvalue())
    st.write(f"{len(rows_gsc)} queries loaded.")
    a = analyze(rows_gsc)
    st.write("Striking distance (position 8-20):")
    st.dataframe(a["striking_distance"])
    st.write("Queries matched to planned pages:")
    st.dataframe(match_queries_to_pages(rows_gsc[:200], plan_from_rows(edited)))
