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
        PURPLE         = '#A78BFA'
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
        card_bg        = '#F0F9FF'
        bdr            = '#E2E8F0'

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
            padding: 28px; border-radius: 16px; text-align: center;
            box-shadow: 0 8px 20px rgba(0,0,0,0.18); transition: transform 0.3s ease;
        }}
        .kpi-card:hover {{ transform: translateY(-6px); }}
        .kpi-title {{
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
        .stat-row {{
            display:flex; justify-content:space-between; align-items:center;
            padding:8px 0; border-bottom:1px solid {bdr};
        }}
        .stat-label {{ font-size:13px; font-weight:700; color:{text_color}; }}
        .stat-val   {{ font-size:14px; font-weight:900; color:{PRIMARY_BLUE}; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='page-title'>Staffing & Resource Optimization</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Strategic workforce analytics and resource allocation insights for optimal healthcare delivery</div>", unsafe_allow_html=True)

    @st.cache_data
    def load_data():
        xls = pd.ExcelFile("data/dataFinal.xlsx")
        return {sheet: pd.read_excel(xls, sheet) for sheet in xls.sheet_names}

    tables = load_data()

    patients     = tables["Patients"]
    appointments = tables["Appointment"]
    bed_records  = tables["BedRecords"]
    doctor       = tables["Doctor"]
    department   = tables["Department"]
    nurse        = tables["Nurse"]

    appointments["appointment_Date"] = pd.to_datetime(appointments["appointment_Date"])
    bed_records["admission_Date"]    = pd.to_datetime(bed_records["admission_Date"])

    doctor_dept  = doctor.merge(department, on="dept_Id", how="left")
    appointments = appointments.merge(
        doctor_dept[["doct_Id","dept_Name","FName"]], on="doct_Id", how="left"
    )
    appointments["Doctor_Name"] = appointments["FName"]
    nurse_dept   = nurse.merge(department, on="dept_Id", how="left")
    nurse_count  = nurse_dept.groupby("dept_Name")["nurse_Id"].nunique().reset_index()
    nurse_count.columns = ["dept_Name","nurse_Id"]

    # Use full unfiltered data — filters removed per user request
    appointments_f = appointments.copy()
    patients_f     = patients.copy()
    bed_f          = bed_records.copy()

    # ── KPIs ─────────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    for col, lbl, val in [
        (col1, "Active Doctors",   appointments_f["doct_Id"].nunique()),
        (col2, "Total Nurses",     nurse["nurse_Id"].nunique()),
        (col3, "Departments",      appointments_f["dept_Name"].nunique()),
    ]:
        col.markdown(f"""<div class="kpi-card">
            <div class="kpi-title">{lbl}</div>
            <div class="kpi-value">{val}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    # Quick insight cards REMOVED per user request

    # ── Nurse Distribution ────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Nurse Distribution by Department</div>", unsafe_allow_html=True)

    nurse_count_sorted = nurse_count.sort_values("nurse_Id", ascending=True)

    nd1, nd2 = st.columns([3, 1], gap="large")
    with nd1:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=nurse_count_sorted['nurse_Id'],
            y=nurse_count_sorted['dept_Name'],
            orientation='h',
            marker=dict(
                color=nurse_count_sorted['nurse_Id'],
                colorscale=[[0, SUCCESS_GREEN],[1, PRIMARY_BLUE]],
                line=dict(color='white', width=2), cornerradius=8
            ),
            hovertemplate='<b>%{y}</b><br>Nurses: %{x}<extra></extra>'
        ))
        # Title removed from chart — section header above serves as title
        fig1.update_layout(
            xaxis_title="<b>Number of Nurses</b>", yaxis_title="",
            xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
            yaxis=dict(tickfont=TICK_FONT),
            height=500, margin=dict(l=20, r=20, t=20, b=50),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', showlegend=False
        )
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
    with nd2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        top_nd  = nurse_count_sorted.iloc[-1]
        low_nd  = nurse_count_sorted.iloc[0]
        avg_nur = round(nurse_count_sorted["nurse_Id"].mean(), 1)
        st.markdown(f"""<div class='insight-box'>
            <div class='insight-title'>Most Staffed</div>
            <div class='insight-text'><b>{top_nd['dept_Name']}</b> — {int(top_nd['nurse_Id'])} nurses</div>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"""<div class='insight-box'>
            <div class='insight-title'>Least Staffed</div>
            <div class='insight-text'><b>{low_nd['dept_Name']}</b> — {int(low_nd['nurse_Id'])} nurses</div>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"""<div class='insight-box'>
            <div class='insight-title'>Avg per Dept</div>
            <div class='insight-text'>{avg_nur} nurses on average per department.</div>
        </div>""", unsafe_allow_html=True)

    # ── Doctor Workload Heatmap ───────────────────────────────────────────────
    st.markdown("<div class='section-header'>Doctor Workload Heatmap (Top 10)</div>", unsafe_allow_html=True)

    doctor_workload = appointments_f.groupby(["Doctor_Name","dept_Name"]).size().reset_index(name="Appointments")
    top10_doctors   = doctor_workload.groupby("Doctor_Name")["Appointments"].sum().sort_values(ascending=False).head(10).index
    heatmap_df      = doctor_workload[doctor_workload["Doctor_Name"].isin(top10_doctors)]
    pivot_heatmap   = heatmap_df.pivot(index="Doctor_Name", columns="dept_Name", values="Appointments").fillna(0)

    if not pivot_heatmap.empty:
        z_vals = pivot_heatmap.values
        fig2 = go.Figure(data=go.Heatmap(
            z=z_vals,
            x=pivot_heatmap.columns.tolist(),
            y=pivot_heatmap.index.tolist(),
            colorscale=[[0.0,'#FFFFFF'],[0.2,'#FFCDD2'],[0.4,'#EF9A9A'],
                        [0.6,'#E53935'],[0.8,'#C62828'],[1.0,'#7B1010']],
            text=pivot_heatmap.values.astype(int), texttemplate='%{text}',
            textfont=dict(size=14, family="Arial Black", color='black'),
            hovertemplate='<b>Doctor: %{y}</b><br>Department: %{x}<br>Appointments: %{z}<extra></extra>',
            colorbar=dict(
                title=dict(text="<b>Appointments</b>", font=dict(size=14, family="Arial Black", color=text_color)),
                tickfont=dict(size=13, family="Arial Black", color=text_color), thickness=18
            )
        ))
        # Title removed from chart — section header above serves as title
        fig2.update_layout(
            xaxis_title="<b>Department</b>", yaxis_title="<b>Doctor Name</b>",
            xaxis=dict(tickfont=dict(size=13, color=text_color, family="Arial Black"),
                       title_font=TITLE_FONT, side='bottom', tickangle=-45),
            yaxis=dict(tickfont=dict(size=14, color=text_color, family="Arial Black"), title_font=TITLE_FONT),
            height=580, margin=dict(l=130, r=100, t=30, b=140),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No data available for Doctor Workload Heatmap.")

    # ── Patient-to-Nurse Ratio ────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Patient-to-Nurse Ratio</div>", unsafe_allow_html=True)

    admissions_dept = bed_f.merge(
        appointments_f[["patient_Id","dept_Name"]].drop_duplicates(), on="patient_Id", how="left"
    ).groupby("dept_Name").size().reset_index(name="Total_Admissions")

    ratio_df = admissions_dept.merge(nurse_count, on="dept_Name", how="left")
    ratio_df["Patient_per_Nurse"] = (ratio_df["Total_Admissions"] / ratio_df["nurse_Id"].replace(0,1)).round(2)

    rc1, rc2 = st.columns([3,1], gap="large")
    with rc1:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=ratio_df['nurse_Id'], y=ratio_df['Total_Admissions'], mode='markers',
            marker=dict(
                size=ratio_df['Patient_per_Nurse'] * 3,
                color=ratio_df['Patient_per_Nurse'],
                colorscale=[[0, SUCCESS_GREEN],[0.5, SECONDARY_BLUE],[1, CORAL]],
                line=dict(color='white', width=2), showscale=True,
                colorbar=dict(
                    title=dict(text="<b>Ratio</b>", font=dict(size=14, family="Arial Black", color=text_color)),
                    tickfont=dict(size=13, family="Arial Black", color=text_color)
                )
            ),
            text=ratio_df['dept_Name'],
            hovertemplate='<b>%{text}</b><br>Nurses: %{x}<br>Admissions: %{y}<br>Ratio: %{marker.color:.2f}<extra></extra>'
        ))
        # Title removed from chart — section header above serves as title
        fig3.update_layout(
            xaxis_title="<b>Number of Nurses</b>", yaxis_title="<b>Total Admissions</b>",
            xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
            yaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
            height=500, margin=dict(l=20, r=20, t=20, b=50),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
    with rc2:
        st.markdown("<br>", unsafe_allow_html=True)
        if len(ratio_df) > 0:
            top_r = ratio_df.nlargest(1, "Patient_per_Nurse").iloc[0]
            low_r = ratio_df.nsmallest(1, "Patient_per_Nurse").iloc[0]
            st.markdown(f"""<div class='insight-box'>
                <div class='insight-title'>Highest Ratio</div>
                <div class='insight-text'><b>{top_r['dept_Name']}</b> — {top_r['Patient_per_Nurse']:.1f} patients per nurse</div>
            </div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class='insight-box'>
                <div class='insight-title'>Lowest Ratio</div>
                <div class='insight-text'><b>{low_r['dept_Name']}</b> — {low_r['Patient_per_Nurse']:.1f} patients per nurse</div>
            </div>""", unsafe_allow_html=True)

    # ── Department-wise Admissions vs Staff ───────────────────────────────────
    st.markdown("<div class='section-header'>Department-wise Admissions vs Staff</div>", unsafe_allow_html=True)

    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=ratio_df['dept_Name'], y=ratio_df['Total_Admissions'], name='Total Admissions',
        marker=dict(color=PRIMARY_BLUE, line=dict(color='white', width=2), cornerradius=4),
        hovertemplate='<b>%{x}</b><br>Admissions: %{y:,}<extra></extra>'
    ))
    fig4.add_trace(go.Bar(
        x=ratio_df['dept_Name'], y=ratio_df['nurse_Id'], name='Nurses',
        marker=dict(color=SUCCESS_GREEN, line=dict(color='white', width=2), cornerradius=4),
        hovertemplate='<b>%{x}</b><br>Nurses: %{y}<extra></extra>'
    ))
    # Title removed from chart — section header above serves as title
    fig4.update_layout(
        xaxis_title="<b>Department</b>", yaxis_title="<b>Count</b>",
        xaxis=dict(tickfont=dict(size=12, color=text_color, family="Arial Black"),
                   title_font=TITLE_FONT, tickangle=-45),
        yaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        barmode='group', height=500, margin=dict(l=20, r=20, t=20, b=100),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(font=dict(size=14, family="Arial Black", color=text_color), bgcolor='rgba(0,0,0,0)')
    )
    st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

    # ── Admissions Reference View ─────────────────────────────────────────────
    st.markdown("<div class='section-header'>Admissions Reference View for Staffing</div>", unsafe_allow_html=True)

    monthly_admissions_view = bed_f.set_index("admission_Date").resample("M").size().reset_index(name="Admissions")
    monthly_admissions_view['Month_Display'] = monthly_admissions_view['admission_Date'].dt.strftime('%b %Y')

    x_vals     = monthly_admissions_view['Month_Display'].tolist()
    show_every = max(1, len(x_vals) // 6)
    tick_vals  = x_vals[::show_every]

    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=monthly_admissions_view['Month_Display'], y=monthly_admissions_view['Admissions'],
        mode='lines+markers', name='Admissions',
        line=dict(color=SUCCESS_GREEN, width=5),
        marker=dict(size=10, color=SUCCESS_GREEN, line=dict(color='white', width=3)),
        hovertemplate='<b>%{x}</b><br>Admissions: %{y:,}<extra></extra>'
    ))
    # Moving average and its legend REMOVED per user request

    fig5.update_xaxes(tickmode='array', tickvals=tick_vals, tickangle=-45)
    # Title removed from chart — section header above serves as title
    fig5.update_layout(
        xaxis_title="<b>Admission Date</b>", yaxis_title="<b>Admissions</b>",
        xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        hovermode='x unified', height=450, margin=dict(l=20, r=20, t=20, b=100),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    st.plotly_chart(fig5, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<br><br>", unsafe_allow_html=True)