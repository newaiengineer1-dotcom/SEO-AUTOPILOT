import streamlit as st

from src.llm import LLMError, groq_chat
from src.tools.github_ops import GitHubError, GitHubOps
from src.tools.pagespeed import run_pagespeed
from src.ui import setup_page

s = setup_page("Connections", "🔌")
st.caption("Keys are read from environment variables, `.env`, or Streamlit secrets. Values are never displayed.")

st.table({"Setting": ["GROQ_API_KEY", "GROQ_MODEL", "GITHUB_TOKEN", "SITE_REPO", "SITE_BRANCH", "SITE_URL", "PAGESPEED_API_KEY", "GSC_CREDENTIALS", "GSC_SITE_URL", "APP_PASSWORD"],
          "Status": ["set" if s.groq_api_key else "MISSING", s.groq_model, "set" if s.github_token else "MISSING", s.site_repo or "MISSING", s.site_branch, s.site_url,
                     "set" if s.pagespeed_api_key else "not set (optional)", "set" if s.gsc_credentials else "not set (optional)", s.gsc_site_url or "not set (optional)", "set" if s.app_password else "NOT SET"]})

c1, c2, c3, c4 = st.columns(4)
if c1.button("Test Groq"):
    try:
        out = groq_chat([{"role": "user", "content": "Reply with the single word OK."}], fast=True, max_tokens=8)
        st.success(f"Groq responded: {out.strip()[:40]}")
    except LLMError as e:
        st.error(str(e))
    except Exception as e:  # network etc.
        st.error(f"Could not reach Groq: {e}")
if c2.button("Test GitHub"):
    try:
        st.success(GitHubOps(s.github_token, s.site_repo, s.site_branch).check())
    except (GitHubError, Exception) as e:
        st.error(f"GitHub check failed: {e}")
if c3.button("Test PageSpeed"):
    with st.spinner("Running PageSpeed (can take ~30s)..."):
        r = run_pagespeed(s.site_url, api_key=s.pagespeed_api_key)
    st.error(r["error"]) if r.get("error") else st.success(f"Performance {r['performance']}, SEO {r['seo']}")
if c4.button("Check CrewAI"):
    try:
        import crewai

        st.success(f"crewai {getattr(crewai, '__version__', 'installed')}")
    except ImportError:
        st.warning("crewai is not installed. Engines 'offline' and 'direct' still work. `pip install crewai` to enable the multi-agent crew.")
