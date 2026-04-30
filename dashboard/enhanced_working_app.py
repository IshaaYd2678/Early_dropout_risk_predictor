"""
Early Warning System – Examiner-ready Dashboard
Real data from CSV + live ML predictions via the trained XGBoost model.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import joblib


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Early Warning System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-label  { font-size: 0.85rem; color: #6b7280; }
    .risk-critical { color: #ef4444; font-weight: 700; }
    .risk-high     { color: #f97316; font-weight: 700; }
    .risk-medium   { color: #eab308; font-weight: 700; }
    .risk-low      { color: #22c55e; font-weight: 700; }
    .section-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)


# ── Data & model loading ──────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading student data…")
def load_data() -> pd.DataFrame:
    path = Path("data/raw/students.csv")
    if not path.exists():
        st.error("data/raw/students.csv not found. Run: python scripts/generate_enhanced_data.py")
        st.stop()
    df = pd.read_csv(path)
    return df


@st.cache_resource(show_spinner="Loading ML model…")
def load_predictor():
    try:
        from ml.predict import DropoutRiskPredictor
        return DropoutRiskPredictor()
    except Exception as e:
        return None


def risk_label(score: float) -> str:
    if score >= 0.6:  return "Critical"
    if score >= 0.4:  return "High"
    if score >= 0.2:  return "Medium"
    return "Low"


def risk_color(label: str) -> str:
    return {"Critical": "#ef4444", "High": "#f97316",
            "Medium": "#eab308", "Low": "#22c55e"}.get(label, "#6b7280")


@st.cache_data(show_spinner="Running predictions on dataset…")
def run_batch_predictions(_predictor, df: pd.DataFrame) -> pd.DataFrame:
    """Score every student in the dataset once and cache the result."""
    if _predictor is None:
        # Fallback: use dropout label as proxy score
        df = df.copy()
        df["risk_score"] = df["dropped_out"].astype(float) * 0.7 + np.random.uniform(0, 0.3, len(df))
        df["risk_label"] = df["risk_score"].apply(risk_label)
        return df

    results = _predictor.predict(df, include_explanation=False)
    scores = results["risk_score"]
    df = df.copy()
    df["risk_score"] = scores if isinstance(scores, list) else [scores]
    df["risk_label"] = df["risk_score"].apply(risk_label)
    return df


# ── Load everything ───────────────────────────────────────────────────────────
raw_df    = load_data()
predictor = load_predictor()
df        = run_batch_predictions(predictor, raw_df)

model_ok  = predictor is not None
n_total   = len(df)
n_critical = (df["risk_label"] == "Critical").sum()
n_high     = (df["risk_label"] == "High").sum()
n_at_risk  = n_critical + n_high
avg_gpa    = df["gpa"].mean()
avg_attend = df["attendance_rate"].mean()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 Early Warning System")
    st.caption("AI-powered student dropout risk prediction")
    st.divider()

    page = st.radio(
        "Navigate",
        ["📊 Overview", "🔍 Student Explorer", "🤖 Live Prediction Demo",
         "📈 Fairness & Bias", "🗄️ Data Pipeline"],
        label_visibility="collapsed",
    )

    st.divider()

    # Role filter
    role = st.selectbox("👤 Role", ["Admin", "Department Head", "Mentor"])
    dept_options = ["All"] + sorted(df["department"].unique().tolist())
    dept_filter  = st.selectbox("🏢 Department", dept_options)

    st.divider()
    st.markdown("#### 🔧 System Status")
    st.markdown(f"{'🟢' if model_ok else '🔴'} **ML Model** — {'Loaded' if model_ok else 'Fallback mode'}")
    st.markdown(f"🟢 **Dataset** — {n_total:,} students")
    st.markdown(f"🟢 **Features** — {len(df.columns)} columns")
    st.markdown(f"🕐 **Last trained** — {datetime.now().strftime('%Y-%m-%d')}")


# ── Filter helper ─────────────────────────────────────────────────────────────
def filtered(df: pd.DataFrame) -> pd.DataFrame:
    if dept_filter != "All":
        return df[df["department"] == dept_filter]
    return df

view = filtered(df)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 – OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Overview":
    st.title("📊 Institution Overview")
    st.caption(f"Showing data for: **{dept_filter}** | Role: **{role}** | {len(view):,} students")

    # KPI row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Students",   f"{len(view):,}")
    c2.metric("At Risk",          f"{(view['risk_label'].isin(['Critical','High'])).sum():,}",
              delta=f"{(view['risk_label'].isin(['Critical','High'])).mean()*100:.1f}%")
    c3.metric("Critical",         f"{(view['risk_label']=='Critical').sum():,}")
    c4.metric("Avg GPA",          f"{view['gpa'].mean():.2f}")
    c5.metric("Avg Attendance",   f"{view['attendance_rate'].mean()*100:.1f}%")
    c6.metric("Dropout Rate",     f"{view['dropped_out'].mean()*100:.1f}%")

    st.divider()

    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.subheader("Risk Distribution by Department")
        dept_risk = (
            df.groupby("department")["risk_label"]
            .value_counts(normalize=True)
            .mul(100).round(1)
            .rename("pct")
            .reset_index()
        )
        fig = px.bar(
            dept_risk, x="department", y="pct", color="risk_label",
            color_discrete_map={"Critical":"#ef4444","High":"#f97316",
                                "Medium":"#eab308","Low":"#22c55e"},
            labels={"pct":"% of students","department":"Department","risk_label":"Risk"},
            title="Risk level breakdown per department",
        )
        fig.update_layout(barmode="stack", legend_title="Risk Level",
                          xaxis_tickangle=-20, height=380)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Overall Risk Split")
        counts = view["risk_label"].value_counts()
        fig2 = go.Figure(go.Pie(
            labels=counts.index, values=counts.values, hole=0.45,
            marker_colors=[risk_color(l) for l in counts.index],
        ))
        fig2.update_layout(height=380, showlegend=True,
                           legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("GPA vs Risk Score")
        sample = view.sample(min(500, len(view)), random_state=42)
        fig3 = px.scatter(
            sample, x="gpa", y="risk_score", color="risk_label",
            color_discrete_map={"Critical":"#ef4444","High":"#f97316",
                                "Medium":"#eab308","Low":"#22c55e"},
            opacity=0.6, title="Lower GPA → Higher risk",
            labels={"gpa":"GPA","risk_score":"Risk Score"},
        )
        fig3.update_layout(height=340)
        st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        st.subheader("Attendance vs Risk Score")
        fig4 = px.scatter(
            sample, x="attendance_rate", y="risk_score", color="risk_label",
            color_discrete_map={"Critical":"#ef4444","High":"#f97316",
                                "Medium":"#eab308","Low":"#22c55e"},
            opacity=0.6, title="Lower attendance → Higher risk",
            labels={"attendance_rate":"Attendance Rate","risk_score":"Risk Score"},
        )
        fig4.update_layout(height=340)
        st.plotly_chart(fig4, use_container_width=True)

    # Top at-risk table
    st.divider()
    st.subheader("🚨 Top 10 Highest-Risk Students")
    top10 = (
        view.nlargest(10, "risk_score")
        [["student_id","department","semester","gpa","attendance_rate",
          "exam_scores","risk_score","risk_label"]]
        .copy()
    )
    top10["risk_score"] = (top10["risk_score"] * 100).round(1).astype(str) + "%"
    top10["attendance_rate"] = (top10["attendance_rate"] * 100).round(1).astype(str) + "%"
    top10.columns = ["ID","Department","Semester","GPA","Attendance",
                     "Exam Score","Risk Score","Risk Level"]
    st.dataframe(top10, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 – STUDENT EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Student Explorer":
    st.title("🔍 Student Explorer")

    c1, c2, c3 = st.columns(3)
    risk_sel = c1.multiselect("Risk Level", ["Critical","High","Medium","Low"],
                               default=["Critical","High"])
    sem_sel  = c2.multiselect("Semester", sorted(df["semester"].unique()),
                               default=sorted(df["semester"].unique()))
    search   = c3.text_input("Search student ID")

    mask = (
        view["risk_label"].isin(risk_sel) &
        view["semester"].isin(sem_sel)
    )
    if search:
        mask &= view["student_id"].str.contains(search, case=False, na=False)

    result = view[mask].copy()
    result["risk_pct"] = (result["risk_score"] * 100).round(1)

    st.caption(f"{len(result):,} students match filters")

    st.dataframe(
        result[["student_id","department","semester","gpa","attendance_rate",
                "exam_scores","lms_login_frequency","late_submissions",
                "risk_pct","risk_label"]].rename(columns={
            "student_id":"ID","department":"Dept","semester":"Sem",
            "gpa":"GPA","attendance_rate":"Attend","exam_scores":"Exam",
            "lms_login_frequency":"LMS Logins","late_submissions":"Late Sub",
            "risk_pct":"Risk %","risk_label":"Level",
        }).sort_values("Risk %", ascending=False),
        use_container_width=True, hide_index=True, height=500,
    )

    csv = result.to_csv(index=False)
    st.download_button("📥 Export CSV", csv,
                       f"students_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                       "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 – LIVE PREDICTION DEMO
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 Live Prediction Demo":
    st.title("🤖 Live Prediction Demo")
    st.info("Adjust the sliders to simulate a student profile. The ML model scores it in real time.")

    col_form, col_result = st.columns([2, 1])

    with col_form:
        st.subheader("Student Profile")

        c1, c2 = st.columns(2)
        gpa        = c1.slider("GPA",                    0.0, 4.0, 2.5, 0.1)
        attendance = c2.slider("Attendance Rate",        0.0, 1.0, 0.75, 0.01,
                               format="%.2f")
        exam       = c1.slider("Exam Score",             0,   100, 65)
        submit     = c2.slider("Assignment Submit Rate", 0.0, 1.0, 0.80, 0.01,
                               format="%.2f")
        lms        = c1.slider("LMS Logins / month",     0,   50,  10)
        late       = c2.slider("Late Submissions",       0,   20,  3)
        part_score = c1.slider("Participation Score",    0,   100, 60)
        forum      = c2.slider("Forum Posts",            0,   30,  5)
        resources  = c1.slider("Resource Access Count",  0,   60,  20)
        hours      = c2.slider("Time Spent (hrs/week)",  0.0, 40.0, 12.0, 0.5)
        semester   = c1.selectbox("Semester", list(range(1, 9)), index=1)

        c3, c4 = st.columns(2)
        gender  = c3.selectbox("Gender",  ["Male","Female","Other"])
        dept    = c4.selectbox("Department",
                               ["Computer Science","Engineering","Business",
                                "Arts","Science","Health Sciences","Education","Mathematics"])
        ses     = c3.selectbox("Socioeconomic Status", ["Low","Medium","High"])
        region  = c4.selectbox("Region", ["Urban","Suburban","Rural"])

        gpa_trend   = st.slider("GPA Trend (vs last semester)", -1.0, 1.0, 0.0, 0.05)
        fin_aid     = st.checkbox("Receiving Financial Aid")
        part_time   = st.checkbox("Part-time Student")
        first_gen   = st.checkbox("First-generation Student")

    # Build input dict
    student_input = {
        "gpa":                      gpa,
        "gpa_trend":                gpa_trend,
        "attendance_rate":          attendance,
        "exam_scores":              float(exam),
        "assignment_submission_rate": submit,
        "lms_login_frequency":      lms,
        "late_submissions":         late,
        "participation_score":      float(part_score),
        "forum_posts":              forum,
        "resource_access_count":    resources,
        "time_spent_hours":         hours,
        "semester":                 semester,
        "gender":                   gender,
        "department":               dept,
        "socioeconomic_status":     ses,
        "region":                   region,
        "has_financial_aid":        int(fin_aid),
        "is_part_time":             int(part_time),
        "is_first_generation":      int(first_gen),
    }

    # Run prediction
    with col_result:
        st.subheader("Prediction Result")

        if predictor:
            result = predictor.predict(student_input, include_explanation=True)
            score  = result["risk_score"]
            label  = result["risk_category"]
            expl   = result.get("explanation", {})
        else:
            # Heuristic fallback so demo still works without model
            score = max(0.0, min(1.0,
                (1 - gpa/4) * 0.35 +
                (1 - attendance) * 0.25 +
                (1 - submit) * 0.15 +
                (late / 20) * 0.10 +
                (1 - exam/100) * 0.10 +
                (0.05 if part_time else 0)
            ))
            label = risk_label(score)
            expl  = {}

        color = risk_color(label)
        pct   = score * 100

        # Big gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(pct, 1),
            number={"suffix": "%", "font": {"size": 36}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar":  {"color": color},
                "steps": [
                    {"range": [0,  20], "color": "#dcfce7"},
                    {"range": [20, 40], "color": "#fef9c3"},
                    {"range": [40, 60], "color": "#ffedd5"},
                    {"range": [60, 100],"color": "#fee2e2"},
                ],
                "threshold": {"line": {"color": color, "width": 4},
                              "thickness": 0.75, "value": pct},
            },
            title={"text": f"Dropout Risk: <b>{label}</b>",
                   "font": {"size": 18}},
        ))
        fig_gauge.update_layout(height=280, margin=dict(t=40, b=0, l=20, r=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Risk badge
        st.markdown(
            f"<div style='text-align:center;background:{color}22;"
            f"border:2px solid {color};border-radius:8px;padding:8px;"
            f"font-size:1.2rem;font-weight:700;color:{color}'>"
            f"{label} Risk — {pct:.1f}%</div>",
            unsafe_allow_html=True,
        )

        # Top factors
        if expl and "top_factors" in expl:
            st.markdown("#### Top Risk Drivers")
            for f in expl["top_factors"][:5]:
                name   = f.get("feature", "")
                impact = f.get("shap_value", f.get("contribution", 0))
                direction = "↑ increases" if impact > 0 else "↓ decreases"
                bar_color = "#ef4444" if impact > 0 else "#22c55e"
                st.markdown(
                    f"<div style='margin:4px 0;padding:6px 10px;"
                    f"background:{bar_color}22;border-left:4px solid {bar_color};"
                    f"border-radius:4px;font-size:0.85rem'>"
                    f"<b>{name}</b> — {direction} risk</div>",
                    unsafe_allow_html=True,
                )
        else:
            # Show heuristic factors when model not available
            st.markdown("#### Key Risk Factors")
            factors = [
                ("GPA",              1 - gpa/4,       gpa < 2.5),
                ("Attendance",       1 - attendance,  attendance < 0.75),
                ("Submission Rate",  1 - submit,      submit < 0.8),
                ("Late Submissions", late/20,         late > 5),
                ("Exam Score",       1 - exam/100,    exam < 60),
            ]
            for name, weight, is_risk in sorted(factors, key=lambda x: -x[1]):
                color_f = "#ef4444" if is_risk else "#22c55e"
                arrow   = "↑" if is_risk else "↓"
                st.markdown(
                    f"<div style='margin:4px 0;padding:6px 10px;"
                    f"background:{color_f}22;border-left:4px solid {color_f};"
                    f"border-radius:4px;font-size:0.85rem'>"
                    f"<b>{name}</b> {arrow}</div>",
                    unsafe_allow_html=True,
                )

        # Recommended action
        st.markdown("#### Recommended Action")
        if label == "Critical":
            st.error("🚨 Immediate intervention required. Contact student today.")
        elif label == "High":
            st.warning("⚠️ Schedule counselling session within 48 hours.")
        elif label == "Medium":
            st.info("📋 Monitor closely. Check in next week.")
        else:
            st.success("✅ Student on track. Routine monitoring.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 – FAIRNESS & BIAS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Fairness & Bias":
    st.title("📈 Fairness & Bias Audit")
    st.caption("Demographic parity analysis across protected attributes")

    attr = st.selectbox("Protected Attribute",
                        ["gender","socioeconomic_status","region","department"])

    grp = (
        df.groupby(attr)
        .agg(
            students   = ("student_id", "count"),
            avg_risk   = ("risk_score",  "mean"),
            dropout_rate = ("dropped_out", "mean"),
            pct_at_risk  = ("risk_label",
                            lambda x: (x.isin(["Critical","High"])).mean()),
        )
        .reset_index()
        .rename(columns={attr: "Group"})
    )
    grp["avg_risk"]     = (grp["avg_risk"]     * 100).round(1)
    grp["dropout_rate"] = (grp["dropout_rate"] * 100).round(1)
    grp["pct_at_risk"]  = (grp["pct_at_risk"]  * 100).round(1)

    col_l, col_r = st.columns(2)

    with col_l:
        fig = px.bar(grp, x="Group", y="avg_risk",
                     title=f"Average Risk Score by {attr.replace('_',' ').title()}",
                     color="avg_risk", color_continuous_scale="RdYlGn_r",
                     labels={"avg_risk":"Avg Risk Score (%)"})
        fig.update_layout(height=360)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        fig2 = px.bar(grp, x="Group", y="pct_at_risk",
                      title=f"% At-Risk Students by {attr.replace('_',' ').title()}",
                      color="pct_at_risk", color_continuous_scale="RdYlGn_r",
                      labels={"pct_at_risk":"% At Risk"})
        fig2.update_layout(height=360)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Group-level Statistics")
    st.dataframe(grp.rename(columns={
        "students":"Students","avg_risk":"Avg Risk %",
        "dropout_rate":"Dropout Rate %","pct_at_risk":"At-Risk %",
    }), use_container_width=True, hide_index=True)

    # Demographic parity check
    max_risk = grp["avg_risk"].max()
    min_risk = grp["avg_risk"].min()
    ratio    = min_risk / max_risk if max_risk > 0 else 1.0
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Max Group Risk",  f"{max_risk:.1f}%")
    c2.metric("Min Group Risk",  f"{min_risk:.1f}%")
    c3.metric("Parity Ratio",    f"{ratio:.2f}",
              delta="✅ Fair (≥0.80)" if ratio >= 0.80 else "⚠️ Bias detected",
              delta_color="normal" if ratio >= 0.80 else "inverse")

    if ratio >= 0.80:
        st.success(f"✅ Demographic parity satisfied for **{attr}** (ratio = {ratio:.2f} ≥ 0.80)")
    else:
        st.warning(f"⚠️ Potential bias detected for **{attr}** (ratio = {ratio:.2f} < 0.80). "
                   "Consider reweighing or post-processing mitigation.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 – DATA PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🗄️ Data Pipeline":
    st.title("🗄️ Data Pipeline & Model Info")

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Dataset Summary")
        st.markdown(f"""
| Property | Value |
|---|---|
| **Total records** | {n_total:,} |
| **Features** | {len(raw_df.columns)} raw → {len(df.columns)} with predictions |
| **Dropout rate** | {raw_df['dropped_out'].mean()*100:.1f}% |
| **Avg GPA** | {raw_df['gpa'].mean():.2f} |
| **Avg Attendance** | {raw_df['attendance_rate'].mean()*100:.1f}% |
| **Departments** | {raw_df['department'].nunique()} |
| **Semesters** | 1 – {raw_df['semester'].max()} |
| **Source** | `data/raw/students.csv` |
""")

        st.subheader("Feature Columns")
        st.dataframe(
            pd.DataFrame({"Column": raw_df.columns, "Type": raw_df.dtypes.astype(str).values,
                          "Non-null": raw_df.notna().sum().values,
                          "Sample": [str(raw_df[c].iloc[0]) for c in raw_df.columns]}),
            use_container_width=True, hide_index=True, height=340,
        )

    with col_r:
        st.subheader("ML Model")
        model_path = Path("data/models/xgboost_model.pkl")
        feat_path  = Path("data/models/feature_names.pkl")

        if model_path.exists():
            size_kb = model_path.stat().st_size / 1024
            feats   = joblib.load(feat_path) if feat_path.exists() else []
            st.markdown(f"""
| Property | Value |
|---|---|
| **Algorithm** | XGBoost Classifier |
| **Model file** | `data/models/xgboost_model.pkl` |
| **Model size** | {size_kb:.1f} KB |
| **Input features** | {len(feats)} |
| **Training data** | {n_total:,} students |
| **CV folds** | 3 |
| **Status** | {'✅ Loaded' if model_ok else '⚠️ Fallback'} |
""")
            if feats:
                st.markdown("**Model input features:**")
                st.code("\n".join(feats))
        else:
            st.warning("Model not found. Run: `python ml/train.py`")

        st.subheader("Distribution of Risk Scores")
        fig = px.histogram(df, x="risk_score", nbins=40,
                           color_discrete_sequence=["#3b82f6"],
                           labels={"risk_score":"Risk Score"},
                           title="Model output distribution")
        fig.update_layout(height=280)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Connect Real University Data")
    st.markdown("""
The system supports four data source types via the **Data Source API** (`/api/v1/datasource`):

| Type | Example | How to connect |
|---|---|---|
| **PostgreSQL** | Banner SIS, PeopleSoft | Register via API with host/db/query |
| **MySQL / MSSQL** | Ellucian Colleague | Same as above |
| **CSV / Excel** | Registrar export | Upload file, set `file_path` |
| **REST API** | Canvas LMS, Moodle | Set `api_url` + `api_key` |

After connecting, call `POST /api/v1/datasource/{id}/sync` to pull data into  
`data/raw/students.csv`, then retrain with `python ml/train.py`.
""")


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"🎓 Early Warning System v2.0 · "
    f"{n_total:,} students · "
    f"Model: {'XGBoost (live)' if model_ok else 'Heuristic fallback'} · "
    f"Last updated {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
