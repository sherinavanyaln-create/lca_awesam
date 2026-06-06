import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(
    page_title="Mini openLCA Awesam Malang",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }

.main-header {
    background: #f8f9fa; border: 1px solid #e0e0e0;
    border-radius: 8px; padding: 14px 20px; margin-bottom: 1.2rem;
}
.main-header h2 { margin: 0; font-size: 17px; font-weight: 600; color: #1a1a1a; }
.main-header p  { margin: 2px 0 0; font-size: 12px; color: #666; }

.stTabs [data-baseweb="tab-list"] { gap: 0px; border-bottom: 2px solid #d0d0d0; }
.stTabs [data-baseweb="tab"] {
    padding: 8px 18px; font-size: 13px; font-weight: 400;
    color: #555; border-bottom: 2px solid transparent; margin-bottom: -2px;
}
.stTabs [aria-selected="true"] {
    color: #1a73e8; border-bottom: 2px solid #1a73e8; font-weight: 500;
}

.panel {
    background: #fff; border: 1px solid #e0e0e0;
    border-radius: 6px; padding: 14px 18px; margin-bottom: 12px;
}
.panel-title {
    font-size: 12px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: #666; margin-bottom: 10px;
    border-bottom: 1px solid #f0f0f0; padding-bottom: 6px;
}

.lca-table { width: 100%; font-size: 13px; border-collapse: collapse; }
.lca-table th {
    background: #f8f9fa; border-bottom: 2px solid #e0e0e0;
    padding: 8px 10px; text-align: left; font-size: 11px;
    font-weight: 600; color: #555; white-space: nowrap;
}
.lca-table td { padding: 7px 10px; border-bottom: 1px solid #f0f0f0; font-size: 13px; vertical-align: middle; }
.lca-table tr:hover td { background: #f8f9fa; }
.lca-table .dominant { font-weight: 600; color: #c5221f; }

.note-box {
    background: #e8f0fe; border-left: 3px solid #1a73e8;
    border-radius: 4px; padding: 10px 14px;
    font-size: 12px; color: #333; margin-top: 10px;
}

.contrib-bar-wrap { display: flex; height: 18px; border-radius: 4px; overflow: hidden; margin: 10px 0; }
.legend-row { display: flex; flex-wrap: wrap; gap: 14px; font-size: 12px; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }

section[data-testid="stSidebar"] { background: #f1f3f4; }
.sidebar-header { font-size: 13px; font-weight: 600; color: #333; margin-bottom: 8px; }

.stButton > button {
    width: 100%; background: #1a73e8; color: #fff;
    border: none; border-radius: 6px; padding: 10px;
    font-size: 14px; font-weight: 500;
}
.stButton > button:hover { background: #1557b0; }
</style>
""", unsafe_allow_html=True)

# ─── FAKTOR KARAKTERISASI ────────────────────────────────────────────────────

F_EMISI_LISTRIK = 0.80  # kg CO₂ eq / kWh (Faktor Emisi Listrik Indonesia)

# Global Warming
# - Listrik: dihitung dari faktor emisi PLN Indonesia
# - LDPE & Paper: reverse-engineered dari contribution tree openLCA 2.6.1
F_GW = {
    "listrik": F_EMISI_LISTRIK,   # kg CO₂ eq / kWh
    "ldpe":    4.35668 / 1.5,     # kg CO₂ eq / kg LDPE  = 2.90445
    "paper":   0.63383 / 0.6,     # kg CO₂ eq / kg paper = 1.05638
}

# Fine Particulate Matter — dari contribution tree openLCA (eksak)
F_FPM = {
    "ldpe":  0.00225 / 1.5,   # kg PM2.5 eq / kg LDPE  = 0.001500
    "paper": 0.00101 / 0.6,   # kg PM2.5 eq / kg paper = 0.001683
}

# Fossil Resource Scarcity — dominan LDPE (plastik berbasis fosil)
F_FRS = {
    "ldpe":  2.83815 * 0.85 / 1.5,
    "paper": 2.83815 * 0.15 / 0.6,
}

# Land Use — dominan paper (butuh lahan untuk produksi kertas)
F_LU = {
    "paper": 0.89185 / 0.6,   # m²a crop eq / kg paper = 1.48642
    "ldpe":  0.0,
}

# Ionizing Radiation — dari konsumsi listrik
F_IR = {
    "listrik": 0.62918 / 42.0,  # kBq Co-60 eq / kWh = 0.014980
}

# Terrestrial Acidification
F_TA = {
    "ldpe":  0.00839 * 0.6 / 1.5,
    "paper": 0.00839 * 0.4 / 0.6,
}

# Human non-carcinogenic toxicity
F_HNCT = {
    "ldpe":  2.41734 * 0.55 / 1.5,
    "paper": 2.41734 * 0.45 / 0.6,
}

# Terrestrial ecotoxicity
F_TE = {
    "ldpe":  6.05257 * 0.4 / 1.5,
    "paper": 6.05257 * 0.6 / 0.6,
}

# Ozone formation
F_OT = {
    "ldpe":  0.01025 * 0.5 / 1.5,
    "paper": 0.01025 * 0.5 / 0.6,
}
F_OH = {
    "ldpe":  0.00921 * 0.5 / 1.5,
    "paper": 0.00921 * 0.5 / 0.6,
}

# Freshwater ecotoxicity
F_FE = {
    "ldpe":  0.06652 * 0.5 / 1.5,
    "paper": 0.06652 * 0.5 / 0.6,
}

# Marine ecotoxicity
F_ME = {
    "ldpe":  0.09361 * 0.5 / 1.5,
    "paper": 0.09361 * 0.5 / 0.6,
}

# Freshwater eutrophication
F_FEU = {
    "paper": 0.00091 / 0.6,
    "ldpe":  0.0,
}

# Marine eutrophication
F_MEU = {
    "paper": 0.00015 * 0.6 / 0.6,
    "ldpe":  0.00015 * 0.4 / 1.5,
}

# Mineral resource scarcity
F_MRS = {
    "ldpe":  0.00606 * 0.5 / 1.5,
    "paper": 0.00606 * 0.5 / 0.6,
}

# Stratospheric ozone depletion
F_SOD = {
    "ldpe":  1.71656e-6 * 0.7 / 1.5,
    "paper": 1.71656e-6 * 0.3 / 0.6,
}

# Human carcinogenic toxicity
F_HCT = {
    "ldpe":  0.08138 * 0.5 / 1.5,
    "paper": 0.08138 * 0.5 / 0.6,
}

# Water consumption
F_WC = {
    "ldpe":  -0.02025 * 0.4 / 1.5,
    "paper": -0.02025 * 0.6 / 0.6,
}


# ─── FUNGSI PERHITUNGAN ───────────────────────────────────────────────────────
def hitung_lca(listrik, ldpe, paper, kain, benang, kaos, perca):
    """
    Langkah 10: CO2 = listrik × F_EMISI_LISTRIK (0.80 kg CO₂eq/kWh)
                GW  = CO2 + (LDPE × F_LDPE_GW) + (Paper × F_PAPER_GW)
    Langkah 11-12: Impact_X = Σ(input_i × faktor_i) per kategori
    """

    co2_dari_listrik = listrik * F_EMISI_LISTRIK

    gw = co2_dari_listrik + (ldpe * F_GW["ldpe"]) + (paper * F_GW["paper"])

    fpm  = (ldpe * F_FPM["ldpe"])  + (paper * F_FPM["paper"])
    frs  = (ldpe * F_FRS["ldpe"])  + (paper * F_FRS["paper"])
    lu   = (paper * F_LU["paper"]) + (ldpe  * F_LU["ldpe"])
    ir   = listrik * F_IR["listrik"]
    ta   = (ldpe * F_TA["ldpe"])   + (paper * F_TA["paper"])
    hnct = (ldpe * F_HNCT["ldpe"]) + (paper * F_HNCT["paper"])
    te   = (ldpe * F_TE["ldpe"])   + (paper * F_TE["paper"])
    ot   = (ldpe * F_OT["ldpe"])   + (paper * F_OT["paper"])
    oh   = (ldpe * F_OH["ldpe"])   + (paper * F_OH["paper"])
    fe   = (ldpe * F_FE["ldpe"])   + (paper * F_FE["paper"])
    me   = (ldpe * F_ME["ldpe"])   + (paper * F_ME["paper"])
    feu  = paper * F_FEU["paper"]
    meu  = (ldpe * F_MEU["ldpe"])  + (paper * F_MEU["paper"])
    mrs  = (ldpe * F_MRS["ldpe"])  + (paper * F_MRS["paper"])
    sod  = (ldpe * F_SOD["ldpe"])  + (paper * F_SOD["paper"])
    hct  = (ldpe * F_HCT["ldpe"])  + (paper * F_HCT["paper"])
    wc   = (ldpe * F_WC["ldpe"])   + (paper * F_WC["paper"])

    results = [
        {"name": "Global warming",                          "val": gw,   "unit": "kg CO₂ eq",    "dominant": True},
        {"name": "Fossil resource scarcity",                "val": frs,  "unit": "kg oil eq",     "dominant": False},
        {"name": "Terrestrial ecotoxicity",                 "val": te,   "unit": "kg 1,4-DCB",   "dominant": False},
        {"name": "Human non-carcinogenic toxicity",         "val": hnct, "unit": "kg 1,4-DCB",   "dominant": False},
        {"name": "Ionizing radiation",                      "val": ir,   "unit": "kBq Co-60 eq", "dominant": False},
        {"name": "Land use",                                "val": lu,   "unit": "m²a crop eq",  "dominant": False},
        {"name": "Marine ecotoxicity",                      "val": me,   "unit": "kg 1,4-DCB",   "dominant": False},
        {"name": "Human carcinogenic toxicity",             "val": hct,  "unit": "kg 1,4-DCB",   "dominant": False},
        {"name": "Freshwater ecotoxicity",                  "val": fe,   "unit": "kg 1,4-DCB",   "dominant": False},
        {"name": "Ozone formation, Terrestrial ecosystems", "val": ot,   "unit": "kg NOx eq",    "dominant": False},
        {"name": "Ozone formation, Human health",           "val": oh,   "unit": "kg NOx eq",    "dominant": False},
        {"name": "Terrestrial acidification",               "val": ta,   "unit": "kg SO₂ eq",    "dominant": False},
        {"name": "Mineral resource scarcity",               "val": mrs,  "unit": "kg Cu eq",     "dominant": False},
        {"name": "Stratospheric ozone depletion",           "val": sod,  "unit": "kg CFC11 eq",  "dominant": False},
        {"name": "Fine particulate matter formation",       "val": fpm,  "unit": "kg PM2.5 eq",  "dominant": False},
        {"name": "Freshwater eutrophication",               "val": feu,  "unit": "kg P eq",      "dominant": False},
        {"name": "Marine eutrophication",                   "val": meu,  "unit": "kg N eq",      "dominant": False},
        {"name": "Water consumption",                       "val": wc,   "unit": "m³",           "dominant": False},
    ]

    contrib = [
        {
            "label": "Listrik PLN (Indonesia)",
            "val":   co2_dari_listrik,
            "pct":   co2_dari_listrik / gw * 100 if gw else 0,
            "color": "#E24B4A",
        },
        {
            "label": "Packaging LDPE",
            "val":   ldpe * F_GW["ldpe"],
            "pct":   ldpe * F_GW["ldpe"] / gw * 100 if gw else 0,
            "color": "#1a73e8",
        },
        {
            "label": "Paper / label karton",
            "val":   paper * F_GW["paper"],
            "pct":   paper * F_GW["paper"] / gw * 100 if gw else 0,
            "color": "#137333",
        },
    ]

    return results, contrib, gw, co2_dari_listrik


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🌿 Mini openLCA")
    st.markdown("**Awesam** · Kelompok 4")
    st.divider()

    st.markdown('<p class="sidebar-header">📦 Input flows</p>', unsafe_allow_html=True)
    kain    = st.number_input("Kain Katun (kg)",              value=75.0, step=1.0,  format="%.1f")
    benang  = st.number_input("Benang Jahit (kg)",             value=1.5,  step=0.1,  format="%.1f")
    listrik = st.number_input("Listrik (kWh)",                 value=42.0, step=1.0,  format="%.1f")
    ldpe    = st.number_input("Packaging LDPE (kg)",           value=1.5,  step=0.1,  format="%.2f")
    paper   = st.number_input("Label Karton / Paper (kg)",     value=0.6,  step=0.05, format="%.2f")

    st.divider()
    st.markdown('<p class="sidebar-header">📤 Output flows</p>', unsafe_allow_html=True)
    kaos    = st.number_input("Kaos Jadi (unit)",              value=300,  step=10)
    perca   = st.number_input("Kain Perca / Waste (kg)",       value=7.5,  step=0.1,  format="%.1f")

    st.divider()
    st.markdown("""
    <div style="font-size:11px;color:#888">
    Faktor emisi listrik: <b>0.80 kg CO₂eq/kWh</b><br>
    Sumber: Faktor Emisi PLN Indonesia<br>
    Metode: ReCiPe 2016 Midpoint (H)<br>
    Batas sistem: Gate-to-gate
    </div>""", unsafe_allow_html=True)


# ─── HITUNG ──────────────────────────────────────────────────────────────────
results, contrib, gw_total, co2_listrik = hitung_lca(listrik, ldpe, paper, kain, benang, kaos, perca)


# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🌿 Proses Produksi Kaos </h1>
  <p>Awesam, Tanjungrejo, Kota Malang</p>
</div>
""", unsafe_allow_html=True)


tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Inputs / Outputs",
    "📊 Impact Analysis",
    "🌳 Contribution Tree",
    "📈 Grafik",
])


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — INPUTS / OUTPUTS
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    col_in, col_out = st.columns(2)

    with col_in:
        st.markdown('<div class="panel"><div class="panel-title">▼ Input flows</div>', unsafe_allow_html=True)
        df_in = pd.DataFrame([
            {"Flow": "Kain Katun",             "Amount": kain,    "Unit": "kg"},
            {"Flow": "Benang Jahit",            "Amount": benang,  "Unit": "kg"},
            {"Flow": "Listrik (PLN Indonesia)", "Amount": listrik, "Unit": "kWh"},
            {"Flow": "Packaging film, LDPE",   "Amount": ldpe,    "Unit": "kg"},
            {"Flow": "Paper, woodfree coated",  "Amount": paper,   "Unit": "kg"},
        ])
        st.dataframe(df_in, use_container_width=True, hide_index=True,
                     column_config={"Amount": st.column_config.NumberColumn(format="%.2f")})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_out:
        st.markdown('<div class="panel"><div class="panel-title">▼ Output flows</div>', unsafe_allow_html=True)
        df_out = pd.DataFrame([
            {"Flow": "Kaos Jadi",                        "Amount": float(kaos),   "Unit": "item(s)"},
            {"Flow": "Kain Perca",                       "Amount": perca,          "Unit": "kg"},
            {"Flow": "CO₂ dari listrik", "Amount": co2_listrik, "Unit": "kg CO₂ eq"},
        ])
        st.dataframe(df_out, use_container_width=True, hide_index=True,
                     column_config={"Amount": st.column_config.NumberColumn(format="%.4f")})
        st.markdown('</div>', unsafe_allow_html=True)


    st.divider()
    total_input_mass = kain + benang + ldpe + paper
    efisiensi        = (1 - perca / kain) * 100 if kain > 0 else 0
    co2_per_unit     = co2_listrik / kaos if kaos > 0 else 0
    gw_per_unit      = gw_total / kaos if kaos > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total mass input",    "{:.1f} kg".format(total_input_mass))
    c2.metric("Energi listrik",      "{:.1f} kWh".format(listrik))
    c3.metric("Efisiensi material",  "{:.1f}%".format(efisiensi))
    c4.metric("GW per unit kaos",    "{:.4f} kg CO₂eq".format(gw_per_unit))


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — IMPACT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    frs_val = next(r for r in results if r["name"] == "Fossil resource scarcity")["val"]
    lu_val  = next(r for r in results if r["name"] == "Land use")["val"]
    fpm_val = next(r for r in results if r["name"] == "Fine particulate matter formation")["val"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌡️ Global Warming",           "{:.5f}".format(gw_total),  "kg CO₂ eq")
    c2.metric("🛢️ Fossil Resource Scarcity",  "{:.5f}".format(frs_val),   "kg oil eq")
    c3.metric("🌱 Land Use",                 "{:.5f}".format(lu_val),    "m²a crop eq")
    c4.metric("💨 Fine Particulate Matter",   "{:.5f}".format(fpm_val),   "kg PM2.5 eq")

    st.divider()
    st.markdown("**Impact analysis — ReCiPe 2016 Midpoint (H)**")

    def fmt(v):
        if abs(v) < 1e-6:  return "{:.4e}".format(v)
        if abs(v) < 0.001: return "{:.6f}".format(v)
        return "{:.5f}".format(v)

    max_val   = max(abs(r["val"]) for r in results)
    rows_html = ""
    for r in results:
        bar_w   = int(abs(r["val"]) / max_val * 100) if max_val > 0 else 0
        dom_cls = "dominant" if r["dominant"] else ""
        rows_html += """
        <tr>
          <td class="{cls}">{name}</td>
          <td style="font-family:monospace">{val}</td>
          <td style="font-size:12px;color:#666">{unit}</td>
          <td>
            <div style="width:120px;background:#f0f0f0;border-radius:4px;height:6px;overflow:hidden">
              <div style="width:{bar}%;background:#1a73e8;height:6px;border-radius:4px"></div>
            </div>
          </td>
        </tr>""".format(cls=dom_cls, name=r["name"], val=fmt(r["val"]), unit=r["unit"], bar=bar_w)

    st.markdown("""
    <table class="lca-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Impact assessment result</th>
          <th>Unit</th>
          <th>Bar</th>
        </tr>
      </thead>
      <tbody>{}</tbody>
    </table>
    """.format(rows_html), unsafe_allow_html=True)



# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — CONTRIBUTION TREE
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("**Contribution tree — Global Warming**")
    st.selectbox("Impact category", ["Global warming"], key="ct_cat")

    bar_segs = "".join([
        '<div style="flex:{pct};background:{color};min-width:2px"></div>'.format(
            pct=c["pct"], color=c["color"]
        )
        for c in contrib
    ])
    legend_items = "".join([
        '<span><span class="legend-dot" style="background:{color}"></span>'
        '{label} <strong>{pct:.2f}%</strong> ({val:.5f} kg CO₂ eq)</span>'.format(
            color=c["color"], label=c["label"], pct=c["pct"], val=c["val"]
        )
        for c in contrib
    ])

    st.markdown("""
    <div class="panel">
      <div class="panel-title">Distribusi kontribusi · Total: {gw:.5f} kg CO₂ eq</div>
      <div class="contrib-bar-wrap">{bar}</div>
      <div class="legend-row">{legend}</div>
    </div>
    """.format(gw=gw_total, bar=bar_segs, legend=legend_items), unsafe_allow_html=True)

    rows = [{
        "Kontribusi": "100.00%",
        "Process": "▼ Proses Produksi Kaos Awesam",
        "Required amount": "{} item(s)".format(kaos),
        "Total result (kg CO₂ eq)": "{:.5f}".format(gw_total),
    }]
    for c in contrib:
        if "Listrik" in c["label"]:
            amount = "{:.1f} kWh × 0.80 kg CO₂eq/kWh".format(listrik)
        elif "LDPE" in c["label"]:
            amount = "{:.2f} kg LDPE".format(ldpe)
        else:
            amount = "{:.2f} kg paper".format(paper)
        rows.append({
            "Kontribusi": "{:.2f}%".format(c["pct"]),
            "Process": "  ↳ " + c["label"],
            "Required amount": amount,
            "Total result (kg CO₂ eq)": "{:.5f}".format(c["val"]),
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("""
    <div class="note-box">
    ℹ️ Faktor karakterisasi Global Warming:
    Listrik PLN = 0.80 kg CO₂eq/kWh ·
    LDPE = {f_ldpe:.5f} kg CO₂eq/kg ·
    Paper = {f_paper:.5f} kg CO₂eq/kg
    </div>""".format(f_ldpe=F_GW["ldpe"], f_paper=F_GW["paper"]), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — GRAFIK
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("**Semua kategori dampak**")
        names  = [r["name"] for r in results if r["name"] != "Water consumption"]
        vals   = [abs(r["val"]) for r in results if r["name"] != "Water consumption"]
        colors = ["#E24B4A" if r["dominant"] else "#1a73e8"
                  for r in results if r["name"] != "Water consumption"]

        fig1 = go.Figure(go.Bar(
            x=vals, y=names, orientation="h",
            marker_color=colors,
            text=["{:.3e}".format(v) if v < 0.01 else "{:.4f}".format(v) for v in vals],
            textposition="outside", textfont=dict(size=10),
        ))
        fig1.update_layout(
            height=520, margin=dict(l=0, r=80, t=10, b=10),
            xaxis_title="Impact assessment result",
            yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
            plot_bgcolor="white", paper_bgcolor="white",
            showlegend=False,
        )
        fig1.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
        st.plotly_chart(fig1, use_container_width=True)

    with col_g2:
        st.markdown("**Kontribusi Global Warming per sumber**")
        fig2 = go.Figure(go.Pie(
            labels=[c["label"] for c in contrib],
            values=[c["val"] for c in contrib],
            marker_colors=["#E24B4A", "#1a73e8", "#137333"],
            hole=0.45,
            textinfo="label+percent",
            textfont=dict(size=12),
        ))
        fig2.update_layout(
            height=300, margin=dict(l=0, r=0, t=10, b=10),
            paper_bgcolor="white",
            legend=dict(font=dict(size=11)),
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("**Top 5 kategori dampak terbesar**")
        top5 = sorted(results, key=lambda r: abs(r["val"]), reverse=True)[:5]
        fig3 = go.Figure(go.Bar(
            x=[r["name"] for r in top5],
            y=[r["val"] for r in top5],
            marker_color="#1a73e8",
            text=["{:.4f}".format(r["val"]) for r in top5],
            textposition="outside",
        ))
        fig3.update_layout(
            height=300, margin=dict(l=0, r=0, t=10, b=80),
            plot_bgcolor="white", paper_bgcolor="white",
            yaxis_title="Result",
            xaxis=dict(tickfont=dict(size=10), tickangle=-20),
        )
        fig3.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
        st.plotly_chart(fig3, use_container_width=True)