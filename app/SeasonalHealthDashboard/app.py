from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

try:
    from scipy import stats
except Exception:  # scipy is optional – p-values are skipped without it
    stats = None

# ──────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Seasonal Health Insights | TerraPulse",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ──────────────────────────────────────────────────────────────
BG = "#09151d"
CARD = "#102129"
BORDER = "rgba(182, 232, 229, 0.16)"
TEXT = "#eef8f7"
MUTED = "#94aeb3"
GRID = "rgba(182, 232, 229, 0.10)"

CYAN, VIOLET, PINK = "#22d3ee", "#a78bfa", "#f472b6"
AMBER, GREEN, BLUE = "#fbbf24", "#34d399", "#60a5fa"
PALETTE = [CYAN, VIOLET, PINK, AMBER, GREEN, BLUE, "#fb7185", "#2dd4bf"]

SEASONS = ["Winter", "Spring", "Summer", "Autumn"]
SEASON_COLORS = {"Winter": BLUE, "Spring": GREEN, "Summer": AMBER, "Autumn": PINK}
SEASON_ICONS = {"Winter": "❄️", "Spring": "🌸", "Summer": "☀️", "Autumn": "🍂"}

MONTHS = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
          7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
MONTH_ORDER = list(MONTHS.values())

POLLUTANTS = ["PM2.5", "PM10", "NO2", "CO", "SO2", "O3"]
WEATHER = ["Temperature_C", "Relative_Humidity_pct", "Wind_Speed_kmh"]
ENV_COLS = POLLUTANTS + WEATHER
LABELS = {
    "PM2.5": "PM2.5", "PM10": "PM10", "NO2": "NO₂", "CO": "CO", "SO2": "SO₂", "O3": "O₃",
    "Temperature_C": "Temperature (°C)", "Relative_Humidity_pct": "Humidity (%)",
    "Wind_Speed_kmh": "Wind (km/h)",
}
lab = lambda c: LABELS.get(c, c)

# WHO 2021 24-hour air-quality guidelines (editable in the sidebar).
# PM/NO2/SO2/O3 in µg/m³, CO in mg/m³ (assumed unit of the CO column).
WHO_DEFAULT = {"PM2.5": 15.0, "PM10": 45.0, "NO2": 25.0, "CO": 4.0, "SO2": 40.0, "O3": 100.0}

PATHOGEN_FIX = {"Rhinovirus/Enteroviru": "Rhinovirus/Enterovirus"}  # truncated in the CSV

st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] {{ background: radial-gradient(circle at 20% 0%, rgba(182,232,229,.07), transparent 28%), {BG}; }}
    [data-testid="stSidebar"] {{ background: rgba(10, 24, 32, .98); border-right: 1px solid {BORDER}; width: 285px; }}
    [data-testid="stSidebar"][aria-expanded="true"] {{ width: 285px; max-width: 285px; }}
    [data-testid="stSidebar"] > div:first-child {{ width: 285px; }}
    [data-testid="stSidebarCollapsedControl"] {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; color: {CYAN}; top: 12px; left: 12px; }}
    [data-testid="stToolbar"] {{ visibility: hidden; }}
    [data-testid="stStatusWidget"] {{ visibility: hidden; }}
    [data-testid="stHeader"] {{ background: transparent; height: 0; }}
    [data-testid="stMainBlockContainer"] {{ padding-top: 1.25rem; }}
    .block-container {{ padding: 1.25rem 2.25rem 3rem; max-width: 1480px; }}
    .stApp {{ font-family: "DM Sans", "Segoe UI", sans-serif; }}

    h1 {{ color: {TEXT}; font-family: Outfit, "DM Sans", sans-serif; font-weight: 700; letter-spacing: -0.5px; }}
    h2, h3 {{ color: {TEXT}; font-weight: 600; }}
    p, label, span {{ color: {TEXT}; }}

    [data-testid="stMetric"] {{
        background: linear-gradient(145deg, {CARD}, #0f1428);
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.25);
    }}
    [data-testid="stMetricLabel"] p {{ color: {MUTED}; font-size: 0.85rem; }}
    [data-testid="stMetricValue"] {{ color: {CYAN}; font-weight: 700; }}

    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; border-bottom: 1px solid {BORDER}; flex-wrap: wrap; }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent; border-radius: 8px 8px 0 0;
        padding: 10px 18px; color: {MUTED};
    }}
    .stTabs [aria-selected="true"] {{ color: {CYAN}; background: {CARD}; }}

    .subtitle {{ color: {MUTED}; font-size: 1.02rem; margin-top: -8px; }}
    .note {{ color: {MUTED}; font-size: 0.82rem; }}
    .callout {{
        background: {CARD}; border: 1px solid {BORDER}; border-left: 4px solid {AMBER};
        border-radius: 10px; padding: 12px 16px; color: {MUTED}; font-size: 0.9rem; margin: 6px 0 14px;
    }}
    .insight {{
        background: {CARD}; border: 1px solid {BORDER}; border-left: 4px solid {CYAN};
        border-radius: 10px; padding: 12px 16px; color: {TEXT}; margin-bottom: 10px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────
def style_fig(fig, title, height=430):
    """Apply one consistent, professional look to every chart."""
    fig.update_layout(
        template="plotly_dark",
        title=dict(text=title, x=0.02, xanchor="left", font=dict(size=17, color=TEXT)),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, Roboto, sans-serif", color=MUTED, size=13),
        margin=dict(l=20, r=20, t=70, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", title_text=""),
        hoverlabel=dict(bgcolor=CARD, bordercolor=BORDER, font_size=13, font_color=TEXT),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=BORDER)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=BORDER)
    return fig


def show(fig):
    """Works on both old and new Streamlit versions."""
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def show_df(d, **kw):
    try:
        st.dataframe(d, width="stretch", **kw)
    except TypeError:
        st.dataframe(d, use_container_width=True, **kw)


def callout(text):
    st.markdown(f'<div class="callout">{text}</div>', unsafe_allow_html=True)


def insight(text):
    st.markdown(f'<div class="insight">{text}</div>', unsafe_allow_html=True)


@st.cache_data(show_spinner="Loading satellite & respiratory data…")
def load_data(src):
    df = pd.read_csv(src)
    df["pathogen"] = df["pathogen"].replace(PATHOGEN_FIX)
    df["month"] = df["month"].astype(int)
    df["season"] = pd.Categorical(df["season"], categories=SEASONS, ordered=True)
    return df


# ── analysis functions (pure pandas, no Streamlit) ───────────
def build_monthly(df, months, pathogens):
    """One row per month: environment (constant within a month) + record count."""
    env = df.groupby("month")[ENV_COLS].mean()
    out = env.copy()
    out["season"] = df.groupby("month")["season"].first().astype(str)
    out["cases"] = (df[df["pathogen"].isin(pathogens)].groupby("month").size()
                    .reindex(env.index, fill_value=0))
    out = out.loc[out.index.isin(months)].reset_index()
    out["Month_Name"] = out["month"].map(MONTHS)
    return out


def season_means(m):
    order = [s for s in SEASONS if s in set(m["season"])]
    g = m.groupby("season")[ENV_COLS].mean().reindex(order)
    g["cases"] = m.groupby("season")["cases"].sum().reindex(order)
    return g


def dominance_table(sm, method, annual, who):
    """Season × pollutant score. Dominant pollutant = highest score in each row."""
    pol = sm[POLLUTANTS]
    if method.startswith("WHO"):
        return pol / pd.Series(who)[POLLUTANTS]
    return pol / annual[POLLUTANTS]


def corr_p(x, y, method):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 4 or np.std(x) == 0 or np.std(y) == 0:
        return np.nan, np.nan
    if stats is not None:
        r, p = (stats.spearmanr(x, y) if method == "Spearman" else stats.pearsonr(x, y))
        return float(r), float(p)
    if method == "Spearman":
        x, y = pd.Series(x).rank().values, pd.Series(y).rank().values
    return float(np.corrcoef(x, y)[0, 1]), np.nan


def stars(p):
    return "" if pd.isna(p) else "**" if p < 0.01 else "*" if p < 0.05 else ""


def strength(r):
    a = abs(r)
    return "very strong" if a >= 0.8 else "strong" if a >= 0.6 else "moderate" if a >= 0.4 else "weak"


# ──────────────────────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────────────────────
DATA_FILE = "final_merged_respiratory_satellite_data.csv"
DATA_PATH = Path(__file__).parent / DATA_FILE
uploaded = st.sidebar.file_uploader("Upload CSV (optional)", type="csv")

if uploaded is not None:
    df = load_data(uploaded)
elif DATA_PATH.exists():
    df = load_data(str(DATA_PATH))
else:
    st.error(f"`{DATA_FILE}` not found next to app.py. Place it there or upload it from the sidebar.")
    st.stop()

REQUIRED = ["season", "pathogen", "month"] + ENV_COLS
missing = [c for c in REQUIRED if c not in df.columns]
if missing:
    st.error(f"Missing columns in the CSV: {missing}")
    st.stop()

# ──────────────────────────────────────────────────────────────
# SIDEBAR FILTERS
# ──────────────────────────────────────────────────────────────
st.sidebar.header(" Filters")

all_seasons = [s for s in SEASONS if s in set(df["season"].astype(str))]
sel_seasons = st.sidebar.multiselect("Season(s)", all_seasons, default=all_seasons,
                                     format_func=lambda s: f"{SEASON_ICONS[s]} {s}")
all_pathogens = sorted(df["pathogen"].unique())
sel_pathogens = st.sidebar.multiselect("Pathogen(s)", all_pathogens, default=all_pathogens)

corr_method = st.sidebar.radio("Correlation method", ["Spearman", "Pearson"], horizontal=True,
                               help="Spearman (rank-based) is safer with only 12 monthly points.")

with st.sidebar.expander("⚙️ WHO guideline values (24-h)"):
    st.caption("Used for the 'dominant pollutant' ratio. µg/m³ — CO assumed mg/m³.")
    WHO = {p: st.number_input(lab(p), min_value=0.1, value=WHO_DEFAULT[p], step=1.0, key=f"who_{p}")
           for p in POLLUTANTS}

if not sel_seasons or not sel_pathogens:
    st.warning("Select at least one season and one pathogen in the sidebar.")
    st.stop()

filtered = df[df["season"].astype(str).isin(sel_seasons) & df["pathogen"].isin(sel_pathogens)]
if filtered.empty:
    st.warning("No data matches the selected filters. Please widen your criteria in the sidebar.")
    st.stop()

sel_months = sorted(df.loc[df["season"].astype(str).isin(sel_seasons), "month"].unique())
monthly = build_monthly(df, sel_months, sel_pathogens)           # filtered monthly table
monthly_all = build_monthly(df, range(1, 13), sel_pathogens)     # full year (for lag analysis)
annual = df.groupby("month")[ENV_COLS].mean().mean()             # annual mean of monthly values
sm = season_means(monthly)
month_season = monthly.set_index("month")["season"].to_dict()

st.sidebar.download_button("⬇️ Download monthly table", monthly.to_csv(index=False).encode(),
                           "monthly_environment_health.csv", "text/csv")

# ──────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────
st.title("Seasonal Health Intelligence")
st.markdown('<p class="subtitle">Seasonal pollution patterns, dominant pollutants and their link '
            'to respiratory pathogen activity</p>', unsafe_allow_html=True)

callout("ℹ️ <b>How to read this data:</b> every row is a respiratory-pathogen record. Pollutant and weather "
        "values are <b>monthly satellite aggregates</b> (identical for all records in the same month), so "
        "pollution-vs-health relationships are measured on <b>monthly points</b> (max 12). Correlations "
        "show association, not causation, and should be treated as indicative.")

# ── derived headline numbers ─────────────────────────────────
dom_who = dominance_table(sm, "WHO", annual, WHO)
overall_dom = (sm[POLLUTANTS].mean() / pd.Series(WHO)[POLLUTANTS]).idxmax()
peak_season = sm["cases"].idxmax()
peak_month = monthly.loc[monthly["cases"].idxmax(), "Month_Name"]

corr_rows = []
for v in ENV_COLS:
    r, p = corr_p(monthly[v], monthly["cases"], corr_method)
    corr_rows.append({"Variable": v, "r": r, "p": p})
corr_df = pd.DataFrame(corr_rows)
best = corr_df.loc[corr_df["r"].abs().idxmax()] if corr_df["r"].notna().any() else None

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Pathogen records", f"{len(filtered):,}", f"{len(filtered) / len(df):.0%} of dataset", delta_color="off")
now, base = monthly["PM2.5"].mean(), annual["PM2.5"]
k2.metric("Avg PM2.5", f"{now:,.1f} µg/m³", f"{now - base:+.1f} vs annual", delta_color="inverse")
k3.metric("Peak season (records)", f"{SEASON_ICONS[peak_season]} {peak_season}",
          f"peak month: {peak_month}", delta_color="off")
k4.metric("Dominant pollutant", lab(overall_dom),
          f"{(sm[POLLUTANTS].mean() / pd.Series(WHO)[POLLUTANTS]).max():.1f}× WHO limit", delta_color="off")
if best is not None:
    k5.metric("Strongest health link", lab(best["Variable"]), f"r = {best['r']:+.2f}", delta_color="off")
else:
    k5.metric("Strongest health link", "n/a", "need ≥ 4 months", delta_color="off")

st.write("")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Overview", "🌦️ Seasonal patterns", "🏭 Dominant pollutant",
    "🦠 Respiratory burden", "🔗 Pollution vs health", "💡 Insights & data",
])

# ──────────────────────────────────────────────────────────────
# TAB 1 – OVERVIEW
# ──────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Season at a glance")
    cols = st.columns(len(sm))
    for col, s in zip(cols, sm.index):
        with col:
            st.markdown(f"### {SEASON_ICONS[s]} {s}")
            st.metric("Dominant pollutant (WHO ratio)", lab(dom_who.loc[s].idxmax()),
                      f"{dom_who.loc[s].max():.1f}× limit", delta_color="off")
            st.metric("Avg PM2.5", f"{sm.loc[s, 'PM2.5']:.1f} µg/m³")
            st.metric("Pathogen records", f"{int(sm.loc[s, 'cases']):,}")
            st.metric("Avg temperature", f"{sm.loc[s, 'Temperature_C']:.1f} °C")

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=monthly["Month_Name"], y=monthly["cases"], name="Pathogen records",
                             marker_color=[SEASON_COLORS[s] for s in monthly["season"]], opacity=0.85))
        fig.add_trace(go.Scatter(x=monthly["Month_Name"], y=monthly["PM2.5"], name="PM2.5 (µg/m³)",
                                 yaxis="y2", mode="lines+markers",
                                 line=dict(color=TEXT, width=3, shape="spline")))
        fig.update_layout(
            xaxis=dict(categoryorder="array", categoryarray=MONTH_ORDER),
            yaxis=dict(title="Pathogen records"),
            yaxis2=dict(title="PM2.5 (µg/m³)", overlaying="y", side="right", showgrid=False),
        )
        show(style_fig(fig, "Monthly pathogen records vs PM2.5  ·  bar colour = season"))
    with c2:
        mix = filtered.groupby(["season", "pathogen"], observed=True).size().reset_index(name="Records")
        fig = px.bar(mix, x="season", y="Records", color="pathogen", barmode="stack",
                     category_orders={"season": SEASONS}, color_discrete_sequence=PALETTE)
        fig.update_layout(xaxis_title="", yaxis_title="Records")
        show(style_fig(fig, "Pathogen records by season"))

# ──────────────────────────────────────────────────────────────
# TAB 2 – SEASONAL PATTERNS
# ──────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Seasonal pattern analysis")
    chosen = st.multiselect("Variables to compare (shown as index, annual mean = 100)",
                            ENV_COLS, default=["PM2.5", "PM10", "NO2", "CO"], format_func=lab)

    if chosen:
        fig = go.Figure()
        for i, v in enumerate(chosen):
            fig.add_trace(go.Scatter(
                x=monthly["month"], y=monthly[v] / annual[v] * 100, name=lab(v), mode="lines+markers",
                line=dict(color=PALETTE[i % len(PALETTE)], width=3, shape="spline"), marker=dict(size=7),
                customdata=monthly[v], hovertemplate="%{x}: index %{y:.0f} (value %{customdata:.2f})<extra>" + lab(v) + "</extra>"))
        for mth, s in month_season.items():     # season shading behind the lines
            fig.add_vrect(x0=mth - 0.5, x1=mth + 0.5, fillcolor=SEASON_COLORS[s], opacity=0.08,
                          line_width=0, layer="below")
        fig.add_hline(y=100, line_dash="dot", line_color=MUTED)
        fig.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=MONTH_ORDER)
        fig.update_yaxes(title="Index (annual mean = 100)")
        show(style_fig(fig, "Monthly profile  ·  background tint = season", height=450))

    c1, c2 = st.columns(2)
    with c1:
        idx = sm[POLLUTANTS] / annual[POLLUTANTS] * 100
        theta = [lab(p) for p in POLLUTANTS]
        fig = go.Figure()
        for s in idx.index:
            vals = idx.loc[s].tolist()
            fig.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=theta + theta[:1], name=s,
                                          fill="toself", opacity=0.55,
                                          line=dict(color=SEASON_COLORS[s], width=2)))
        fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                     radialaxis=dict(gridcolor=GRID, linecolor=BORDER),
                                     angularaxis=dict(gridcolor=GRID, linecolor=BORDER)))
        show(style_fig(fig, "Seasonal pollutant fingerprint (index, annual = 100)"))
    with c2:
        zs = (monthly[ENV_COLS] - annual) / df.groupby("month")[ENV_COLS].mean().std()
        zs.index = monthly["Month_Name"]
        zs.columns = [lab(c) for c in zs.columns]
        fig = px.imshow(zs.T, aspect="auto", color_continuous_scale="RdBu_r", zmin=-2.5, zmax=2.5,
                        labels=dict(color="z-score"))
        fig.update_layout(coloraxis_colorbar=dict(title="z-score", thickness=12))
        show(style_fig(fig, "Anomaly heatmap: month × variable (z-score vs the year)"))

    wfig = make_subplots(rows=1, cols=3, subplot_titles=[lab(w) for w in WEATHER])
    for i, w in enumerate(WEATHER, start=1):
        wfig.add_trace(go.Bar(x=sm.index.tolist(), y=sm[w], marker_color=[SEASON_COLORS[s] for s in sm.index],
                              text=sm[w].round(1), textposition="outside", showlegend=False), row=1, col=i)
    wfig.update_annotations(font=dict(color=TEXT, size=14))
    show(style_fig(wfig, "Weather by season", height=360))

    abs_pol = st.selectbox("Absolute seasonal level of a pollutant", POLLUTANTS, format_func=lab)
    fig = px.bar(sm.reset_index(), x="season", y=abs_pol, color="season", text_auto=".1f",
                 color_discrete_map=SEASON_COLORS, category_orders={"season": SEASONS})
    fig.add_hline(y=WHO[abs_pol], line_dash="dash", line_color=PINK,
                  annotation_text=f"WHO 24-h guideline ({WHO[abs_pol]:g})", annotation_font_color=PINK)
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title=f"Mean {lab(abs_pol)}")
    show(style_fig(fig, f"{lab(abs_pol)} by season vs WHO guideline", height=380))

# ──────────────────────────────────────────────────────────────
# TAB 3 – DOMINANT POLLUTANT
# ──────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Which pollutant dominates in each season?")
    method = st.radio(
        "Dominance definition",
        ["WHO ratio – which pollutant exceeds its health guideline the most",
         "Seasonal index – which pollutant is most elevated vs its own annual average"],
        horizontal=False)
    score = dominance_table(sm, method, annual, WHO)
    dominant = score.idxmax(axis=1)
    unit_txt = "× WHO guideline" if method.startswith("WHO") else "× annual mean"

    cols = st.columns(len(score))
    for col, s in zip(cols, score.index):
        col.metric(f"{SEASON_ICONS[s]} {s}", lab(dominant[s]), f"{score.loc[s].max():.2f} {unit_txt}",
                   delta_color="off")

    c1, c2 = st.columns(2)
    with c1:
        hm = score.copy()
        hm.columns = [lab(c) for c in hm.columns]
        fig = px.imshow(hm, text_auto=".2f", aspect="auto", color_continuous_scale="Inferno",
                        labels=dict(x="Pollutant", y="Season", color=unit_txt))
        fig.update_layout(coloraxis_colorbar=dict(title=unit_txt, thickness=12))
        show(style_fig(fig, f"Season × pollutant score ({unit_txt})"))
    with c2:
        share = score.div(score.sum(axis=1), axis=0).mul(100).reset_index().melt(
            id_vars="season", var_name="Pollutant", value_name="Share")
        share["Pollutant"] = share["Pollutant"].map(lab)
        fig = px.bar(share, x="season", y="Share", color="Pollutant", text_auto=".0f",
                     category_orders={"season": SEASONS}, color_discrete_sequence=PALETTE)
        fig.update_layout(xaxis_title="", yaxis_title="Share of total score (%)")
        show(style_fig(fig, "Pollutant share of seasonal burden (normalised)"))

    c1, c2 = st.columns(2)
    with c1:
        who_ratio = (sm[POLLUTANTS] / pd.Series(WHO)[POLLUTANTS]).reset_index().melt(
            id_vars="season", var_name="Pollutant", value_name="Ratio")
        who_ratio["Pollutant"] = who_ratio["Pollutant"].map(lab)
        fig = px.bar(who_ratio, x="Pollutant", y="Ratio", color="season", barmode="group",
                     color_discrete_map=SEASON_COLORS, category_orders={"season": SEASONS})
        fig.add_hline(y=1, line_dash="dash", line_color=PINK, annotation_text="WHO guideline = 1×",
                      annotation_font_color=PINK)
        fig.update_layout(xaxis_title="", yaxis_title="Mean ÷ WHO guideline")
        show(style_fig(fig, "Guideline exceedance by season"))
    with c2:
        idx_tbl = sm[POLLUTANTS] / annual[POLLUTANTS]
        peak = pd.DataFrame({
            "Pollutant": [lab(p) for p in POLLUTANTS],
            "Peak season": [idx_tbl[p].idxmax() for p in POLLUTANTS],
            "Cleanest season": [idx_tbl[p].idxmin() for p in POLLUTANTS],
            "Peak ÷ annual mean": [f"{idx_tbl[p].max():.2f}×" for p in POLLUTANTS],
            "Peak ÷ cleanest": [f"{idx_tbl[p].max() / idx_tbl[p].min():.2f}×" for p in POLLUTANTS],
        })
        st.markdown("##### When does each pollutant peak?")
        show_df(peak, hide_index=True)
        st.markdown('<p class="note">Seasons are averaged from monthly values (equal weight per month).'
                    ' Use the WHO ratio to judge health relevance, and the seasonal index to see what '
                    'is <i>distinctive</i> about a season.</p>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# TAB 4 – RESPIRATORY BURDEN
# ──────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Respiratory pathogen activity")
    c1, c2 = st.columns(2)
    with c1:
        ct = filtered.groupby(["month", "pathogen"]).size().reset_index(name="Records")
        ct["Month"] = ct["month"].map(MONTHS)
        fig = px.bar(ct, x="Month", y="Records", color="pathogen", barmode="stack",
                     category_orders={"Month": MONTH_ORDER}, color_discrete_sequence=PALETTE)
        fig.update_layout(xaxis_title="", yaxis_title="Records")
        show(style_fig(fig, "Monthly records by pathogen"))
    with c2:
        sp = filtered.groupby(["season", "pathogen"], observed=True).size().reset_index(name="Records")
        sp["Share"] = sp["Records"] / sp.groupby("season", observed=True)["Records"].transform("sum") * 100
        fig = px.bar(sp, x="season", y="Share", color="pathogen", text_auto=".0f",
                     category_orders={"season": SEASONS}, color_discrete_sequence=PALETTE)
        fig.update_layout(xaxis_title="", yaxis_title="Share of season's records (%)")
        show(style_fig(fig, "Pathogen mix by season"))

    pm = pd.crosstab(filtered["pathogen"], filtered["month"]).reindex(columns=range(1, 13), fill_value=0)
    pm = pm[[c for c in pm.columns if c in sel_months]]
    pm_share = pm.div(pm.sum(axis=1), axis=0) * 100
    pm_share.columns = [MONTHS[c] for c in pm_share.columns]
    fig = px.imshow(pm_share, text_auto=".0f", aspect="auto", color_continuous_scale="Tealgrn",
                    labels=dict(x="Month", y="Pathogen", color="% of records"))
    fig.update_layout(coloraxis_colorbar=dict(title="% of pathogen's records", thickness=12))
    show(style_fig(fig, "When does each pathogen peak? (share of its records per month)", height=420))

    pk = pd.DataFrame({
        "Pathogen": pm.index,
        "Peak month": [MONTHS[pm.loc[p].idxmax()] for p in pm.index],
        "Peak season": [month_season.get(pm.loc[p].idxmax(), "") for p in pm.index],
        "Total records": pm.sum(axis=1).values,
        "Records in peak month": pm.max(axis=1).values,
    })
    show_df(pk, hide_index=True)
    st.markdown('<p class="note">Note: in this dataset all pathogens except Influenza have identical monthly '
                'record counts, so their seasonal profiles look alike; Influenza has roughly 2.3× as many '
                'records.</p>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# TAB 5 – POLLUTION vs HEALTH
# ──────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Correlation: environment vs respiratory records")
    if len(monthly) < 4:
        st.info("Select at least 4 months (e.g. two seasons) to compute correlations.")
    else:
        target = st.selectbox("Health outcome (monthly record count)",
                              ["All selected pathogens"] + list(sel_pathogens))
        if target == "All selected pathogens":
            y_series = monthly.set_index("month")["cases"]
        else:
            y_series = (df[df["pathogen"] == target].groupby("month").size()
                        .reindex(range(1, 13), fill_value=0).loc[monthly["month"]])
        y_series.index = monthly["month"]

        rows = []
        for v in ENV_COLS:
            r, p = corr_p(monthly[v].values, y_series.values, corr_method)
            rows.append({"Variable": lab(v), "key": v, "r": r, "p": p})
        cr = pd.DataFrame(rows).sort_values("r")
        cr["label"] = [f"{r:+.2f}{stars(p)}" for r, p in zip(cr["r"], cr["p"])]

        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure(go.Bar(
                x=cr["r"], y=cr["Variable"], orientation="h", text=cr["label"], textposition="outside",
                marker=dict(color=cr["r"], colorscale="RdBu_r", cmin=-1, cmax=1),
                customdata=cr["p"], hovertemplate="%{y}: r=%{x:.2f}, p=%{customdata:.3f}<extra></extra>"))
            fig.update_xaxes(range=[-1.15, 1.15], title=f"{corr_method} r  (* p<0.05, ** p<0.01)")
            show(style_fig(fig, f"What moves with {target.lower()}?"))
        with c2:
            hrows = {}
            for pth in sel_pathogens:
                ys = df[df["pathogen"] == pth].groupby("month").size().reindex(
                    range(1, 13), fill_value=0).loc[monthly["month"]]
                hrows[pth] = [corr_p(monthly[v].values, ys.values, corr_method)[0] for v in ENV_COLS]
            hm = pd.DataFrame(hrows, index=[lab(v) for v in ENV_COLS]).T
            fig = px.imshow(hm, text_auto=".2f", zmin=-1, zmax=1, aspect="auto",
                            color_continuous_scale="RdBu_r")
            fig.update_layout(coloraxis_colorbar=dict(title="r", thickness=12))
            show(style_fig(fig, "Pathogen × environment correlation"))

        # scatter with trendline
        c1, c2 = st.columns(2)
        with c1:
            xv = st.selectbox("X variable", ENV_COLS, index=0, format_func=lab)
            fig = go.Figure()
            for s in SEASONS:
                mk = monthly["season"] == s
                if mk.any():
                    fig.add_trace(go.Scatter(
                        x=monthly.loc[mk, xv], y=y_series[monthly.loc[mk, "month"]].values,
                        mode="markers+text", text=monthly.loc[mk, "Month_Name"], textposition="top center",
                        name=s, marker=dict(size=13, color=SEASON_COLORS[s], line=dict(width=1, color=BG))))
            x_all, y_all = monthly[xv].values.astype(float), y_series.values.astype(float)
            if np.std(x_all) > 0:
                k, b = np.polyfit(x_all, y_all, 1)
                xs = np.linspace(x_all.min(), x_all.max(), 50)
                fig.add_trace(go.Scatter(x=xs, y=k * xs + b, mode="lines", name="Linear trend",
                                         line=dict(color=TEXT, dash="dash", width=2)))
            r, p = corr_p(x_all, y_all, corr_method)
            fig.update_layout(xaxis_title=lab(xv), yaxis_title="Monthly records")
            ptxt = f", p = {p:.3f}" if not pd.isna(p) else ""
            show(style_fig(fig, f"{lab(xv)} vs records  ·  {corr_method} r = {r:+.2f}{ptxt}"))

        with c2:
            lag_vars = st.multiselect("Variables for lag analysis", ENV_COLS,
                                      default=["PM2.5", "PM10", "NO2", "CO"], format_func=lab)
            if target == "All selected pathogens":
                cases_full = monthly_all.set_index("month")["cases"].values
            else:
                cases_full = (df[df["pathogen"] == target].groupby("month").size()
                              .reindex(range(1, 13), fill_value=0).values)
            env_full = monthly_all.set_index("month")
            fig = go.Figure()
            for i, v in enumerate(lag_vars):
                rs = [corr_p(env_full[v].values, np.roll(cases_full, -lag), corr_method)[0]
                      for lag in range(0, 4)]
                fig.add_trace(go.Scatter(x=[0, 1, 2, 3], y=rs, name=lab(v), mode="lines+markers",
                                         line=dict(color=PALETTE[i % len(PALETTE)], width=3),
                                         marker=dict(size=8)))
            fig.add_hline(y=0, line_color=MUTED, line_dash="dot")
            fig.update_xaxes(title="Lag (months): pollution in month t → records in month t+lag", dtick=1)
            fig.update_yaxes(title=f"{corr_method} r", range=[-1, 1])
            show(style_fig(fig, "Does pollution lead respiratory records? (full year, circular)"))

        full_corr = monthly[ENV_COLS + ["cases"]].rename(columns={**LABELS, "cases": "Pathogen records"})
        cm = full_corr.corr(method="spearman" if corr_method == "Spearman" else "pearson")
        fig = px.imshow(cm, text_auto=".2f", zmin=-1, zmax=1, aspect="auto", color_continuous_scale="RdBu_r")
        fig.update_layout(coloraxis_colorbar=dict(title="r", thickness=12))
        show(style_fig(fig, "Full correlation matrix (monthly level)", height=540))

# ──────────────────────────────────────────────────────────────
# TAB 6 – INSIGHTS & DATA
# ──────────────────────────────────────────────────────────────
with tab6:
    st.subheader("Auto-generated insights (update with the filters)")

    for s in sm.index:
        w, ix = dom_who.loc[s], dominance_table(sm, "Seasonal", annual, WHO).loc[s]
        insight(f"<b>{SEASON_ICONS[s]} {s}:</b> {lab(w.idxmax())} dominates the guideline burden "
                f"({w.max():.1f}× WHO limit, PM2.5 avg {sm.loc[s, 'PM2.5']:.0f} µg/m³). "
                f"Most elevated vs its annual norm: {lab(ix.idxmax())} ({ix.max():.2f}×). "
                f"{int(sm.loc[s, 'cases']):,} pathogen records.")

    if len(sm) > 1:
        lo = sm["PM2.5"].idxmin()
        insight(f"<b>Seasonal swing:</b> PM2.5 is {sm['PM2.5'].max() / sm['PM2.5'].min():.1f}× higher in "
                f"{sm['PM2.5'].idxmax()} than in {lo}; records peak in <b>{peak_season}</b> "
                f"(month with most records: {peak_month}).")

    if best is not None and len(monthly) >= 4:
        pos = corr_df[corr_df["r"] > 0].sort_values("r", ascending=False).head(3)
        neg = corr_df[corr_df["r"] < 0].sort_values("r").head(2)
        insight(f"<b>Strongest association:</b> {lab(best['Variable'])} has a {strength(best['r'])} "
                f"{'positive' if best['r'] > 0 else 'negative'} {corr_method} correlation with monthly "
                f"records (r = {best['r']:+.2f}{stars(best['p'])}).")
        if len(pos):
            insight("<b>Risk-increasing factors:</b> " + ", ".join(
                f"{lab(r.Variable)} ({r.r:+.2f})" for r in pos.itertuples()))
        if len(neg):
            insight("<b>Protective / inverse factors:</b> " + ", ".join(
                f"{lab(r.Variable)} ({r.r:+.2f})" for r in neg.itertuples()))

    callout("⚠️ Only up to 12 monthly points back every correlation, pollutant and weather values are "
            "shared by all pathogens within a month, and many of these variables co-vary seasonally "
            "(cold + stagnant + polluted months coincide). Treat results as hypotheses, not proof of cause.")

    st.markdown("##### Monthly table")
    tbl = monthly.drop(columns=["Month_Name"]).rename(columns={**LABELS, "cases": "Pathogen records"})
    show_df(tbl.round(2), hide_index=True)

    st.markdown("##### Season summary")
    ss = sm.rename(columns={**LABELS, "cases": "Pathogen records"}).round(2)
    show_df(ss)

st.markdown(
    '<p class="note">Note: the dataset has no latitude/longitude columns, so no map is shown, and its '
    'Hour / DayOfWeek / DayOfYear columns are monthly averages, so no intraday or weekday charts are '
    'shown.</p>',
    unsafe_allow_html=True,
)