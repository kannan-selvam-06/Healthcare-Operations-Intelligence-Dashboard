import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
        grid_color     = 'rgba(255,255,255,0.08)'
        paper_bg       = 'rgba(0,0,0,0)'
        plot_bg        = 'rgba(0,0,0,0)'
        card_bg        = '#1E2A3A'
        bdr            = '#334155'
    else:
        text_color     = '#1E293B'
        secondary_text = '#64748B'
        PRIMARY_BLUE   = '#1E40AF'
        SECONDARY_BLUE = '#3B82F6'
        CORAL          = '#DC2626'
        SUCCESS_GREEN  = '#059669'
        PURPLE         = '#7C3AED'
        grid_color     = 'rgba(0,0,0,0.08)'
        paper_bg       = 'rgba(0,0,0,0)'
        plot_bg        = 'rgba(0,0,0,0)'
        card_bg        = '#F0F9FF'
        bdr            = '#E2E8F0'

    TICK_FONT  = dict(size=14, color=text_color, family="Arial Black")
    TITLE_FONT = dict(size=16, color=text_color, family="Arial Black")

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
        .kpi-box {{
            background: linear-gradient(135deg, {PRIMARY_BLUE} 0%, {SECONDARY_BLUE} 100%);
            padding: 26px; border-radius: 16px; text-align: center;
            box-shadow: 0 8px 20px rgba(0,0,0,0.18); transition: transform 0.3s ease;
        }}
        .kpi-box:hover {{ transform: translateY(-6px); }}
        .kpi-label {{
            font-size: 16px !important; color: rgba(255,255,255,0.9) !important;
            font-weight: 800 !important; text-transform: uppercase;
            letter-spacing: 1px; margin-bottom: 10px;
        }}
        .kpi-value {{
            font-size: 42px !important; font-weight: 900 !important; color: white !important;
        }}
        .section-header {{
            font-size: 24px; font-weight: 800; color: {text_color};
            margin: 45px 0 20px 0; padding-bottom: 12px;
            border-bottom: 4px solid {PRIMARY_BLUE};
        }}
        .insight-box {{
            background: {card_bg}; border: 1px solid {bdr};
            border-left: 5px solid {PRIMARY_BLUE}; border-radius: 10px;
            padding: 16px 20px; margin-bottom: 12px;
        }}
        .insight-title {{ font-size: 17px; font-weight: 800; color: {PRIMARY_BLUE}; margin-bottom: 6px; }}
        .insight-text  {{ font-size: 16px; color: {secondary_text}; line-height: 1.6; }}
        .filter-bar {{
            background: {card_bg}; border: 1px solid {bdr}; border-radius: 12px;
            padding: 16px 20px; margin-bottom: 24px;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='page-title'>Clinical & Disease Intelligence</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Comprehensive medical patterns and surgical analytics for strategic clinical insights</div>", unsafe_allow_html=True)

    @st.cache_data
    def load_data():
        file_path   = "data/dataFinal.xlsx"
        patients    = pd.read_excel(file_path, sheet_name="Patients")
        doctors     = pd.read_excel(file_path, sheet_name="Doctor")
        departments = pd.read_excel(file_path, sheet_name="Department")
        surgeries   = pd.read_excel(file_path, sheet_name="SurgeryRecord")
        return patients, doctors, departments, surgeries

    patients, doctors, departments, surgeries = load_data()

    surgeries["surgery_Date"] = pd.to_datetime(surgeries["surgery_Date"], errors="coerce")

    # ── Interactive Filters ────────────────────────────────────────────────────
    st.markdown("<div class='filter-bar'>", unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        all_depts   = departments['dept_Name'].dropna().unique().tolist()
        sel_dept    = st.multiselect("Department", all_depts, key="p3_dept")
    with fc2:
        all_stypes  = sorted(surgeries['surgery_Type'].dropna().unique().tolist())
        sel_stype   = st.multiselect("Surgery Type", all_stypes, key="p3_stype")
    with fc3:
        yr_opts     = sorted(surgeries["surgery_Date"].dt.year.dropna().unique().astype(int).tolist())
        sel_yrs     = st.multiselect("Year", yr_opts, default=yr_opts, key="p3_yr")
    st.markdown("</div>", unsafe_allow_html=True)

    df = pd.merge(patients, surgeries, on='patient_Id', how='left')
    df = pd.merge(df, doctors[['doct_Id','dept_Id']], left_on='surgeon_Id', right_on='doct_Id', how='left').drop(columns=['doct_Id'])
    df = pd.merge(df, departments, on='dept_Id', how='left')

    current = df.copy()
    if sel_dept:  current = current[current['dept_Name'].isin(sel_dept)]
    if sel_stype: current = current[current['surgery_Type'].isin(sel_stype)]
    if sel_yrs:
        current = current[current['surgery_Date'].dt.year.isin(sel_yrs)]

    # ── KPIs — 3 cards (Total Patients removed) ──────────────────────────────
    col1, col2, col3 = st.columns(3)
    for col, lbl, val in [
        (col1, "Unique Procedures", current['surgery_Type'].nunique()),
        (col2, "Active Surgeons",   current['surgeon_Id'].nunique()),
        (col3, "Departments",       current['dept_Name'].nunique()),
    ]:
        col.markdown(f"""<div class="kpi-box">
            <div class="kpi-label">{lbl}</div>
            <div class="kpi-value">{val}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Chart 1: Top 10 Surgeries — Sorted Horizontal Bar ────────────────────
    st.markdown("<div class='section-header'>Most Common Surgical Procedures</div>", unsafe_allow_html=True)

    top_surg = surgeries['surgery_Type'].value_counts().head(10).reset_index()
    top_surg.columns = ['Surgery','Count']
    top_surg = top_surg.sort_values('Count', ascending=True)

    tc1, tc2 = st.columns([3, 1], gap="large")
    with tc1:
        fig1 = go.Figure(go.Bar(
            x=top_surg['Count'], y=top_surg['Surgery'], orientation='h',
            marker=dict(
                color=top_surg['Count'],
                colorscale=[[0, SECONDARY_BLUE],[0.5, '#7C3AED'],[1, '#C026D3']],
                showscale=True,
                colorbar=dict(
                    title=dict(text="<b>Count</b>", font=dict(size=13, family="Arial Black", color=text_color)),
                    tickfont=dict(size=12, family="Arial Black", color=text_color),
                    thickness=15, len=0.7
                ),
                line=dict(color='white', width=1), cornerradius=6
            ),
            hovertemplate='<b>%{y}</b><br>Count: %{x:,}<extra></extra>'
        ))
        fig1.update_layout(
            xaxis_title="<b>Number of Cases</b>", yaxis_title="",
            xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=grid_color),
            yaxis=dict(tickfont=TICK_FONT),
            height=500, margin=dict(l=20, r=80, t=20, b=50),
            plot_bgcolor=plot_bg, paper_bgcolor=paper_bg, showlegend=False
        )
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
    with tc2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        top1 = top_surg.iloc[-1]
        top2 = top_surg.iloc[-2]
        total_surgs = top_surg["Count"].sum()
        st.markdown(f"""<div class='insight-box'>
            <div class='insight-title'>#1 Procedure</div>
            <div class='insight-text'><b>{top1['Surgery']}</b> with {int(top1['Count']):,} cases.</div>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"""<div class='insight-box'>
            <div class='insight-title'>#2 Procedure</div>
            <div class='insight-text'><b>{top2['Surgery']}</b> with {int(top2['Count']):,} cases.</div>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"""<div class='insight-box'>
            <div class='insight-title'>Total (Top 10)</div>
            <div class='insight-text'>{total_surgs:,} combined cases across top 10 procedures.</div>
        </div>""", unsafe_allow_html=True)

    # ── Chart 2: Surgery Distribution by Department ───────────────────────────
    st.markdown("<div class='section-header'>Surgery Distribution by Department</div>", unsafe_allow_html=True)

    dept_counts = current['dept_Name'].value_counts().reset_index()
    dept_counts.columns = ['dept_Name','Surgeries']
    dept_counts = dept_counts.sort_values('Surgeries', ascending=True)

    fig4 = go.Figure(go.Bar(
        x=dept_counts['Surgeries'],
        y=dept_counts['dept_Name'],
        orientation='h',
        marker=dict(
            color=dept_counts['Surgeries'],
            colorscale=[[0, SECONDARY_BLUE],[0.5, PRIMARY_BLUE],[1, PURPLE]],
            showscale=True,
            colorbar=dict(
                title=dict(text="<b>Surgeries</b>", font=dict(size=13, family="Arial Black", color=text_color)),
                tickfont=dict(size=12, family="Arial Black", color=text_color),
                thickness=15, len=0.7
            ),
            line=dict(color='white', width=1.5), cornerradius=6
        ),
        hovertemplate='<b>%{y}</b><br>Surgeries: %{x:,}<extra></extra>'
    ))
    fig4.update_layout(
        xaxis_title="<b>Number of Surgeries</b>", yaxis_title="",
        xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=grid_color),
        yaxis=dict(tickfont=TICK_FONT),
        height=500, margin=dict(l=20, r=80, t=20, b=50),
        plot_bgcolor=plot_bg, paper_bgcolor=paper_bg, showlegend=False
    )
    st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

    # ── Chart 3: Department-wise Surgery Type Distribution ────────────────────
    st.markdown("<div class='section-header'>Department-wise Surgery Type Distribution</div>", unsafe_allow_html=True)

    top_depts  = current['dept_Name'].value_counts().head(5).index
    top_stypes = current['surgery_Type'].value_counts().head(5).index
    dm = current[current['dept_Name'].isin(top_depts) & current['surgery_Type'].isin(top_stypes)]
    dm = dm.groupby(['dept_Name','surgery_Type']).size().reset_index(name='Count')

    GROUP_COLORS = [PRIMARY_BLUE,'#0891b2', SUCCESS_GREEN, CORAL, PURPLE]

    fig5 = px.bar(
        dm, x='dept_Name', y='Count', color='surgery_Type',
        barmode='group', color_discrete_sequence=GROUP_COLORS,
        labels={'dept_Name':'Department','Count':'Number of Cases','surgery_Type':'Surgery Type'}
    )
    fig5.update_traces(
        marker=dict(cornerradius=4),
        hovertemplate='<b>%{fullData.name}</b><br>%{x}: %{y} cases<extra></extra>'
    )
    fig5.update_layout(
        xaxis_title="<b>Department</b>", yaxis_title="<b>Number of Cases</b>",
        xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=False),
        yaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=grid_color),
        height=480, margin=dict(l=60, r=40, t=30, b=60),
        plot_bgcolor=plot_bg, paper_bgcolor=paper_bg,
        legend=dict(
            title=dict(text="<b>Surgery Type</b>", font=dict(size=13, color=text_color)),
            font=dict(size=12, color=text_color, family="Arial Black"),
            orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
            bgcolor='rgba(0,0,0,0)'
        )
    )
    st.plotly_chart(fig5, use_container_width=True, config={'displayModeBar': False})

    # ── Chart 4: Surgery Trend Over Time ─────────────────────────────────────
    st.markdown("<div class='section-header'>Surgery Trend Over Time</div>", unsafe_allow_html=True)

    surgery_trend_df = surgeries.copy()
    surgery_trend_df['Month_Year'] = surgery_trend_df['surgery_Date'].dt.strftime('%b %Y')
    surgery_trend_df['Sort_Date']  = surgery_trend_df['surgery_Date'].dt.to_period('M')
    surgery_trend = surgery_trend_df.groupby(['Month_Year','Sort_Date']).size().reset_index(name="Count").sort_values('Sort_Date')

    x_vals2    = surgery_trend['Month_Year'].tolist()
    show_every2= max(1, len(x_vals2) // 6)
    tick_vals2 = x_vals2[::show_every2]

    fig6 = go.Figure(go.Scatter(
        x=surgery_trend['Month_Year'], y=surgery_trend['Count'], mode='lines+markers',
        line=dict(color=PURPLE, width=3),
        marker=dict(size=7, color=PURPLE, line=dict(color='white', width=2)),
        hovertemplate='<b>%{x}</b><br>Surgeries: %{y:,}<extra></extra>'
    ))
    fig6.update_xaxes(tickmode='array', tickvals=tick_vals2, tickangle=-45)
    fig6.update_layout(
        xaxis_title="<b>Month</b>", yaxis_title="<b>Number of Surgeries</b>",
        xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=grid_color),
        yaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=grid_color),
        height=450, margin=dict(l=20, r=20, t=30, b=80),
        plot_bgcolor=plot_bg, paper_bgcolor=paper_bg
    )
    st.plotly_chart(fig6, use_container_width=True, config={'displayModeBar': False})

    # ── Chart 5: Doctor-Department Surgery Heatmap ───────────────────────────
    st.markdown("<div class='section-header'>Doctor–Department Surgery Heatmap</div>", unsafe_allow_html=True)

    surg_heat  = surgeries.copy()
    doc_dept   = doctors.merge(departments, on='dept_Id', how='left')[['doct_Id','FName','dept_Name']]
    surg_heat  = surg_heat.merge(doc_dept, left_on='surgeon_Id', right_on='doct_Id', how='inner')
    surg_heat  = surg_heat.dropna(subset=['FName','dept_Name'])
    heat_counts= surg_heat.groupby(['FName','dept_Name']).size().reset_index(name='Count')
    top10      = heat_counts.groupby('FName')['Count'].sum().nlargest(10).index
    heat_counts= heat_counts[heat_counts['FName'].isin(top10)]
    pivot      = heat_counts.pivot(index='FName', columns='dept_Name', values='Count').fillna(0)
    pivot      = pivot.loc[pivot.sum(axis=1).sort_values(ascending=True).index]

    z_vals = pivot.values.astype(float)
    max_z  = z_vals.max() if z_vals.max() > 0 else 1

    HEAT_COLORSCALE = [[0.0,'#FFFFFF'],[0.15,'#FFCDD2'],[0.35,'#EF9A9A'],
                       [0.55,'#E53935'],[0.75,'#C62828'],[1.0,'#7B1010']]

    fig_heat = go.Figure()
    fig_heat.add_trace(go.Heatmap(
        z=z_vals, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=HEAT_COLORSCALE, showscale=True,
        text=z_vals.astype(int), texttemplate='%{text}',
        textfont=dict(size=12, family="Arial Black", color='#1A1A2E'),
        colorbar=dict(
            title=dict(text="<b>Cases</b>", font=dict(size=13, family="Arial Black", color=text_color)),
            tickfont=dict(size=12, family="Arial Black", color=text_color),
            thickness=16, len=0.85
        ),
        hovertemplate='<b>%{y}</b><br>%{x}: %{z} surgeries<extra></extra>',
        zmin=0, zmax=max_z
    ))
    annotations = []
    cols_h = pivot.columns.tolist()
    rows_h = pivot.index.tolist()
    for r_idx, r_name in enumerate(rows_h):
        for c_idx, c_name in enumerate(cols_h):
            val = int(z_vals[r_idx, c_idx])
            if (val / max_z) > 0.5:
                annotations.append(dict(
                    x=c_name, y=r_name, text=str(val), showarrow=False,
                    font=dict(size=12, family="Arial Black", color='white'),
                    xref='x', yref='y'
                ))
    fig_heat.update_layout(
        annotations=annotations,
        xaxis_title="<b>Department</b>", yaxis_title="",
        xaxis=dict(tickfont=dict(size=11, color=text_color, family="Arial Black"),
                   title_font=TITLE_FONT, tickangle=-45, side='bottom'),
        yaxis=dict(tickfont=dict(size=12, color=text_color, family="Arial Black")),
        height=560, margin=dict(l=140, r=90, t=30, b=150),
        plot_bgcolor=plot_bg, paper_bgcolor=paper_bg
    )
    st.plotly_chart(fig_heat, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<br><br>", unsafe_allow_html=True)