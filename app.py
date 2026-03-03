import streamlit as st
import pandas as pd
import time

st.set_page_config(
    page_title="Healthcare Operations Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Session state defaults ─────────────────────────────────────────────────────
for key, val in {
    'dark_mode':        False,
    'auto_refresh':     False,
    'refresh_interval': 60,
    'annotations':      {},
    'last_refresh':     time.time(),
    'current_page':     0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Load ALL data once ────────────────────────────────────────────────────────
from myPages.data_loader import load_all, apply_filters
from myPages import page1, page2, page3, page4, page5, page6

DATA_PATH = "data/dataFinal.xlsx"

if "_raw" not in st.session_state:
    st.session_state["_raw"] = load_all(DATA_PATH)

_raw = st.session_state["_raw"]

# ── Filter option lists (always from raw unfiltered data) ─────────────────────
_appts_raw   = _raw["appointments"]
_depts_raw   = _raw["departments"]
_min_date    = _appts_raw["appointment_Date"].min().date()
_max_date    = _appts_raw["appointment_Date"].max().date()
_dept_opts   = ["All Departments"] + sorted(_depts_raw["dept_Name"].dropna().unique().tolist())
_status_opts = ["All Status"]      + sorted(_appts_raw["appointment_status"].dropna().unique().tolist())

# ── Initialise filter defaults once ──────────────────────────────────────────
if "_gf_start" not in st.session_state:
    st.session_state["_gf_start"]  = _min_date
    st.session_state["_gf_end"]    = _max_date
    st.session_state["_gf_depts"]  = ["All Departments"]
    st.session_state["_gf_status"] = ["All Status"]

PAGE_NAMES = [
    "Executive Overview",
    "Patient Demographics & Demand Analysis",
    "Clinical & Disease Intelligence",
    "Operational Efficiency & Capacity",
    "Staffing & Resource Optimization",
    "Intelligence & Planning",
]


# ── Theme CSS ──────────────────────────────────────────────────────────────────
def apply_theme():
    if st.session_state.dark_mode:
        st.markdown("""<style>
        .stApp { background-color: #0E1117; color: #FAFAFA; }

        /* ── Sidebar: rich gradient that pops against the dark page ── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg,#0F2456 0%,#0F1F48 40%,#0A1628 100%) !important;
            padding-top:0 !important;
            border-right:1px solid rgba(99,179,237,0.15) !important;
            box-shadow:4px 0 28px rgba(0,0,0,0.6) !important; }
        section[data-testid="stSidebar"] > div { padding-top:0 !important; }

        /* Brand header */
        .sb-brand { background:linear-gradient(135deg,#F97316,#EA580C);
            margin:0; padding:20px 20px 16px; border-bottom:1px solid rgba(255,255,255,0.12); }
        .sb-title { font-size:17px; font-weight:900; color:#fff; margin-bottom:2px; line-height:1.3; }
        .sb-sub   { font-size:11px; color:rgba(255,255,255,0.78); }

        /* Section headers */
        .sb-hdr   { font-size:10px; font-weight:800; color:rgba(255,255,255,0.5);
                    margin:16px 0 8px; text-transform:uppercase; letter-spacing:1.5px; padding:0 16px; }
        .sb-div   { height:1px; background:rgba(255,255,255,0.1); margin:12px 8px; }

        /* Notes box */
        .ann-box  { background:rgba(255,255,255,0.07); border-left:4px solid #F97316;
                    padding:8px 12px; border-radius:6px; margin:4px 0;
                    font-size:12px; color:rgba(255,255,255,0.9) !important; line-height:1.5; }

        /* Filter badges */
        .filter-badge { display:inline-block; background:rgba(249,115,22,0.18);
            border:1px solid #F97316; color:#FDBA74 !important; border-radius:20px;
            padding:2px 10px; font-size:11px; font-weight:700; margin:2px; }

        /* ALL sidebar text — force white/near-white for full visibility */
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div { color:rgba(255,255,255,0.88) !important; }

        /* Top header bar */
        header[data-testid="stHeader"] {
            background-color:#1C1F26 !important; border-bottom:1px solid #334155 !important; }
        header[data-testid="stHeader"] button svg,
        header[data-testid="stHeader"] svg { fill:#F1F5F9 !important; }
        header[data-testid="stHeader"] span,
        header[data-testid="stHeader"] p { color:#F1F5F9 !important; }

        /* Expander text inside sidebar */
        section[data-testid="stSidebar"] .stExpander p,
        section[data-testid="stSidebar"] .stExpander span,
        section[data-testid="stSidebar"] .stExpander label,
        section[data-testid="stSidebar"] .stExpander div { color:rgba(255,255,255,0.88) !important; }
        section[data-testid="stSidebar"] .stExpander textarea,
        section[data-testid="stSidebar"] .stExpander input {
            background-color:#0d1b3e !important;
            color:#fff !important; border:1px solid rgba(255,255,255,0.25) !important; }

        /* Expander header "Add / View Notes" always visible */
        section[data-testid="stSidebar"] details > summary,
        section[data-testid="stSidebar"] details > summary p,
        section[data-testid="stSidebar"] details > summary span,
        section[data-testid="stSidebar"] details > summary svg {
            color:rgba(255,255,255,0.88) !important;
            fill:rgba(255,255,255,0.88) !important; }
        /* All sidebar inputs/textareas: dark bg so white text is visible */
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] textarea {
            background-color:#0d1b3e !important;
            color:#ffffff !important;
            caret-color:#ffffff !important;
            border:1px solid rgba(255,255,255,0.25) !important; }
        section[data-testid="stSidebar"] input::placeholder,
        section[data-testid="stSidebar"] textarea::placeholder {
            color:rgba(255,255,255,0.4) !important; }
        /* Multiselect + selectbox containers: dark bg */
        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-baseweb="base-input"],
        section[data-testid="stSidebar"] [data-baseweb="input"] {
            background-color:#0d1b3e !important;
            border-color:rgba(255,255,255,0.25) !important; }
        section[data-testid="stSidebar"] [data-baseweb="select"] *,
        section[data-testid="stSidebar"] [data-baseweb="base-input"] * {
            color:#ffffff !important; }
        /* Hide the stray text cursor inside multiselect */
        section[data-testid="stSidebar"] [data-baseweb="select"] [contenteditable],
        section[data-testid="stSidebar"] [role="combobox"] input {
            caret-color: transparent !important;
            color: transparent !important;
            width: 2px !important; }
        /* Sidebar buttons: orange bg, white text */
        section[data-testid="stSidebar"] .stButton > button {
            background:rgba(249,115,22,0.9) !important;
            color:#ffffff !important; border:none !important; }
        section[data-testid="stSidebar"] .stButton > button * {
            color:#ffffff !important; }
        div[role="radiogroup"] { gap:2px !important; }
        div[role="radiogroup"] > label {
            display:flex !important; align-items:center !important;
            padding:11px 16px !important; margin:1px 0 !important;
            border-radius:0 !important; font-size:17px !important; font-weight:600 !important;
            color:rgba(255,255,255,0.72) !important; border-left:3px solid transparent !important;
            transition:all 0.15s ease !important; cursor:pointer !important;
            width:100% !important; background:transparent !important; }
        div[role="radiogroup"] > label p {
            font-size:17px !important; font-weight:600 !important;
            color:rgba(255,255,255,0.72) !important; margin:0 !important; }
        div[role="radiogroup"] > label:hover {
            background:rgba(255,255,255,0.07) !important;
            color:rgba(255,255,255,0.95) !important;
            border-left:3px solid rgba(249,115,22,0.55) !important; }
        div[role="radiogroup"] > label:hover p { color:rgba(255,255,255,0.95) !important; }
        div[role="radiogroup"] > label[data-checked="true"],
        div[role="radiogroup"] > label:has(input:checked) {
            background:linear-gradient(90deg,rgba(249,115,22,0.28),rgba(249,115,22,0.10)) !important;
            color:#fff !important; font-weight:800 !important;
            border-left:4px solid #F97316 !important; border-radius:0 8px 8px 0 !important;
            box-shadow:inset 0 0 16px rgba(249,115,22,0.08),2px 0 12px rgba(249,115,22,0.2) !important; }
        div[role="radiogroup"] > label[data-checked="true"] p,
        div[role="radiogroup"] > label:has(input:checked) p {
            color:#fff !important; font-weight:800 !important; font-size:17px !important; }
        div[role="radiogroup"] > label > div:first-child { display:none !important; }

        /* General labels inside sidebar */
        label { color:rgba(255,255,255,0.88) !important; font-weight:700 !important; font-size:14px !important; }

        /* Buttons */
        .stButton > button { background:rgba(249,115,22,0.85); color:white !important; border-radius:8px;
            font-weight:700 !important; font-size:13px !important; border:none; padding:6px 14px; }
        .stButton > button:hover { background:#F97316; color:white !important; }
        .stDownloadButton button { background:#F97316; color:white !important; border-radius:8px;
            padding:8px 16px; font-weight:700 !important; width:100%; }
        .streamlit-expanderHeader { color:rgba(255,255,255,0.88) !important; font-weight:700 !important; }
        .stCaption { color:rgba(255,255,255,0.55) !important; }
        .stMultiSelect span { color:rgba(255,255,255,0.88) !important; }
        </style>""", unsafe_allow_html=True)
    else:
        st.markdown("""<style>
        .stApp { background-color:#F8FAFC; color:#1E293B; }
        section[data-testid="stSidebar"] {
            background:linear-gradient(180deg,#0F2456,#0F1F48 40%,#0A1628) !important;
            padding-top:0 !important; border-right:none !important;
            box-shadow:4px 0 24px rgba(15,36,86,0.25) !important; }
        section[data-testid="stSidebar"] > div { padding-top:0 !important; }
        .sb-brand { background:linear-gradient(135deg,#F97316,#EA580C);
            margin:0; padding:20px 20px 16px; border-bottom:1px solid rgba(255,255,255,0.1); }
        .sb-title { font-size:17px; font-weight:900; color:#fff; margin-bottom:2px; line-height:1.3; }
        .sb-sub   { font-size:11px; color:rgba(255,255,255,0.75); }
        .sb-hdr   { font-size:10px; font-weight:800; color:rgba(255,255,255,0.45);
                    margin:16px 0 8px; text-transform:uppercase; letter-spacing:1.5px; padding:0 16px; }
        .sb-div   { height:1px; background:rgba(255,255,255,0.08); margin:12px 8px; }
        .ann-box  { background:rgba(255,255,255,0.06); border-left:4px solid #F97316;
                    padding:8px 12px; border-radius:6px; margin:4px 0;
                    font-size:12px; color:rgba(255,255,255,0.85); line-height:1.5; }
        .filter-badge { display:inline-block; background:rgba(249,115,22,0.15);
            border:1px solid #F97316; color:#FDBA74 !important; border-radius:20px;
            padding:2px 10px; font-size:11px; font-weight:700; margin:2px; }
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div { color:rgba(255,255,255,0.85) !important; }
        header[data-testid="stHeader"] {
            background-color:#fff !important; border-bottom:1px solid #E2E8F0 !important; }
        header[data-testid="stHeader"] button svg,
        header[data-testid="stHeader"] svg { fill:#1E293B !important; }
        header[data-testid="stHeader"] span,
        header[data-testid="stHeader"] p { color:#1E293B !important; }
        section[data-testid="stSidebar"] .stExpander p,
        section[data-testid="stSidebar"] .stExpander span,
        section[data-testid="stSidebar"] .stExpander label,
        section[data-testid="stSidebar"] .stExpander div { color:rgba(255,255,255,0.85) !important; }
        section[data-testid="stSidebar"] .stExpander textarea,
        section[data-testid="stSidebar"] .stExpander input {
            background-color:#0d1b3e !important;
            color:#fff !important; border:1px solid rgba(255,255,255,0.25) !important; }

        /* Expander header "Add / View Notes" always visible */
        section[data-testid="stSidebar"] details > summary,
        section[data-testid="stSidebar"] details > summary p,
        section[data-testid="stSidebar"] details > summary span,
        section[data-testid="stSidebar"] details > summary svg {
            color:rgba(255,255,255,0.88) !important;
            fill:rgba(255,255,255,0.88) !important; }
        /* All sidebar inputs/textareas: dark bg so white text is visible */
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] textarea {
            background-color:#0d1b3e !important;
            color:#ffffff !important;
            caret-color:#ffffff !important;
            border:1px solid rgba(255,255,255,0.25) !important; }
        section[data-testid="stSidebar"] input::placeholder,
        section[data-testid="stSidebar"] textarea::placeholder {
            color:rgba(255,255,255,0.4) !important; }
        /* Multiselect + selectbox containers: dark bg */
        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-baseweb="base-input"],
        section[data-testid="stSidebar"] [data-baseweb="input"] {
            background-color:#0d1b3e !important;
            border-color:rgba(255,255,255,0.25) !important; }
        section[data-testid="stSidebar"] [data-baseweb="select"] *,
        section[data-testid="stSidebar"] [data-baseweb="base-input"] * {
            color:#ffffff !important; }
        /* Hide the stray text cursor inside multiselect */
        section[data-testid="stSidebar"] [data-baseweb="select"] [contenteditable],
        section[data-testid="stSidebar"] [role="combobox"] input {
            caret-color: transparent !important;
            color: transparent !important;
            width: 2px !important; }
        /* Sidebar buttons: orange bg, white text */
        section[data-testid="stSidebar"] .stButton > button {
            background:rgba(249,115,22,0.9) !important;
            color:#ffffff !important; border:none !important; }
        section[data-testid="stSidebar"] .stButton > button * {
            color:#ffffff !important; }
        div[role="radiogroup"] { gap:2px !important; }
        div[role="radiogroup"] > label {
            display:flex !important; align-items:center !important;
            padding:11px 16px !important; margin:1px 0 !important;
            border-radius:0 !important; font-size:17px !important; font-weight:600 !important;
            color:rgba(255,255,255,0.6) !important; border-left:3px solid transparent !important;
            transition:all 0.15s ease !important; cursor:pointer !important;
            width:100% !important; background:transparent !important; }
        div[role="radiogroup"] > label p {
            font-size:17px !important; font-weight:600 !important;
            color:rgba(255,255,255,0.6) !important; margin:0 !important; }
        div[role="radiogroup"] > label:hover {
            background:rgba(255,255,255,0.07) !important;
            color:rgba(255,255,255,0.9) !important;
            border-left:3px solid rgba(249,115,22,0.5) !important; }
        div[role="radiogroup"] > label:hover p { color:rgba(255,255,255,0.9) !important; }
        div[role="radiogroup"] > label[data-checked="true"],
        div[role="radiogroup"] > label:has(input:checked) {
            background:linear-gradient(90deg,rgba(249,115,22,0.2),rgba(249,115,22,0.08)) !important;
            color:#fff !important; font-weight:800 !important;
            border-left:4px solid #F97316 !important; border-radius:0 8px 8px 0 !important; }
        div[role="radiogroup"] > label[data-checked="true"] p,
        div[role="radiogroup"] > label:has(input:checked) p {
            color:#fff !important; font-weight:800 !important; font-size:17px !important; }
        div[role="radiogroup"] > label > div:first-child { display:none !important; }
        label { color:rgba(255,255,255,0.85) !important; font-weight:700 !important; font-size:14px !important; }
        .stButton > button { background:rgba(249,115,22,0.85); color:white !important; border-radius:8px;
            font-weight:700 !important; font-size:13px !important; border:none; padding:6px 14px; }
        .stButton > button:hover { background:#F97316; color:white !important; }
        .stDownloadButton button { background:#F97316; color:white !important; border-radius:8px;
            padding:8px 16px; font-weight:700 !important; width:100%; }
        .stCaption { color:rgba(255,255,255,0.5) !important; }
        .stMultiSelect span { color:rgba(255,255,255,0.85) !important; }
        </style>""", unsafe_allow_html=True)


apply_theme()

# ── Auto-refresh ───────────────────────────────────────────────────────────────
if st.session_state.auto_refresh:
    elapsed = time.time() - st.session_state.last_refresh
    if elapsed >= st.session_state.refresh_interval:
        st.session_state.last_refresh = time.time()
        st.cache_data.clear()
        st.session_state.pop("_raw", None)
        st.rerun()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div class='sb-brand'>
        <div class='sb-title'>Healthcare Intelligence</div>
        <div class='sb-sub'>Analytics & Strategic Planning Platform</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div class='sb-div'></div>", unsafe_allow_html=True)

    # Theme / live controls
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        dm = st.session_state.dark_mode
        st.markdown(
            f"<div style='font-size:12px;font-weight:800;margin-top:9px;"
            f"color:rgba(255,255,255,0.6);'>{'Light' if dm else 'Dark'} mode</div>",
            unsafe_allow_html=True)
    with c2:
        if st.button("Toggle", key="theme_btn"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    with c3:
        if st.button("Stop" if st.session_state.auto_refresh else "Live", key="refresh_btn"):
            st.session_state.auto_refresh = not st.session_state.auto_refresh
            st.session_state.last_refresh = time.time()
            st.rerun()

    if st.session_state.auto_refresh:
        remaining = max(0, int(st.session_state.refresh_interval -
                                (time.time() - st.session_state.last_refresh)))
        st.markdown(f"<p style='color:rgba(255,255,255,0.85);font-size:12px;margin:2px 0 4px 0;'>Live mode — refreshing in {remaining}s</p>", unsafe_allow_html=True)
        iv     = {"30 sec": 30, "1 min": 60, "2 min": 120, "5 min": 300}
        chosen = st.selectbox("Interval", list(iv.keys()), index=1,
                              key="iv_sel", label_visibility="collapsed")
        st.session_state.refresh_interval = iv[chosen]
    else:
        st.markdown("<p style='color:rgba(255,255,255,0.85);font-size:12px;margin:2px 0 4px 0;'>Static mode — data not auto-refreshing</p>", unsafe_allow_html=True)

    st.markdown("<div class='sb-div'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sb-hdr'>Navigation</div>", unsafe_allow_html=True)

    chosen_idx = st.radio(
        "page_nav",
        options=list(range(len(PAGE_NAMES))),
        format_func=lambda i: PAGE_NAMES[i],
        index=st.session_state.current_page,
        label_visibility="collapsed",
        key="page_radio",
    )
    if chosen_idx != st.session_state.current_page:
        st.session_state.current_page = chosen_idx
    active_page = PAGE_NAMES[st.session_state.current_page]

    # ── Global Filters ─────────────────────────────────────────────────────────
    st.markdown("<div class='sb-div'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sb-hdr'>Global Filters</div>", unsafe_allow_html=True)

    # ── Reset flag: checked BEFORE widgets render so they pick up cleared values ──
    if st.session_state.get("_do_reset", False):
        st.session_state["_gf_start"]  = _min_date
        st.session_state["_gf_end"]    = _max_date
        st.session_state["_gf_depts"]  = ["All Departments"]
        st.session_state["_gf_status"] = ["All Status"]
        st.session_state["ui_depts"]   = ["All Departments"]
        st.session_state["ui_status"]  = ["All Status"]
        st.session_state["_do_reset"]  = False

    # ── Date Range ────────────────────────────────────────────────────────────
    date_range = st.date_input(
        "Date Range",
        value=(st.session_state["_gf_start"], st.session_state["_gf_end"]),
        min_value=_min_date, max_value=_max_date,
        key="ui_date_range",
    )
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        st.session_state["_gf_start"] = date_range[0]
        st.session_state["_gf_end"]   = date_range[1]

    # ── Department Filter ─────────────────────────────────────────────────────
    if "ui_depts" not in st.session_state:
        st.session_state["ui_depts"] = st.session_state["_gf_depts"]

    sel_depts = st.multiselect(
        "Departments", options=_dept_opts,
        key="ui_depts",
    )
    st.session_state["_gf_depts"] = sel_depts if sel_depts else ["All Departments"]

    # ── Appointment Status Filter ─────────────────────────────────────────────
    if "ui_status" not in st.session_state:
        st.session_state["ui_status"] = st.session_state["_gf_status"]

    sel_status = st.multiselect(
        "Appointment Status", options=_status_opts,
        key="ui_status",
    )
    st.session_state["_gf_status"] = sel_status if sel_status else ["All Status"]

    # ── Active filter badge summary + Reset button ────────────────────────────
    active_filters = []
    if st.session_state["_gf_start"] != _min_date or st.session_state["_gf_end"] != _max_date:
        active_filters.append(
            f"{st.session_state['_gf_start'].strftime('%d %b %y')} → "
            f"{st.session_state['_gf_end'].strftime('%d %b %y')}")
    if "All Departments" not in st.session_state["_gf_depts"] and st.session_state["_gf_depts"]:
        active_filters.append(f"{len(st.session_state['_gf_depts'])} dept(s)")
    if "All Status" not in st.session_state["_gf_status"] and st.session_state["_gf_status"]:
        active_filters.append(f"{', '.join(st.session_state['_gf_status'])}")

    if active_filters:
        badges = "".join(f"<span class='filter-badge'>{f}</span>" for f in active_filters)
        st.markdown(f"<div style='margin-top:6px;'>{badges}</div>", unsafe_allow_html=True)
        if st.button("Reset Filters", key="reset_filters"):
            # Set flag — actual reset happens at top of next run, before widgets render
            st.session_state["_do_reset"] = True
            st.rerun()
    else:
        st.caption("No filters active — showing all data")

    # ── Page Notes ─────────────────────────────────────────────────────────────
    st.markdown("<div class='sb-div'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sb-hdr'>Page Notes</div>", unsafe_allow_html=True)

    if active_page not in st.session_state.annotations:
        st.session_state.annotations[active_page] = []

    with st.expander("Add / View Notes", expanded=False):
        author = st.text_input("Your name", key="ann_author", placeholder="e.g. Dr. Sharma")
        ntext  = st.text_area("Note", key="ann_text",
                              placeholder="e.g. Spike caused by seasonal flu", height=70)
        if st.button("Save Note", key="save_ann"):
            if ntext.strip():
                st.session_state.annotations[active_page].append({
                    "author": author.strip() or "Anonymous",
                    "text":   ntext.strip(),
                    "ts":     pd.Timestamp.now().strftime("%d %b %Y, %H:%M"),
                })
                st.success("Saved.")
                st.rerun()
        notes = st.session_state.annotations[active_page]
        if notes:
            st.markdown(f"**{len(notes)} note(s) on this page:**")
            for i, n in enumerate(reversed(notes)):
                ri = len(notes) - 1 - i
                st.markdown(
                    f"<div class='ann-box'><b>{n['author']}</b> "
                    f"<span style='opacity:0.65'>· {n['ts']}</span><br>{n['text']}</div>",
                    unsafe_allow_html=True)
                if st.button("Delete", key=f"del_ann_{active_page}_{ri}"):
                    st.session_state.annotations[active_page].pop(ri)
                    st.rerun()
        else:
            st.caption("No notes yet.")

    # ── Data Export ────────────────────────────────────────────────────────────
    st.markdown("<div class='sb-div'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sb-hdr'>Data Export</div>", unsafe_allow_html=True)
    try:
        with open(DATA_PATH, "rb") as f:
            st.download_button(
                "Download Full Dataset", data=f,
                file_name="Hospital_Dataset.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
    except FileNotFoundError:
        st.warning("Dataset file not found.")

# ══════════════════════════════════════════════════════════════════════════════
# APPLY FILTERS ONCE — pass results as arguments to the active page
# This is the key: filtering happens HERE, pages just receive clean data
# ══════════════════════════════════════════════════════════════════════════════
filtered = apply_filters(
    raw         = _raw,
    start_date  = st.session_state["_gf_start"],
    end_date    = st.session_state["_gf_end"],
    dept_list   = st.session_state["_gf_depts"],
    status_list = st.session_state["_gf_status"],
)

# ── Route to active page ───────────────────────────────────────────────────────
{
    "Executive Overview":                     page1,
    "Patient Demographics & Demand Analysis": page2,
    "Clinical & Disease Intelligence":        page3,
    "Operational Efficiency & Capacity":      page4,
    "Staffing & Resource Optimization":       page5,
    "Intelligence & Planning":                page6,
}[active_page].run(filtered)