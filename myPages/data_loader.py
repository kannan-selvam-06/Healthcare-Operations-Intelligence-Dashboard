"""
data_loader.py
──────────────
Loads every sheet from the Excel file exactly once per session.
Result is stored in st.session_state["_raw"].

All filtering happens in apply_filters() before pages are called.
Pages receive pre-filtered DataFrames as function arguments.

KEY FIX: Appointments and surgeries are enriched with dept_Name via
doctor/surgeon→department join BEFORE dept filtering is applied.
This makes the global Department filter work across all pages.
"""

import pandas as pd
import streamlit as st


@st.cache_data(show_spinner="Loading hospital data…")
def load_all(path: str) -> dict:
    xls = pd.ExcelFile(path)

    def _read(sheet):
        df = pd.read_excel(xls, sheet)
        df.columns = df.columns.str.strip()
        return df

    patients     = _read("Patients")
    appointments = _read("Appointment")
    bed_records  = _read("BedRecords")
    bed_df       = _read("Bed")
    ward_df      = _read("Ward")
    surgeries    = _read("SurgeryRecord")
    doctors      = _read("Doctor")
    departments  = _read("Department")
    nurses       = _read("Nurse")
    rooms        = _read("Room")        if "Room"        in xls.sheet_names else pd.DataFrame()
    room_records = _read("RoomRecords") if "RoomRecords" in xls.sheet_names else pd.DataFrame()

    # ── Parse dates once ─────────────────────────────────────────────────────
    appointments["appointment_Date"] = pd.to_datetime(
        appointments["appointment_Date"], errors="coerce")

    for col in ["admission_Date", "discharge_Date"]:
        if col in bed_records.columns:
            bed_records[col] = pd.to_datetime(bed_records[col], errors="coerce")

    if "surgery_Date" in surgeries.columns:
        surgeries["surgery_Date"] = pd.to_datetime(surgeries["surgery_Date"], errors="coerce")

    if "Date_Of_Birth" in patients.columns:
        patients["Date_Of_Birth"] = pd.to_datetime(patients["Date_Of_Birth"], errors="coerce")

    # ── Derived columns used by multiple pages ────────────────────────────────
    bed_records["Length_of_Stay"] = (
        bed_records["discharge_Date"] - bed_records["admission_Date"]
    ).dt.days
    bed_records["LOS"] = bed_records["Length_of_Stay"]

    # bed_full join used by pages 4, 5, 6
    bed_full = (bed_records
        .merge(bed_df,      on="bed_No",  how="left")
        .merge(ward_df,     on="ward_No", how="left")
        .merge(departments, on="dept_Id", how="left"))

    # ── Enrich appointments with dept_Name via doctor join ────────────────────
    # KEY FIX: appointments get dept_Name so global dept filter works on them.
    doc_dept_map = doctors[["doct_Id", "dept_Id"]].merge(
        departments[["dept_Id", "dept_Name"]], on="dept_Id", how="left"
    )[["doct_Id", "dept_Name"]]
    appointments = appointments.merge(doc_dept_map, on="doct_Id", how="left")

    # ── Enrich surgeries with dept_Name via surgeon→doctor→dept join ──────────
    # KEY FIX: surgeries get dept_Name so global dept filter works on them.
    surg_dept_map = doctors[["doct_Id", "dept_Id"]].merge(
        departments[["dept_Id", "dept_Name"]], on="dept_Id", how="left"
    ).rename(columns={"doct_Id": "surgeon_Id"})[["surgeon_Id", "dept_Name"]]
    surgeries = surgeries.merge(surg_dept_map, on="surgeon_Id", how="left")

    # lowercase copies for page 1
    def _lower(df):
        out = df.copy()
        out.columns = out.columns.str.lower()
        return out

    return {
        "patients":          patients,
        "appointments":      appointments,
        "bed_records":       bed_records,
        "bed_df":            bed_df,
        "ward_df":           ward_df,
        "surgeries":         surgeries,
        "doctors":           doctors,
        "departments":       departments,
        "nurses":            nurses,
        "rooms":             rooms,
        "room_records":      room_records,
        "bed_full":          bed_full,
        # lowercased for page 1
        "apps_lc":           _lower(appointments),
        "room_records_lc":   _lower(room_records) if not room_records.empty else pd.DataFrame(),
        "rooms_lc":          _lower(rooms)        if not rooms.empty        else pd.DataFrame(),
        "bed_lc":            _lower(bed_records),
        "departments_lc":    _lower(departments),
    }


def apply_filters(raw: dict, start_date, end_date, dept_list: list, status_list: list) -> dict:
    """
    Called once in app.py.
    Returns a dict of filtered DataFrames passed into each page's run().

    appointments and surgeries in raw are already enriched with dept_Name
    via doctor/surgeon→department joins done in load_all(), so dept filtering
    works correctly on both tables.
    """
    all_depts  = (not dept_list)  or ("All Departments" in dept_list)
    all_status = (not status_list) or ("All Status"      in status_list)

    ts_start = pd.Timestamp(start_date)
    ts_end   = pd.Timestamp(end_date) + pd.Timedelta(hours=23, minutes=59)

    def _date_filter(df, col):
        if col not in df.columns:
            return df
        return df[(df[col] >= ts_start) & (df[col] <= ts_end)]

    def _status_filter(df, col="appointment_status"):
        if all_status or col not in df.columns:
            return df
        return df[df[col].isin(status_list)]

    def _dept_filter(df, col="dept_Name"):
        if all_depts or col not in df.columns:
            return df
        return df[df[col].isin(dept_list)]

    # ── appointments: date + status + dept ───────────────────────────────────
    appts = _date_filter(raw["appointments"], "appointment_Date")
    appts = _status_filter(appts)
    appts = _dept_filter(appts)

    # ── bed_full: date + dept ─────────────────────────────────────────────────
    bed_full_f = _date_filter(raw["bed_full"], "admission_Date")
    bed_full_f = _dept_filter(bed_full_f)

    # ── bed_records: filter by admission IDs that survived bed_full filter ────
    bed_rec = _date_filter(raw["bed_records"], "admission_Date")
    if not all_depts and "admission_Id" in bed_full_f.columns and "admission_Id" in bed_rec.columns:
        valid_adm_ids = bed_full_f["admission_Id"].dropna().unique()
        bed_rec = bed_rec[bed_rec["admission_Id"].isin(valid_adm_ids)]

    # ── surgeries: date + dept (dept_Name available via enrichment) ───────────
    surgeries = _date_filter(raw["surgeries"], "surgery_Date")
    surgeries = _dept_filter(surgeries)

    # ── lowercased appointment copy for page 1 ────────────────────────────────
    appts_lc = _date_filter(raw["apps_lc"], "appointment_date")
    if not all_status and "appointment_status" in appts_lc.columns:
        appts_lc = appts_lc[appts_lc["appointment_status"].isin(status_list)]
    if not all_depts and "dept_name" in appts_lc.columns:
        appts_lc = appts_lc[appts_lc["dept_name"].isin(dept_list)]

    # ── bed_lc: filtered lowercased bed_records for page 1 ───────────────────
    bed_lc = _date_filter(raw["bed_lc"], "admission_date")
    if not all_depts and "admission_id" in bed_lc.columns and "admission_Id" in bed_full_f.columns:
        valid_adm_ids = bed_full_f["admission_Id"].dropna().unique()
        bed_lc = bed_lc[bed_lc["admission_id"].isin(valid_adm_ids)]

    # ── room_records for page 1 ───────────────────────────────────────────────
    room_rec_lc = raw["room_records_lc"].copy() if not raw["room_records_lc"].empty else pd.DataFrame()

    return {
        # filtered
        "appointments":    appts,
        "bed_records":     bed_rec,
        "bed_full":        bed_full_f,
        "surgeries":       surgeries,
        "appts_lc":        appts_lc,
        "bed_lc":          bed_lc,
        "room_records_lc": room_rec_lc,
        # unfiltered lookup tables
        "patients":        raw["patients"],
        "doctors":         raw["doctors"],
        "departments":     raw["departments"],
        "nurses":          raw["nurses"],
        "rooms_lc":        raw["rooms_lc"],
        "departments_lc":  raw["departments_lc"],
        # raw appointments for valid_years (always full range)
        "appointments_raw": raw["appointments"],
        # active dept list exposed for cross-filtering in pages
        "active_depts":    dept_list,
    }