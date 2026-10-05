import requests
import streamlit as st
import streamlit.components.v1 as components

from src import flows, theme
from src.ui import control, engine, setup_page

s = setup_page("Premium Theme Studio", "🎨")
st.caption("A restrained, fast design system (no external fonts/scripts) applied through ONE scoped stylesheet. Preview first; it only goes live through an approved patch.")
t = theme.load_theme()

c1, c2, c3 = st.columns(3)
keys = list(theme.PALETTES)
palette = c1.selectbox("Palette", keys, index=keys.index(t["palette"]) if t["palette"] in keys else 0, format_func=lambda k: theme.PALETTES[k]["label"])
font = c2.selectbox("Headings", list(theme.FONTS), index=list(theme.FONTS).index(t["font"]) if t["font"] in theme.FONTS else 0)
enabled = c3.checkbox("Apply theme in patches", value=t["enabled"])
pal = theme.PALETTES[palette]
st.markdown("".join(f'<span style="display:inline-block;width:90px;height:44px;background:{pal[k]};color:#fff;border-radius:8px;margin:0 6px 6px 0;padding:4px 8px;font-size:12px">{k}<br>{pal[k]}</span>' for k in ("primary", "dark", "accent", "bg_alt")), unsafe_allow_html=True)

extra = st.text_area("Extra CSS (every selector must start with body.kg-premium)", t.get("extra_css", ""), height=140)
problems = theme.sanitize_css(extra) if extra.strip() else []
for p in problems:
    st.error(p)

if st.button("🤖 Designer agent: suggest extra CSS for the real site", disabled=engine() == "offline"):
    if control()["kill_switch"]:
        st.error("Kill switch is on.")
    else:
        try:
            html = requests.get(s.site_url, timeout=20, headers={"User-Agent": "KunergySEOAutopilot/1.0"}).text
            with st.spinner("Designer agent working..."):
                css, probs = flows.design_extra_css(html, {"palette": palette, "font": font}, engine())
            if probs:
                st.error("Rejected by the CSS safety check: " + "; ".join(probs[:4]))
            else:
                st.session_state["suggested_css"] = css
                st.success("Suggestion passed the safety check. Copy it into the box above to use it.")
                st.code(css, language="css")
        except Exception as e:
            st.error(str(e))

cfg = {"enabled": enabled, "palette": palette, "font": font, "extra_css": extra if not problems else ""}
css = theme.build_css(cfg)
if st.button("Save theme", type="primary", disabled=bool(problems)):
    theme.save_theme(cfg)
    st.success("Saved (download data/theme.yaml and commit it on Streamlit Cloud).")
with st.expander("Generated CSS"):
    st.code(css, language="css")
st.download_button("Download CSS", css, "kunergy-premium.css", "text/css")

st.subheader("Live preview of kunergy.com with this theme (nothing is saved or deployed)")
if st.button("Load preview"):
    try:
        html = requests.get(s.site_url, timeout=20, headers={"User-Agent": "KunergySEOAutopilot/1.0"}).text
        components.html(theme.preview_html(html, css, s.site_url), height=760, scrolling=True)
    except Exception as e:
        st.error(f"Could not load the live site: {e}")
