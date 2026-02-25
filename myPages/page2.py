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
        TEAL           = '#2DD4BF'
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
        TEAL           = '#0D9488'
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
        .kpi-box {{
            background: linear-gradient(135deg, {PRIMARY_BLUE} 0%, {SECONDARY_BLUE} 100%);
            border-radius: 16px; padding: 26px 20px; text-align: center;
            box-shadow: 0 8px 20px rgba(0,0,0,0.18); transition: transform 0.3s ease;
        }}
        .kpi-box:hover {{ transform: translateY(-6px); }}
        .kpi-label {{
            font-size: 16px !important; color: rgba(255,255,255,0.9) !important;
            font-weight: 800 !important; margin-bottom: 10px;
            text-transform: uppercase; letter-spacing: 1.2px;
        }}
        .kpi-value {{
            font-size: 42px !important; font-weight: 900 !important; color: white !important;
        }}
        .section-header {{
            font-size: 24px; font-weight: 800; color: {text_color};
            margin: 45px 0 20px 0; padding-bottom: 12px;
            border-bottom: 4px solid {PRIMARY_BLUE};
        }}
        .journey-card {{
            background: {card_bg}; border: 1px solid {bdr};
            border-left: 5px solid {TEAL}; border-radius: 10px;
            padding: 14px 18px; margin: 6px 0;
        }}
        .journey-event {{
            font-size: 14px; font-weight: 800; color: {text_color}; margin-bottom: 2px;
        }}
        .journey-detail {{
            font-size: 12px; color: {secondary_text}; line-height: 1.5;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='page-title'>Patient Demographics & Demand Analysis</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Comprehensive insights into patient populations, service demand patterns & care journeys</div>", unsafe_allow_html=True)

    @st.cache_data
    def load_data():
        file_path    = "data/dataFinal.xlsx"
        patients     = pd.read_excel(file_path, sheet_name="Patients")
        appointments = pd.read_excel(file_path, sheet_name="Appointment")
        bed_records  = pd.read_excel(file_path, sheet_name="BedRecords")
        surgeries    = pd.read_excel(file_path, sheet_name="SurgeryRecord")
        doctors      = pd.read_excel(file_path, sheet_name="Doctor")
        depts        = pd.read_excel(file_path, sheet_name="Department")
        return patients, appointments, bed_records, surgeries, doctors, depts

    patients, appointments, bed_records, surgeries, doctors, depts = load_data()

    data = pd.merge(appointments, patients, on="patient_Id", how="left")
    data["appointment_Date"] = pd.to_datetime(data["appointment_Date"], errors="coerce")
    data["Date_Of_Birth"]    = pd.to_datetime(data["Date_Of_Birth"],    errors="coerce")
    today = pd.Timestamp.today()
    data["Age"]      = (today - data["Date_Of_Birth"]).dt.days // 365
    bins   = [0, 18, 30, 45, 60, 75, 100]
    labels = ["0-18","19-30","31-45","46-60","61-75","76+"]
    data["Age_Group"]  = pd.cut(data["Age"], bins=bins, labels=labels)
    data["Month"]      = data["appointment_Date"].dt.month
    data["Month_Name"] = data["appointment_Date"].dt.strftime("%b")
    data["Year"]       = data["appointment_Date"].dt.year

    bed_records["admission_Date"]  = pd.to_datetime(bed_records["admission_Date"],  errors="coerce")
    bed_records["discharge_Date"]  = pd.to_datetime(bed_records["discharge_Date"],  errors="coerce")
    bed_records["LOS"]             = (bed_records["discharge_Date"] - bed_records["admission_Date"]).dt.days
    surgeries["surgery_Date"]      = pd.to_datetime(surgeries["surgery_Date"], errors="coerce")

    MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    monthly_counts = data.groupby(["Year","Month","Month_Name"]).size().reset_index(name="Count").sort_values(["Year","Month"])
    valid_years    = data.groupby("Year")["Month"].nunique()
    valid_years    = valid_years[valid_years >= 6].index.tolist()
    monthly_counts = monthly_counts[monthly_counts["Year"].isin(valid_years)]

    st.sidebar.markdown(f"<h3 style='color:{PRIMARY_BLUE};font-size:16px;font-weight:800;'>Page Filters</h3>", unsafe_allow_html=True)
    min_age        = int(data["Age"].min())
    max_age        = int(data["Age"].max())
    age_range      = st.sidebar.slider("Select Age Range", min_value=min_age, max_value=max_age, value=(min_age, max_age))
    gender_options = data["Gender"].dropna().unique().tolist()
    selected_gender= st.sidebar.multiselect("Select Gender", options=gender_options, default=gender_options)
    filtered_data  = data[(data["Age"].between(age_range[0], age_range[1])) & (data["Gender"].isin(selected_gender))]

    most_common_reason = filtered_data["reason"].mode()[0] if not filtered_data["reason"].isna().all() else "N/A"
    peak_age_group     = filtered_data["Age_Group"].mode()[0] if not filtered_data["Age_Group"].isna().all() else "N/A"
    top_city           = filtered_data["city"].value_counts().index[0] if not filtered_data["city"].isna().all() else "N/A"
    reason_display     = most_common_reason[:18] + "..." if len(str(most_common_reason)) > 18 else most_common_reason

    # ── KPIs ─────────────────────────────────────────────────────────────────
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    with kpi_col1:
        st.markdown(f"""<div class="kpi-box"><div class="kpi-label">Top Visit Reason</div>
        <div class="kpi-value">{reason_display}</div></div>""", unsafe_allow_html=True)
    with kpi_col2:
        st.markdown(f"""<div class="kpi-box"><div class="kpi-label">Peak Age Group</div>
        <div class="kpi-value">{str(peak_age_group)}</div></div>""", unsafe_allow_html=True)
    with kpi_col3:
        st.markdown(f"""<div class="kpi-box"><div class="kpi-label">Top City</div>
        <div class="kpi-value">{top_city}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # PATIENT JOURNEY TIMELINE
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("<div class='section-header'>Patient Journey Timeline</div>", unsafe_allow_html=True)
    st.caption("Select a patient to view their complete care pathway — appointments, admissions, discharges, and surgeries.")

    all_ids  = sorted(patients["patient_Id"].dropna().unique().tolist())
    name_col = next((c for c in patients.columns if c.lower() in ("fname","name","patient_name")), None)
    nm_map   = patients.set_index("patient_Id")[name_col].to_dict() if name_col else {}
    options  = [f"{pid}  —  {nm_map.get(pid,'')}" for pid in all_ids] if name_col else [str(p) for p in all_ids]
    opt_map  = dict(zip(options, all_ids))

    sel = st.selectbox("Search patient by ID / Name", options, key="p2_j_sel")
    pid = opt_map.get(sel)

    if pid:
        rows = []
        # Appointments
        pa = appointments[appointments["patient_Id"] == pid][["appointment_Date","appointment_status","doct_Id","reason"]]\
                         .dropna(subset=["appointment_Date"])
        pa["appointment_Date"] = pd.to_datetime(pa["appointment_Date"], errors="coerce")
        for _, r in pa.iterrows():
            st_ = str(r["appointment_status"]).strip()
            clr = SUCCESS_GREEN if "complet" in st_.lower() else CORAL if "cancel" in st_.lower() else \
                  "#FBBF24" if "no" in st_.lower() else SECONDARY_BLUE
            rows.append(dict(
                Start=r["appointment_Date"],
                Finish=r["appointment_Date"] + pd.Timedelta(hours=1),
                Category="Appointment",
                Label=f"Appointment — {st_}",
                Detail=f"Doctor: {r['doct_Id']} | Reason: {r.get('reason','N/A')}",
                Color=clr
            ))
        # Admissions + Discharges
        pb = bed_records[bed_records["patient_Id"] == pid][["admission_Date","discharge_Date","bed_No","LOS"]]\
                        .dropna(subset=["admission_Date"])
        for _, r in pb.iterrows():
            fin = r["discharge_Date"] if pd.notna(r["discharge_Date"]) else r["admission_Date"] + pd.Timedelta(days=1)
            los = int(r["LOS"]) if pd.notna(r["LOS"]) else "N/A"
            rows.append(dict(
                Start=r["admission_Date"], Finish=fin,
                Category="Admission",
                Label="Inpatient Stay",
                Detail=f"Bed: {r['bed_No']} | LOS: {los} days | Discharge: {fin.strftime('%d %b %Y') if pd.notna(r['discharge_Date']) else 'Pending'}",
                Color=PRIMARY_BLUE
            ))
        # Surgeries
        ps = surgeries[surgeries["patient_Id"] == pid][["surgery_Date","surgery_Type","surgeon_Id"]]\
                      .dropna(subset=["surgery_Date"])
        for _, r in ps.iterrows():
            rows.append(dict(
                Start=r["surgery_Date"],
                Finish=r["surgery_Date"] + pd.Timedelta(hours=3),
                Category="Surgery",
                Label=str(r["surgery_Type"]),
                Detail=f"Surgeon ID: {r['surgeon_Id']} | Type: {r['surgery_Type']}",
                Color=PURPLE
            ))

        if not rows:
            st.info("No recorded events found for this patient.")
        else:
            ev = pd.DataFrame(rows).sort_values("Start").reset_index(drop=True)
            fig_j = px.timeline(
                ev, x_start="Start", x_end="Finish", y="Category",
                color="Category",
                color_discrete_map={"Appointment": SECONDARY_BLUE, "Admission": PRIMARY_BLUE, "Surgery": PURPLE},
                hover_name="Label",
                hover_data={"Detail": True, "Start": True, "Finish": False, "Category": False}
            )
            fig_j.update_yaxes(categoryorder="array", categoryarray=["Appointment","Admission","Surgery"],
                               tickfont=TICK_FONT)
            fig_j.update_layout(
                xaxis=dict(tickfont=TICK_FONT, showgrid=True, gridcolor=GRID_COLOR,
                           title="Date", title_font=TITLE_FONT),
                yaxis=dict(title=""),
                height=300, margin=dict(l=20, r=20, t=40, b=60),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                showlegend=True,
                legend=dict(font=dict(size=13, color=text_color), orientation="h", y=1.1, x=0,
                            bgcolor='rgba(0,0,0,0)')
            )
            st.plotly_chart(fig_j, use_container_width=True, config={"displayModeBar": False})

            # Summary metrics for this patient
            m1, m2, m3, m4 = st.columns(4)
            n_appts   = len(pa)
            n_admits  = len(pb)
            n_surgs   = len(ps)
            avg_los_p = pb["LOS"].mean() if len(pb) > 0 else 0
            for col, lbl, val in [
                (m1, "Appointments",  n_appts),
                (m2, "Admissions",    n_admits),
                (m3, "Surgeries",     n_surgs),
                (m4, "Avg LOS (days)", f"{avg_los_p:.1f}" if avg_los_p else "N/A")
            ]:
                col.markdown(f"""<div style='background:linear-gradient(135deg,{PRIMARY_BLUE},{SECONDARY_BLUE});
                    padding:14px;border-radius:12px;text-align:center;'>
                    <div style='font-size:12px;font-weight:800;color:rgba(255,255,255,0.85);
                    text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>{lbl}</div>
                    <div style='font-size:28px;font-weight:900;color:white;'>{val}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("Full Event Log", expanded=False):
                d = ev[["Start","Category","Label","Detail"]].copy()
                d["Start"] = d["Start"].dt.strftime("%d %b %Y")
                st.dataframe(d, use_container_width=True, hide_index=True)

    # ── Map ────────────────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Patient Distribution Across India</div>", unsafe_allow_html=True)

    city_coordinates = {
        "Delhi": (28.6139, 77.2090, "Delhi"), "Mumbai": (19.0760, 72.8777, "Maharashtra"),
        "Bangalore": (12.9716, 77.5946, "Karnataka"), "Chennai": (13.0827, 80.2707, "Tamil Nadu"),
        "Kolkata": (22.5726, 88.3639, "West Bengal"), "Hyderabad": (17.3850, 78.4867, "Telangana"),
        "Ahmedabad": (23.0225, 72.5714, "Gujarat"), "Pune": (18.5204, 73.8567, "Maharashtra"),
        "Jaipur": (26.9124, 75.7873, "Rajasthan"), "Lucknow": (26.8467, 80.9462, "Uttar Pradesh"),
        "Kanpur": (26.4499, 80.3319, "Uttar Pradesh"), "Nagpur": (21.1458, 79.0882, "Maharashtra"),
        "Indore": (22.7196, 75.8577, "Madhya Pradesh"), "Bhopal": (23.2599, 77.4126, "Madhya Pradesh"),
        "Visakhapatnam": (17.6868, 83.2185, "Andhra Pradesh"),
    }

    patients_copy = patients.copy()
    patients_copy["city"] = patients_copy["city"].astype(str).str.strip().str.title()
    city_counts_map = patients_copy.groupby("city").size().reset_index(name="Patient_Count")

    def get_coordinates(city_name):
        return city_coordinates.get(city_name, (None, None, None))

    city_counts_map[["lat","lon","state"]] = city_counts_map["city"].apply(lambda x: pd.Series(get_coordinates(x)))
    city_counts_mapped = city_counts_map.dropna().nlargest(15, "Patient_Count")

    if len(city_counts_mapped) > 0:
        min_val = city_counts_mapped["Patient_Count"].min()
        max_val = city_counts_mapped["Patient_Count"].max()
        fig_map = px.scatter_mapbox(
            city_counts_mapped, lat="lat", lon="lon",
            color="Patient_Count", size="Patient_Count",
            hover_name="city",
            hover_data={"Patient_Count": True, "state": True, "lat": False, "lon": False},
            zoom=3.8, center=dict(lat=22.5937, lon=78.9629),
            mapbox_style="carto-positron",
            color_continuous_scale=[[0.0,"#FFC107"],[0.5,"#FF6F00"],[1.0,"#FF1744"]],
            range_color=(min_val, max_val), size_max=50
        )
        fig_map.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_colorbar=dict(
                title=dict(text="<b>Patient Count</b>", font=dict(size=14, family="Arial Black", color='#1E293B')),
                thickness=25, len=0.7,
                tickfont=dict(size=13, family="Arial Black", color='#1E293B')
            ),
            height=560, font=dict(color='#1E293B')
        )
        st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False})

    # ── Gender Distribution ────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Gender Distribution</div>", unsafe_allow_html=True)

    gender_counts = filtered_data["Gender"].value_counts()
    fig1 = go.Figure(data=[go.Pie(
        labels=gender_counts.index, values=gender_counts.values, hole=0.5,
        marker=dict(colors=[CORAL, SECONDARY_BLUE, SUCCESS_GREEN], line=dict(color='white', width=4)),
        textfont=dict(size=14, family="Arial Black", color=text_color),
        hovertemplate='<b>%{label}</b><br>Count: %{value:,}<br>%{percent}<extra></extra>'
    )])
    fig1.update_traces(textposition='outside', textinfo='label+percent', pull=[0.05, 0.05, 0.05])
    fig1.update_layout(
        height=500, showlegend=True,
        legend=dict(font=dict(size=14, family="Arial Black", color=text_color),
                    bgcolor='rgba(0,0,0,0)', x=1.05, y=0.5),
        margin=dict(l=60, r=200, t=40, b=40),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

    # ── Age Groups ─────────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Age Groups</div>", unsafe_allow_html=True)

    age_group_counts = filtered_data["Age_Group"].value_counts().sort_index()
    ag_labels = age_group_counts.index.astype(str).tolist()
    ag_values = age_group_counts.values.tolist()

    fig3 = go.Figure()
    for lbl, val in zip(ag_labels, ag_values):
        fig3.add_shape(type="line", x0=0, x1=val, y0=lbl, y1=lbl,
                       line=dict(color=PURPLE, width=4))
    fig3.add_trace(go.Scatter(
        x=ag_values, y=ag_labels, mode="markers",
        marker=dict(color=PURPLE, size=18, line=dict(color="white", width=4)),
        hovertemplate="<b>Age: %{y}</b><br>Patients: %{x:,}<extra></extra>",
        showlegend=False
    ))
    fig3.update_layout(
        xaxis_title="<b>Patients</b>", yaxis_title="<b>Age Group</b>",
        xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, rangemode="tozero",
                   showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=False),
        height=450, margin=dict(l=20, r=20, t=30, b=50),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

    # ── Top 10 Cities ──────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Top 10 Cities by Patient Count</div>", unsafe_allow_html=True)

    city_counts_top = filtered_data["city"].value_counts().head(10).reset_index()
    city_counts_top.columns = ["City","Patients"]
    city_counts_top = city_counts_top.sort_values("Patients", ascending=True)

    fig_city = go.Figure()
    fig_city.add_trace(go.Bar(
        x=city_counts_top["Patients"], y=city_counts_top["City"], orientation="h",
        marker=dict(color=CORAL, cornerradius=8, line=dict(color='white', width=1)),
        hovertemplate="<b>%{y}</b><br>Patients: %{x:,}<extra></extra>"
    ))
    fig_city.update_layout(
        xaxis_title="<b>Number of Patients</b>", yaxis_title="",
        xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(tickfont=TICK_FONT),
        height=500, margin=dict(l=20, r=20, t=30, b=50), showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_city, use_container_width=True, config={'displayModeBar': False})

    # ── Payment Methods ────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Payment Methods</div>", unsafe_allow_html=True)

    payment_counts = filtered_data["mode_of_payment"].value_counts()
    fig_pay = go.Figure(data=[go.Pie(
        labels=payment_counts.index, values=payment_counts.values, hole=0,
        marker=dict(colors=[SUCCESS_GREEN, SECONDARY_BLUE, PURPLE, CORAL, "#FBBF24", "#06B6D4"],
                    line=dict(color='white', width=4)),
        textfont=dict(size=14, family="Arial Black", color=text_color),
        hovertemplate="<b>%{label}</b><br>Count: %{value:,}<br>%{percent}<extra></extra>"
    )])
    fig_pay.update_traces(textposition='outside', textinfo='label+percent', pull=[0.05]*6)
    fig_pay.update_layout(
        height=500, showlegend=True,
        legend=dict(font=dict(size=14, family="Arial Black", color=text_color),
                    bgcolor='rgba(0,0,0,0)', x=1.05, y=0.5),
        margin=dict(l=60, r=200, t=40, b=40),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_pay, use_container_width=True, config={'displayModeBar': False})

    # ── Appointment Trend 2024 vs 2025 ─────────────────────────────────────────
    st.markdown("<div class='section-header'>Appointment Trend: 2024 vs 2025</div>", unsafe_allow_html=True)

    fig_line = go.Figure()
    line_styles = {2024: dict(color=SECONDARY_BLUE, width=5), 2025: dict(color=CORAL, width=5)}

    for year in sorted(monthly_counts["Year"].unique()):
        yd = monthly_counts[monthly_counts["Year"] == year].copy()
        yd["Month_Name"] = pd.Categorical(yd["Month_Name"], categories=MONTH_ORDER, ordered=True)
        yd = yd.sort_values("Month_Name")
        style = line_styles.get(year, dict(color="#95A5A6", width=3))
        fig_line.add_trace(go.Scatter(
            x=yd["Month_Name"], y=yd["Count"], mode="lines+markers", name=str(year),
            line=dict(color=style["color"], width=style["width"]),
            marker=dict(size=10, color=style["color"], line=dict(color="white", width=3)),
            hovertemplate=f"<b>{year}</b><br>%{{x}}: %{{y:,}}<extra></extra>"
        ))

    peak_row = monthly_counts.loc[monthly_counts["Count"].idxmax()]
    fig_line.add_annotation(
        x=peak_row["Month_Name"], y=peak_row["Count"],
        text=f"Peak: {int(peak_row['Count'])}",
        showarrow=True, arrowhead=2, arrowcolor=CORAL, arrowwidth=3,
        font=dict(color=CORAL, size=14, family="Arial Black"),
        yshift=15, bgcolor="rgba(255,255,255,0.9)",
        bordercolor=CORAL, borderwidth=2, borderpad=6
    )
    fig_line.update_xaxes(tickmode='array', tickvals=MONTH_ORDER[::4], ticktext=MONTH_ORDER[::4])
    fig_line.update_layout(
        xaxis_title="<b>Month</b>", yaxis_title="<b>Appointments</b>",
        xaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(tickfont=TICK_FONT, title_font=TITLE_FONT, showgrid=True, gridcolor=GRID_COLOR),
        height=500, margin=dict(l=20, r=20, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        legend=dict(font=dict(size=14, family="Arial Black", color=text_color), bgcolor='rgba(0,0,0,0)')
    )
    st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<br>", unsafe_allow_html=True)