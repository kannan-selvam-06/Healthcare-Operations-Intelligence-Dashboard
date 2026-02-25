import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def run():
    dark_mode = st.session_state.get('dark_mode', False)

    if dark_mode:
        text_color     = '#FAFAFA'
        secondary_text = '#94A3B8'
        PRIMARY_BLUE   = '#60A5FA'
        SECONDARY_BLUE = '#3B82F6'
        CORAL          = '#F87171'
        SUCCESS_GREEN  = '#34D399'
        WARNING_AMBER  = '#FBBF24'
        PURPLE         = '#A78BFA'
        card_bg        = '#1E2A3A'
        bdr            = '#334155'
        highlight_bg   = '#0F172A'
    else:
        text_color     = '#1E293B'
        secondary_text = '#64748B'
        PRIMARY_BLUE   = '#1E40AF'
        SECONDARY_BLUE = '#3B82F6'
        CORAL          = '#DC2626'
        SUCCESS_GREEN  = '#059669'
        WARNING_AMBER  = '#D97706'
        PURPLE         = '#7C3AED'
        card_bg        = '#F0F9FF'
        bdr            = '#E2E8F0'
        highlight_bg   = '#EFF6FF'

    EXCEL_PATH  = "data/dataFinal.xlsx"
    MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    YEAR_COLORS = {2024: SECONDARY_BLUE, 2025: CORAL}

    TICK_FONT  = dict(size=14, color=text_color, family="Arial Black")
    TITLE_FONT = dict(size=16, color=text_color, family="Arial Black")
    GRID_COLOR = 'rgba(128,128,128,0.2)'

    st.markdown(f"""
    <style>
        .page-title {{
            font-size: 48px; font-weight: 900; text-align: center;
            background: linear-gradient(135deg, {PRIMARY_BLUE} 0%, {PURPLE} 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 10px; letter-spacing: -0.5px;
        }}
        .page-subtitle {{
            font-size: 19px; font-weight: 500; color: {secondary_text};
            text-align: center; margin-bottom: 36px;
        }}
        .kpi-card {{
            background: linear-gradient(135deg, {PRIMARY_BLUE} 0%, {SECONDARY_BLUE} 100%);
            padding: 26px; border-radius: 16px; text-align: center;
            box-shadow: 0 8px 20px rgba(0,0,0,0.18); transition: transform 0.3s ease;
        }}
        .kpi-card:hover {{ transform: translateY(-6px); }}
        .kpi-card h3 {{
            font-size: 16px !important; font-weight: 800 !important;
            color: rgba(255,255,255,0.9) !important; margin-bottom: 10px;
            text-transform: uppercase; letter-spacing: 1.2px;
        }}
        .kpi-card h1 {{
            font-size: 42px !important; margin: 0; font-weight: 900 !important; color: white !important;
        }}
        .section-header {{
            font-size: 24px; font-weight: 800; color: {text_color};
            margin: 45px 0 20px 0; padding-bottom: 12px;
            border-bottom: 4px solid {PRIMARY_BLUE};
        }}
        .insight-box {{
            background: {card_bg}; border: 1px solid {bdr};
            border-left: 5px solid {PRIMARY_BLUE}; border-radius: 10px;
            padding: 16px 20px; margin-bottom: 10px;
        }}
        .insight-title {{
            font-size: 16px; font-weight: 800; color: {PRIMARY_BLUE}; margin-bottom: 6px;
        }}
        .insight-text {{
            font-size: 15px; color: {secondary_text}; line-height: 1.6;
        }}
        .stat-pill {{
            display: inline-block; background: {highlight_bg}; border: 1px solid {bdr};
            border-radius: 20px; padding: 4px 14px; margin: 4px;
            font-size: 13px; font-weight: 700; color: {text_color};
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='page-title'>Healthcare Operations Intelligence Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Real-time Operational Intelligence & Strategic Insights</div>", unsafe_allow_html=True)

    @st.cache_data
    def load_healthcare_data(path):
        sheets = pd.read_excel(path, sheet_name=None)
        sheets = {k.strip().lower(): v for k, v in sheets.items()}
        dfs = [sheets[name].copy() for name in ["patients","appointment","surgeryrecord","roomrecords","room","bedrecords","department"]]
        for df in dfs:
            df.columns = df.columns.str.strip().str.lower()
        if "appointment_date" in dfs[1].columns:
            dfs[1]["appointment_date"] = pd.to_datetime(dfs[1]["appointment_date"], errors="coerce")
        if "admission_date" in dfs[3].columns:
            dfs[3]["admission_date"] = pd.to_datetime(dfs[3]["admission_date"], errors="coerce")
        return dfs

    pts, apps, surg, room_recs, rooms, bed, depts = load_healthcare_data(EXCEL_PATH)

    apps["month"]      = apps["appointment_date"].dt.month
    apps["month_name"] = apps["appointment_date"].dt.strftime("%b")
    apps["year"]       = apps["appointment_date"].dt.year

    monthly_counts = apps.groupby(["year","month","month_name"]).size().reset_index(name="Count").sort_values(["year","month"])
    valid_years    = apps.groupby("year")["month"].nunique()
    valid_years    = valid_years[valid_years >= 6].index.tolist()
    monthly_counts = monthly_counts[monthly_counts["year"].isin(valid_years)]

    # Use full data — no top-of-page filters
    apps_f = apps.copy()
    dept_flow_all = room_recs.merge(rooms, on="room_no", how="left").merge(depts, on="dept_id", how="left")
    dept_flow_f   = dept_flow_all.copy()

    # ── KPIs ─────────────────────────────────────────────────────────────────
    total_patients    = pts["patient_id"].nunique()
    total_appointments= apps_f["appointment_id"].nunique()
    admitted_patients = pd.concat([room_recs["patient_id"], bed["patient_id"]]).dropna()
    total_admissions  = admitted_patients.nunique()
    cancel_count      = apps_f["appointment_status"].astype(str).str.lower().isin(["cancelled","canceled"]).sum()
    cancel_rate       = round((cancel_count / max(total_appointments, 1)) * 100, 2)

    st.markdown(f"""
    <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:24px;margin-bottom:36px;'>
        <div class='kpi-card'><h3>Total Patients</h3><h1>{total_patients:,}</h1></div>
        <div class='kpi-card'><h3>Appointments</h3><h1>{total_appointments:,}</h1></div>
        <div class='kpi-card'><h3>Admissions</h3><h1>{total_admissions:,}</h1></div>
        <div class='kpi-card'><h3>Cancellation Rate</h3><h1>{cancel_rate}%</h1></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Patient Flow Trends ────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Patient Flow Trends</div>", unsafe_allow_html=True)

    if "appointment_date" in apps_f.columns and "admission_date" in room_recs.columns:
        flow_apps = apps_f.dropna(subset=["appointment_date"]).groupby(apps_f["appointment_date"].dt.to_period("M")).size().rename("Appointments")
        flow_adm  = room_recs.dropna(subset=["admission_date"]).groupby(room_recs["admission_date"].dt.to_period("M")).size().rename("Admissions")
        flow_data = pd.concat([flow_apps, flow_adm], axis=1).fillna(0)
        flow_data.index = flow_data.index.to_timestamp().strftime('%b %Y')

        x_vals     = list(flow_data.index)
        show_every = max(1, len(x_vals) // 6)
        tick_vals  = x_vals[::show_every]

        fig_flow = go.Figure()
        fig_flow.add_trace(go.Scatter(
            x=flow_data.index, y=flow_data["Appointments"], mode='lines+markers', name='Appointments',
            line=dict(color=PRIMARY_BLUE, width=5),
            marker=dict(size=12, color=PRIMARY_BLUE, line=dict(width=3, color='white')),
            hovertemplate='<b>%{x}</b><br>Appointments: %{y:,}<extra></extra>'
        ))
        fig_flow.add_trace(go.Scatter(
            x=flow_data.index, y=flow_data["Admissions"], mode='lines+markers', name='Admissions',
            line=dict(color=CORAL, width=5),
            marker=dict(size=12, color=CORAL, line=dict(width=3, color='white')),
            hovertemplate='<b>%{x}</b><br>Admissions: %{y:,}<extra></extra>'
        ))
        # Moving average REMOVED per user request

        fig_flow.update_xaxes(tickmode='array', tickvals=tick_vals, tickangle=-45)
        fig_flow.update_layout(
            xaxis_title="<b>Month</b>", yaxis_title="<b>Patient Count</b>",
            hovermode="x unified", height=480,
            font=dict(size=14, color=text_color, family="Arial Black"),
            legend=dict(orientation="h", y=1.04, x=0.5, xanchor="center",
                        font=dict(size=13, color=text_color, family="Arial Black"),
                        bgcolor='rgba(0,0,0,0)'),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=60, b=80, l=70, r=40),
            xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, tickfont=TICK_FONT, title_font=TITLE_FONT),
            yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, tickfont=TICK_FONT, title_font=TITLE_FONT)
        )
        st.plotly_chart(fig_flow, use_container_width=True, config={'displayModeBar': True})

    # ── Appointment Outcomes ──────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Appointment Outcomes</div>", unsafe_allow_html=True)

    oc1, oc2 = st.columns([3, 2], gap="large")
    with oc1:
        if "appointment_status" in apps_f.columns:
            status_counts = apps_f["appointment_status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            colors = [PRIMARY_BLUE, SUCCESS_GREEN, WARNING_AMBER, '#94A3B8']
            fig_pie = go.Figure(data=[go.Pie(
                labels=status_counts["Status"], values=status_counts["Count"], hole=0.5,
                marker=dict(colors=colors, line=dict(color='white', width=3)),
                textposition='inside', textinfo='label+percent',
                textfont=dict(size=14, family="Arial Black", color='white'),
                hovertemplate='<b>%{label}</b><br>Count: %{value:,}<br>%{percent}<extra></extra>',
                insidetextorientation='radial'
            )])
            fig_pie.update_layout(
                height=420, showlegend=True,
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=14, color=text_color, family="Arial Black"),
                legend=dict(orientation="v", y=0.5, x=1.02, xanchor="left",
                            font=dict(size=14, family="Arial Black", color=text_color),
                            bgcolor='rgba(0,0,0,0)'),
                margin=dict(t=20, b=20, l=40, r=160)
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

    with oc2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:18px;font-weight:800;color:{text_color};margin-bottom:14px;'>Status Breakdown</div>", unsafe_allow_html=True)
        if "appointment_status" in apps_f.columns:
            sc = apps_f["appointment_status"].value_counts()
            for s, c in sc.items():
                pct = round(c / len(apps_f) * 100, 1)
                st.markdown(f"""<div style='display:flex;justify-content:space-between;
                    padding:12px 18px;border-radius:10px;margin:6px 0;
                    background:{card_bg};border:1px solid {bdr};'>
                    <span style='font-weight:700;color:{text_color};font-size:16px;'>{s}</span>
                    <span style='font-weight:800;color:{PRIMARY_BLUE};font-size:16px;'>{c:,} ({pct}%)</span>
                </div>""", unsafe_allow_html=True)

    # ── Department Demand ─────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Department Demand</div>", unsafe_allow_html=True)

    dept_chart = dept_flow_f.groupby("dept_name").size().reset_index(name="Admissions").sort_values("Admissions", ascending=True)

    dc1, dc2 = st.columns([3, 1], gap="large")
    with dc1:
        fig_dept = go.Figure(go.Bar(
            x=dept_chart["Admissions"], y=dept_chart["dept_name"], orientation="h",
            marker=dict(
                color=dept_chart["Admissions"],
                colorscale=[[0, SECONDARY_BLUE], [1, PRIMARY_BLUE]],
                cornerradius=8,
                line=dict(color='white', width=1)
            ),
            hovertemplate='<b>%{y}</b><br>Admissions: %{x:,}<extra></extra>'
        ))
        fig_dept.update_layout(
            height=500, showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="<b>Number of Admissions</b>", yaxis_title="",
            xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, tickfont=TICK_FONT, title_font=TITLE_FONT),
            yaxis=dict(showgrid=False, tickfont=TICK_FONT),
            margin=dict(t=20, b=60, l=30, r=30)
        )
        st.plotly_chart(fig_dept, use_container_width=True, config={'displayModeBar': False})

    with dc2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if len(dept_chart) > 0:
            top_d  = dept_chart.iloc[-1]
            low_d  = dept_chart.iloc[0]
            avg_ad = dept_chart["Admissions"].mean()
            st.markdown(f"""<div class='insight-box'>
                <div class='insight-title'>Top Department</div>
                <div class='insight-text'><b>{top_d['dept_name']}</b> leads with {int(top_d['Admissions']):,} admissions.</div>
            </div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class='insight-box'>
                <div class='insight-title'>Lowest Volume</div>
                <div class='insight-text'><b>{low_d['dept_name']}</b> has {int(low_d['Admissions']):,} admissions.</div>
            </div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class='insight-box'>
                <div class='insight-title'>Avg per Dept</div>
                <div class='insight-text'>Average admissions per department: <b>{avg_ad:.0f}</b>.</div>
            </div>""", unsafe_allow_html=True)

    # ── Peak Appointment Months ───────────────────────────────────────────────
    st.markdown("<div class='section-header'>Peak Appointment Months</div>", unsafe_allow_html=True)

    mc_f = apps_f.groupby(["year","month","month_name"]).size().reset_index(name="Count").sort_values(["year","month"])
    mc_f = mc_f[mc_f["year"].isin(valid_years)]

    fig_months = go.Figure()
    for year in sorted(mc_f["year"].unique()):
        yd = mc_f[mc_f["year"] == year].copy()
        yd["month_name"] = pd.Categorical(yd["month_name"], categories=MONTH_ORDER, ordered=True)
        yd = yd.sort_values("month_name")
        fig_months.add_trace(go.Bar(
            name=str(year), x=yd["month_name"], y=yd["Count"],
            marker=dict(color=YEAR_COLORS.get(year, "#95A5A6"), opacity=0.88,
                        cornerradius=6, line=dict(color='white', width=1)),
            hovertemplate=f"<b>{year}</b><br>%{{x}}: %{{y:,}}<extra></extra>"
        ))
    fig_months.update_layout(
        barmode="group",
        xaxis_title="<b>Month</b>", yaxis_title="<b>Appointments</b>",
        xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT),
        yaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        height=450, margin=dict(l=20, r=20, t=30, b=50),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(font=dict(size=14, family="Arial Black", color=text_color),
                    bgcolor='rgba(0,0,0,0)')
    )
    st.plotly_chart(fig_months, use_container_width=True, config={'displayModeBar': True})

    # ── Appointment Completion Rate ───────────────────────────────────────────
    st.markdown("<div class='section-header'>Appointment Completion Rate</div>", unsafe_allow_html=True)

    if "appointment_date" in apps_f.columns and "appointment_status" in apps_f.columns:
        apps_f2 = apps_f.copy()
        apps_f2["month_period"] = apps_f2["appointment_date"].dt.to_period("M")
        monthly_total     = apps_f2.groupby("month_period").size()
        monthly_completed = apps_f2[apps_f2["appointment_status"].astype(str).str.lower()=="completed"].groupby("month_period").size()
        cr_data           = ((monthly_completed / monthly_total) * 100).fillna(0).reset_index()
        cr_data.columns   = ["Month","Completion Rate (%)"]
        cr_data["Month"]  = cr_data["Month"].dt.to_timestamp().dt.strftime('%b %Y')

        x_vals     = cr_data["Month"].tolist()
        show_every = max(1, len(x_vals) // 6)
        tick_vals  = x_vals[::show_every]

        # Fixed y-axis from 40 to ~85 so variation is clearly visible
        data_max = cr_data["Completion Rate (%)"].max()
        y_min = 40
        y_max = max(85, data_max + 3)

        fig_cr = go.Figure()
        fig_cr.add_hrect(y0=80, y1=y_max,
                         fillcolor=SUCCESS_GREEN, opacity=0.05, line_width=0)
        fig_cr.add_hline(y=80, line_width=2, line_dash="dash", line_color=SUCCESS_GREEN,
                         annotation_text="80% Target", annotation_position="top right",
                         annotation_font=dict(size=12, color=SUCCESS_GREEN, family="Arial Black"))
        fig_cr.add_trace(go.Scatter(
            x=cr_data["Month"], y=cr_data["Completion Rate (%)"],
            mode='lines+markers',
            line=dict(color=SUCCESS_GREEN, width=5),
            marker=dict(size=12, color=cr_data["Completion Rate (%)"],
                        colorscale=[[0,CORAL],[0.5,WARNING_AMBER],[1,SUCCESS_GREEN]],
                        cmin=60, cmax=85,
                        line=dict(width=3, color='white'), showscale=False),
            hovertemplate='<b>%{x}</b><br>Completion: %{y:.1f}%<extra></extra>'
        ))
        fig_cr.update_xaxes(tickmode='array', tickvals=tick_vals, tickangle=-45)
        fig_cr.update_layout(
            xaxis_title="<b>Month</b>", yaxis_title="<b>Completion Rate (%)</b>",
            hovermode="x unified", showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            height=450, font=dict(size=14, color=text_color, family="Arial Black"),
            margin=dict(t=40, b=80, l=60, r=40),
            xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, tickfont=TICK_FONT, title_font=TITLE_FONT),
            yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, tickfont=TICK_FONT, title_font=TITLE_FONT,
                       range=[y_min, y_max],
                       dtick=10)
        )
        st.plotly_chart(fig_cr, use_container_width=True, config={'displayModeBar': True})

    st.markdown("<br><br>", unsafe_allow_html=True)