import streamlit as st
import streamlit.components.v1 as components

from src.facts import load_facts
from src.flows import DEFAULT_OPTIONS, LOW_RISK_ONLY, build_patch, pr_body, publish_patch
from src.models import PageDraft
from src.storage import load_json, save_json
from src.tools import site_io
from src.tools.snapshot import snapshot_site
from src.tools.github_ops import GitHubError, GitHubOps
from src.ui import control, setup_page

s = setup_page("Approvals", "✅")
facts = load_facts()
st.caption("Load the site source, build the patch, review diffs + QA, then approve. Agents never push to your main branch: they open a Pull Request, or you download a ZIP.")

# ---------------- 1. source
src = st.radio("Site source", ["Live site URL (auto-snapshot)", "Upload site ZIP", "GitHub repository"], horizontal=True)
if src.startswith("Live"):
    st.caption("No repository needed: the app downloads your pages and their CSS/JS/images from the live URL and builds the site ZIP for you. Only use it on sites you own.")
    url = st.text_input("Website URL", s.site_url)
    c1, c2 = st.columns(2)
    max_pages = c1.slider("Max pages", 1, 100, 30)
    max_mb = c2.slider("Max total size (MB)", 5, 200, 60)
    if st.button("Take snapshot", type="primary"):
        with st.spinner("Downloading pages and assets..."):
            snap = snapshot_site(url, max_pages=max_pages, max_total_mb=max_mb)
        st.session_state.update(site_files=snap.files, site_zip=snap.zip_bytes, site_prefix="", site_src="snapshot", snapshot=snap)
        st.session_state.pop("patch", None)
    snap = st.session_state.get("snapshot")
    if snap:
        m = st.columns(4)
        m[0].metric("Pages", snap.pages)
        m[1].metric("Patchable text files", len(snap.files))
        m[2].metric("Images/fonts/PDFs kept", len(snap.binaries))
        m[3].metric("Size (MB)", round(snap.total_bytes / 1_048_576, 1))
        for w in snap.warnings[:15]:
            st.warning(w)
        st.download_button("⬇️ Download BACKUP ZIP of the current live site", snap.zip_bytes, "kunergy-live-backup.zip", "application/zip")
elif src == "Upload site ZIP":
    up = st.file_uploader("ZIP of your website files (index.html, css/, images/...)", type=["zip"])
    if up and st.button("Load ZIP"):
        files, prefix = site_io.load_zip(up.getvalue())
        st.session_state.update(site_files=files, site_zip=up.getvalue(), site_prefix=prefix, site_src="zip")
else:
    if st.button("Fetch from GitHub"):
        try:
            ops = GitHubOps(s.github_token, s.site_repo, s.site_branch)
            st.session_state.update(site_files=ops.fetch_text_files(), site_zip=None, site_prefix="", site_src="github")
        except (GitHubError, Exception) as e:
            st.error(f"GitHub: {e}")
files = st.session_state.get("site_files")
if not files:
    st.info("Load your site files to continue. (Don't have them? Export from your host/cPanel, or ask your developer for the repo.)")
    st.stop()
st.success(f"Loaded {len(files)} text file(s) from {st.session_state.get('site_src')}; {sum(1 for p in files if p.endswith('.html'))} HTML page(s).")

# ---------------- 2. scope & options
scope = st.radio("Scope", ["All reviewed changes (SEO + content + premium theme)", "Low-risk fixes only (typos, alt text, canonical, sitemap...)"])
low_only = scope.startswith("Low-risk")
opts = dict(LOW_RISK_ONLY if low_only else DEFAULT_OPTIONS)
if not low_only:
    cols = st.columns(4)
    for col, k in zip(cols * 2, [k for k in DEFAULT_OPTIONS if k not in ("low_risk", "sitemap")]):
        opts[k] = col.checkbox(k, value=True, key=f"opt_{k}")
drafts = [PageDraft(**d) for d in (load_json("drafts.json", []) or [])]
use = st.multiselect("Drafts to include as new pages", [d.slug for d in drafts], default=[d.slug for d in drafts], disabled=low_only)

# ---------------- 3. build
if st.button("Build patch", type="primary"):
    patch = build_patch(files, [d for d in drafts if d.slug in use], facts, options=opts)
    st.session_state["patch"] = patch
    save_json("last_patch_summary.json", patch.summary())
patch = st.session_state.get("patch")
if not patch:
    st.stop()

sm = patch.summary()
c = st.columns(5)
for col, (k, v) in zip(c, sm.items()):
    col.metric(k.replace("_", " "), v)
if patch.qa.errors:
    st.error("QA gate: BLOCKED")
    for i in patch.qa.errors:
        st.write(f"❌ `{i.code}` {i.page}: {i.message}")
else:
    st.success("QA gate: passed")
if patch.qa.warnings:
    with st.expander(f"{len(patch.qa.warnings)} warning(s)"):
        for i in patch.qa.warnings:
            st.write(f"⚠️ `{i.code}` {i.page}: {i.message}")

st.subheader("Changes")
st.dataframe([c.__dict__ for c in patch.changes])
st.subheader("Diffs")
for path, diff in patch.diffs.items():
    with st.expander(path):
        lines = diff.splitlines()
        st.code("\n".join(lines[:400]) + ("\n... (truncated)" if len(lines) > 400 else ""), language="diff")
html_files = [p for p in patch.files if p.endswith(".html")]
if html_files:
    pick = st.selectbox("Preview a page (layout only; relative assets may not load in the preview)", html_files)
    components.html(patch.files[pick], height=620, scrolling=True)

# ---------------- 4. approve
st.subheader("Approve")
ok = st.checkbox("I have read every diff and QA item and every claim in the new pages is true.")
ctl = control()
d1, d2 = st.columns(2)
zip_bytes = site_io.export_zip(st.session_state.get("site_zip"), patch.files, st.session_state.get("site_prefix", "")) if patch.files else b""
d1.download_button("⬇️ Download patched ZIP", zip_bytes, "kunergy-site-patched.zip", "application/zip", disabled=not (ok and patch.qa.passed))
can_pr = st.session_state.get("site_src") == "github"
if d2.button("🚀 Open Pull Request" if not ctl["dry_run"] else "🧪 Dry run (save patch only)", disabled=not (ok and patch.qa.passed and (can_pr or ctl["dry_run"]))):
    try:
        ops = GitHubOps(s.github_token, s.site_repo, s.site_branch) if (can_pr and not ctl["dry_run"]) else None
        out = publish_patch(patch, ops=ops, dry_run=ctl["dry_run"], title="SEO Autopilot: " + ("low-risk fixes" if patch.low_risk_only else "SEO + content + theme"),
                            body=pr_body(patch), draft_pr=not (patch.low_risk_only and s.allow_automerge_low_risk))
        if out["pr_url"]:
            st.success(f"Pull request opened: {out['pr_url']}")
            if patch.low_risk_only and s.allow_automerge_low_risk and ops:
                st.info("Auto-merge of low-risk PRs is enabled by configuration.")
                st.write(ops.merge_pr_number(int(out["pr_url"].rstrip("/").split("/")[-1])))
        else:
            st.success(f"Dry run complete: patch saved to data/state/{out['saved']}. Turn off 'Dry run' in the sidebar to open a real PR.")
    except Exception as e:
        st.error(str(e))
if not can_pr:
    st.caption("PRs need the 'GitHub repository' source. With a snapshot or ZIP, download the patched ZIP, extract it and upload the files to your host (cPanel File Manager / FTP), overwriting the old ones. Keep the backup ZIP so you can roll back.")
