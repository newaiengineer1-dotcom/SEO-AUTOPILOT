import csv
import io

import streamlit as st

from src.storage import read_logs
from src.ui import setup_page

setup_page("Run Logs", "🧾")
logs = read_logs(1000)
if not logs:
    st.info("No activity yet.")
    st.stop()
kinds = sorted({l["kind"] for l in logs})
sel = st.multiselect("Kind", kinds, default=kinds)
rows = [l for l in logs if l["kind"] in sel]
st.dataframe(rows)
buf = io.StringIO()
w = csv.DictWriter(buf, fieldnames=sorted({k for r in rows for k in r}))
w.writeheader()
w.writerows(rows)
st.download_button("Download CSV", buf.getvalue(), "run_logs.csv", "text/csv")
