import streamlit as st

from src.facts import FACTS_PATH, parse_facts_text, save_facts_text, years_in_business
from src.ui import setup_page

setup_page("Facts Editor", "📝")
st.warning("Everything the AI may claim comes from this file. Leave unknown items empty: they will never be claimed. Add real proof (projects, certifications, brands, testimonials with permission).")
text = st.text_area("facts.yaml", FACTS_PATH.read_text(encoding="utf-8"), height=560)
c1, c2, c3 = st.columns(3)
if c1.button("Validate"):
    try:
        f = parse_facts_text(text)
        st.success(f"Valid YAML. {len(f.get('services', []))} services, {len(f.get('entities', []))} entities, years in business: {years_in_business(f)}")
    except Exception as e:
        st.error(f"Invalid: {e}")
if c2.button("Save"):
    try:
        save_facts_text(text)
        st.success("Saved. On Streamlit Cloud this is temporary: download the file and commit it to your repo.")
    except Exception as e:
        st.error(f"Not saved: {e}")
c3.download_button("Download facts.yaml", text, "facts.yaml", "text/yaml")
