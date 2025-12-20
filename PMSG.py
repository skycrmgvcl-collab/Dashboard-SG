import streamlit as st
import pandas as pd
import io
from datetime import date

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="Pending for Release – PMSGMBY",
    layout="wide"
)

# =================================================
# STYLE
# =================================================
st.markdown("""
<style>
.stApp { background-color:#f4fbf6; }
thead th {
    position: sticky;
    top: 0;
    background:#198754 !important;
    color:white !important;
}
</style>
""", unsafe_allow_html=True)

st.title("⏳ Pending for Release under PMSGMBY")

# =================================================
# FILE UPLOAD
# =================================================
file = st.file_uploader(
    "📤 Upload Excel File (No Header)",
    type=["xlsx"]
)

if not file:
    st.info("Please upload Excel file to continue")
    st.stop()

# =================================================
# READ & PROCESS DATA
# =================================================
with st.spinner("Processing Excel file..."):
    raw_df = pd.read_excel(file, header=None, engine="openpyxl")

    df = raw_df.rename(columns={
        0: "installation_date",
        1: "application_no",
        2: "consumer_no",
        5: "sub_division"
    })

    df = df[
        ["installation_date", "application_no", "consumer_no", "sub_division"]
    ].copy()

    df["installation_date"] = pd.to_datetime(
        df["installation_date"],
        format="%d-%m-%Y",
        errors="coerce"
    )

    df = df.dropna(subset=["installation_date"])

    today = pd.to_datetime(date.today())
    df["days_pending"] = (today - df["installation_date"]).dt.days + 1

    def ageing_bucket(days):
        if days <= 7:
            return "0 to 7 Days"
        elif days <= 15:
            return "8 to 15 Days"
        elif days <= 30:
            return "16 to 30 Days"
        elif days <= 45:
            return "31 to 45 Days"
        else:
            return "More than 45 Days"

    df["age_bucket"] = df["days_pending"].apply(ageing_bucket)

# =================================================
# SIDEBAR FILTERS
# =================================================
bucket_order = [
    "0 to 7 Days",
    "8 to 15 Days",
    "16 to 30 Days",
    "31 to 45 Days",
    "More than 45 Days"
]

st.sidebar.header("🔍 Filters")

sel_sd = st.sidebar.selectbox(
    "Sub Division",
    ["ALL"] + sorted(df["sub_division"].unique())
)

sel_bucket = st.sidebar.selectbox(
    "Age Bucket",
    ["ALL"] + bucket_order
)

# =================================================
# APPLY FILTERS (CORE FIX)
# =================================================
filtered_df = df.copy()

if sel_sd != "ALL":
    filtered_df = filtered_df[filtered_df["sub_division"] == sel_sd]

if sel_bucket != "ALL":
    filtered_df = filtered_df[filtered_df["age_bucket"] == sel_bucket]

# =================================================
# KPI CARDS (ALL BUCKETS SHOWN)
# =================================================
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total", len(filtered_df))
k2.metric("0–7 Days", (filtered_df["age_bucket"] == "0 to 7 Days").sum())
k3.metric("8–15 Days", (filtered_df["age_bucket"] == "8 to 15 Days").sum())
k4.metric("16–30 Days", (filtered_df["age_bucket"] == "16 to 30 Days").sum())
k5.metric(">45 Days", (filtered_df["age_bucket"] == "More than 45 Days").sum())

# =================================================
# SUMMARY TABLE (FILTERED)
# =================================================
summary = (
    filtered_df.pivot_table(
        index="sub_division",
        columns="age_bucket",
        values="application_no",
        aggfunc="count",
        fill_value=0
    )
    .reindex(columns=bucket_order, fill_value=0)
)

summary["TOTAL"] = summary.sum(axis=1)
summary = summary.reset_index()
summary.rename(columns={"sub_division": "Sub Division"}, inplace=True)
summary.insert(0, "Sr No.", range(1, len(summary) + 1))

totals = summary[bucket_order + ["TOTAL"]].sum()
grand_row = pd.DataFrame(
    [[0, "Grand Total", *totals.tolist()]],
    columns=summary.columns
)

final_summary = pd.concat([summary, grand_row], ignore_index=True)
final_summary["Sr No."] = final_summary["Sr No."].astype("int64")

# =================================================
# DETAIL TABLE (FILTERED)
# =================================================
detail_df = filtered_df.sort_values("days_pending", ascending=False)

detail_view = detail_df[
    [
        "installation_date",
        "application_no",
        "consumer_no",
        "sub_division",
        "days_pending",
        "age_bucket"
    ]
].copy()

detail_view["installation_date"] = detail_view["installation_date"].dt.strftime("%d-%m-%Y")
detail_view.insert(0, "Sr No.", range(1, len(detail_view) + 1))
detail_view["Sr No."] = detail_view["Sr No."].astype("int64")

detail_view.rename(columns={
    "installation_date": "Installation Date",
    "application_no": "Application Number",
    "consumer_no": "Consumer Number",
    "sub_division": "Sub Division",
    "days_pending": "Pending (Days)",
    "age_bucket": "Age Bucket"
}, inplace=True)

# =================================================
# TABS
# =================================================
tab1, tab2 = st.tabs(["📊 Summary", "📋 Detail"])

with tab1:
    st.dataframe(final_summary, use_container_width=True)

with tab2:
    st.dataframe(detail_view, use_container_width=True)

# =================================================
# DOWNLOADS
# =================================================
def to_excel(df, sheet):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name=sheet)
    buf.seek(0)
    return buf

st.divider()
st.subheader("⬇ Downloads")

c1, c2 = st.columns(2)

with c1:
    st.download_button(
        "📥 Download Summary",
        to_excel(final_summary, "Summary"),
        "PMSGMBY_Pending_Summary.xlsx"
    )

with c2:
    st.download_button(
        "📥 Download Detail",
        to_excel(detail_view, "Detail"),
        f"PMSGMBY_Pending_{sel_sd}_{sel_bucket}.xlsx"
    )

# =================================================
# FOOTER
# =================================================
st.markdown(
    f"""
    <hr>
    <p style="text-align:center;color:gray;">
    Internal Use Only | PMSGMBY Dashboard | Generated on {date.today().strftime('%d-%m-%Y')}
    </p>
    """,
    unsafe_allow_html=True
)







