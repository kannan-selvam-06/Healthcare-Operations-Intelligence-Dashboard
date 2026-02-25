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

from myPages import page1, page2, page3, page4, page5, page6

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
        section[data-testid="stSidebar"] { background-color: #1C1F26; padding-top: 16px; }
        .sb-title   { font-size:22px; font-weight:900; color:#60A5FA; margin-bottom:4px; }
        .sb-sub     { font-size:12px; color:#CBD5E1; margin-bottom:14px; }
        .sb-hdr     { font-size:12px; font-weight:800; color:#60A5FA; margin:14px 0 6px 0;
                      text-transform:uppercase; letter-spacing:1px; }
        .sb-div     { height:1px; background:#334155; margin:12px 0; }
        .ann-box    { background:#1E2A3A; border-left:4px solid #60A5FA; padding:8px 12px;
                      border-radius:6px; margin:4px 0; font-size:12px; color:#E2E8F0; line-height:1.5; }
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div { color:#F1F5F9 !important; }
        section[data-testid="stSidebar"] h3  { color:#60A5FA !important; }

        /* ── Topbar (deploy bar) theme fix — dark ── */
        header[data-testid="stHeader"] {
            background-color: #1C1F26 !important;
            border-bottom: 1px solid #334155 !important;
        }
        header[data-testid="stHeader"] button svg,
        header[data-testid="stHeader"] svg { fill: #F1F5F9 !important; }
        header[data-testid="stHeader"] span,
        header[data-testid="stHeader"] p { color: #F1F5F9 !important; }

        /* ── Page notes expander text — dark ── */
        section[data-testid="stSidebar"] .stExpander p,
        section[data-testid="stSidebar"] .stExpander span,
        section[data-testid="stSidebar"] .stExpander label,
        section[data-testid="stSidebar"] .stExpander div { color: #F1F5F9 !important; }
        section[data-testid="stSidebar"] .stExpander textarea,
        section[data-testid="stSidebar"] .stExpander input {
            background-color: #0F172A !important;
            color: #F1F5F9 !important;
            border: 1px solid #334155 !important;
        }
        section[data-testid="stSidebar"] .stExpander textarea::placeholder,
        section[data-testid="stSidebar"] .stExpander input::placeholder {
            color: #94A3B8 !important; opacity: 1 !important;
        }

        /* ── Navigation radio — dark mode ── */
        div[role="radiogroup"] > label {
            padding: 10px 14px;
            border-radius: 10px;
            font-size: 15px !important;
            font-weight: 700 !important;
            color: #CBD5E1 !important;
            margin-bottom: 3px;
            border-left: 4px solid transparent;
            transition: all 0.15s ease;
            cursor: pointer;
        }
        div[role="radiogroup"] > label p {
            font-size: 15px !important;
            font-weight: 700 !important;
            color: #CBD5E1 !important;
        }
        div[role="radiogroup"] > label:hover {
            background: #253047;
            color: #93C5FD !important;
        }
        div[role="radiogroup"] > label:hover p { color: #93C5FD !important; }

        /* ACTIVE page — strong blue gradient highlight */
        div[role="radiogroup"] > label[data-checked="true"],
        div[role="radiogroup"] > label:has(input:checked) {
            background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%) !important;
            color: #FFFFFF !important;
            font-weight: 900 !important;
            border-left: 4px solid #93C5FD !important;
            box-shadow: 0 3px 12px rgba(37,99,235,0.45) !important;
            border-radius: 10px !important;
        }
        div[role="radiogroup"] > label[data-checked="true"] p,
        div[role="radiogroup"] > label:has(input:checked) p {
            color: #FFFFFF !important;
            font-weight: 900 !important;
            font-size: 15px !important;
        }
        /* Radio dot on active */
        div[role="radiogroup"] > label:has(input:checked) div[data-testid="stMarkdownContainer"] {
            color: #FFFFFF !important;
        }

        label { color:#F1F5F9 !important; font-weight:700 !important; font-size:14px !important; }
        .stButton > button {
            background:#1E40AF; color:white !important; border-radius:8px;
            font-weight:700 !important; font-size:13px !important; border:none; padding:6px 14px;
        }
        .stButton > button:hover { background:#2563EB; color:white !important; }
        .stDownloadButton button {
            background:#2563EB; color:white !important; border-radius:8px;
            padding:8px 16px; font-weight:700 !important; width:100%;
        }
        .streamlit-expanderHeader { color:#F1F5F9 !important; font-weight:700 !important; }
        .stCaption { color:#94A3B8 !important; }
        .stMultiSelect span { color:#F1F5F9 !important; }
        </style>""", unsafe_allow_html=True)

    else:
        st.markdown("""<style>
        .stApp { background-color:#F8FAFC; color:#1E293B; }
        section[data-testid="stSidebar"] { background:#FFFFFF; padding-top:16px;
                                           border-right:1px solid #E2E8F0; }
        .sb-title { font-size:22px; font-weight:900; color:#1E3A8A; margin-bottom:4px; }
        .sb-sub   { font-size:12px; color:#64748B; margin-bottom:14px; }
        .sb-hdr   { font-size:12px; font-weight:800; color:#1E3A8A; margin:14px 0 6px 0;
                    text-transform:uppercase; letter-spacing:1px; }
        .sb-div   { height:1px; background:#E2E8F0; margin:12px 0; }
        .ann-box  { background:#F0F9FF; border-left:4px solid #1E40AF; padding:8px 12px;
                    border-radius:6px; margin:4px 0; font-size:12px; color:#1E293B; line-height:1.5; }

        /* ── Navigation radio — light mode ── */
        div[role="radiogroup"] > label {
            padding: 10px 14px;
            border-radius: 10px;
            font-size: 15px !important;
            font-weight: 700 !important;
            color: #475569 !important;
            margin-bottom: 3px;
            border-left: 4px solid transparent;
            transition: all 0.15s ease;
            cursor: pointer;
        }
        div[role="radiogroup"] > label p {
            font-size: 15px !important;
            font-weight: 700 !important;
            color: #475569 !important;
        }
        div[role="radiogroup"] > label:hover {
            background: #EFF6FF;
            color: #1D4ED8 !important;
        }
        div[role="radiogroup"] > label:hover p { color: #1D4ED8 !important; }

        /* ACTIVE page — strong blue gradient highlight */
        div[role="radiogroup"] > label[data-checked="true"],
        div[role="radiogroup"] > label:has(input:checked) {
            background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%) !important;
            color: #FFFFFF !important;
            font-weight: 900 !important;
            border-left: 4px solid #93C5FD !important;
            box-shadow: 0 3px 12px rgba(37,99,235,0.30) !important;
            border-radius: 10px !important;
        }
        div[role="radiogroup"] > label[data-checked="true"] p,
        div[role="radiogroup"] > label:has(input:checked) p {
            color: #FFFFFF !important;
            font-weight: 900 !important;
            font-size: 15px !important;
        }

        /* ── Topbar (deploy bar) theme fix — light ── */
        header[data-testid="stHeader"] {
            background-color: #FFFFFF !important;
            border-bottom: 1px solid #E2E8F0 !important;
        }
        header[data-testid="stHeader"] button svg,
        header[data-testid="stHeader"] svg { fill: #1E293B !important; }
        header[data-testid="stHeader"] span,
        header[data-testid="stHeader"] p { color: #1E293B !important; }

        /* ── Page notes expander text — light ── */
        section[data-testid="stSidebar"] .stExpander p,
        section[data-testid="stSidebar"] .stExpander span,
        section[data-testid="stSidebar"] .stExpander label,
        section[data-testid="stSidebar"] .stExpander div { color: #1E293B !important; }
        section[data-testid="stSidebar"] .stExpander textarea,
        section[data-testid="stSidebar"] .stExpander input {
            background-color: #FFFFFF !important;
            color: #1E293B !important;
            border: 1px solid #CBD5E1 !important;
        }
        section[data-testid="stSidebar"] .stExpander textarea::placeholder,
        section[data-testid="stSidebar"] .stExpander input::placeholder {
            color: #64748B !important; opacity: 1 !important;
        }

        label { color:#1E293B !important; font-weight:700 !important; font-size:14px !important; }
        .stButton > button {
            background:#1E40AF; color:white !important; border-radius:8px;
            font-weight:700 !important; font-size:13px !important; border:none; padding:6px 14px;
        }
        .stButton > button:hover { background:#2563EB; color:white !important; }
        .stDownloadButton button {
            background:#2563EB; color:white !important; border-radius:8px;
            padding:8px 16px; font-weight:700 !important; width:100%;
        }
        .stCaption { color:#64748B !important; }
        </style>""", unsafe_allow_html=True)

apply_theme()

# ── Auto-refresh logic ─────────────────────────────────────────────────────────
if st.session_state.auto_refresh:
    elapsed = time.time() - st.session_state.last_refresh
    if elapsed >= st.session_state.refresh_interval:
        st.session_state.last_refresh = time.time()
        st.cache_data.clear()
        st.rerun()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div class='sb-title'>Healthcare Operations Intelligence</div>", unsafe_allow_html=True)
    st.markdown("<div class='sb-sub'>Analytics and Strategic Planning Platform</div>", unsafe_allow_html=True)
    st.markdown("<div class='sb-div'></div>", unsafe_allow_html=True)

    # Theme / refresh controls
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        mode_txt   = "Dark mode" if not st.session_state.dark_mode else "Light mode"
        dm         = st.session_state.dark_mode
        mode_color = "#60A5FA" if dm else "#1E3A8A"
        st.markdown(
            f"<div style='font-size:12px;font-weight:800;margin-top:9px;color:{mode_color};'>"
            f"{mode_txt}</div>", unsafe_allow_html=True)
    with c2:
        if st.button("Toggle", key="theme_btn"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    with c3:
        live_lbl = "Stop" if st.session_state.auto_refresh else "Live"
        if st.button(live_lbl, key="refresh_btn"):
            st.session_state.auto_refresh = not st.session_state.auto_refresh
            st.session_state.last_refresh = time.time()
            st.rerun()

    if st.session_state.auto_refresh:
        remaining = max(0, int(st.session_state.refresh_interval -
                                (time.time() - st.session_state.last_refresh)))
        st.caption(f"Live mode — refreshing in {remaining}s")
        iv     = {"30 sec": 30, "1 min": 60, "2 min": 120, "5 min": 300}
        chosen = st.selectbox("Interval", list(iv.keys()), index=1,
                              key="iv_sel", label_visibility="collapsed")
        st.session_state.refresh_interval = iv[chosen]
    else:
        st.caption("Static mode — data not auto-refreshing")

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

    # ── Global filters ─────────────────────────────────────────────────────────
    st.markdown("<div class='sb-div'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sb-hdr'>Global Filters</div>", unsafe_allow_html=True)

    @st.cache_data(show_spinner=False)
    def _load_filter_meta():
        xls  = pd.ExcelFile("data/dataFinal.xlsx")
        dept = pd.read_excel(xls, "Department")
        appt = pd.read_excel(xls, "Appointment",
                             usecols=["appointment_Date", "appointment_status"])
        appt["appointment_Date"] = pd.to_datetime(appt["appointment_Date"], errors="coerce")
        return dept, appt

    try:
        dept_df, appt_df = _load_filter_meta()
        min_d = appt_df["appointment_Date"].min()
        max_d = appt_df["appointment_Date"].max()
        st.date_input("Date Range", value=(min_d, max_d),
                      min_value=min_d, max_value=max_d, key="global_date_filter")
        dept_opts = ["All Departments"] + sorted(dept_df["dept_Name"].dropna().unique().tolist())
        st.multiselect("Departments", dept_opts, default=["All Departments"],
                       key="global_dept_filter")
        stat_opts = ["All Status"] + sorted(appt_df["appointment_status"].dropna().unique().tolist())
        st.multiselect("Appointment Status", stat_opts, default=["All Status"],
                       key="global_status_filter")
    except Exception:
        st.caption("Filters unavailable — check data path.")

    # ── Page notes / annotation layer ─────────────────────────────────────────
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
                    unsafe_allow_html=True,
                )
                if st.button("Delete", key=f"del_ann_{active_page}_{ri}"):
                    st.session_state.annotations[active_page].pop(ri)
                    st.rerun()
        else:
            st.caption("No notes yet.")

    # ── Data export ────────────────────────────────────────────────────────────
    st.markdown("<div class='sb-div'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sb-hdr'>Data Export</div>", unsafe_allow_html=True)
    try:
        with open("data/dataFinal.xlsx", "rb") as f:
            st.download_button("Download Full Dataset", data=f,
                               file_name="Hospital_Dataset.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
    except FileNotFoundError:
        st.warning("Dataset file not found.")

# ── Route to active page ───────────────────────────────────────────────────────
{
    "Executive Overview":                     page1,
    "Patient Demographics & Demand Analysis": page2,
    "Clinical & Disease Intelligence":        page3,
    "Operational Efficiency & Capacity":      page4,
    "Staffing & Resource Optimization":       page5,
    "Intelligence & Planning":                page6,
}[active_page].run()