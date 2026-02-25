import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime

# ── Data loader ────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading data...")
def _load_p6():
    xls     = pd.ExcelFile("data/dataFinal.xlsx")
    patients= pd.read_excel(xls, "Patients")
    appts   = pd.read_excel(xls, "Appointment")
    bed_rec = pd.read_excel(xls, "BedRecords")
    bed_df  = pd.read_excel(xls, "Bed")
    ward_df = pd.read_excel(xls, "Ward")
    surg    = pd.read_excel(xls, "SurgeryRecord")
    doctors = pd.read_excel(xls, "Doctor")
    depts   = pd.read_excel(xls, "Department")
    nurses  = pd.read_excel(xls, "Nurse")

    appts["appointment_Date"] = pd.to_datetime(appts["appointment_Date"],  errors="coerce")
    bed_rec["admission_Date"] = pd.to_datetime(bed_rec["admission_Date"],  errors="coerce")
    bed_rec["discharge_Date"] = pd.to_datetime(bed_rec["discharge_Date"],  errors="coerce")
    surg["surgery_Date"]      = pd.to_datetime(surg["surgery_Date"],       errors="coerce")
    bed_rec["LOS"]            = (bed_rec["discharge_Date"] - bed_rec["admission_Date"]).dt.days

    bed_full = (bed_rec
        .merge(bed_df,  on="bed_No",  how="left")
        .merge(ward_df, on="ward_No", how="left")
        .merge(depts,   on="dept_Id", how="left"))

    return patients, appts, bed_rec, bed_full, surg, doctors, depts, nurses


# ── Matplotlib chart helpers ───────────────────────────────────────────────────
PALETTE = ["#1E40AF","#3B82F6","#059669","#DC2626","#D97706","#7C3AED","#0D9488","#64748B"]

def _fig_to_bytes(fig, dpi=150):
    buf = io.BytesIO()
    fig.patch.set_facecolor('white')
    for ax in fig.get_axes():
        ax.set_facecolor('white')
    fig.subplots_adjust(left=0.12, right=0.97, top=0.92, bottom=0.18)
    fig.savefig(buf, format="png", dpi=dpi, facecolor='white', edgecolor='none')
    buf.seek(0)
    return buf.read()

def _make_bar_h(labels, values, title, color="#1E40AF", figsize=(9,4)):
    fig, ax = plt.subplots(figsize=figsize, facecolor="white")
    y   = range(len(labels))
    bars= ax.barh(y, values, color=color, height=0.6)
    ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontsize=9)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Count", fontsize=9)
    ax.spines[["top","right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.3)
    for bar in bars:
        ax.text(bar.get_width() + max(values)*0.01, bar.get_y()+bar.get_height()/2,
                f"{int(bar.get_width()):,}", va="center", fontsize=8)
    fig.tight_layout(); return fig

def _make_bar_v(labels, values, title, colors_list=None, figsize=(9,4)):
    fig, ax = plt.subplots(figsize=figsize, facecolor="white")
    c = colors_list or PALETTE[:len(labels)]
    ax.bar(range(len(labels)), values, color=c[:len(labels)], width=0.6)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.spines[["top","right"]].set_visible(False); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); return fig

def _make_line(x, ys, labels, title, colors_list=None, figsize=(9,4)):
    fig, ax = plt.subplots(figsize=figsize, facecolor="white")
    c = colors_list or PALETTE
    for i, (y, lbl) in enumerate(zip(ys, labels)):
        ax.plot(x, y, marker="o", markersize=4, linewidth=2, color=c[i % len(c)], label=lbl)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.legend(fontsize=9); ax.spines[["top","right"]].set_visible(False); ax.grid(alpha=0.3)
    step = max(1, len(x)//8)
    ax.set_xticks(range(0, len(x), step))
    ax.set_xticklabels([x[i] for i in range(0, len(x), step)], rotation=45, ha="right", fontsize=8)
    fig.tight_layout(); return fig

def _make_pie(labels, values, title, figsize=(7,5)):
    fig, ax = plt.subplots(figsize=figsize, facecolor="white")
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, autopct="%1.1f%%", colors=PALETTE[:len(labels)],
        startangle=140, pctdistance=0.75, wedgeprops=dict(width=0.55))
    for t in autotexts: t.set_fontsize(8)
    for t in texts:     t.set_fontsize(8)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=12)
    fig.tight_layout(); return fig

def _make_heatmap(data_2d, row_labels, col_labels, title, figsize=(11,5)):
    fig, ax = plt.subplots(figsize=figsize, facecolor="white")
    im = ax.imshow(data_2d, cmap="Reds", aspect="auto")
    ax.set_xticks(range(len(col_labels))); ax.set_xticklabels(col_labels, rotation=45, ha="right", fontsize=7)
    ax.set_yticks(range(len(row_labels))); ax.set_yticklabels(row_labels, fontsize=8)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            v = data_2d[i,j]
            ax.text(j, i, str(int(v)), ha="center", va="center", fontsize=7,
                    color="white" if v > data_2d.max()*0.5 else "black")
    plt.colorbar(im, ax=ax, shrink=0.8); fig.tight_layout(); return fig

def _make_grouped_bar(categories, groups, values_dict, title, figsize=(9,4)):
    fig, ax = plt.subplots(figsize=figsize, facecolor="white")
    x = np.arange(len(categories)); w = 0.8 / len(groups)
    for i, grp in enumerate(groups):
        ax.bar(x + i*w - 0.4 + w/2, values_dict[grp], width=w, label=grp, color=PALETTE[i % len(PALETTE)])
    ax.set_xticks(x); ax.set_xticklabels(categories, rotation=45, ha="right", fontsize=8)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.legend(fontsize=8, ncol=min(3, len(groups))); ax.spines[["top","right"]].set_visible(False); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); return fig


# ── Build chart by ID ─────────────────────────────────────────────────────────
def build_chart(chart_id, patients, appts, bed_rec, bed_full, surg, doctors, depts, nurses):
    MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    if chart_id == "p1_patient_flow":
        flow_apps = appts.dropna(subset=["appointment_Date"]).groupby(appts["appointment_Date"].dt.to_period("M")).size()
        flow_adm  = bed_rec.dropna(subset=["admission_Date"]).groupby(bed_rec["admission_Date"].dt.to_period("M")).size()
        df = pd.concat([flow_apps.rename("Appointments"), flow_adm.rename("Admissions")], axis=1).fillna(0)
        df.index = df.index.to_timestamp().strftime("%b %Y")
        fig = _make_line(list(df.index), [df["Appointments"].tolist(), df["Admissions"].tolist()],
                         ["Appointments","Admissions"], "Patient Flow Trends", [PALETTE[0], PALETTE[3]])
        return "Patient Flow Trends", fig, None

    if chart_id == "p1_outcomes":
        s   = appts["appointment_status"].value_counts()
        fig = _make_pie(s.index.tolist(), s.values.tolist(), "Appointment Outcomes")
        return "Appointment Outcomes", fig, None

    if chart_id == "p1_dept_demand":
        dept_flow = bed_full.groupby("dept_Name").size().reset_index(name="Admissions").sort_values("Admissions")
        fig = _make_bar_h(dept_flow["dept_Name"].tolist(), dept_flow["Admissions"].tolist(), "Department Demand")
        return "Department Demand", fig, None

    if chart_id == "p1_peak_months":
        appts["month_name"] = appts["appointment_Date"].dt.strftime("%b")
        appts["year"]       = appts["appointment_Date"].dt.year
        mc    = appts.groupby(["year","month_name"]).size().reset_index(name="Count")
        years = sorted(mc["year"].dropna().unique())
        groups= {str(y): [] for y in years}
        for mo in MONTH_ORDER:
            for y in years:
                row = mc[(mc["year"]==y) & (mc["month_name"]==mo)]
                groups[str(y)].append(int(row["Count"].values[0]) if len(row) else 0)
        fig = _make_grouped_bar(MONTH_ORDER, [str(y) for y in years], groups, "Peak Appointment Months")
        return "Peak Appointment Months", fig, None

    if chart_id == "p1_completion":
        monthly_total = appts.groupby(appts["appointment_Date"].dt.to_period("M")).size()
        monthly_comp  = appts[appts["appointment_status"].astype(str).str.lower()=="completed"]\
                            .groupby(appts["appointment_Date"].dt.to_period("M")).size()
        rate = (monthly_comp / monthly_total * 100).fillna(0).reset_index()
        rate.columns = ["Month","Rate"]
        rate["Month"] = rate["Month"].dt.to_timestamp().dt.strftime("%b %Y")
        fig = _make_line(rate["Month"].tolist(), [rate["Rate"].tolist()],
                         ["Completion Rate %"], "Appointment Completion Rate", [PALETTE[2]])
        return "Appointment Completion Rate", fig, None

    if chart_id == "p2_gender":
        col = next((c for c in patients.columns if "gender" in c.lower()), None)
        if col:
            g   = patients[col].value_counts()
            fig = _make_pie(g.index.tolist(), g.values.tolist(), "Gender Distribution")
        else: fig = None
        return "Gender Distribution", fig, None

    if chart_id == "p2_age":
        age_col = next((c for c in patients.columns if "age" in c.lower()), None)
        if age_col:
            bins = [0,18,35,50,65,120]; lbls = ["0-18","19-35","36-50","51-65","65+"]
            patients["age_group"] = pd.cut(patients[age_col], bins=bins, labels=lbls)
            ag  = patients["age_group"].value_counts().reindex(lbls).fillna(0)
            fig = _make_bar_v(ag.index.tolist(), ag.values.tolist(), "Age Group Distribution")
        else: fig = None
        return "Age Group Distribution", fig, None

    if chart_id == "p2_top_cities":
        city_col = next((c for c in patients.columns if "city" in c.lower()), None)
        if city_col:
            top = patients[city_col].value_counts().head(10)
            fig = _make_bar_h(top.index.tolist(), top.values.tolist(), "Top 10 Cities by Patient Count")
        else: fig = None
        return "Top 10 Cities by Patient Count", fig, None

    if chart_id == "p2_payment":
        pay_col = next((c for c in patients.columns if "payment" in c.lower()), None)
        if pay_col:
            p   = patients[pay_col].value_counts()
            fig = _make_pie(p.index.tolist(), p.values.tolist(), "Payment Methods")
        else: fig = None
        return "Payment Methods", fig, None

    if chart_id == "p2_appt_trend":
        appts["year"]  = appts["appointment_Date"].dt.year
        appts["month"] = appts["appointment_Date"].dt.month
        appts["month_name"] = appts["appointment_Date"].dt.strftime("%b")
        mc    = appts.groupby(["year","month","month_name"]).size().reset_index(name="Count")
        years = sorted(mc["year"].dropna().unique())[-2:]
        ys, lbls = [], []
        for y in years:
            sub = mc[mc["year"]==y].sort_values("month")
            ys.append(sub["Count"].tolist()); lbls.append(str(int(y)))
        fig = _make_line(MONTH_ORDER[:max(len(y) for y in ys)], ys, lbls, "Appointment Trend 2024 vs 2025")
        return "Appointment Trend 2024 vs 2025", fig, None

    if chart_id == "p3_top_surgeries":
        top = surg["surgery_Type"].value_counts().head(10)
        fig = _make_bar_h(top.index.tolist(), top.values.tolist(), "Top 10 Most Common Surgical Procedures", color=PALETTE[5])
        return "Top 10 Surgical Procedures", fig, None

    if chart_id == "p3_surgery_trend":
        surg["month"] = surg["surgery_Date"].dt.to_period("M")
        st_trend = surg.groupby("month").size().reset_index(name="Count")
        st_trend["month"] = st_trend["month"].dt.to_timestamp().dt.strftime("%b %Y")
        fig = _make_line(st_trend["month"].tolist(), [st_trend["Count"].tolist()], ["Surgeries"], "Surgery Trend Over Time", [PALETTE[5]])
        return "Surgery Trend Over Time", fig, None

    if chart_id == "p3_surgery_dept":
        sc = surg.merge(doctors[["doct_Id","dept_Id"]], left_on="surgeon_Id", right_on="doct_Id", how="left")\
                 .merge(depts[["dept_Id","dept_Name"]], on="dept_Id", how="left")
        sc = sc.groupby("dept_Name").size().reset_index(name="Count").sort_values("Count")
        fig = _make_bar_h(sc["dept_Name"].tolist(), sc["Count"].tolist(), "Surgery Distribution by Department", color=PALETTE[2])
        return "Surgery Distribution by Department", fig, None

    if chart_id == "p3_heatmap":
        doc_dept = doctors.merge(depts, on="dept_Id", how="left")[["doct_Id","FName","dept_Name"]]
        hd = surg.merge(doc_dept, left_on="surgeon_Id", right_on="doct_Id", how="inner").dropna(subset=["FName","dept_Name"])
        hc = hd.groupby(["FName","dept_Name"]).size().reset_index(name="Count")
        top10 = hc.groupby("FName")["Count"].sum().nlargest(10).index
        hc  = hc[hc["FName"].isin(top10)]
        piv = hc.pivot(index="FName", columns="dept_Name", values="Count").fillna(0)
        fig = _make_heatmap(piv.values, piv.index.tolist(), piv.columns.tolist(), "Doctor-Department Surgery Heatmap")
        return "Doctor-Department Surgery Heatmap", fig, None

    if chart_id == "p4_los":
        if "dept_Name" in bed_full.columns and "LOS" in bed_full.columns:
            los = bed_full.groupby("dept_Name")["LOS"].mean().dropna().sort_values()
            fig = _make_bar_h(los.index.tolist(), los.values.round(1).tolist(), "Average Length of Stay by Department")
        else: fig = None
        return "Avg LOS by Department", fig, None

    if chart_id == "p4_ward":
        if "ward_Name" in bed_full.columns:
            w   = bed_full.groupby("ward_Name")["admission_Id"].count().sort_values()
            fig = _make_bar_h(w.index.tolist(), w.values.tolist(), "Ward Utilization Overview", color=PALETTE[1])
        else: fig = None
        return "Ward Utilization", fig, None

    if chart_id == "p4_flow":
        adm_t = bed_rec.dropna(subset=["admission_Date"]).groupby(bed_rec["admission_Date"].dt.to_period("M")).size()
        dis_t = bed_rec.dropna(subset=["discharge_Date"]).groupby(bed_rec["discharge_Date"].dt.to_period("M")).size()
        df = pd.concat([adm_t.rename("Admissions"), dis_t.rename("Discharges")], axis=1).fillna(0)
        df.index = df.index.to_timestamp().strftime("%b %Y")
        fig = _make_line(list(df.index), [df["Admissions"].tolist(), df["Discharges"].tolist()],
                         ["Admissions","Discharges"], "Patient Flow — Admissions vs Discharges", [PALETTE[0], PALETTE[2]])
        return "Admissions vs Discharges", fig, None

    if chart_id == "p5_nurse_dist":
        nurse_dept = nurses.merge(depts, on="dept_Id", how="left")
        nd  = nurse_dept.groupby("dept_Name")["nurse_Id"].nunique().sort_values()
        fig = _make_bar_h(nd.index.tolist(), nd.values.tolist(), "Nurse Distribution by Department", color=PALETTE[4])
        return "Nurse Distribution by Department", fig, None

    if chart_id == "p5_heatmap":
        doc_dept = doctors.merge(depts, on="dept_Id", how="left")[["doct_Id","FName","dept_Name"]]
        merged   = appts.merge(doc_dept, on="doct_Id", how="left").dropna(subset=["FName","dept_Name"])
        hc       = merged.groupby(["FName","dept_Name"]).size().reset_index(name="Count")
        top10    = hc.groupby("FName")["Count"].sum().nlargest(10).index
        hc       = hc[hc["FName"].isin(top10)]
        piv      = hc.pivot(index="FName", columns="dept_Name", values="Count").fillna(0)
        fig      = _make_heatmap(piv.values, piv.index.tolist(), piv.columns.tolist(), "Doctor Workload Heatmap (Appointments per Dept)")
        return "Doctor Workload Heatmap", fig, None

    if chart_id == "p5_pt_nurse_ratio":
        nurse_dept = nurses.merge(depts, on="dept_Id", how="left")\
                           .groupby("dept_Name")["nurse_Id"].nunique().reset_index(name="Nurses")
        if "dept_Name" in bed_full.columns:
            pt_dept  = bed_full.groupby("dept_Name")["patient_Id"].nunique().reset_index(name="Patients")
            ratio_df = pt_dept.merge(nurse_dept, on="dept_Name", how="inner")
            ratio_df["Ratio"] = (ratio_df["Patients"] / ratio_df["Nurses"].replace(0,1)).round(1)
            ratio_df = ratio_df.sort_values("Ratio")
            fig = _make_bar_h(ratio_df["dept_Name"].tolist(), ratio_df["Ratio"].tolist(),
                              "Patient-to-Nurse Ratio by Department", color=PALETTE[3])
        else: fig = None
        return "Patient-to-Nurse Ratio", fig, None

    if chart_id == "p6_capacity_proj":
        n_months = max(bed_rec["admission_Date"].dt.to_period("M").nunique(), 1)
        mo_adm   = len(bed_rec) / n_months
        cur_beds = bed_rec["bed_No"].nunique()
        avg_los  = bed_rec["LOS"].dropna().mean() or 5
        gr, hor  = 20, 12
        mx       = list(range(1, hor+1))
        pvol     = [mo_adm * (1 + (gr/100) * (m/hor)) for m in mx]
        pbeds    = [(v * avg_los) / (30 * 0.80) for v in pvol]
        fig, ax1 = plt.subplots(figsize=(9,4), facecolor="white")
        ax2 = ax1.twinx()
        ax1.plot(mx, pvol,  "o-", color=PALETTE[0], linewidth=2, markersize=5, label="Projected Admissions")
        ax1.axhline(mo_adm, color=PALETTE[3], linewidth=2, linestyle="--", label="Current Baseline")
        ax2.plot(mx, pbeds, "s-", color=PALETTE[5], linewidth=2, markersize=5, label="Beds Required")
        ax2.axhline(cur_beds, color=PALETTE[6], linewidth=2, linestyle="--", label="Current Beds")
        ax1.set_xlabel("Month"); ax1.set_ylabel("Monthly Admissions")
        ax2.set_ylabel("Beds Required")
        ax1.set_title("Capacity Projection (+20% growth, 12 months)", fontsize=12, fontweight="bold")
        lines1, labs1 = ax1.get_legend_handles_labels()
        lines2, labs2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1+lines2, labs1+labs2, fontsize=8, loc="upper left")
        ax1.spines[["top"]].set_visible(False)
        fig.tight_layout()
        return "Capacity Projection", fig, None

    return chart_id, None, None


# ── PDF builder ────────────────────────────────────────────────────────────────
def build_pdf(selected_chart_ids, r_title, r_author, r_dept, r_notes,
              kpi_data, alert_data,
              patients, appts, bed_rec, bed_full, surg, doctors, depts, nurses):

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm, mm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Image, Table, TableStyle, HRFlowable,
                                        PageBreak, KeepTogether)
        from reportlab.lib.colors import HexColor
        from reportlab.platypus.flowables import Flowable
    except ImportError:
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab", "-q"])
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm, mm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Image, Table, TableStyle, HRFlowable,
                                        PageBreak, KeepTogether)
        from reportlab.lib.colors import HexColor
        from reportlab.platypus.flowables import Flowable

    C_NAVY    = HexColor("#0F2456")
    C_BLUE    = HexColor("#1E40AF")
    C_BLUE2   = HexColor("#2563EB")
    C_LBLUE   = HexColor("#EFF6FF")
    C_LBLUE2  = HexColor("#DBEAFE")
    C_GRAY    = HexColor("#64748B")
    C_LGRAY   = HexColor("#F1F5F9")
    C_BLACK   = HexColor("#0F172A")
    C_WHITE   = colors.white
    C_RED     = HexColor("#DC2626")
    C_RED_BG  = HexColor("#FEF2F2")
    C_GREEN   = HexColor("#059669")
    C_GREEN_BG= HexColor("#F0FDF4")
    C_AMBER   = HexColor("#D97706")
    C_AMBER_BG= HexColor("#FFFBEB")
    C_BORDER  = HexColor("#CBD5E1")
    C_DIVIDER = HexColor("#E2E8F0")

    PAGE_M_L = 2.0 * cm; PAGE_M_R = 2.0 * cm
    PAGE_M_T = 2.5 * cm; PAGE_M_B = 2.0 * cm
    buf = io.BytesIO()
    report_date_str   = datetime.now().strftime("%d %B %Y, %H:%M")
    report_date_short = datetime.now().strftime("%d %b %Y")

    def _on_page(canvas_obj, doc_obj):
        W_pg, H_pg = A4; pg = doc_obj.page
        canvas_obj.saveState()
        canvas_obj.setFillColor(C_DIVIDER)
        canvas_obj.rect(PAGE_M_L, 1.2*cm, W_pg - PAGE_M_L - PAGE_M_R, 0.3, fill=1, stroke=0)
        canvas_obj.setFont("Helvetica", 7); canvas_obj.setFillColor(C_GRAY)
        canvas_obj.drawString(PAGE_M_L, 0.9*cm, f"Confidential — {r_title} — {report_date_short}")
        canvas_obj.drawRightString(W_pg - PAGE_M_R, 0.9*cm, f"Page {pg}")
        canvas_obj.restoreState()
        if pg > 1:
            canvas_obj.saveState()
            canvas_obj.setFillColor(C_NAVY)
            canvas_obj.rect(0, H_pg - 1.1*cm, W_pg, 1.1*cm, fill=1, stroke=0)
            canvas_obj.setFont("Helvetica-Bold", 9); canvas_obj.setFillColor(C_WHITE)
            canvas_obj.drawString(PAGE_M_L, H_pg - 0.72*cm, r_title)
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.drawRightString(W_pg - PAGE_M_R, H_pg - 0.72*cm, report_date_str)
            canvas_obj.restoreState()

    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=PAGE_M_L, rightMargin=PAGE_M_R,
        topMargin=PAGE_M_T, bottomMargin=PAGE_M_B, onPage=_on_page)
    W, H = A4; body_w = W - PAGE_M_L - PAGE_M_R

    def S(name, **kw): return ParagraphStyle(name, **kw)

    sTitle = S("sTitle", fontSize=28, fontName="Helvetica-Bold", textColor=C_NAVY, alignment=TA_CENTER, spaceAfter=6, leading=34)
    sMeta  = S("sMeta",  fontSize=10, fontName="Helvetica", textColor=C_GRAY, alignment=TA_CENTER, spaceAfter=3, leading=15)
    sH1    = S("sH1",    fontSize=13, fontName="Helvetica-Bold", textColor=C_WHITE, alignment=TA_LEFT, spaceAfter=0, spaceBefore=0, leading=17, leftIndent=6)
    sH2    = S("sH2",    fontSize=11, fontName="Helvetica-Bold", textColor=C_BLUE, alignment=TA_LEFT, spaceBefore=6, spaceAfter=4, leading=15)
    sBody  = S("sBody",  fontSize=9,  fontName="Helvetica", textColor=C_BLACK, spaceAfter=4, leading=14, alignment=TA_JUSTIFY)
    sCapt  = S("sCapt",  fontSize=8,  fontName="Helvetica-Oblique", textColor=C_GRAY, alignment=TA_CENTER, spaceAfter=6)
    sKPIv  = S("sKPIv",  fontSize=20, fontName="Helvetica-Bold", textColor=C_BLUE2, alignment=TA_CENTER, spaceAfter=2, leading=24)
    sKPIl  = S("sKPIl",  fontSize=8,  fontName="Helvetica", textColor=C_GRAY, alignment=TA_CENTER, leading=11)
    sAlrtTt= S("sAlrtTt",fontSize=8,  fontName="Helvetica-Bold", textColor=C_BLACK, alignment=TA_LEFT)
    sAlrtDt= S("sAlrtDt",fontSize=8,  fontName="Helvetica", textColor=C_BLACK, alignment=TA_LEFT, leading=12)

    story = []

    def section_heading(text):
        hdr_tbl = Table([[Paragraph(text, sH1)]], colWidths=[body_w], rowHeights=[0.65*cm])
        hdr_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), C_BLUE),
            ("TOPPADDING",    (0,0),(-1,-1), 8),
            ("BOTTOMPADDING", (0,0),(-1,-1), 0),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("RIGHTPADDING",  (0,0),(-1,-1), 6),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        return hdr_tbl

    # Cover page
    story.append(Spacer(1, 2.0*cm))
    story.append(HRFlowable(width="100%", thickness=5, color=C_NAVY, spaceAfter=0))
    story.append(HRFlowable(width="100%", thickness=2, color=C_BLUE2, spaceAfter=14))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(r_title, sTitle))
    story.append(Spacer(1, 0.5*cm))

    meta_data = [["Prepared by:", r_author],["Department:", r_dept],["Generated:", report_date_str]]
    col_label_w = 3.0 * cm; col_value_w = body_w - col_label_w
    sMetaLbl = S("sMetaLbl", fontSize=9, fontName="Helvetica-Bold", textColor=C_GRAY, alignment=TA_LEFT)
    sMetaVal = S("sMetaVal", fontSize=9, fontName="Helvetica", textColor=C_BLACK, alignment=TA_LEFT)
    meta_rows = [[Paragraph(k, sMetaLbl), Paragraph(v, sMetaVal)] for k, v in meta_data]
    meta_tbl  = Table(meta_rows, colWidths=[col_label_w, col_value_w])
    meta_tbl.setStyle(TableStyle([
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_DIVIDER, spaceAfter=10))
    story.append(Spacer(1, 0.4*cm))

    if r_notes and r_notes.strip():
        story.append(section_heading("Executive Summary"))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(r_notes, sBody))
        story.append(Spacer(1, 0.5*cm))

    # KPI cards
    if kpi_data:
        story.append(section_heading("Key Performance Indicators"))
        story.append(Spacer(1, 0.35*cm))
        n_cols = 4; col_w = body_w / n_cols
        for row_start in range(0, len(kpi_data), n_cols):
            chunk = kpi_data[row_start : row_start + n_cols]
            while len(chunk) < n_cols: chunk.append(("",""))
            card_cells = []
            for lbl, val in chunk:
                if lbl == "" and val == "":
                    card_cells.append(""); continue
                inner = Table([[Paragraph(str(val), sKPIv)],[Paragraph(str(lbl), sKPIl)]],
                              colWidths=[col_w - 0.4*cm])
                inner.setStyle(TableStyle([
                    ("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                    ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),
                    ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                ]))
                card_cells.append(inner)
            row_tbl = Table([card_cells], colWidths=[col_w]*n_cols)
            row_tbl.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,-1),C_LBLUE),
                ("BOX",(0,0),(-1,-1),0.75,C_BLUE),
                ("INNERGRID",(0,0),(-1,-1),0.5,C_LBLUE2),
                ("TOPPADDING",(0,0),(-1,-1),14),("BOTTOMPADDING",(0,0),(-1,-1),14),
                ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
                ("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ]))
            story.append(row_tbl); story.append(Spacer(1, 0.25*cm))
        story.append(Spacer(1, 0.3*cm))

    # Operational alerts
    if alert_data:
        story.append(section_heading("Operational Alerts"))
        story.append(Spacer(1, 0.35*cm))
        lvl_fg  = {"RED": C_RED,     "AMBER": C_AMBER,     "GREEN": C_GREEN}
        lvl_bg  = {"RED": C_RED_BG,  "AMBER": C_AMBER_BG,  "GREEN": C_GREEN_BG}
        sHdrCell= S("sHdrCell", fontSize=8, fontName="Helvetica-Bold", textColor=C_WHITE, alignment=TA_LEFT)
        col_lvl_w   = 1.8 * cm; col_title_w = 5.2 * cm; col_det_w = body_w - col_lvl_w - col_title_w
        rows = [[Paragraph("Level",sHdrCell), Paragraph("Alert",sHdrCell), Paragraph("Detail",sHdrCell)]]
        for lvl, title, detail in alert_data:
            sLvl = S(f"sLvl_{lvl}", fontSize=8, fontName="Helvetica-Bold",
                     textColor=lvl_fg.get(lvl, C_BLACK), alignment=TA_CENTER)
            rows.append([Paragraph(lvl, sLvl), Paragraph(title, sAlrtTt), Paragraph(detail, sAlrtDt)])
        alert_tbl = Table(rows, colWidths=[col_lvl_w, col_title_w, col_det_w])
        ts = TableStyle([
            ("BACKGROUND",(0,0),(-1,0),C_NAVY),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("TOPPADDING",(0,0),(-1,0),7),
            ("BOTTOMPADDING",(0,0),(-1,0),7),("LEFTPADDING",(0,0),(-1,-1),8),
            ("RIGHTPADDING",(0,0),(-1,-1),6),("FONTSIZE",(0,1),(-1,-1),8),
            ("TOPPADDING",(0,1),(-1,-1),7),("BOTTOMPADDING",(0,1),(-1,-1),7),
            ("GRID",(0,0),(-1,-1),0.4,C_BORDER),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ])
        for i, (lvl, _, _) in enumerate(alert_data, start=1):
            ts.add("BACKGROUND",(0,i),(-1,i), lvl_bg.get(lvl, C_WHITE))
            ts.add("BACKGROUND",(0,i),(0,i),  lvl_bg.get(lvl, C_LGRAY))
        alert_tbl.setStyle(ts)
        story.append(alert_tbl); story.append(Spacer(1, 0.5*cm))

    # Charts
    if selected_chart_ids:
        story.append(PageBreak())
        story.append(section_heading("Dashboard Visualizations"))
        story.append(Spacer(1, 0.4*cm))
        for idx_c, cid in enumerate(selected_chart_ids):
            ch_title, fig, _ = build_chart(cid, patients, appts, bed_rec, bed_full, surg, doctors, depts, nurses)
            if fig is None: continue
            png = _fig_to_bytes(fig, dpi=150); plt.close(fig)
            img_w = body_w; img_h = round(img_w * 7 / 16, 2)
            img_obj = Image(io.BytesIO(png), width=img_w, height=img_h)
            chart_block = [
                HRFlowable(width="100%", thickness=0.5, color=C_DIVIDER, spaceAfter=6, spaceBefore=4),
                Paragraph(ch_title, sH2), Spacer(1, 0.15*cm),
                Table([[img_obj]], colWidths=[body_w], style=TableStyle([
                    ("ALIGN",(0,0),(0,0),"CENTER"),("VALIGN",(0,0),(0,0),"MIDDLE"),
                    ("TOPPADDING",(0,0),(0,0),0),("BOTTOMPADDING",(0,0),(0,0),0),
                    ("LEFTPADDING",(0,0),(0,0),0),("RIGHTPADDING",(0,0),(0,0),0),
                    ("BOX",(0,0),(0,0),0.5,C_BORDER),
                ])),
                Spacer(1, 0.15*cm), Paragraph(f"Figure {idx_c+1}: {ch_title}", sCapt),
            ]
            story.append(KeepTogether(chart_block))
            if idx_c < len(selected_chart_ids) - 1:
                story.append(PageBreak())
                story.append(section_heading("Dashboard Visualizations"))
                story.append(Spacer(1, 0.4*cm))

    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_DIVIDER))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(f"Confidential — {r_title} — {report_date_short}",
        S("foot", fontSize=7, fontName="Helvetica-Oblique", textColor=C_GRAY, alignment=TA_CENTER)))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    buf.seek(0); return buf.read()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
def run():
    dm = st.session_state.get("dark_mode", False)

    PB  = "#60A5FA" if dm else "#1E40AF"
    PU  = "#A78BFA" if dm else "#7C3AED"
    CR  = "#F87171" if dm else "#DC2626"
    GR  = "#34D399" if dm else "#059669"
    AM  = "#FBBF24" if dm else "#D97706"
    SB  = "#3B82F6"
    TE  = "#2DD4BF" if dm else "#0D9488"
    text_color   = "#FAFAFA" if dm else "#1E293B"
    sec_text     = "#94A3B8" if dm else "#64748B"
    card_bg      = "#1E2A3A" if dm else "#F0F9FF"
    bdr          = "#334155" if dm else "#E2E8F0"
    input_bg     = "#0F172A" if dm else "#FFFFFF"
    input_text   = "#F1F5F9" if dm else "#1E293B"
    input_border = "#334155" if dm else "#CBD5E1"

    TF  = dict(size=15, color=text_color, family="Arial Black")
    TTF = dict(size=17, color=text_color, family="Arial Black")
    GC  = "rgba(128,128,128,0.15)"

    # Topbar background adapts to theme
    topbar_bg = "#1C1F26" if dm else "#FFFFFF"
    topbar_border = "#334155" if dm else "#E2E8F0"
    # Page notes / expander text visibility
    ann_text_color = "#F1F5F9" if dm else "#1E293B"

    st.markdown(f"""<style>
        /* ── Topbar (deploy bar) theme fix ── */
        header[data-testid="stHeader"] {{
            background-color: {topbar_bg} !important;
            border-bottom: 1px solid {topbar_border} !important;
        }}
        header[data-testid="stHeader"] button,
        header[data-testid="stHeader"] svg,
        header[data-testid="stHeader"] span {{
            color: {text_color} !important;
            fill: {text_color} !important;
        }}

        .pg-title {{ font-size:42px; font-weight:900; text-align:center; margin-bottom:8px;
                     background:linear-gradient(135deg,{PB},{PU});
                     -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
        .pg-sub   {{ font-size:16px; font-weight:500; color:{sec_text}; text-align:center; margin-bottom:32px; }}
        .sec-hdr  {{ font-size:22px; font-weight:800; color:{text_color};
                     margin:36px 0 16px 0; padding-bottom:8px; border-bottom:4px solid {PB}; }}
        .sim-box  {{ background:{card_bg}; border:2px solid {PB}; border-radius:12px;
                     padding:20px 24px; margin-top:12px; }}
        /* Capacity simulator: increased font sizes throughout */
        .sim-ttl  {{ font-size:18px; font-weight:800; color:{text_color}; margin-bottom:12px; }}
        .g-row    {{ display:flex; justify-content:space-between; padding:10px 0;
                     border-bottom:1px solid {bdr}; font-size:16px; color:{text_color}; }}
        .g-ok     {{ color:{GR};  font-weight:700; font-size:16px; }}
        .g-warn   {{ color:{AM};  font-weight:700; font-size:16px; }}
        .g-crit   {{ color:{CR};  font-weight:700; font-size:16px; }}
        .chart-group {{ background:{card_bg}; border:1px solid {bdr}; border-radius:10px;
                        padding:14px 16px; margin-bottom:12px; }}
        .chart-group-title {{ font-size:14px; font-weight:800; color:{PB};
                               text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px; }}
        /* Fix input, label, checkbox text in dark mode */
        .stTextInput input, .stTextArea textarea {{
            background-color:{input_bg} !important; color:{input_text} !important;
            border:1px solid {input_border} !important;
        }}
        /* Text area placeholder color — visible in both themes */
        .stTextArea textarea::placeholder {{
            color: {"#94A3B8" if dm else "#94A3B8"} !important;
            opacity: 1 !important;
        }}
        .stTextInput label, .stTextArea label, .stCheckbox label,
        .stCheckbox span, .stCheckbox p {{
            color:{text_color} !important; font-weight:600 !important;
        }}
        .stCheckbox > label > span {{ color:{text_color} !important; }}
        /* Fix section subheadings */
        h4, h3 {{ color:{text_color} !important; }}
        /* Report details section labels */
        .report-label {{
            font-size:14px; font-weight:700; color:{text_color}; margin-bottom:4px;
        }}
        /* KPI strip — increased sizes */
        .kpi {{ background:linear-gradient(135deg,{PB},{SB}); padding:20px; border-radius:13px;
                text-align:center; box-shadow:0 4px 12px rgba(0,0,0,0.10); }}
        .kpi-l {{ font-size:14px; color:rgba(255,255,255,0.9); font-weight:800;
                  text-transform:uppercase; letter-spacing:1px; margin-bottom:6px; }}
        .kpi-v {{ font-size:36px; font-weight:900; color:white; }}
        /* Page notes / expander text in sidebar */
        section[data-testid="stSidebar"] .stExpander p,
        section[data-testid="stSidebar"] .stExpander span,
        section[data-testid="stSidebar"] .stExpander label,
        section[data-testid="stSidebar"] .stExpander div {{
            color: {ann_text_color} !important;
        }}
        section[data-testid="stSidebar"] .stExpander textarea,
        section[data-testid="stSidebar"] .stExpander input {{
            background-color: {input_bg} !important;
            color: {ann_text_color} !important;
            border: 1px solid {input_border} !important;
        }}
        section[data-testid="stSidebar"] .stExpander textarea::placeholder,
        section[data-testid="stSidebar"] .stExpander input::placeholder {{
            color: #94A3B8 !important;
            opacity: 1 !important;
        }}
    </style>""", unsafe_allow_html=True)

    st.markdown("<div class='pg-title'>Intelligence & Capacity Planning</div>", unsafe_allow_html=True)
    st.markdown("<div class='pg-sub'>Capacity Planning Simulator  |  PDF Report Builder  |  Strategic Resource Forecasting</div>", unsafe_allow_html=True)

    patients, appts, bed_rec, bed_full, surg, doctors, depts, nurses = _load_p6()

    # Shared metrics
    n_months    = max(bed_rec["admission_Date"].dt.to_period("M").nunique(), 1)
    mo_adm      = round(len(bed_rec) / n_months, 1)
    cur_beds    = bed_rec["bed_No"].nunique()
    cur_nurses  = len(nurses)
    cur_docs    = len(doctors)
    avg_los_raw = bed_rec["LOS"].dropna().mean()
    avg_los     = round(avg_los_raw, 1) if pd.notna(avg_los_raw) else 0.0
    nur_ratio   = cur_nurses / max(mo_adm, 1)
    doc_ratio   = cur_docs   / max(mo_adm, 1)
    cancel_r    = round(appts["appointment_status"].astype(str).str.lower().isin(["cancelled","canceled"]).sum()
                        / max(len(appts), 1) * 100, 1)

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 1 — CAPACITY PLANNING SIMULATOR
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("<div class='sec-hdr'>Capacity Planning Simulator</div>", unsafe_allow_html=True)
    st.caption("Adjust the sliders to model future resource requirements based on growth projections.")

    sc1, sc2 = st.columns([1, 1], gap="large")
    with sc1:
        st.markdown(f"<div style='color:{text_color};font-size:17px;font-weight:800;margin-bottom:10px;'>Current Baseline</div>", unsafe_allow_html=True)
        for lbl, val in [
            ("Monthly admissions", f"{int(mo_adm):,}"),
            ("Total beds", f"{cur_beds:,}"),
            ("Nurses", f"{cur_nurses:,}"),
            ("Doctors", f"{cur_docs:,}"),
            ("Average LOS (days)", str(avg_los)),
        ]:
            st.markdown(f"<div style='color:{sec_text};font-size:16px;padding:4px 0;'>• {lbl}: <b style='color:{text_color}'>{val}</b></div>", unsafe_allow_html=True)
        st.markdown("---")
        gr  = st.slider("Expected volume growth (%)",   0, 100, 20, 5, key="sim_gr")
        lsc = st.slider("Change in average LOS (%)", -50,  50,  0, 5, key="sim_los")
        hor = st.select_slider("Planning horizon (months)", options=[3,6,12,24,36], value=12, key="sim_hor")
        occ = st.slider("Target bed occupancy (%)",  50,  95, 80, 5, key="sim_occ")

    with sc2:
        p_adm  = mo_adm * (1 + gr/100)
        p_los  = avg_los * (1 + lsc/100)
        p_beds = (p_adm * p_los) / (30 * (occ/100))
        p_nur  = p_adm * nur_ratio * (1 + gr/100)
        p_doc  = p_adm * doc_ratio * (1 + gr/100)
        bg, ng, dg = int(p_beds - cur_beds), int(p_nur - cur_nurses), int(p_doc - cur_docs)
        rev_leak   = round(cancel_r/100 * p_adm * 12 * 5000, 0)

        def gc(v):
            if v <= 0:   return "g-ok",   f"Surplus of {abs(v)}"
            elif v < 10: return "g-warn",  f"Need +{v}"
            else:        return "g-crit",  f"Critical gap: +{v}"

        bc, bt = gc(bg); nc, nt = gc(ng); dc, dt = gc(dg)
        st.markdown(f"""<div class="sim-box">
          <div class="sim-ttl">Projected needs at +{gr}% growth over {hor} months</div>
          <div class="g-row"><span>Monthly admissions</span><b>{int(p_adm):,}</b></div>
          <div class="g-row"><span>Average LOS</span><b>{p_los:.1f} days</b></div>
          <div class="g-row"><span>Beds required</span>
            <span><b>{int(p_beds):,}</b> &nbsp;<span class="{bc}">{bt}</span></span></div>
          <div class="g-row"><span>Nurses required</span>
            <span><b>{int(p_nur):,}</b> &nbsp;<span class="{nc}">{nt}</span></span></div>
          <div class="g-row"><span>Doctors required</span>
            <span><b>{int(p_doc):,}</b> &nbsp;<span class="{dc}">{dt}</span></span></div>
          <div class="g-row"><span>Est. annual revenue leakage</span>
            <b style="color:{CR}">Rs {rev_leak:,.0f}</b></div>
        </div>""", unsafe_allow_html=True)

    # Capacity projection chart
    mx           = list(range(1, hor+1))
    pvol         = [mo_adm*(1+(gr/100)*(m/hor)) for m in mx]
    pbeds_line   = [(v*p_los)/(30*(occ/100)) for v in pvol]
    fp = go.Figure()
    fp.add_trace(go.Scatter(x=mx, y=pvol, name="Projected Admissions",
        mode="lines+markers", line=dict(color=PB, width=3), marker=dict(size=6)))
    fp.add_trace(go.Scatter(x=mx, y=[mo_adm]*hor, name="Current Baseline",
        mode="lines", line=dict(color=CR, width=2, dash="dash")))
    fp.add_trace(go.Scatter(x=mx, y=pbeds_line, name="Beds Required",
        mode="lines+markers", line=dict(color=PU, width=3), marker=dict(size=6), yaxis="y2"))
    fp.add_trace(go.Scatter(x=mx, y=[cur_beds]*hor, name="Current Beds",
        mode="lines", line=dict(color=TE, width=2, dash="dash"), yaxis="y2"))
    fp.update_layout(
        xaxis=dict(title="<b>Month</b>", tickfont=TF, title_font=TTF, showgrid=True, gridcolor=GC),
        yaxis=dict(title="<b>Monthly Admissions</b>", tickfont=TF, title_font=TTF, showgrid=True, gridcolor=GC),
        yaxis2=dict(title="<b>Beds Required</b>", overlaying="y", side="right", tickfont=TF, title_font=TTF, showgrid=False),
        legend=dict(font=dict(size=14, color=text_color), orientation="h", y=1.06, x=0.5, xanchor="center",
                    bgcolor="rgba(0,0,0,0)"),
        height=460, margin=dict(l=70, r=80, t=60, b=60),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", hovermode="x unified"
    )
    st.plotly_chart(fp, use_container_width=True, config={"displayModeBar": False})

    # KPI strip
    k1, k2, k3, k4 = st.columns(4)
    for col, lbl, val in [
        (k1, "Projected Beds",     f"{int(p_beds):,}"),
        (k2, "Projected Nurses",   f"{int(p_nur):,}"),
        (k3, "Projected Doctors",  f"{int(p_doc):,}"),
        (k4, "Bed Gap",            f"+{max(0,bg)}")
    ]:
        col.markdown(f'<div class="kpi"><div class="kpi-l">{lbl}</div>'
                     f'<div class="kpi-v">{val}</div></div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 2 — PDF REPORT BUILDER
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='sec-hdr'>PDF Report Builder</div>", unsafe_allow_html=True)
    st.caption("Select charts from across the dashboard, fill in report details, and generate a professional PDF report.")

    CHART_GROUPS = {
        "Executive Overview (Page 1)": [
            ("p1_patient_flow",  "Patient Flow Trends"),
            ("p1_outcomes",      "Appointment Outcomes (Donut)"),
            ("p1_dept_demand",   "Department Demand"),
            ("p1_peak_months",   "Peak Appointment Months"),
            ("p1_completion",    "Appointment Completion Rate"),
        ],
        "Patient Demographics (Page 2)": [
            ("p2_gender",        "Gender Distribution"),
            ("p2_age",           "Age Group Distribution"),
            ("p2_top_cities",    "Top 10 Cities by Patient Count"),
            ("p2_payment",       "Payment Methods"),
            ("p2_appt_trend",    "Appointment Trend 2024 vs 2025"),
        ],
        "Clinical & Disease Intelligence (Page 3)": [
            ("p3_top_surgeries", "Top 10 Surgical Procedures"),
            ("p3_surgery_trend", "Surgery Trend Over Time"),
            ("p3_surgery_dept",  "Surgery Distribution by Department"),
            ("p3_heatmap",       "Doctor-Department Surgery Heatmap"),
        ],
        "Operational Efficiency (Page 4)": [
            ("p4_los",           "Avg Length of Stay by Department"),
            ("p4_ward",          "Ward Utilization"),
            ("p4_flow",          "Admissions vs Discharges"),
        ],
        "Staffing & Resources (Page 5)": [
            ("p5_nurse_dist",    "Nurse Distribution by Department"),
            ("p5_heatmap",       "Doctor Workload Heatmap"),
            ("p5_pt_nurse_ratio","Patient-to-Nurse Ratio"),
        ],
        "Intelligence & Planning (Page 6)": [
            ("p6_capacity_proj", "Capacity Projection Chart"),
        ],
    }

    st.markdown(f"<div style='color:{text_color};font-size:16px;font-weight:800;margin-bottom:12px;'>Select Charts to Include</div>", unsafe_allow_html=True)
    selected_ids = []

    for group_name, charts in CHART_GROUPS.items():
        st.markdown(f"""<div class='chart-group'>
            <div class='chart-group-title'>{group_name}</div>""", unsafe_allow_html=True)
        cols = st.columns(len(charts))
        for col, (cid, clabel) in zip(cols, charts):
            if col.checkbox(clabel, value=False, key=f"chk_{cid}"):
                selected_ids.append(cid)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:{text_color};font-size:16px;font-weight:800;margin-bottom:12px;'>Report Details</div>", unsafe_allow_html=True)

    rd1, rd2 = st.columns([1,1], gap="large")
    with rd1:
        st.markdown(f"<div class='report-label'>Report Title</div>", unsafe_allow_html=True)
        r_title  = st.text_input("", value="Hospital Operations Report", key="pdf_title", label_visibility="collapsed")
        st.markdown(f"<div class='report-label'>Prepared By</div>", unsafe_allow_html=True)
        r_author = st.text_input("", value="Hospital Administrator", key="pdf_author", label_visibility="collapsed")
        st.markdown(f"<div class='report-label'>Department</div>", unsafe_allow_html=True)
        r_dept   = st.text_input("", value="Operations Management", key="pdf_dept", label_visibility="collapsed")
    with rd2:
        st.markdown(f"<div class='report-label'>Executive Summary (optional)</div>", unsafe_allow_html=True)
        r_notes  = st.text_area("", placeholder="Key findings, observations, and recommendations...",
                                height=120, key="pdf_notes", label_visibility="collapsed")
        inc_kpi  = st.checkbox("Include KPI summary table",  value=True, key="pdf_kpi")
        inc_alrt = st.checkbox("Include operational alerts", value=True, key="pdf_alrt")

    n_sel = len(selected_ids)
    if n_sel > 0:
        st.info(f"✅ {n_sel} chart(s) selected for the report.")
    else:
        st.warning("⚠️ No charts selected — the report will include only KPIs, alerts, and summary text.")

    if st.button("Generate PDF Report", key="gen_pdf", type="primary"):
        with st.spinner("Building PDF — rendering charts..."):
            # Recalculate alert metrics
            avg_daily  = avg_los * (len(bed_rec) / max(n_months * 30, 1))
            occ_pct    = round(avg_daily / max(cur_beds, 1) * 100, 1)
            noshow_r   = round(appts["appointment_status"].astype(str).str.lower()
                               .str.contains(r"no.?show", regex=True).sum() / max(len(appts),1)*100,1)

            kpi_data = []
            if inc_kpi:
                kpi_data = [
                    ("Total Patients",     patients["patient_Id"].nunique()),
                    ("Appointments",       len(appts)),
                    ("Bed Occupancy",      f"{occ_pct}%"),
                    ("Cancel Rate",        f"{cancel_r}%"),
                    ("Avg LOS (days)",     avg_los),
                    ("No-Show Rate",       f"{noshow_r}%"),
                    ("Total Beds",         cur_beds),
                    ("Nurses",             cur_nurses),
                ]

            alert_data_pdf = []
            if inc_alrt:
                for val, hi, mid, titles, detls in [
                    (occ_pct, 85, 70,
                     ["Critical Bed Occupancy","High Bed Occupancy","Bed Occupancy Normal"],
                     [f"At {occ_pct}% — above 85% critical threshold.",
                      f"At {occ_pct}% — approaching critical.",
                      f"At {occ_pct}% — healthy range."]),
                    (cancel_r, 15, 8,
                     ["High Cancellation","Elevated Cancellation","Normal Cancellation"],
                     [f"{cancel_r}% — revenue impact likely.",
                      f"{cancel_r}% — consider reminders.",
                      f"{cancel_r}% — acceptable."]),
                    (avg_los, 10, 7,
                     ["Long LOS","Above-Avg LOS","Normal LOS"],
                     [f"{avg_los} days — discharge bottlenecks.",
                      f"{avg_los} days — review discharge.",
                      f"{avg_los} days — efficient."]),
                    (noshow_r, 10, 5,
                     ["Critical No-Show","Elevated No-Show","Normal No-Show"],
                     [f"{noshow_r}% — urgent action.",
                      f"{noshow_r}% — send reminders.",
                      f"{noshow_r}% — acceptable."]),
                ]:
                    lvl = "RED" if val >= hi else "AMBER" if val >= mid else "GREEN"
                    idx = 0 if val >= hi else 1 if val >= mid else 2
                    alert_data_pdf.append((lvl, titles[idx], detls[idx]))

            pdf_bytes = build_pdf(
                selected_ids, r_title, r_author, r_dept, r_notes,
                kpi_data, alert_data_pdf,
                patients, appts, bed_rec, bed_full, surg, doctors, depts, nurses
            )

        fname = f"Hospital_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        st.download_button(
            label="⬇️ Download PDF Report",
            data=pdf_bytes, file_name=fname, mime="application/pdf",
            use_container_width=True,
        )
        st.success(f"PDF ready — {n_sel} chart(s) included. Click above to download.")

    st.markdown("<br><br>", unsafe_allow_html=True)