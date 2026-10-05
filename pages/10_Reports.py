import streamlit as st

from src import flows
from src.tools import gsc
from src.ui import control, engine, setup_page

s = setup_page("Weekly Report", "📈")
rows = None
src = st.radio("Data source", ["Upload Search Console CSV", "Search Console API"], horizontal=True)
if src == "Upload Search Console CSV":
    up = st.file_uploader("Performance export (Queries.csv)", type=["csv"])
    if up:
        rows = gsc.load_gsc_csv(up.getvalue())
else:
    st.caption("Needs GSC_CREDENTIALS (service-account JSON, added as a user in Search Console) and GSC_SITE_URL (e.g. sc-domain:kunergy.com).")
    days = st.slider("Days", 7, 90, 28)
    if st.button("Fetch from API"):
        try:
            st.session_state["gsc_rows"] = gsc.fetch_queries(s.gsc_site_url, s.gsc_credentials, days)
        except Exception as e:
            st.error(f"GSC API: {e}")
    rows = st.session_state.get("gsc_rows")

if not rows:
    st.info("Load data to build the report.")
    st.stop()
a = gsc.analyze(rows)
c = st.columns(4)
c[0].metric("Queries", a["queries"])
c[1].metric("Clicks", int(a["clicks"]))
c[2].metric("Impressions", int(a["impressions"]))
c[3].metric("Avg CTR %", a["avg_ctr"])
ai = ""
if engine() != "offline" and not control()["kill_switch"] and st.checkbox("Add AI recommendations (Reporter agent)"):
    try:
        ai = flows.weekly_report_ai(a, engine())
    except Exception as e:
        st.error(str(e))
md = flows.weekly_report_md(a, ai)
st.markdown(md)
st.download_button("Download report (Markdown)", md, "weekly_seo_report.md", "text/markdown")
