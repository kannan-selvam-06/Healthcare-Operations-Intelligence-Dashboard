import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def run():
    dark_mode = st.session_state.get('dark_mode', False)

    if dark_mode:
        text_color     = '#FAFAFA'
        secondary_text = '#94A3B8'
        PRIMARY_BLUE   = '#60A5FA'
        SECONDARY_BLUE = '#3B82F6'
        CORAL          = '#F87171'
        SUCCESS_GREEN  = '#34D399'
        PURPLE         = '#A78BFA'
        ORANGE         = '#FBBF24'
        TEAL           = '#2DD4BF'
        card_bg        = '#1E2A3A'
        bdr            = '#334155'
        ar             = '#3B1010'
        aa             = '#3B2A00'
        ag_bg          = '#0D2E1A'
    else:
        text_color     = '#1E293B'
        secondary_text = '#64748B'
        PRIMARY_BLUE   = '#1E40AF'
        SECONDARY_BLUE = '#3B82F6'
        CORAL          = '#DC2626'
        SUCCESS_GREEN  = '#059669'
        PURPLE         = '#7C3AED'
        ORANGE         = '#D97706'
        TEAL           = '#0D9488'
        card_bg        = '#F0F9FF'
        bdr            = '#E2E8F0'
        ar             = '#FEF2F2'
        aa             = '#FFFBEB'
        ag_bg          = '#F0FDF4'

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
        .section-header {{
            font-size: 24px; font-weight: 800; color: {text_color};
            margin: 40px 0 20px 0; padding-bottom: 12px;
            border-bottom: 4px solid {PRIMARY_BLUE};
        }}
        .ac-red   {{ background:{ar};    border-left:5px solid {CORAL};         padding:16px 20px; border-radius:10px; margin:8px 0; }}
        .ac-amber {{ background:{aa};    border-left:5px solid {ORANGE};        padding:16px 20px; border-radius:10px; margin:8px 0; }}
        .ac-green {{ background:{ag_bg}; border-left:5px solid {SUCCESS_GREEN}; padding:16px 20px; border-radius:10px; margin:8px 0; }}
        .at {{ font-size: 18px; font-weight: 800; color: {text_color}; margin-bottom: 5px; }}
        .ad {{ font-size: 16px; color: {secondary_text}; line-height: 1.6; }}
        .kpi-inline {{
            background: linear-gradient(135deg, {PRIMARY_BLUE} 0%, {SECONDARY_BLUE} 100%);
            padding: 20px 24px; border-radius: 14px; text-align: center;
        }}
        .kpi-inline-l {{
            font-size: 14px; font-weight: 800; color: rgba(255,255,255,0.9);
            text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;
        }}
        .kpi-inline-v {{
            font-size: 34px; font-weight: 900; color: white;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='page-title'>Operational Efficiency & Capacity</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Comprehensive analysis of bed utilization, patient flow, and operational performance metrics</div>", unsafe_allow_html=True)

    # ── Load Data ──────────────────────────────────────────────────────────────
    @st.cache_data
    def load_data():
        file_path   = "data/dataFinal.xlsx"
        xls         = pd.ExcelFile(file_path)
        bed_records = xls.parse("BedRecords")
        bed         = xls.parse("Bed")
        ward        = xls.parse("Ward")
        department  = xls.parse("Department")
        appointments= xls.parse("Appointment")
        nurses      = xls.parse("Nurse")

        df = bed_records.merge(bed, on="bed_No", how="left")
        df = df.merge(ward, on="ward_No", how="left")
        df = df.merge(department, on="dept_Id", how="left")

        df['admission_Date']  = pd.to_datetime(df['admission_Date'])
        df['discharge_Date']  = pd.to_datetime(df['discharge_Date'])
        df['Length_of_Stay']  = (df['discharge_Date'] - df['admission_Date']).dt.days
        appointments["appointment_Date"] = pd.to_datetime(appointments["appointment_Date"], errors="coerce")
        return df[df['Length_of_Stay'].isna() | (df['Length_of_Stay'] >= 0)], appointments, nurses

    df, appointments, nurses = load_data()
    df_completed = df.dropna(subset=["discharge_Date"]).copy()
    cutoff_date  = pd.Timestamp("2025-12-01")

    # ── Compute alert metrics ──────────────────────────────────────────────────
    n_months   = max(df["admission_Date"].dt.to_period("M").nunique(), 1)
    mo_adm     = len(df) / n_months
    cur_beds   = df["bed_No"].nunique()
    cur_nurses = len(nurses)
    avg_los_raw= df["Length_of_Stay"].dropna().mean()
    avg_los    = round(avg_los_raw, 1) if pd.notna(avg_los_raw) else 0.0
    avg_daily  = avg_los * (len(df) / max(n_months * 30, 1))
    occ_pct    = round(avg_daily / max(cur_beds, 1) * 100, 1)
    cancel_n   = appointments["appointment_status"].astype(str).str.lower().isin(["cancelled","canceled"]).sum()
    cancel_r   = round(cancel_n / max(len(appointments), 1) * 100, 1)
    noshow_n   = appointments["appointment_status"].astype(str).str.lower().str.contains(r"no.?show", regex=True).sum()
    noshow_r   = round(noshow_n / max(len(appointments), 1) * 100, 1)

    # ══════════════════════════════════════════════════════════════════════════
    # OPERATIONAL ALERTS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("<div class='section-header'>Operational Alerts</div>", unsafe_allow_html=True)
    st.caption("Auto-generated flags based on current data.  🔴 Red = critical  |  🟠 Amber = warning  |  🟢 Green = healthy")

    def alert_card(val, hi, mid, titles, msgs):
        lvl = "red" if val >= hi else "amber" if val >= mid else "green"
        idx = 0     if val >= hi else 1        if val >= mid else 2
        # Titles have NO emojis (emojis kept only in the caption above)
        st.markdown(f'<div class="ac-{lvl}"><div class="at">{titles[idx]}</div>'
                    f'<div class="ad">{msgs[idx]}</div></div>', unsafe_allow_html=True)

    alert_card(occ_pct, 85, 70,
        ["Critical Bed Occupancy", "High Bed Occupancy", "Bed Occupancy Normal"],
        [f"Occupancy at <b>{occ_pct}%</b> — above 85% critical threshold. Immediate action required.",
         f"Occupancy at <b>{occ_pct}%</b> — approaching critical. Monitor closely.",
         f"Occupancy at <b>{occ_pct}%</b> — within healthy range."])
    alert_card(cancel_r, 15, 8,
        ["High Cancellation Rate", "Elevated Cancellation Rate", "Cancellation Rate Normal"],
        [f"Cancellation rate <b>{cancel_r}%</b> — significant revenue impact likely.",
         f"Cancellation rate <b>{cancel_r}%</b> — consider reminder interventions.",
         f"Cancellation rate <b>{cancel_r}%</b> — within acceptable range."])
    alert_card(avg_los, 10, 7,
        ["Long Average LOS", "Above-Average LOS", "LOS Within Range"],
        [f"Avg LOS <b>{avg_los} days</b> — possible discharge bottlenecks. Review processes.",
         f"Avg LOS <b>{avg_los} days</b> — above average. Review discharge planning.",
         f"Avg LOS <b>{avg_los} days</b> — efficient patient throughput."])
    alert_card(noshow_r, 10, 5,
        ["No-Show Rate Critical", "No-Show Rate Elevated", "No-Show Rate Normal"],
        [f"No-show rate <b>{noshow_r}%</b> — immediate reminder campaign needed.",
         f"No-show rate <b>{noshow_r}%</b> — recommend 24h SMS reminders.",
         f"No-show rate <b>{noshow_r}%</b> — within acceptable range."])

    # KPI strip
    st.markdown("<br>", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    for col, lbl, val in [
        (k1, "Bed Occupancy",  f"{occ_pct}%"),
        (k2, "Cancel Rate",    f"{cancel_r}%"),
        (k3, "Avg LOS (days)", str(avg_los)),
        (k4, "No-Show Rate",   f"{noshow_r}%")
    ]:
        col.markdown(f"""<div class="kpi-inline">
            <div class="kpi-inline-l">{lbl}</div>
            <div class="kpi-inline-v">{val}</div>
        </div>""", unsafe_allow_html=True)

    # ── Monthly summary ────────────────────────────────────────────────────────
    df["Month"]           = df["admission_Date"].dt.to_period("M").astype(str)
    df_completed["Month"] = df_completed["discharge_Date"].dt.to_period("M").astype(str)

    monthly_admissions = df.groupby("Month")["admission_Id"].count().reset_index()
    monthly_discharges = df_completed.groupby("Month")["admission_Id"].count().reset_index()
    monthly_summary    = pd.merge(monthly_admissions, monthly_discharges, on="Month", how="outer",
                                  suffixes=("_Admissions","_Discharges")).fillna(0).sort_values("Month")
    avg_adm  = monthly_summary["admission_Id_Admissions"].mean()
    last_mo  = monthly_summary["Month"].max()
    last_val = monthly_summary.loc[monthly_summary["Month"] == last_mo, "admission_Id_Admissions"].values[0]
    if last_val < avg_adm * 0.5:
        monthly_summary = monthly_summary[monthly_summary["Month"] != last_mo]
    monthly_summary['Month_Display'] = pd.to_datetime(monthly_summary['Month']).dt.strftime('%b %Y')

    def spaced_ticks(labels, step=4):
        idx  = list(range(0, len(labels), step))
        vals = [labels[i] for i in idx]
        return vals, vals

    # ── LOS Analysis ──────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Length of Stay Analysis</div>", unsafe_allow_html=True)

    los_df = df[df['discharge_Date'] < cutoff_date].copy()

    fig1 = go.Figure()
    fig1.add_trace(go.Histogram(
        x=los_df['Length_of_Stay'], nbinsx=20,
        marker=dict(color=SECONDARY_BLUE, line=dict(color='white', width=1)),
        hovertemplate='LOS: %{x} days<br>Patients: %{y}<extra></extra>'
    ))
    fig1.update_layout(
        title=dict(text="<b>Length of Stay Distribution</b>",
                   font=dict(size=20, color=text_color, family="Arial Black"), x=0.5, xanchor='center'),
        xaxis_title="<b>Days</b>", yaxis_title="<b>Number of Patients</b>",
        xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        height=430, margin=dict(l=60, r=40, t=70, b=60),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

    # LOS Donut
    bins       = [0, 3, 7, 14, 30, float('inf')]
    labels_los = ['0-3 days','4-7 days','8-14 days','15-30 days','30+ days']
    los_df['LOS_Cat'] = pd.cut(los_df['Length_of_Stay'], bins=bins, labels=labels_los, right=True)
    cat_counts  = los_df['LOS_Cat'].value_counts().reindex(labels_los).fillna(0)
    donut_colors= ['#DC2626','#D97706','#059669','#0891B2','#1E40AF']

    fig2 = go.Figure(go.Pie(
        labels=cat_counts.index.tolist(), values=cat_counts.values.tolist(), hole=0.45,
        marker=dict(colors=donut_colors, line=dict(color='white', width=2)),
        textinfo='label+percent', textfont=dict(size=13, family="Arial Black", color=text_color),
        hovertemplate='<b>%{label}</b><br>Patients: %{value:,}<br>Share: %{percent}<extra></extra>',
        direction='clockwise', sort=False
    ))
    fig2.update_layout(
        title=dict(text="<b>LOS Category Breakdown</b>",
                   font=dict(size=20, color=text_color, family="Arial Black"), x=0.5, xanchor='center'),
        legend=dict(font=dict(size=13, family="Arial Black", color=text_color),
                    orientation='v', x=1.05, y=0.5, xanchor='left', bgcolor='rgba(0,0,0,0)'),
        height=450, margin=dict(l=80, r=200, t=70, b=60),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

    # ── Ward & Department Insights ─────────────────────────────────────────────
    st.markdown("<div class='section-header'>Ward & Department Insights</div>", unsafe_allow_html=True)

    # Ward admissions
    ward_adm = df.groupby('ward_Name')['admission_Id'].count().sort_values()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=ward_adm.values, y=ward_adm.index, orientation='h',
        marker=dict(color=ORANGE, line=dict(color='white', width=1.5), cornerradius=6),
        hovertemplate='<b>%{y}</b><br>Admissions: %{x:,}<extra></extra>'
    ))
    fig3.update_layout(
        title=dict(text="<b>Ward Utilization Overview</b>",
                   font=dict(size=20, color=text_color, family="Arial Black"), x=0.5, xanchor='center'),
        xaxis_title="<b>Total Admissions</b>", yaxis_title="",
        xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(tickfont=TICK_FONT),
        height=430, margin=dict(l=20, r=20, t=70, b=60),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

    # Dept LOS deviation
    overall_avg = df["Length_of_Stay"].mean()
    dept_los    = df.groupby('dept_Name')['Length_of_Stay'].mean()
    dept_diff   = (dept_los - overall_avg).sort_values()
    bar_colors  = [CORAL if x > 0 else PRIMARY_BLUE for x in dept_diff.values]

    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=dept_diff.values, y=dept_diff.index, orientation='h',
        marker=dict(color=bar_colors, line=dict(color='white', width=1.5)),
        hovertemplate='<b>%{y}</b><br>Deviation: %{x:.2f} days<extra></extra>'
    ))
    fig4.add_vline(x=0, line_width=2.5, line_color=text_color, opacity=0.6)
    fig4.update_layout(
        title=dict(text="<b>Dept Deviation from Avg LOS</b>",
                   font=dict(size=20, color=text_color, family="Arial Black"), x=0.5, xanchor='center'),
        xaxis_title="<b>Days Above / Below Hospital Average</b>", yaxis_title="",
        xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(tickfont=TICK_FONT),
        height=500, margin=dict(l=20, r=20, t=70, b=60),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

    # Department Workload Sunburst — REMOVED per user request

    # ── Patient Flow Trends ────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Patient Flow Trends</div>", unsafe_allow_html=True)

    adm_trend = (df[df['admission_Date'] < cutoff_date]
                 .groupby(df['admission_Date'].dt.to_period('M'))['patient_Id']
                 .count().reset_index())
    adm_trend.columns = ['Month','Admissions']
    adm_trend['Month_Display'] = adm_trend['Month'].dt.to_timestamp().dt.strftime('%b %Y')

    dis_trend = (df_completed[df_completed['discharge_Date'] < cutoff_date]
                 .groupby(df_completed['discharge_Date'].dt.to_period('M'))['patient_Id']
                 .count().reset_index())
    dis_trend.columns = ['Month','Discharges']
    dis_trend['Month_Display'] = dis_trend['Month'].dt.to_timestamp().dt.strftime('%b %Y')

    tv5, tt5 = spaced_ticks(adm_trend['Month_Display'].tolist(), step=4)
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=adm_trend['Month_Display'], y=adm_trend['Admissions'],
        mode='lines+markers', name='Admissions',
        line=dict(color=PRIMARY_BLUE, width=4),
        marker=dict(size=8, color=PRIMARY_BLUE, line=dict(color='white', width=2)),
        hovertemplate='<b>%{x}</b><br>Admissions: %{y:,}<extra></extra>'
    ))
    fig5.add_trace(go.Scatter(
        x=dis_trend['Month_Display'], y=dis_trend['Discharges'],
        mode='lines+markers', name='Discharges',
        line=dict(color=CORAL, width=4),
        marker=dict(size=8, color=CORAL, line=dict(color='white', width=2)),
        hovertemplate='<b>%{x}</b><br>Discharges: %{y:,}<extra></extra>'
    ))
    fig5.update_layout(
        title=dict(text="<b>Admission vs Discharge Trend</b>",
                   font=dict(size=22, color=text_color, family="Arial Black"), x=0.5, xanchor='center'),
        xaxis_title="<b>Month</b>", yaxis_title="<b>Count</b>",
        xaxis=dict(tickmode='array', tickvals=tv5, ticktext=tt5,
                   tickfont=TICK_FONT, title_font=TITLE_FONT, tickangle=-45,
                   showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        height=450, margin=dict(l=40, r=40, t=70, b=110),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(font=dict(size=14, family="Arial Black", color=text_color), bgcolor='rgba(0,0,0,0)'),
        hovermode='x unified'
    )
    st.plotly_chart(fig5, use_container_width=True, config={'displayModeBar': False})

    # ── Monthly Admission Trend ────────────────────────────────────────────────
    tv6, tt6 = spaced_ticks(monthly_summary['Month_Display'].tolist(), step=4)
    fig6 = go.Figure()
    fig6.add_trace(go.Scatter(
        x=monthly_summary['Month_Display'], y=monthly_summary['admission_Id_Admissions'],
        mode='lines+markers', line=dict(color=SUCCESS_GREEN, width=5),
        marker=dict(size=8, color=SUCCESS_GREEN, line=dict(color='white', width=3)),
        hovertemplate='<b>%{x}</b><br>Admissions: %{y:,}<extra></extra>'
    ))
    fig6.update_layout(
        title=dict(text="<b>Monthly Admission Trend</b>",
                   font=dict(size=22, color=text_color, family="Arial Black"), x=0.5, xanchor='center'),
        xaxis_title="<b>Month</b>", yaxis_title="<b>Admissions</b>",
        xaxis=dict(tickmode='array', tickvals=tv6, ticktext=tt6,
                   tickfont=TICK_FONT, title_font=TITLE_FONT, tickangle=-45,
                   showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        height=450, margin=dict(l=40, r=40, t=70, b=110),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig6, use_container_width=True, config={'displayModeBar': False})

    # ── Bed Turnover Rate ──────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Bed Turnover Rate</div>", unsafe_allow_html=True)

    total_beds = df["bed_No"].nunique()
    monthly_summary["Monthly_BTR"] = monthly_summary["admission_Id_Discharges"] / total_beds
    tv8, tt8 = spaced_ticks(monthly_summary['Month_Display'].tolist(), step=4)

    fig8 = go.Figure()
    fig8.add_trace(go.Bar(
        x=monthly_summary['Month_Display'], y=monthly_summary['Monthly_BTR'],
        marker=dict(color=PURPLE, line=dict(color='white', width=2), cornerradius=8),
        hovertemplate='<b>%{x}</b><br>Bed Turnover Rate: %{y:.2f}<extra></extra>'
    ))
    fig8.update_layout(
        title=dict(text="<b>Monthly Bed Turnover Rate</b>",
                   font=dict(size=22, color=text_color, family="Arial Black"), x=0.5, xanchor='center'),
        xaxis_title="<b>Month</b>", yaxis_title="<b>Turnover Rate</b>",
        xaxis=dict(tickmode='array', tickvals=tv8, ticktext=tt8,
                   tickfont=TICK_FONT, title_font=TITLE_FONT, tickangle=-45),
        yaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        height=450, margin=dict(l=40, r=40, t=70, b=110),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig8, use_container_width=True, config={'displayModeBar': False})

    # ── Monthly Summary Table ──────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Monthly Summary</div>", unsafe_allow_html=True)
    display_summary = monthly_summary[['Month_Display','admission_Id_Admissions',
                                        'admission_Id_Discharges','Monthly_BTR']].copy()
    display_summary.columns = ['Month','Admissions','Discharges','Bed Turnover Rate']
    display_summary['Bed Turnover Rate'] = display_summary['Bed Turnover Rate'].round(2)
    st.dataframe(display_summary, use_container_width=True, hide_index=True)

    st.markdown("<br><br>", unsafe_allow_html=True)