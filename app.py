"""
Kaizen Autopeças — Dashboard Reajuste Goiânia
Jan-Mar/2026 vs Maio/2026 — Comparativo em MÉDIA DIÁRIA (dias úteis seg-sex)
Período D atualizado automaticamente via _config.json / gerar_dados.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import html as _html
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Kaizen GO — Análise Reajuste",
    page_icon="📊",
    layout="wide",
)

DATA_DIR   = os.path.dirname(__file__)

# ── Lê configuração dinâmica (atualizada por gerar_dados.py) ──────────────────
_cfg_path = os.path.join(DATA_DIR, "_config.json")
if os.path.exists(_cfg_path):
    with open(_cfg_path, encoding="utf-8") as _f:
        _cfg = json.load(_f)
    N_DIAS_A  = int(_cfg.get("n_dias_a",  64))
    N_DIAS_D  = int(_cfg.get("n_dias_d",  20))
    PERIODO_A = _cfg.get("periodo_a", "Jan-Mar 2026")
    PERIODO_D = _cfg.get("periodo_d", "Mai 2026")
    DATA_FIM_D = _cfg.get("data_fim_d", "2026-05-31")
    ATUALIZDO  = _cfg.get("atualizado_em", "")
else:
    # Fallback: valores fixos caso o arquivo não exista
    N_DIAS_A  = 64   # jan+fev+mar 2026 — dias úteis
    N_DIAS_D  = 20   # mai 2026 — dias úteis (estimativa)
    PERIODO_A = "Jan-Mar 2026"
    PERIODO_D = "Mai 2026"
    DATA_FIM_D = "2026-05-31"
    ATUALIZDO  = ""

# ── CSS: evita truncamento dos valores nos cards ──────────────────────────────
st.markdown("""
<style>
[data-testid="stMetricValue"] {
    font-size: 1.15rem !important;
    white-space: nowrap !important;
    overflow: visible !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    white-space: nowrap !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.75rem !important;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    cli  = pd.read_csv(os.path.join(DATA_DIR, "clientes.csv"),    dtype=str)
    forn = pd.read_csv(os.path.join(DATA_DIR, "fornecedores.csv"), dtype=str)
    grp  = pd.read_csv(os.path.join(DATA_DIR, "grupos.csv"),       dtype=str)
    ft   = pd.read_csv(os.path.join(DATA_DIR, "for_tipo.csv"),     dtype=str)

    num_cli  = ["a_vl","a_cmv","a_mc","a_qtde","a_ped","d_vl","d_cmv","d_mc","d_qtde","d_ped"]
    num_forn = ["a_vl","a_cmv","a_mc","a_qtde","a_cli","d_vl","d_cmv","d_mc","d_qtde","d_cli"]
    num_ft = ["pc_acre_k","pc_acre_o","pc_acre_q","pc_acre_n","pc_acre_p","pc_acre_b","pc_acre_f","pc_acre_e","pc_acre_u"]

    for c in num_cli:  cli[c]  = pd.to_numeric(cli[c],  errors="coerce").fillna(0)
    for c in num_forn:
        forn[c] = pd.to_numeric(forn[c], errors="coerce").fillna(0)
        grp[c]  = pd.to_numeric(grp[c],  errors="coerce").fillna(0)
    for c in num_ft:   ft[c]   = pd.to_numeric(ft[c],   errors="coerce").fillna(0)
    if "fantasia" in forn.columns:
        forn["fantasia"] = forn["fantasia"].fillna(forn["fornecedor"])

    cli["a_vl_d"]  = cli["a_vl"]  / N_DIAS_A
    cli["d_vl_d"]  = cli["d_vl"]  / N_DIAS_D
    cli["a_mc_d"]  = cli["a_mc"]  / N_DIAS_A
    cli["d_mc_d"]  = cli["d_mc"]  / N_DIAS_D
    cli["a_cmv_d"] = cli["a_cmv"] / N_DIAS_A
    cli["d_cmv_d"] = cli["d_cmv"] / N_DIAS_D

    cli["delta_vl_d"]  = cli["d_vl_d"] - cli["a_vl_d"]
    cli["delta_pct"]   = (cli["delta_vl_d"] / cli["a_vl_d"].replace(0, float("nan"))) * 100
    cli["delta_mc_d"]  = cli["d_mc_d"] - cli["a_mc_d"]
    cli["delta_mc_pct"]= (cli["delta_mc_d"] / cli["a_mc_d"].replace(0, float("nan"))) * 100
    cli["a_margem_pct"] = (cli["a_mc"] / cli["a_vl"].replace(0, float("nan"))) * 100
    cli["d_margem_pct"] = (cli["d_mc"] / cli["d_vl"].replace(0, float("nan"))) * 100
    cli["a_cmv_pct"]    = (cli["a_cmv"] / cli["a_vl"].replace(0, float("nan"))) * 100
    cli["d_cmv_pct"]    = (cli["d_cmv"] / cli["d_vl"].replace(0, float("nan"))) * 100
    cli["a_qtde_d"] = cli["a_qtde"] / N_DIAS_A
    cli["d_qtde_d"] = cli["d_qtde"] / N_DIAS_D
    cli["a_ped_d"]  = cli["a_ped"]  / N_DIAS_A
    cli["d_ped_d"]  = cli["d_ped"]  / N_DIAS_D
    cli["a_ticket"] = cli["a_vl"] / cli["a_ped"].replace(0, float("nan"))
    cli["d_ticket"] = cli["d_vl"] / cli["d_ped"].replace(0, float("nan"))

    for df in [forn, grp]:
        df["a_vl_d"]    = df["a_vl"]   / N_DIAS_A
        df["d_vl_d"]    = df["d_vl"]   / N_DIAS_D
        df["a_mc_d"]    = df["a_mc"]   / N_DIAS_A
        df["d_mc_d"]    = df["d_mc"]   / N_DIAS_D
        df["a_cmv_d"]   = df["a_cmv"]  / N_DIAS_A
        df["d_cmv_d"]   = df["d_cmv"]  / N_DIAS_D
        df["a_qtde_d"]  = df["a_qtde"] / N_DIAS_A
        df["d_qtde_d"]  = df["d_qtde"] / N_DIAS_D
        df["delta_vl_d"]   = df["d_vl_d"] - df["a_vl_d"]
        df["delta_pct"]    = (df["delta_vl_d"] / df["a_vl_d"].replace(0, float("nan"))) * 100
        df["a_margem_pct"] = (df["a_mc"]  / df["a_vl"].replace(0, float("nan"))) * 100
        df["d_margem_pct"] = (df["d_mc"]  / df["d_vl"].replace(0, float("nan"))) * 100
        df["a_cmv_pct"]    = (df["a_cmv"] / df["a_vl"].replace(0, float("nan"))) * 100
        df["d_cmv_pct"]    = (df["d_cmv"] / df["d_vl"].replace(0, float("nan"))) * 100

    cf = pd.read_csv(os.path.join(DATA_DIR, "cli_forn.csv"), dtype=str, sep=',')
    cf["codfor"] = cf["codfor"].str.strip().str.zfill(5)
    num_cf = ["a_vl_d","a_cmv_d","a_mc_d","d_vl_d","d_cmv_d","d_mc_d"]
    for c in num_cf: cf[c] = pd.to_numeric(cf[c], errors="coerce").fillna(0)
    cf["a_qtde"] = pd.to_numeric(cf["a_qtde"], errors="coerce").fillna(0)
    cf["d_qtde"] = pd.to_numeric(cf["d_qtde"], errors="coerce").fillna(0)
    cf["delta_pct"] = (cf["d_vl_d"] - cf["a_vl_d"]) / cf["a_vl_d"].replace(0, float("nan")) * 100
    cf["a_mc_pct"]  = cf["a_mc_d"] / cf["a_vl_d"].replace(0, float("nan")) * 100
    cf["d_mc_pct"]  = cf["d_mc_d"] / cf["d_vl_d"].replace(0, float("nan")) * 100
    if "fantasia" in cf.columns:
        cf["fantasia"] = cf["fantasia"].fillna(cf["fornecedor"])
    else:
        cf["fantasia"] = cf["fornecedor"]

    return cli, forn, grp, ft, cf

cli_df, forn_df, grp_df, ft_df, cf_df = load_data()

# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt_brl(v):
    if pd.isna(v): return "—"
    if abs(v) >= 1_000_000: return f"R$ {v/1_000_000:.1f}M"
    if abs(v) >= 1_000:     return f"R$ {v/1_000:.0f}K"
    return f"R$ {v:.0f}"

def fmt_brl_full(v):
    if pd.isna(v): return "—"
    return f"R$ {v:,.0f}".replace(",","X").replace(".",",").replace("X",".")

def fmt_ticket(v):
    if pd.isna(v): return "—"
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def fmt_pct(v):
    if pd.isna(v): return "—"
    return f"{v:+.1f}%"

def fmt_pct_abs(v):
    if pd.isna(v): return "—"
    return f"{v:.1f}%"

def color_delta_pct(val):
    try:
        v = float(str(val).replace("%","").replace("+",""))
        if v < -30: return "background-color:#ffe0e0; color:#7b0000"
        if v < -10: return "background-color:#fff3cd; color:#5c4400"
        if v > 0:   return "background-color:#d4edda; color:#155724"
    except: pass
    return ""

def _cv(val, fmt_fn, is_delta):
    if val is None:
        return "—"
    try:
        if pd.isna(val):
            return "—"
    except (TypeError, ValueError):
        pass
    if not callable(fmt_fn):
        return _html.escape(str(val))
    s = _html.escape(str(fmt_fn(val)))
    if is_delta:
        try:
            fv = float(val)
            if fv < -30: return f'<span class="cr">{s}</span>'
            if fv < -10: return f'<span class="cy">{s}</span>'
            if fv > 0:   return f'<span class="cg">{s}</span>'
        except: pass
    return s

def _det_tbl(rows, cols, title=""):
    if not rows:
        return "<em style='color:#888;font-size:12px'>Sem dados.</em>"
    ths = "".join(f"<th>{_html.escape(lbl)}</th>" for _, lbl, _, _ in cols)
    trs = ""
    for r in rows:
        tds = "".join(f"<td>{_cv(r.get(k), f, d)}</td>" for k, _, f, d in cols)
        trs += f"<tr>{tds}</tr>"
    t = "" if not title else f"<p class='dt-title'>{_html.escape(title)}</p>"
    return f"{t}<table class='dt'><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>"

def build_total_row(df, label_col="nome", label="TOTAL"):
    r = {label_col: label}
    sum_cols = [
        "a_vl_d","d_vl_d","a_mc_d","d_mc_d","a_cmv_d","d_cmv_d",
        "a_qtde_d","d_qtde_d","a_ped_d","d_ped_d","a_qtde","d_qtde",
        "n_cli_a","n_cli_d","clientes_zerados",
    ]
    for col in sum_cols:
        if col in df.columns:
            r[col] = df[col].sum()
    av  = r.get("a_vl_d",  0) or float("nan")
    dv  = r.get("d_vl_d",  0) or float("nan")
    am  = r.get("a_mc_d",  0) or float("nan")
    dm  = r.get("d_mc_d",  0) or float("nan")
    acv = r.get("a_cmv_d", 0) or float("nan")
    dcv = r.get("d_cmv_d", 0) or float("nan")
    ap  = r.get("a_ped_d", float("nan"))
    dp  = r.get("d_ped_d", float("nan"))
    r["delta_vl_d"]    = dv - av
    r["delta_pct"]     = (dv - av) / av * 100
    r["delta_mc_d"]    = dm - am
    r["delta_mc_pct"]  = (dm - am) / am * 100
    r["a_margem_pct"]  = am  / av  * 100
    r["d_margem_pct"]  = dm  / dv  * 100
    r["a_cmv_pct"]     = acv / av  * 100
    r["d_cmv_pct"]     = dcv / dv  * 100
    r["a_ticket"]      = av  / ap  if ap  and ap  > 0 else float("nan")
    r["d_ticket"]      = dv  / dp  if dp  and dp  > 0 else float("nan")
    return r

def tree_table_html(main_rows, detail_fn, main_cols, max_height=750, total_row=None,
                    n_sticky=1, sticky_widths=None):
    W0 = 28
    if sticky_widths is None:
        sticky_widths = [160] * n_sticky
    STICKY_WIDTHS = sticky_widths[:n_sticky]
    offsets = [W0]
    for w in STICKY_WIDTHS[: n_sticky - 1]:
        offsets.append(offsets[-1] + w)

    BG_HEAD  = "#eef0f6"
    BG_ODD   = "#ffffff"
    BG_EVEN  = "#f6f7fb"
    BG_HOVER = "#e8eeff"

    sticky_head_css = f"""
    table.mt thead th.sc0{{position:sticky;left:0;z-index:9;background:{BG_HEAD};width:{W0}px;min-width:{W0}px}}
    """ + "".join(
        f"table.mt thead th.sc{i+1}{{position:sticky;left:{offsets[i]}px;z-index:9;background:{BG_HEAD};"
        f"min-width:{STICKY_WIDTHS[i]}px;"
        f"border-right:{'2px solid #9aa3c0' if i==n_sticky-1 else '1px solid #d0d5e8'};}}\n"
        for i in range(n_sticky)
    )
    sticky_body_css = f"""
    table.mt tbody td.sc0{{position:sticky;left:0;z-index:2;width:{W0}px;min-width:{W0}px}}
    """ + "".join(
        f"table.mt tbody td.sc{i+1}{{position:sticky;left:{offsets[i]}px;z-index:2;"
        f"min-width:{STICKY_WIDTHS[i]}px;"
        f"border-right:{'2px solid #9aa3c0' if i==n_sticky-1 else '1px solid #e0e4f0'};}}\n"
        for i in range(n_sticky)
    )

    CSS = f"""
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
          font-size:12.5px;color:#1a1c23;background:#fff}}
    .wrap{{overflow:auto;max-height:{max_height}px;
           border:1px solid #d8dce8;border-radius:5px}}
    table.mt{{border-collapse:separate;border-spacing:0}}
    table.mt thead th{{
        position:sticky;top:0;z-index:4;background:{BG_HEAD};
        padding:7px 9px;font-size:11.5px;font-weight:600;
        text-align:right;white-space:nowrap;
        border-bottom:2px solid #bcc2d8;border-right:1px solid #d0d5e8}}
    table.mt thead th:first-child{{text-align:center;padding:7px 4px}}
    table.mt tbody tr.mr{{cursor:pointer}}
    table.mt tbody tr.mr td{{
        padding:6px 9px;border-bottom:1px solid #e6e9f2;
        text-align:right;white-space:nowrap;vertical-align:middle;
        border-right:1px solid #eff1f8}}
    table.mt tbody tr.mr td:first-child{{text-align:center;padding:6px 4px}}
    table.mt tbody tr.mr:hover td{{background:{BG_HOVER}!important}}
    {sticky_head_css}
    {sticky_body_css}
    .odd  td{{background:{BG_ODD}}}
    .even td{{background:{BG_EVEN}}}
    .odd  td.sc0,.odd  td.sc1,.odd  td.sc2,.odd  td.sc3,.odd  td.sc4,.odd  td.sc5{{background:{BG_ODD}}}
    .even td.sc0,.even td.sc1,.even td.sc2,.even td.sc3,.even td.sc4,.even td.sc5{{background:{BG_EVEN}}}
    .tgl{{display:inline-block;font-size:9px;color:#8890aa;
          transition:transform .15s;line-height:1;user-select:none}}
    tr.dr{{display:none}}
    tr.dr>td{{background:#f0f3fa!important;padding:0;
              border-bottom:2px solid #bcc2d8}}
    .din{{padding:10px 14px 14px 52px;overflow-x:auto}}
    table.dt{{border-collapse:collapse;font-size:11.5px;margin-top:5px}}
    table.dt thead th{{background:#dde3f0;padding:5px 8px;text-align:right;
                       border-bottom:1px solid #adb5cc;white-space:nowrap;font-weight:600}}
    table.dt thead th:first-child{{text-align:left}}
    table.dt tbody tr:nth-child(even) td{{background:#e8ecf6}}
    table.dt tbody tr:nth-child(odd)  td{{background:#f3f5fb}}
    table.dt tbody td{{padding:4px 8px;border-bottom:1px solid #dde1ee;
                       text-align:right;white-space:nowrap}}
    table.dt tbody td:first-child{{text-align:left}}
    tr.tot td{{background:#d8e0f0!important;font-weight:700;
               border-top:2px solid #8892b8;position:sticky;bottom:0;z-index:3}}
    .cr{{background:#ffd6d6;color:#6b0000;border-radius:3px;padding:1px 5px;font-weight:600}}
    .cy{{background:#fff0c0;color:#4a3500;border-radius:3px;padding:1px 5px;font-weight:600}}
    .cg{{background:#c6efce;color:#0b5e1e;border-radius:3px;padding:1px 5px;font-weight:600}}
    .dt-title{{font-size:11px;font-weight:700;color:#3a4060;margin:8px 0 3px}}
    """

    JS = """
    function tog(id){
      var dr=document.getElementById('d'+id);
      var tgl=document.getElementById('tgl'+id);
      if(!dr)return;
      var open=dr.style.display==='table-row';
      dr.style.display=open?'none':'table-row';
      tgl.style.transform=open?'':'rotate(90deg)';
    }
    """

    def _th_cls(i):
        return f" class='sc{i+1}'" if i < n_sticky else ""

    th = f"<th class='sc0'></th>"
    th += "".join(
        f"<th{_th_cls(i)}>{_html.escape(lbl)}</th>"
        for i, (_, lbl, _, _) in enumerate(main_cols)
    )

    def _td_cls(i):
        return f" class='sc{i+1}'" if i < n_sticky else ""

    rows_html = ""
    parity = 0
    for i, row in enumerate(main_rows):
        det_html = detail_fn(row)
        zebra = "odd" if parity % 2 == 0 else "even"
        parity += 1
        tds = f"<td class='sc0'><span class='tgl' id='tgl{i}'>&#9654;</span></td>"
        tds += "".join(
            f"<td{_td_cls(j)}>{_cv(row.get(k), f, d)}</td>"
            for j, (k, _, f, d) in enumerate(main_cols)
        )
        rows_html += f"<tr class='mr {zebra}' onclick='tog({i})'>{tds}</tr>\n"
        ncols = len(main_cols) + 1
        rows_html += (f"<tr class='dr' id='d{i}'>"
                      f"<td colspan='{ncols}'><div class='din'>{det_html}</div></td>"
                      f"</tr>\n")

    total_html = ""
    if total_row:
        ttds = "<td style='text-align:center;color:#667'>Σ</td>"
        ttds += "".join(
            f"<td>{_cv(total_row.get(k), f, d)}</td>"
            for k, _, f, d in main_cols
        )
        total_html = f"<tr class='tot'>{ttds}</tr>"

    return (f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<style>{CSS}</style></head><body>"
            f"<div class='wrap'><table class='mt'>"
            f"<thead><tr>{th}</tr></thead>"
            f"<tbody>{rows_html}{total_html}</tbody>"
            f"</table></div>"
            f"<script>{JS}</script></body></html>")

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🔍 Filtros")
st.sidebar.caption(f"Loja 08 GO · {PERIODO_A} vs {PERIODO_D} · Dias úteis")

siglas_all  = sorted(cli_df["sigla"].dropna().unique().tolist())
siglas_sel  = st.sidebar.multiselect("Letra (sigla)", siglas_all, default=["O","Q"],
                                      help="O=Revendedores, K=Oficinas, Q=Eletropeças")
cart_all    = sorted(cli_df["carteira"].dropna().unique().tolist())
cart_sel    = st.sidebar.multiselect("Carteira", cart_all, default=[])
est_all     = sorted(cli_df["estado"].dropna().unique().tolist())
est_sel     = st.sidebar.multiselect("Estado", est_all, default=["GO"])
busca_cli   = st.sidebar.text_input("🔎 Buscar cliente", "")
st.sidebar.divider()
forn_all    = sorted(forn_df["fantasia"].dropna().unique().tolist())
forn_sel    = st.sidebar.multiselect("Fornecedor", forn_all, default=[])
grp_all     = sorted(grp_df["grupo"].dropna().unique().tolist())
grp_sel     = st.sidebar.multiselect("Grupo de produto", grp_all, default=[])

# ── Filtros ───────────────────────────────────────────────────────────────────
mask = pd.Series(True, index=cli_df.index)
if siglas_sel: mask &= cli_df["sigla"].isin(siglas_sel)
if cart_sel:   mask &= cli_df["carteira"].isin(cart_sel)
if est_sel:    mask &= cli_df["estado"].isin(est_sel)
if busca_cli:
    b = busca_cli.upper()
    mask &= (cli_df["nome"].str.upper().str.contains(b, na=False) |
             cli_df["codcli"].str.upper().str.contains(b, na=False))
cli_fil = cli_df[mask].copy()

forn_mask = pd.Series(True, index=forn_df.index)
if siglas_sel: forn_mask &= forn_df["sigla"].isin(siglas_sel)
if forn_sel:   forn_mask &= forn_df["fantasia"].isin(forn_sel)
forn_fil = forn_df[forn_mask].copy()

grp_mask = pd.Series(True, index=grp_df.index)
if siglas_sel: grp_mask &= grp_df["sigla"].isin(siglas_sel)
if grp_sel:    grp_mask &= grp_df["grupo"].isin(grp_sel)
grp_fil = grp_df[grp_mask].copy()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 Kaizen GO — Impacto do Reajuste de Preços")
_upd_str = f" · Dados até {DATA_FIM_D}" + (f" (atualizado {ATUALIZDO})" if ATUALIZDO else "")
st.caption(
    f"**Referência:** {PERIODO_A} — {N_DIAS_A} dias úteis (seg–sex) · "
    f"**Atual:** {PERIODO_D} — {N_DIAS_D} dias úteis (seg–sex) · "
    f"Loja 08 Goiânia · Comparativo {PERIODO_A} vs {PERIODO_D}{_upd_str}"
)

# ── KPIs — 3 linhas ───────────────────────────────────────────────────────────
total_a = cli_fil["a_vl"].sum()
total_d = cli_fil["d_vl"].sum()
mc_a    = cli_fil["a_mc"].sum()
mc_d    = cli_fil["d_mc"].sum()
cmv_a   = cli_fil["a_cmv"].sum()
cmv_d   = cli_fil["d_cmv"].sum()

fat_dia_a = total_a / N_DIAS_A
fat_dia_d = total_d / N_DIAS_D
mc_dia_a  = mc_a   / N_DIAS_A
mc_dia_d  = mc_d   / N_DIAS_D
cmv_dia_a = cmv_a  / N_DIAS_A
cmv_dia_d = cmv_d  / N_DIAS_D

mg_a_pct  = mc_a  / total_a * 100 if total_a else 0
mg_d_pct  = mc_d  / total_d * 100 if total_d else 0
cmv_a_pct = cmv_a / total_a * 100 if total_a else 0
cmv_d_pct = cmv_d / total_d * 100 if total_d else 0

delta_fat = (fat_dia_d - fat_dia_a) / fat_dia_a * 100 if fat_dia_a else 0
delta_mc  = (mc_dia_d  - mc_dia_a)  / mc_dia_a  * 100 if mc_dia_a  else 0
delta_cmv = (cmv_dia_d - cmv_dia_a) / cmv_dia_a * 100 if cmv_dia_a else 0

n_cli_a = (cli_fil["a_vl"] > 0).sum()
n_cli_d = (cli_fil["d_vl"] > 0).sum()
zeraram  = ((cli_fil["a_vl"] > 0) & (cli_fil["d_vl"] == 0)).sum()

st.markdown("#### 💰 Faturamento")
c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
c1.metric(f"Total {PERIODO_A}",     fmt_brl(total_a))
c2.metric(f"Total {PERIODO_D}",     fmt_brl(total_d))
c3.metric(f"Média/dia {PERIODO_A}", fmt_brl(fat_dia_a))
c4.metric(f"Média/dia {PERIODO_D}", fmt_brl(fat_dia_d), f"{delta_fat:+.1f}%")
c5.metric(f"Clientes {PERIODO_A}",  f"{n_cli_a}")
c6.metric(f"Clientes {PERIODO_D}",  f"{n_cli_d}")
c7.metric("Zeraram",                f"{zeraram}")

st.divider()

st.markdown("#### 📈 Margem de Contribuição (MC)")
m1,m2,m3,m4,m5,m6,m7 = st.columns(7)
m1.metric(f"MC Total {PERIODO_A}",  fmt_brl(mc_a))
m2.metric(f"MC Total {PERIODO_D}",  fmt_brl(mc_d))
m3.metric(f"MC/dia {PERIODO_A}",    fmt_brl(mc_dia_a))
m4.metric(f"MC/dia {PERIODO_D}",    fmt_brl(mc_dia_d), f"{delta_mc:+.1f}%")
m5.metric(f"MC% {PERIODO_A}",       f"{mg_a_pct:.1f}%")
m6.metric(f"MC% {PERIODO_D}",       f"{mg_d_pct:.1f}%", f"{mg_d_pct-mg_a_pct:+.1f}pp")
m7.metric("Dias úteis",             f"{N_DIAS_A} → {N_DIAS_D}")

st.divider()

st.markdown("#### 🏷️ Custo das Mercadorias Vendidas (CMV)")
v1,v2,v3,v4,v5,v6,_ = st.columns(7)
v1.metric(f"CMV Total {PERIODO_A}", fmt_brl(cmv_a))
v2.metric(f"CMV Total {PERIODO_D}", fmt_brl(cmv_d))
v3.metric(f"CMV/dia {PERIODO_A}",   fmt_brl(cmv_dia_a))
v4.metric(f"CMV/dia {PERIODO_D}",   fmt_brl(cmv_dia_d), f"{delta_cmv:+.1f}%")
v5.metric(f"CMV% {PERIODO_A}",      f"{cmv_a_pct:.1f}%")
v6.metric(f"CMV% {PERIODO_D}",      f"{cmv_d_pct:.1f}%", f"{cmv_d_pct-cmv_a_pct:+.1f}pp")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "👤 Por Cliente",
    "🏭 Por Fornecedor",
    "📦 Por Grupo",
    "🏷️ Descontos (for_tipo)",
    "📐 Simulador Letra O",
    "📐 Simulador Letra Q",
    "🧑‍💼 Por Vendedor",
    "📐 Simulador Letra E",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — POR CLIENTE
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    col_ord, col_dir = st.columns([3,1])
    ordem = col_ord.selectbox("Ordenar por", [
        "Fat/dia Antes ↓","Fat/dia Depois ↓","Maior Queda Fat R$ ↓","Maior Queda Fat % ↓",
        "Maior Queda MC R$ ↓","Maior Queda MC % ↓","MC% Antes ↓","CMV% Antes ↓",
    ])
    show_n = col_dir.slider("Linhas", 20, 200, 50, 10)

    sort_map = {
        "Fat/dia Antes ↓":        ("a_vl_d",       False),
        "Fat/dia Depois ↓":       ("d_vl_d",       False),
        "Maior Queda Fat R$ ↓":   ("delta_vl_d",   True ),
        "Maior Queda Fat % ↓":    ("delta_pct",    True ),
        "Maior Queda MC R$ ↓":    ("delta_mc_d",   True ),
        "Maior Queda MC % ↓":     ("delta_mc_pct", True ),
        "MC% Antes ↓":            ("a_margem_pct", False),
        "CMV% Antes ↓":           ("a_cmv_pct",   False),
    }
    sc, sa = sort_map[ordem]
    cli_show = cli_fil.sort_values(sc, ascending=sa).head(show_n)

    st.caption(
        f"Exibindo {min(show_n, len(cli_fil))} de {len(cli_fil)} clientes filtrados · "
        "Clique em ▶ para ver o detalhe por fornecedor"
    )
    csv_bytes = cli_fil.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exportar clientes filtrados (CSV)", csv_bytes,
                       "clientes_filtrados.csv", "text/csv")

    if cli_show.empty:
        st.info("Nenhum cliente nos filtros atuais.")
    else:
        _brl = fmt_brl_full
        _pct = fmt_pct
        _pa  = fmt_pct_abs
        _txt = lambda v: str(v) if v is not None else "—"
        _num = lambda v: f"{v:.2f}" if not pd.isna(v) else "—"

        main_cols_1 = [
            ("codcli",       "Cód",            _txt, False),
            ("nome",         "Cliente",        _txt, False),
            ("sigla",        "Sig",            _txt, False),
            ("carteira",     "Carteira",       _txt, False),
            ("estado",       "UF",             _txt, False),
            ("a_vl_d",       "Fat/dia Antes",  _brl, False),
            ("d_vl_d",       "Fat/dia Depois", _brl, False),
            ("delta_vl_d",   "Δ Fat/dia R$",   _brl, False),
            ("delta_pct",    "Δ Fat %",        _pct, True ),
            ("a_mc_d",       "MC/dia Antes",   _brl, False),
            ("d_mc_d",       "MC/dia Depois",  _brl, False),
            ("delta_mc_d",   "Δ MC/dia R$",    _brl, False),
            ("delta_mc_pct", "Δ MC %",         _pct, True ),
            ("a_margem_pct", "MC% Antes",      _pa,  False),
            ("d_margem_pct", "MC% Depois",     _pa,  False),
            ("a_cmv_d",      "CMV/dia Antes",  _brl, False),
            ("a_cmv_pct",    "CMV% Antes",     _pa,  False),
            ("d_cmv_d",      "CMV/dia Depois", _brl, False),
            ("d_cmv_pct",    "CMV% Depois",    _pa,  False),
            ("a_qtde_d",     "Qtde/dia Antes",  _num, False),
            ("d_qtde_d",     "Qtde/dia Depois", _num, False),
            ("a_ped_d",      "Ped/dia Antes",   _num, False),
            ("d_ped_d",      "Ped/dia Depois",  _num, False),
            ("a_ticket",     "Ticket Antes",    fmt_ticket, False),
            ("d_ticket",     "Ticket Depois",   fmt_ticket, False),
        ]
        detail_cols_1 = [
            ("fantasia",   "Fornecedor",       _txt, False),
            ("a_vl_d",     "Fat/dia Antes",    _brl, False),
            ("d_vl_d",     "Fat/dia Depois",   _brl, False),
            ("delta_pct",  "Δ %",              _pct, True ),
            ("a_mc_d",     "MC/dia Antes",     _brl, False),
            ("a_mc_pct",   "MC% Antes",        _pa,  False),
            ("d_mc_d",     "MC/dia Depois",    _brl, False),
            ("d_mc_pct",   "MC% Depois",       _pa,  False),
            ("a_cmv_d",    "CMV/dia Antes",    _brl, False),
            ("d_cmv_d",    "CMV/dia Depois",   _brl, False),
            ("a_qtde",     "Qtde Antes",       _num, False),
            ("d_qtde",     "Qtde Depois",      _num, False),
        ]
        main_rows_1 = cli_show[[
            "codcli","nome","sigla","carteira","estado",
            "a_vl_d","d_vl_d","delta_vl_d","delta_pct",
            "a_mc_d","d_mc_d","delta_mc_d","delta_mc_pct",
            "a_margem_pct","d_margem_pct",
            "a_cmv_d","a_cmv_pct","d_cmv_d","d_cmv_pct",
            "a_qtde_d","d_qtde_d","a_ped_d","d_ped_d","a_ticket","d_ticket",
        ]].to_dict("records")

        _cf_codcli = cf_df["codcli"].str.strip()
        def detail_fn_1(row):
            cid = str(row.get("codcli", "")).strip()
            sub = cf_df[_cf_codcli == cid].sort_values("a_vl_d", ascending=False)
            return _det_tbl(sub.to_dict("records"), detail_cols_1)

        tot1 = build_total_row(cli_show, label_col="nome", label="TOTAL")
        components.html(
            tree_table_html(main_rows_1, detail_fn_1, main_cols_1, total_row=tot1,
                            max_height=980, n_sticky=5),
            height=1010, scrolling=False
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — POR FORNECEDOR
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Média Diária por Fornecedor")
    st.caption("Filtrado pelas siglas selecionadas na barra lateral")

    forn_agg = (
        forn_fil.groupby(["codfor","fornecedor","fantasia"], as_index=False)
        .agg(a_vl=("a_vl","sum"), a_cmv=("a_cmv","sum"), a_mc=("a_mc","sum"), a_qtde=("a_qtde","sum"), a_cli=("a_cli","max"),
             d_vl=("d_vl","sum"), d_cmv=("d_cmv","sum"), d_mc=("d_mc","sum"), d_qtde=("d_qtde","sum"), d_cli=("d_cli","max"))
    )
    forn_agg["a_vl_d"]      = forn_agg["a_vl"]  / N_DIAS_A
    forn_agg["d_vl_d"]      = forn_agg["d_vl"]  / N_DIAS_D
    forn_agg["a_mc_d"]      = forn_agg["a_mc"]  / N_DIAS_A
    forn_agg["d_mc_d"]      = forn_agg["d_mc"]  / N_DIAS_D
    forn_agg["delta_vl_d"]  = forn_agg["d_vl_d"] - forn_agg["a_vl_d"]
    forn_agg["delta_pct"]   = (forn_agg["delta_vl_d"] / forn_agg["a_vl_d"].replace(0, float("nan"))) * 100
    forn_agg["a_margem_pct"]= (forn_agg["a_mc"] / forn_agg["a_vl"].replace(0, float("nan"))) * 100
    forn_agg["d_margem_pct"]= (forn_agg["d_mc"] / forn_agg["d_vl"].replace(0, float("nan"))) * 100
    forn_agg["a_cmv_pct"]   = (forn_agg["a_cmv"] / forn_agg["a_vl"].replace(0, float("nan"))) * 100
    forn_agg["d_cmv_pct"]   = (forn_agg["d_cmv"] / forn_agg["d_vl"].replace(0, float("nan"))) * 100
    forn_agg["delta_mc_d"]  = forn_agg["d_mc_d"] - forn_agg["a_mc_d"]
    forn_agg["delta_mc_pct"]= (forn_agg["delta_mc_d"] / forn_agg["a_mc_d"].replace(0, float("nan"))) * 100
    forn_agg["a_qtde_d"]    = forn_agg["a_qtde"] / N_DIAS_A
    forn_agg["d_qtde_d"]    = forn_agg["d_qtde"] / N_DIAS_D

    ft_cross = ft_df[["codfor","pc_acre_o","pc_acre_q","pc_acre_k"]].copy()
    forn_agg = forn_agg.merge(ft_cross, on="codfor", how="left")
    forn_agg = forn_agg.sort_values("delta_vl_d", ascending=True)

    forn_csv = forn_agg.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exportar fornecedores (CSV)", forn_csv, "fornecedores_filtrados.csv", "text/csv")
    st.caption("Clique em ▶ para ver os clientes O/Q afetados dentro de cada fornecedor")

    if forn_agg.empty:
        st.info("Nenhum fornecedor nos filtros atuais.")
    else:
        _brl  = fmt_brl_full
        _pct  = fmt_pct
        _pa   = fmt_pct_abs
        _txt  = lambda v: str(v) if v is not None else "—"
        _num  = lambda v: f"{v:.0f}" if not pd.isna(v) else "—"
        _desc = lambda v: f"{v:.1f}%" if not pd.isna(v) else "—"

        main_cols_2 = [
            ("fantasia",     "Fornecedor",       _txt,  False),
            ("a_vl_d",       "Fat/dia Antes",    _brl,  False),
            ("d_vl_d",       "Fat/dia Depois",   _brl,  False),
            ("delta_vl_d",   "Δ Fat/dia R$",     _brl,  False),
            ("delta_pct",    "Δ Fat %",          _pct,  True ),
            ("a_mc_d",       "MC/dia Antes",     _brl,  False),
            ("d_mc_d",       "MC/dia Depois",    _brl,  False),
            ("delta_mc_d",   "Δ MC/dia R$",      _brl,  False),
            ("delta_mc_pct", "Δ MC %",           _pct,  True ),
            ("a_margem_pct", "MC% Antes",        _pa,   False),
            ("d_margem_pct", "MC% Depois",       _pa,   False),
            ("a_cmv_pct",    "CMV% Antes",       _pa,   False),
            ("d_cmv_pct",    "CMV% Depois",      _pa,   False),
            ("a_qtde_d",     "Qtde/dia Antes",   _num,  False),
            ("d_qtde_d",     "Qtde/dia Depois",  _num,  False),
            ("pc_acre_o",    "Desc O",           _desc, False),
            ("pc_acre_q",    "Desc Q",           _desc, False),
            ("pc_acre_k",    "Desc K",           _desc, False),
        ]
        detail_cols_2 = [
            ("nome",      "Cliente",         _txt, False),
            ("sigla",     "Sig",             _txt, False),
            ("a_vl_d",    "Fat/dia Antes",   _brl, False),
            ("d_vl_d",    "Fat/dia Depois",  _brl, False),
            ("delta_pct", "Δ %",             _pct, True ),
            ("a_mc_d",    "MC/dia Antes",    _brl, False),
            ("a_mc_pct",  "MC% Antes",       _pa,  False),
            ("d_mc_d",    "MC/dia Depois",   _brl, False),
            ("d_mc_pct",  "MC% Depois",      _pa,  False),
            ("a_qtde",    "Qtde Antes",      _num, False),
            ("d_qtde",    "Qtde Depois",     _num, False),
        ]
        main_rows_2 = forn_agg[[
            "codfor","fantasia","a_vl_d","d_vl_d","delta_vl_d","delta_pct",
            "a_mc_d","d_mc_d","delta_mc_d","delta_mc_pct",
            "a_margem_pct","d_margem_pct","a_cmv_pct","d_cmv_pct",
            "a_qtde_d","d_qtde_d",
            "pc_acre_o","pc_acre_q","pc_acre_k",
        ]].to_dict("records")

        _cf_codfor = cf_df["codfor"].str.strip()
        def detail_fn_2(row):
            fid = str(row.get("codfor", "")).strip()
            sub = cf_df[_cf_codfor == fid].sort_values("delta_pct", ascending=True)
            return _det_tbl(sub.to_dict("records"), detail_cols_2)

        tot2 = build_total_row(forn_agg, label_col="fantasia", label="TOTAL")
        components.html(
            tree_table_html(main_rows_2, detail_fn_2, main_cols_2, total_row=tot2,
                            max_height=980, n_sticky=1, sticky_widths=[175]),
            height=1010, scrolling=False
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — POR GRUPO
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Média Diária por Grupo de Produto")

    grp_agg = (
        grp_fil.groupby(["codgru","grupo"], as_index=False)
        .agg(a_vl=("a_vl","sum"), a_cmv=("a_cmv","sum"), a_mc=("a_mc","sum"), a_qtde=("a_qtde","sum"),
             d_vl=("d_vl","sum"), d_cmv=("d_cmv","sum"), d_mc=("d_mc","sum"), d_qtde=("d_qtde","sum"))
    )
    grp_agg["a_vl_d"]      = grp_agg["a_vl"]  / N_DIAS_A
    grp_agg["d_vl_d"]      = grp_agg["d_vl"]  / N_DIAS_D
    grp_agg["a_mc_d"]      = grp_agg["a_mc"]  / N_DIAS_A
    grp_agg["d_mc_d"]      = grp_agg["d_mc"]  / N_DIAS_D
    grp_agg["delta_vl_d"]  = grp_agg["d_vl_d"] - grp_agg["a_vl_d"]
    grp_agg["delta_pct"]   = (grp_agg["delta_vl_d"] / grp_agg["a_vl_d"].replace(0, float("nan"))) * 100
    grp_agg["a_margem_pct"]= (grp_agg["a_mc"] / grp_agg["a_vl"].replace(0, float("nan"))) * 100
    grp_agg["d_margem_pct"]= (grp_agg["d_mc"] / grp_agg["d_vl"].replace(0, float("nan"))) * 100
    grp_agg["a_cmv_pct"]   = (grp_agg["a_cmv"] / grp_agg["a_vl"].replace(0, float("nan"))) * 100
    grp_agg["d_cmv_pct"]   = (grp_agg["d_cmv"] / grp_agg["d_vl"].replace(0, float("nan"))) * 100
    grp_agg["delta_mc_d"]  = grp_agg["d_mc_d"] - grp_agg["a_mc_d"]
    grp_agg["delta_mc_pct"]= (grp_agg["delta_mc_d"] / grp_agg["a_mc_d"].replace(0, float("nan"))) * 100
    grp_agg["a_qtde_d"]    = grp_agg["a_qtde"] / N_DIAS_A
    grp_agg["d_qtde_d"]    = grp_agg["d_qtde"] / N_DIAS_D
    grp_agg = grp_agg.sort_values("delta_vl_d", ascending=True)

    t3 = build_total_row(grp_agg, label_col="grupo", label="TOTAL")
    tot_g = pd.DataFrame([t3])

    disp_g = pd.concat([
        grp_agg[["grupo","a_vl_d","d_vl_d","delta_vl_d","delta_pct",
                 "a_mc_d","d_mc_d","delta_mc_d","delta_mc_pct",
                 "a_margem_pct","d_margem_pct",
                 "a_cmv_pct","d_cmv_pct","a_qtde_d","d_qtde_d"]],
        tot_g[ ["grupo","a_vl_d","d_vl_d","delta_vl_d","delta_pct",
                "a_mc_d","d_mc_d","delta_mc_d","delta_mc_pct",
                "a_margem_pct","d_margem_pct",
                "a_cmv_pct","d_cmv_pct","a_qtde_d","d_qtde_d"]],
    ], ignore_index=True).copy()

    disp_g.columns = [
        "Grupo","Fat/dia Antes","Fat/dia Depois","Δ Fat/dia R$","Δ Fat %",
        "MC/dia Antes","MC/dia Depois","Δ MC/dia R$","Δ MC %",
        "MC% Antes","MC% Depois",
        "CMV% Antes","CMV% Depois","Qtde/dia Antes","Qtde/dia Depois",
    ]

    fmt_g = {
        "Fat/dia Antes":  fmt_brl_full, "Fat/dia Depois": fmt_brl_full, "Δ Fat/dia R$": fmt_brl_full,
        "MC/dia Antes":   fmt_brl_full, "MC/dia Depois":  fmt_brl_full, "Δ MC/dia R$":  fmt_brl_full,
        "Δ Fat %":  fmt_pct, "Δ MC %":   fmt_pct,
        "MC% Antes":       fmt_pct_abs, "MC% Depois":  fmt_pct_abs,
        "CMV% Antes":      fmt_pct_abs, "CMV% Depois": fmt_pct_abs,
        "Qtde/dia Antes":  lambda v: f"{v:.2f}" if not pd.isna(v) else "—",
        "Qtde/dia Depois": lambda v: f"{v:.2f}" if not pd.isna(v) else "—",
    }

    def highlight_total(row):
        if row["Grupo"] == "TOTAL":
            return ["font-weight:bold; background-color:#e8ecf0"] * len(row)
        return [""] * len(row)

    st.dataframe(
        disp_g.style.format(fmt_g, na_rep="—")
            .map(color_delta_pct, subset=["Δ Fat %", "Δ MC %"])
            .apply(highlight_total, axis=1),
        use_container_width=True, height=570,
    )
    grp_csv = grp_agg.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exportar grupos (CSV)", grp_csv, "grupos_filtrados.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — DESCONTOS FOR_TIPO
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Tabela de Descontos por Fornecedor (for_tipo · cd_tploja=02)")
    st.caption("Apenas fornecedores com vendas no período analisado · "
               "pc_acre_X = percentual de acréscimo (negativo = desconto) para cada sigla de cliente")

    codfor_com_vendas = forn_df[forn_df["a_vl"] > 0]["codfor"].str.strip().str.zfill(5).unique()
    ft_show = ft_df[ft_df["codfor"].str.strip().str.zfill(5).isin(codfor_com_vendas)].copy()

    fantasia_map_ft = forn_df.drop_duplicates("codfor").set_index("codfor")["fantasia"].to_dict()
    ft_show["fantasia"] = ft_show["codfor"].str.strip().str.zfill(5).map(fantasia_map_ft).fillna(ft_show["fornecedor"])

    busca_ft = st.text_input("🔎 Buscar fornecedor", "", key="ft_busca")
    if busca_ft:
        b = busca_ft.upper()
        ft_show = ft_show[
            ft_show["fantasia"].str.upper().str.contains(b, na=False) |
            ft_show["fornecedor"].str.upper().str.contains(b, na=False)
        ]

    col_ft = ["codfor","fantasia","pc_acre_k","pc_acre_o","pc_acre_q","pc_acre_n","pc_acre_p","pc_acre_b","pc_acre_f","pc_acre_e","pc_acre_u"]
    ft_disp = ft_show[col_ft].copy()
    ft_disp.columns = ["Cód","Fornecedor","Desc K","Desc O","Desc Q","Desc N","Desc P","Desc B","Desc F","Desc E","Desc U"]

    def fmt_desc(v):
        if pd.isna(v): return "—"
        return f"{v:.1f}%"

    def color_desc(v):
        try:
            fv = float(str(v).replace("%","").replace("+",""))
            if fv < -20: return "background-color:#1a6db5; color:#ffffff; font-weight:bold"
            if fv < -10: return "background-color:#4a9ede; color:#ffffff"
            if fv < 0:   return "background-color:#a8d4f5; color:#0a2a4a"
        except: pass
        return ""

    desc_cols = ["Desc K","Desc O","Desc Q","Desc N","Desc P","Desc B","Desc F","Desc E"]
    st.dataframe(
        ft_disp.style.format({c: fmt_desc for c in desc_cols}, na_rep="—").map(color_desc, subset=desc_cols),
        use_container_width=True, height=550,
    )
    ft_csv = ft_show.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exportar for_tipo (CSV)", ft_csv, "for_tipo.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# ── Helpers dos simuladores ───────────────────────────────────────────────────
def _opt_delta(desc_atual, d_vl_d, d_cost_d, eps, max_pp=15.0, n=301):
    if d_vl_d <= 0 or d_cost_d < 0 or eps >= 0:
        return 0.0
    try:
        deltas = np.linspace(0.0, max_pp, n)
        denom  = max(1.0 + desc_atual / 100.0, 0.001)
        r_arr  = np.clip((1.0 + (desc_atual - deltas) / 100.0) / denom, 0.001, None)
        mc_arr = d_vl_d * r_arr ** (1.0 + eps) - d_cost_d * r_arr ** eps
        best_i = int(np.argmax(mc_arr))
        return float(deltas[best_i]) if best_i > 0 else 0.0
    except Exception:
        return 0.0


def _calc_eps_obs(row, n_dias_a=N_DIAS_A, n_dias_d=N_DIAS_D):
    q_a = row.get("a_qtde", 0)
    q_d = row.get("d_qtde", 0)
    if q_a <= 0 or q_d <= 0:
        return float("nan")
    q_a_d = q_a / n_dias_a
    q_d_d = q_d / n_dias_d
    P_a = (row["a_vl_d"] * n_dias_a) / q_a
    P_d = (row["d_vl_d"] * n_dias_d) / q_d
    if P_a <= 0 or P_d <= 0:
        return float("nan")
    ratio = P_d / P_a
    if ratio <= 1.005:
        return float("nan")
    try:
        eps = np.log(q_d_d / q_a_d) / np.log(ratio)
    except Exception:
        return float("nan")
    return eps if eps < 0 else float("nan")


def _eps_conf_label(q_a_dia, q_d_dia, has_eps):
    if not has_eps:
        return "—"
    vol = min(q_a_dia, q_d_dia)
    if vol >= 20: return "🟢 Alta"
    if vol >= 3:  return "🟡 Média"
    return "🔴 Baixa"


# ══════════════════════════════════════════════════════════════════════════════
# SIMULADOR HEURÍSTICO — LETRA O
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("📐 Simulador Heurístico — Letra O")
    st.caption(
        "Elasticidade de mercado **assumida** (ajustável) · "
        "Clientes **Letra O** com queda de faturamento · "
        "Desconto configurado **por fornecedor**, aplicado igualmente a todos do grupo"
    )

    st.markdown("### 🔍 Definir o Grupo")
    queda_thr_o = st.slider(
        "Queda mínima de Fat/dia (%)", min_value=-50, max_value=-5,
        value=-10, step=5, key="qthr_o"
    )

    sigla_sim_o = ["O"]
    fallen_o = cli_df[
        cli_df["sigla"].isin(sigla_sim_o) &
        (cli_df["delta_pct"] < queda_thr_o)
    ].copy()
    fallen_o      = fallen_o.drop_duplicates("codcli")
    fallen_cods_o = set(fallen_o["codcli"].str.strip())
    n_fallen_o    = len(fallen_o)

    gh1, gh2, gh3 = st.columns(3)
    gh1.metric("Clientes no grupo",       f"{n_fallen_o}")
    gh2.metric("Fat/dia perdida (grupo)", fmt_brl_full(fallen_o["delta_vl_d"].sum() if not fallen_o.empty else 0))
    gh3.metric("MC/dia perdida (grupo)",  fmt_brl_full(fallen_o["delta_mc_d"].sum() if not fallen_o.empty else 0))

    if fallen_o.empty:
        st.info("Nenhum cliente encontrado. Reduza o threshold de queda.")
    else:
        cf_grp_o = cf_df[
            cf_df["codcli"].str.strip().isin(fallen_cods_o) &
            cf_df["sigla"].isin(sigla_sim_o)
        ].copy()

        rev_ant_o = fallen_o["a_vl_d"].sum()
        mc_ant_o  = fallen_o["a_mc_d"].sum()
        rev_cur_o = cf_grp_o["d_vl_d"].sum()  if not cf_grp_o.empty else fallen_o["d_vl_d"].sum()
        mc_cur_o  = cf_grp_o["d_mc_d"].sum()  if not cf_grp_o.empty else fallen_o["d_mc_d"].sum()

        ka1, ka2, ka3, ka4 = st.columns(4)
        ka1.metric(f"Fat/dia {PERIODO_A}", fmt_brl_full(rev_ant_o))
        ka2.metric(f"Fat/dia {PERIODO_D}", fmt_brl_full(rev_cur_o),
                   f"{(rev_cur_o/rev_ant_o-1)*100:+.1f}%" if rev_ant_o > 0 else "—")
        ka3.metric(f"MC/dia {PERIODO_A}",  fmt_brl_full(mc_ant_o))
        ka4.metric(f"MC/dia {PERIODO_D}",  fmt_brl_full(mc_cur_o),
                   f"{(mc_cur_o/mc_ant_o-1)*100:+.1f}%" if mc_ant_o > 0 else "—")

        if cf_grp_o.empty:
            st.warning("Sem dados de cf_df para o grupo. Verifique o arquivo cli_forn.csv.")
        else:
            forn_agg_o = cf_grp_o.groupby(["codfor","fantasia"], as_index=False).agg(
                a_vl_d  =("a_vl_d",  "sum"),
                d_vl_d  =("d_vl_d",  "sum"),
                d_cmv_d =("d_cmv_d", "sum"),
                a_mc_d  =("a_mc_d",  "sum"),
                d_mc_d  =("d_mc_d",  "sum"),
                a_qtde  =("a_qtde",  "sum"),
                d_qtde  =("d_qtde",  "sum"),
                n_cli   =("codcli",  "nunique"),
            )
            forn_agg_o["codfor"] = forn_agg_o["codfor"].astype(str).str.strip().str.zfill(5)
            forn_agg_o["delta_pct_f"]  = (
                (forn_agg_o["d_vl_d"] - forn_agg_o["a_vl_d"])
                / forn_agg_o["a_vl_d"].replace(0, float("nan")) * 100
            )
            forn_agg_o["delta_vl_d_r"] = forn_agg_o["d_vl_d"] - forn_agg_o["a_vl_d"]
            forn_agg_o["delta_mc_d_r"] = forn_agg_o["d_mc_d"] - forn_agg_o["a_mc_d"]
            forn_agg_o["delta_mc_pct"] = (
                forn_agg_o["delta_mc_d_r"]
                / forn_agg_o["a_mc_d"].replace(0, float("nan")) * 100
            )

            ft_o = ft_df.copy()
            ft_o["codfor"] = ft_o["codfor"].astype(str).str.strip().str.zfill(5)
            forn_agg_o = forn_agg_o.merge(
                ft_o[["codfor", "pc_acre_o"]].rename(columns={"pc_acre_o": "desc_atual"}),
                on="codfor", how="left"
            )
            forn_agg_o["desc_atual"] = forn_agg_o["desc_atual"].fillna(0.0)

            forn_agg_o["eps_obs"]  = forn_agg_o.apply(_calc_eps_obs, axis=1)
            forn_agg_o["conf_eps"] = forn_agg_o.apply(
                lambda r: _eps_conf_label(
                    r["a_qtde"] / N_DIAS_A,
                    r["d_qtde"] / N_DIAS_D,
                    not pd.isna(r["eps_obs"])
                ), axis=1
            )

            st.divider()
            st.markdown("### 🎛️ Elasticidade Assumida")

            _eps_val_o = forn_agg_o.dropna(subset=["eps_obs"])
            if not _eps_val_o.empty:
                _w_o  = _eps_val_o["a_vl_d"].values
                _v_o  = _eps_val_o["eps_obs"].values
                _si_o = np.argsort(_v_o)
                _sv_o = _v_o[_si_o]; _sw_o = _w_o[_si_o]
                _cw_o = np.cumsum(_sw_o)
                _med_o = float(_sv_o[np.searchsorted(_cw_o, _cw_o[-1] / 2)])
                st.info(
                    f"📊 **ε observado calculado para {len(_eps_val_o)} de "
                    f"{len(forn_agg_o)} fornecedores** "
                    f"(filtros: ΔP > 0,5% · volume ≥ 5 un/dia · ε < 0).  \n"
                    f"**Mediana ponderada pelo faturamento: ε = {_med_o:.1f}** "
                    f"— use como referência para o slider abaixo."
                )
            else:
                st.warning("Nenhum fornecedor com dados suficientes para calcular ε observado.")

            eps_o = st.slider(
                "Elasticidade (ε) assumida — Letra O",
                min_value=-15.0, max_value=-0.1, value=-2.0, step=0.1, key="eps_o",
            )

            forn_agg_o["sug_delta"] = forn_agg_o.apply(
                lambda row: _opt_delta(row["desc_atual"], row["d_vl_d"], row["d_vl_d"] - row["d_mc_d"], eps_o), axis=1
            )
            forn_agg_o["desc_final_sug"] = forn_agg_o["desc_atual"] - forn_agg_o["sug_delta"]
            forn_agg_o["sug_delta_obs"] = forn_agg_o.apply(
                lambda row: (
                    _opt_delta(row["desc_atual"], row["d_vl_d"], row["d_vl_d"] - row["d_mc_d"], row["eps_obs"])
                    if not pd.isna(row["eps_obs"]) else float("nan")
                ), axis=1
            )

            st.divider()
            st.markdown("### 📋 Descontos por Fornecedor → Nova Letra O")

            disc_o = forn_agg_o[[
                "codfor","fantasia",
                "a_vl_d","d_vl_d","delta_vl_d_r","delta_pct_f",
                "a_mc_d","d_mc_d","delta_mc_d_r","delta_mc_pct",
                "n_cli","eps_obs","conf_eps","desc_atual",
                "sug_delta","sug_delta_obs","desc_final_sug",
            ]].copy()
            disc_o.columns = [
                "Cód","Fornecedor",
                "Fat/dia Antes","Fat/dia Atual","Δ Fat/dia R$","Δ Fat %",
                "MC/dia Antes","MC/dia Atual","Δ MC/dia R$","Δ MC %",
                "Clientes","ε Obs","Confiança ε","Desc Atual %",
                "Δ Sug slider (pp)","Δ Sug ε Obs (pp)","Desc Final Sug %",
            ]
            disc_o["Δ Desc (pp)"] = 0.0
            disc_o = disc_o.sort_values("Fat/dia Atual", ascending=False).reset_index(drop=True)

            if "my_deltas_o" not in st.session_state:
                st.session_state["my_deltas_o"] = {}
            for _ri, _rc in st.session_state.get("disc_edit_o", {}).get("edited_rows", {}).items():
                if "Δ Desc (pp)" in _rc and int(_ri) < len(disc_o):
                    _cf = str(disc_o["Cód"].iat[int(_ri)]).strip()
                    try:
                        _dv = float(_rc["Δ Desc (pp)"])
                    except (TypeError, ValueError):
                        continue
                    if _dv > 0:
                        st.session_state["my_deltas_o"][_cf] = _dv
                    else:
                        st.session_state["my_deltas_o"].pop(_cf, None)
            disc_o["Δ Desc (pp)"] = disc_o["Cód"].map(
                lambda c: st.session_state["my_deltas_o"].get(str(c).strip(), 0.0)
            )
            disc_o["Desc Final %"] = disc_o["Desc Atual %"] - disc_o["Δ Desc (pp)"]

            edited_o = st.data_editor(
                disc_o,
                column_config={
                    "Cód":              st.column_config.TextColumn("Cód", disabled=True, width="small"),
                    "Fornecedor":       st.column_config.TextColumn("Fornecedor", disabled=True),
                    "Fat/dia Antes":    st.column_config.NumberColumn("Fat/dia Antes",    disabled=True, format="R$ %.0f"),
                    "Fat/dia Atual":    st.column_config.NumberColumn("Fat/dia Atual",    disabled=True, format="R$ %.0f"),
                    "Δ Fat/dia R$":     st.column_config.NumberColumn("Δ Fat/dia R$",     disabled=True, format="R$ %.0f"),
                    "Δ Fat %":          st.column_config.NumberColumn("Δ Fat %",          disabled=True, format="%.1f%%"),
                    "MC/dia Antes":     st.column_config.NumberColumn("MC/dia Antes",     disabled=True, format="R$ %.0f"),
                    "MC/dia Atual":     st.column_config.NumberColumn("MC/dia Atual",     disabled=True, format="R$ %.0f"),
                    "Δ MC/dia R$":      st.column_config.NumberColumn("Δ MC/dia R$",      disabled=True, format="R$ %.0f"),
                    "Δ MC %":           st.column_config.NumberColumn("Δ MC %",           disabled=True, format="%.1f%%"),
                    "Clientes":         st.column_config.NumberColumn("Clientes",         disabled=True, width="small"),
                    "ε Obs":            st.column_config.NumberColumn("ε Obs 📊",         disabled=True, format="%.2f"),
                    "Confiança ε":      st.column_config.TextColumn("Confiança",          disabled=True, width="small"),
                    "Desc Atual %":     st.column_config.NumberColumn("Desc Atual %",     disabled=True, format="%.1f%%"),
                    "Δ Sug slider (pp)": st.column_config.NumberColumn("Δ Sug slider 💡", disabled=True, format="+%.1f pp"),
                    "Δ Sug ε Obs (pp)": st.column_config.NumberColumn("Δ Sug ε Obs 📊",  disabled=True, format="+%.1f pp"),
                    "Desc Final Sug %": st.column_config.NumberColumn("Desc Final Sug %", disabled=True, format="%.1f%%"),
                    "Δ Desc (pp)":      st.column_config.NumberColumn("Δ Desc (pp) ✏️", min_value=0.0, max_value=20.0, step=0.5, format="+%.1f pp"),
                    "Desc Final %":     st.column_config.NumberColumn("Desc Final % ✅",  disabled=True, format="%.1f%%"),
                },
                hide_index=True, key="disc_edit_o",
                height=min(500, 60 + len(disc_o) * 35),
            )

            curr_desc_map_o = dict(zip(forn_agg_o["codfor"].astype(str).str.zfill(5), forn_agg_o["desc_atual"]))
            delta_map_o = {
                str(k).strip(): float(v)
                for k, v in st.session_state.get("my_deltas_o", {}).items()
            }

            proj_o = cf_grp_o.copy()
            proj_o["codfor_k"]  = proj_o["codfor"].astype(str).str.strip().str.zfill(5)
            proj_o["curr_desc"] = proj_o["codfor_k"].map(curr_desc_map_o).fillna(0.0)
            proj_o["delta_pp"]  = proj_o["codfor_k"].map(delta_map_o).fillna(0.0)
            proj_o["new_desc"]  = proj_o["curr_desc"] - proj_o["delta_pp"]
            _denom_o            = (1 + proj_o["curr_desc"] / 100).clip(lower=0.001)
            proj_o["r"]         = ((1 + proj_o["new_desc"] / 100) / _denom_o).clip(lower=0.001)
            proj_o["cost_d"]    = proj_o["d_vl_d"] - proj_o["d_mc_d"]
            proj_o["Rev_new"]   = proj_o["d_vl_d"]  * (proj_o["r"] ** (1 + eps_o))
            proj_o["CMV_new"]   = proj_o["cost_d"]  * (proj_o["r"] ** eps_o)
            proj_o["MC_new"]    = proj_o["Rev_new"] - proj_o["CMV_new"]

            mc_new_o  = proj_o["MC_new"].sum()
            rev_new_o = proj_o["Rev_new"].sum()

            st.divider()
            st.markdown("### 📊 Resultado do Grupo com os Novos Descontos")
            pr1, pr2, pr3, pr4 = st.columns(4)
            pr1.metric("Fat/dia projetado", fmt_brl_full(rev_new_o),
                       f"{(rev_new_o/rev_cur_o-1)*100:+.1f}% vs atual" if rev_cur_o > 0 else "—")
            pr2.metric("MC/dia projetada",  fmt_brl_full(mc_new_o),
                       f"{mc_new_o-mc_cur_o:+.2f} R$/dia vs atual")
            pr3.metric(f"Fat/dia vs {PERIODO_A}",  fmt_brl_full(rev_new_o - rev_ant_o),
                       f"{(rev_new_o/rev_ant_o-1)*100:+.1f}%" if rev_ant_o > 0 else "—")
            pr4.metric(f"MC/dia vs {PERIODO_A}",   fmt_brl_full(mc_new_o - mc_ant_o),
                       f"{(mc_new_o/mc_ant_o-1)*100:+.1f}%" if mc_ant_o > 0 else "—")

            st.divider()
            st.markdown("### 📈 Sensibilidade — pp Adicionais sobre os Δ Configurados")
            delta_range_o = np.linspace(0, 15, 201)
            mc_sens_o, rev_sens_o = [], []
            for _dd in delta_range_o:
                _mc = 0.0; _rev = 0.0
                for _, row in proj_o.iterrows():
                    _new_d  = row["curr_desc"] - row["delta_pp"] - _dd
                    _den    = max(1 + row["curr_desc"] / 100, 0.001)
                    _r      = max((1 + _new_d / 100) / _den, 0.001)
                    _rv       = row["d_vl_d"]  * (_r ** (1 + eps_o))
                    _cost_row = row["cost_d"]  * (_r ** eps_o)
                    _mc      += _rv - _cost_row
                    _rev   += _rv
                mc_sens_o.append(float(_mc))
                rev_sens_o.append(float(_rev))

            idx_s   = int(np.argmax(mc_sens_o))
            adj_ot  = float(delta_range_o[idx_s])
            mc_ot   = mc_sens_o[idx_s]
            curva_s = pd.DataFrame({
                "pp adicionais": delta_range_o,
                "MC/dia R$":     mc_sens_o,
                "Fat/dia R$":    rev_sens_o,
            }).set_index("pp adicionais")
            st.markdown(f"**Ótimo com +{adj_ot:.1f} pp adicionais** → MC = {fmt_brl_full(mc_ot)}")
            st.line_chart(curva_s, color=["#4CAF50","#2196F3"], height=240)

            st.divider()
            st.markdown("### 👀 Quais clientes ainda precisam de mais atenção?")
            cli_ant_o = cf_grp_o.groupby("codcli", as_index=False).agg(
                a_vl_d=("a_vl_d","sum"), a_mc_d=("a_mc_d","sum"),
                d_vl_d=("d_vl_d","sum"), d_mc_d=("d_mc_d","sum"),
            )
            proj_o_cli = proj_o.groupby("codcli", as_index=False).agg(
                Rev_new=("Rev_new","sum"), MC_new=("MC_new","sum"),
            )
            proj_o_cli = proj_o_cli.merge(cli_ant_o, on="codcli", how="left")
            nome_map_o = fallen_o.set_index("codcli")["nome"].to_dict()
            proj_o_cli["nome"] = proj_o_cli["codcli"].map(nome_map_o).fillna(proj_o_cli["codcli"])
            proj_o_cli["delta_vs_ref"] = (
                proj_o_cli["Rev_new"] / proj_o_cli["a_vl_d"].replace(0, float("nan")) - 1
            ) * 100
            proj_o_cli["delta_mc_pct"] = (
                (proj_o_cli["MC_new"] - proj_o_cli["d_mc_d"])
                / proj_o_cli["d_mc_d"].replace(0, float("nan")) * 100
            )
            # ── NOVO: queda de margem em R$/dia ──────────────────────────────
            proj_o_cli["delta_mc_rs"] = proj_o_cli["MC_new"] - proj_o_cli["a_mc_d"]

            def _color_attn_o(val):
                try:
                    v = float(val)
                    if v >= -5:  return "color:#155724"
                    if v >= -15: return "color:#b35a00"
                    return "color:#721c24; font-weight:bold"
                except: pass
                return ""

            attn_o = proj_o_cli.sort_values("delta_vs_ref")[[
                "codcli","nome","a_vl_d","d_vl_d","Rev_new","delta_vs_ref",
                "a_mc_d","d_mc_d","MC_new","delta_mc_rs","delta_mc_pct"
            ]].copy()
            attn_o.columns = [
                "Cód Cliente","Cliente",
                f"Fat/dia {PERIODO_A}","Fat/dia Atual","Fat/dia Projetado",f"Δ vs {PERIODO_A} %",
                f"MC/dia {PERIODO_A}","MC/dia Atual","MC/dia Projetada","Δ MC R$/dia","Δ MC %"
            ]
            _attn_styled = attn_o.style.format({
                f"Fat/dia {PERIODO_A}":  fmt_brl_full,
                "Fat/dia Atual":         fmt_brl_full,
                "Fat/dia Projetado":     fmt_brl_full,
                f"MC/dia {PERIODO_A}":   fmt_brl_full,
                "MC/dia Atual":          fmt_brl_full,
                "MC/dia Projetada":      fmt_brl_full,
                "Δ MC R$/dia":           fmt_brl_full,
                f"Δ vs {PERIODO_A} %": lambda x: f"{x:+.1f}%" if pd.notna(x) else "—",
                "Δ MC %":              lambda x: f"{x:+.1f}%" if pd.notna(x) else "—",
            }, na_rep="—")
            try:
                _attn_styled = _attn_styled.map(_color_attn_o, subset=[f"Δ vs {PERIODO_A} %", "Δ MC %"])
            except AttributeError:
                _attn_styled = _attn_styled.applymap(_color_attn_o, subset=[f"Δ vs {PERIODO_A} %", "Δ MC %"])
            st.dataframe(_attn_styled, use_container_width=True, height=350)

    st.caption("Modelo heurístico — sazonalidade e outros fatores não são capturados.")

# ══════════════════════════════════════════════════════════════════════════════
# SIMULADOR HEURÍSTICO — LETRA Q
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.subheader("📐 Simulador Heurístico — Letra Q")
    st.caption(
        "Elasticidade de mercado **assumida** (ajustável) · "
        "Clientes **Letra Q** com queda de faturamento · "
        "Desconto configurado **por fornecedor**, aplicado igualmente a todos do grupo"
    )

    st.markdown("### 🔍 Definir o Grupo")
    queda_thr_q = st.slider(
        "Queda mínima de Fat/dia (%)", min_value=-50, max_value=-5,
        value=-10, step=5, key="qthr_q"
    )

    sigla_sim_q = ["Q"]
    fallen_q = cli_df[
        cli_df["sigla"].isin(sigla_sim_q) &
        (cli_df["delta_pct"] < queda_thr_q)
    ].copy()
    fallen_q      = fallen_q.drop_duplicates("codcli")
    fallen_cods_q = set(fallen_q["codcli"].str.strip())
    n_fallen_q    = len(fallen_q)

    gh1, gh2, gh3 = st.columns(3)
    gh1.metric("Clientes no grupo",       f"{n_fallen_q}")
    gh2.metric("Fat/dia perdida (grupo)", fmt_brl_full(fallen_q["delta_vl_d"].sum() if not fallen_q.empty else 0))
    gh3.metric("MC/dia perdida (grupo)",  fmt_brl_full(fallen_q["delta_mc_d"].sum() if not fallen_q.empty else 0))

    if fallen_q.empty:
        st.info("Nenhum cliente encontrado. Reduza o threshold de queda.")
    else:
        cf_grp_q = cf_df[
            cf_df["codcli"].str.strip().isin(fallen_cods_q) &
            cf_df["sigla"].isin(sigla_sim_q)
        ].copy()

        rev_ant_q = fallen_q["a_vl_d"].sum()
        mc_ant_q  = fallen_q["a_mc_d"].sum()
        rev_cur_q = cf_grp_q["d_vl_d"].sum()  if not cf_grp_q.empty else fallen_q["d_vl_d"].sum()
        mc_cur_q  = cf_grp_q["d_mc_d"].sum()  if not cf_grp_q.empty else fallen_q["d_mc_d"].sum()

        ka1, ka2, ka3, ka4 = st.columns(4)
        ka1.metric(f"Fat/dia {PERIODO_A}", fmt_brl_full(rev_ant_q))
        ka2.metric(f"Fat/dia {PERIODO_D}", fmt_brl_full(rev_cur_q),
                   f"{(rev_cur_q/rev_ant_q-1)*100:+.1f}%" if rev_ant_q > 0 else "—")
        ka3.metric(f"MC/dia {PERIODO_A}",  fmt_brl_full(mc_ant_q))
        ka4.metric(f"MC/dia {PERIODO_D}",  fmt_brl_full(mc_cur_q),
                   f"{(mc_cur_q/mc_ant_q-1)*100:+.1f}%" if mc_ant_q > 0 else "—")

        if cf_grp_q.empty:
            st.warning("Sem dados de cf_df para o grupo. Verifique o arquivo cli_forn.csv.")
        else:
            forn_agg_q = cf_grp_q.groupby(["codfor","fantasia"], as_index=False).agg(
                a_vl_d  =("a_vl_d",  "sum"),
                d_vl_d  =("d_vl_d",  "sum"),
                d_cmv_d =("d_cmv_d", "sum"),
                a_mc_d  =("a_mc_d",  "sum"),
                d_mc_d  =("d_mc_d",  "sum"),
                a_qtde  =("a_qtde",  "sum"),
                d_qtde  =("d_qtde",  "sum"),
                n_cli   =("codcli",  "nunique"),
            )
            forn_agg_q["codfor"] = forn_agg_q["codfor"].astype(str).str.strip().str.zfill(5)
            forn_agg_q["delta_pct_f"]  = (
                (forn_agg_q["d_vl_d"] - forn_agg_q["a_vl_d"])
                / forn_agg_q["a_vl_d"].replace(0, float("nan")) * 100
            )
            forn_agg_q["delta_vl_d_r"] = forn_agg_q["d_vl_d"] - forn_agg_q["a_vl_d"]
            forn_agg_q["delta_mc_d_r"] = forn_agg_q["d_mc_d"] - forn_agg_q["a_mc_d"]
            forn_agg_q["delta_mc_pct"] = (
                forn_agg_q["delta_mc_d_r"]
                / forn_agg_q["a_mc_d"].replace(0, float("nan")) * 100
            )

            ft_q = ft_df.copy()
            ft_q["codfor"] = ft_q["codfor"].astype(str).str.strip().str.zfill(5)
            forn_agg_q = forn_agg_q.merge(
                ft_q[["codfor", "pc_acre_q"]].rename(columns={"pc_acre_q": "desc_atual"}),
                on="codfor", how="left"
            )
            forn_agg_q["desc_atual"] = forn_agg_q["desc_atual"].fillna(0.0)

            forn_agg_q["eps_obs"]  = forn_agg_q.apply(_calc_eps_obs, axis=1)
            forn_agg_q["conf_eps"] = forn_agg_q.apply(
                lambda r: _eps_conf_label(
                    r["a_qtde"] / N_DIAS_A,
                    r["d_qtde"] / N_DIAS_D,
                    not pd.isna(r["eps_obs"])
                ), axis=1
            )

            st.divider()
            st.markdown("### 🎛️ Elasticidade Assumida")

            _eps_val_q = forn_agg_q.dropna(subset=["eps_obs"])
            if not _eps_val_q.empty:
                _w_q  = _eps_val_q["a_vl_d"].values
                _v_q  = _eps_val_q["eps_obs"].values
                _si_q = np.argsort(_v_q)
                _sv_q = _v_q[_si_q]; _sw_q = _w_q[_si_q]
                _cw_q = np.cumsum(_sw_q)
                _med_q = float(_sv_q[np.searchsorted(_cw_q, _cw_q[-1] / 2)])
                st.info(
                    f"📊 **ε observado calculado para {len(_eps_val_q)} de "
                    f"{len(forn_agg_q)} fornecedores** · "
                    f"**Mediana ponderada: ε = {_med_q:.1f}**"
                )
            else:
                st.warning("Nenhum fornecedor com dados suficientes para calcular ε observado.")

            eps_q = st.slider(
                "Elasticidade (ε) assumida — Letra Q",
                min_value=-15.0, max_value=-0.1, value=-2.0, step=0.1, key="eps_q",
            )

            forn_agg_q["sug_delta"] = forn_agg_q.apply(
                lambda row: _opt_delta(row["desc_atual"], row["d_vl_d"], row["d_vl_d"] - row["d_mc_d"], eps_q), axis=1
            )
            forn_agg_q["desc_final_sug"] = forn_agg_q["desc_atual"] - forn_agg_q["sug_delta"]
            forn_agg_q["sug_delta_obs"] = forn_agg_q.apply(
                lambda row: (
                    _opt_delta(row["desc_atual"], row["d_vl_d"], row["d_vl_d"] - row["d_mc_d"], row["eps_obs"])
                    if not pd.isna(row["eps_obs"]) else float("nan")
                ), axis=1
            )

            st.divider()
            st.markdown("### 📋 Descontos por Fornecedor → Nova Letra Q")

            disc_q = forn_agg_q[[
                "codfor","fantasia",
                "a_vl_d","d_vl_d","delta_vl_d_r","delta_pct_f",
                "a_mc_d","d_mc_d","delta_mc_d_r","delta_mc_pct",
                "n_cli","eps_obs","conf_eps","desc_atual",
                "sug_delta","sug_delta_obs","desc_final_sug",
            ]].copy()
            disc_q.columns = [
                "Cód","Fornecedor",
                "Fat/dia Antes","Fat/dia Atual","Δ Fat/dia R$","Δ Fat %",
                "MC/dia Antes","MC/dia Atual","Δ MC/dia R$","Δ MC %",
                "Clientes","ε Obs","Confiança ε","Desc Atual %",
                "Δ Sug slider (pp)","Δ Sug ε Obs (pp)","Desc Final Sug %",
            ]
            disc_q["Δ Desc (pp)"] = 0.0
            disc_q = disc_q.sort_values("Fat/dia Atual", ascending=False).reset_index(drop=True)

            if "my_deltas_q" not in st.session_state:
                st.session_state["my_deltas_q"] = {}
            for _ri, _rc in st.session_state.get("disc_edit_q", {}).get("edited_rows", {}).items():
                if "Δ Desc (pp)" in _rc and int(_ri) < len(disc_q):
                    _cf = str(disc_q["Cód"].iat[int(_ri)]).strip()
                    try:
                        _dv = float(_rc["Δ Desc (pp)"])
                    except (TypeError, ValueError):
                        continue
                    if _dv > 0:
                        st.session_state["my_deltas_q"][_cf] = _dv
                    else:
                        st.session_state["my_deltas_q"].pop(_cf, None)
            disc_q["Δ Desc (pp)"] = disc_q["Cód"].map(
                lambda c: st.session_state["my_deltas_q"].get(str(c).strip(), 0.0)
            )
            disc_q["Desc Final %"] = disc_q["Desc Atual %"] - disc_q["Δ Desc (pp)"]

            edited_q = st.data_editor(
                disc_q,
                column_config={
                    "Cód":              st.column_config.TextColumn("Cód", disabled=True, width="small"),
                    "Fornecedor":       st.column_config.TextColumn("Fornecedor", disabled=True),
                    "Fat/dia Antes":    st.column_config.NumberColumn("Fat/dia Antes",    disabled=True, format="R$ %.0f"),
                    "Fat/dia Atual":    st.column_config.NumberColumn("Fat/dia Atual",    disabled=True, format="R$ %.0f"),
                    "Δ Fat/dia R$":     st.column_config.NumberColumn("Δ Fat/dia R$",     disabled=True, format="R$ %.0f"),
                    "Δ Fat %":          st.column_config.NumberColumn("Δ Fat %",          disabled=True, format="%.1f%%"),
                    "MC/dia Antes":     st.column_config.NumberColumn("MC/dia Antes",     disabled=True, format="R$ %.0f"),
                    "MC/dia Atual":     st.column_config.NumberColumn("MC/dia Atual",     disabled=True, format="R$ %.0f"),
                    "Δ MC/dia R$":      st.column_config.NumberColumn("Δ MC/dia R$",      disabled=True, format="R$ %.0f"),
                    "Δ MC %":           st.column_config.NumberColumn("Δ MC %",           disabled=True, format="%.1f%%"),
                    "Clientes":         st.column_config.NumberColumn("Clientes",         disabled=True, width="small"),
                    "ε Obs":            st.column_config.NumberColumn("ε Obs 📊",         disabled=True, format="%.2f"),
                    "Confiança ε":      st.column_config.TextColumn("Confiança",          disabled=True, width="small"),
                    "Desc Atual %":     st.column_config.NumberColumn("Desc Atual %",     disabled=True, format="%.1f%%"),
                    "Δ Sug slider (pp)": st.column_config.NumberColumn("Δ Sug slider 💡", disabled=True, format="+%.1f pp"),
                    "Δ Sug ε Obs (pp)": st.column_config.NumberColumn("Δ Sug ε Obs 📊",  disabled=True, format="+%.1f pp"),
                    "Desc Final Sug %": st.column_config.NumberColumn("Desc Final Sug %", disabled=True, format="%.1f%%"),
                    "Δ Desc (pp)":      st.column_config.NumberColumn("Δ Desc (pp) ✏️", min_value=0.0, max_value=20.0, step=0.5, format="+%.1f pp"),
                    "Desc Final %":     st.column_config.NumberColumn("Desc Final % ✅",  disabled=True, format="%.1f%%"),
                },
                hide_index=True, key="disc_edit_q",
                height=min(500, 60 + len(disc_q) * 35),
            )

            curr_desc_map_q = dict(zip(forn_agg_q["codfor"].astype(str).str.zfill(5), forn_agg_q["desc_atual"]))
            delta_map_q     = dict(zip(
                edited_q["Cód"].astype(str).str.strip().str.zfill(5),
                edited_q["Δ Desc (pp)"]
            ))

            proj_q = cf_grp_q.copy()
            proj_q["codfor_k"]  = proj_q["codfor"].astype(str).str.strip().str.zfill(5)
            proj_q["curr_desc"] = proj_q["codfor_k"].map(curr_desc_map_q).fillna(0.0)
            proj_q["delta_pp"]  = proj_q["codfor_k"].map(delta_map_q).fillna(0.0)
            proj_q["new_desc"]  = proj_q["curr_desc"] - proj_q["delta_pp"]
            _denom_q            = (1 + proj_q["curr_desc"] / 100).clip(lower=0.001)
            proj_q["r"]         = ((1 + proj_q["new_desc"] / 100) / _denom_q).clip(lower=0.001)
            proj_q["cost_d"]    = proj_q["d_vl_d"] - proj_q["d_mc_d"]
            proj_q["Rev_new"]   = proj_q["d_vl_d"]  * (proj_q["r"] ** (1 + eps_q))
            proj_q["CMV_new"]   = proj_q["cost_d"]  * (proj_q["r"] ** eps_q)
            proj_q["MC_new"]    = proj_q["Rev_new"] - proj_q["CMV_new"]

            mc_new_q  = proj_q["MC_new"].sum()
            rev_new_q = proj_q["Rev_new"].sum()

            st.divider()
            st.markdown("### 📊 Resultado do Grupo com os Novos Descontos")
            pr1, pr2, pr3, pr4 = st.columns(4)
            pr1.metric("Fat/dia projetado", fmt_brl_full(rev_new_q),
                       f"{(rev_new_q/rev_cur_q-1)*100:+.1f}% vs atual" if rev_cur_q > 0 else "—")
            pr2.metric("MC/dia projetada",  fmt_brl_full(mc_new_q),
                       f"{mc_new_q-mc_cur_q:+.2f} R$/dia vs atual")
            pr3.metric(f"Fat/dia vs {PERIODO_A}",  fmt_brl_full(rev_new_q - rev_ant_q),
                       f"{(rev_new_q/rev_ant_q-1)*100:+.1f}%" if rev_ant_q > 0 else "—")
            pr4.metric(f"MC/dia vs {PERIODO_A}",   fmt_brl_full(mc_new_q - mc_ant_q),
                       f"{(mc_new_q/mc_ant_q-1)*100:+.1f}%" if mc_ant_q > 0 else "—")

            st.divider()
            st.markdown("### 📈 Sensibilidade — pp Adicionais sobre os Δ Configurados")
            delta_range_q = np.linspace(0, 15, 201)
            mc_sens_q, rev_sens_q = [], []
            for _dd in delta_range_q:
                _mc = 0.0; _rev = 0.0
                for _, row in proj_q.iterrows():
                    _new_d  = row["curr_desc"] - row["delta_pp"] - _dd
                    _den    = max(1 + row["curr_desc"] / 100, 0.001)
                    _r      = max((1 + _new_d / 100) / _den, 0.001)
                    _rv       = row["d_vl_d"]  * (_r ** (1 + eps_q))
                    _cost_row = row["cost_d"]  * (_r ** eps_q)
                    _mc      += _rv - _cost_row
                    _rev   += _rv
                mc_sens_q.append(float(_mc))
                rev_sens_q.append(float(_rev))

            idx_s   = int(np.argmax(mc_sens_q))
            adj_ot  = float(delta_range_q[idx_s])
            mc_ot   = mc_sens_q[idx_s]
            curva_s = pd.DataFrame({
                "pp adicionais": delta_range_q,
                "MC/dia R$":     mc_sens_q,
                "Fat/dia R$":    rev_sens_q,
            }).set_index("pp adicionais")
            st.markdown(f"**Ótimo com +{adj_ot:.1f} pp adicionais** → MC = {fmt_brl_full(mc_ot)}")
            st.line_chart(curva_s, color=["#4CAF50","#2196F3"], height=240)

            st.divider()
            st.markdown("### 👀 Quais clientes ainda precisam de mais atenção?")
            cli_ant_q = cf_grp_q.groupby("codcli", as_index=False).agg(
                a_vl_d=("a_vl_d","sum"), a_mc_d=("a_mc_d","sum"),
                d_vl_d=("d_vl_d","sum"), d_mc_d=("d_mc_d","sum"),
            )
            proj_q_cli = proj_q.groupby("codcli", as_index=False).agg(
                Rev_new=("Rev_new","sum"), MC_new=("MC_new","sum"),
            )
            proj_q_cli = proj_q_cli.merge(cli_ant_q, on="codcli", how="left")
            nome_map_q = fallen_q.set_index("codcli")["nome"].to_dict()
            proj_q_cli["nome"] = proj_q_cli["codcli"].map(nome_map_q).fillna(proj_q_cli["codcli"])
            proj_q_cli["delta_vs_ref"] = (
                proj_q_cli["Rev_new"] / proj_q_cli["a_vl_d"].replace(0, float("nan")) - 1
            ) * 100
            proj_q_cli["delta_mc_pct"] = (
                (proj_q_cli["MC_new"] - proj_q_cli["d_mc_d"])
                / proj_q_cli["d_mc_d"].replace(0, float("nan")) * 100
            )
            # ── NOVO: queda de margem em R$/dia ──────────────────────────────
            proj_q_cli["delta_mc_rs"] = proj_q_cli["MC_new"] - proj_q_cli["a_mc_d"]

            def _color_attn_q(val):
                try:
                    v = float(val)
                    if v >= -5:  return "color:#155724"
                    if v >= -15: return "color:#b35a00"
                    return "color:#721c24; font-weight:bold"
                except: pass
                return ""

            attn_q = proj_q_cli.sort_values("delta_vs_ref")[[
                "codcli","nome","a_vl_d","d_vl_d","Rev_new","delta_vs_ref",
                "a_mc_d","d_mc_d","MC_new","delta_mc_rs","delta_mc_pct"
            ]].copy()
            attn_q.columns = [
                "Cód Cliente","Cliente",
                f"Fat/dia {PERIODO_A}","Fat/dia Atual","Fat/dia Projetado",f"Δ vs {PERIODO_A} %",
                f"MC/dia {PERIODO_A}","MC/dia Atual","MC/dia Projetada","Δ MC R$/dia","Δ MC %"
            ]
            _attn_styled_q = attn_q.style.format({
                f"Fat/dia {PERIODO_A}":  fmt_brl_full,
                "Fat/dia Atual":         fmt_brl_full,
                "Fat/dia Projetado":     fmt_brl_full,
                f"MC/dia {PERIODO_A}":   fmt_brl_full,
                "MC/dia Atual":          fmt_brl_full,
                "MC/dia Projetada":      fmt_brl_full,
                "Δ MC R$/dia":           fmt_brl_full,
                f"Δ vs {PERIODO_A} %": lambda x: f"{x:+.1f}%" if pd.notna(x) else "—",
                "Δ MC %":              lambda x: f"{x:+.1f}%" if pd.notna(x) else "—",
            }, na_rep="—")
            try:
                _attn_styled_q = _attn_styled_q.map(_color_attn_q, subset=[f"Δ vs {PERIODO_A} %", "Δ MC %"])
            except AttributeError:
                _attn_styled_q = _attn_styled_q.applymap(_color_attn_q, subset=[f"Δ vs {PERIODO_A} %", "Δ MC %"])
            st.dataframe(_attn_styled_q, use_container_width=True, height=350)

    st.caption("Modelo heurístico — sazonalidade e outros fatores não são capturados.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — POR VENDEDOR (CARTEIRA)
# ══════════════════════════════════════════════════════════════════════════════
with tab7:
    st.subheader("🧑‍💼 Desempenho por Vendedor / Carteira")
    st.caption("Impacto do reajuste nas carteiras ativas · filtros de sigla, estado e carteira da barra lateral")

    vend_agg = (
        cli_fil.groupby("carteira", as_index=False)
        .agg(
            a_vl    =("a_vl",   "sum"), a_mc  =("a_mc",   "sum"), a_cmv =("a_cmv",  "sum"),
            a_qtde  =("a_qtde", "sum"), a_ped =("a_ped",  "sum"),
            d_vl    =("d_vl",   "sum"), d_mc  =("d_mc",   "sum"), d_cmv =("d_cmv",  "sum"),
            d_qtde  =("d_qtde", "sum"), d_ped =("d_ped",  "sum"),
            n_cli_a =("a_vl",   lambda s: (s > 0).sum()),
            n_cli_d =("d_vl",   lambda s: (s > 0).sum()),
        )
    )
    vend_agg["a_vl_d"]     = vend_agg["a_vl"]  / N_DIAS_A
    vend_agg["d_vl_d"]     = vend_agg["d_vl"]  / N_DIAS_D
    vend_agg["a_mc_d"]     = vend_agg["a_mc"]  / N_DIAS_A
    vend_agg["d_mc_d"]     = vend_agg["d_mc"]  / N_DIAS_D
    vend_agg["a_cmv_d"]    = vend_agg["a_cmv"] / N_DIAS_A
    vend_agg["d_cmv_d"]    = vend_agg["d_cmv"] / N_DIAS_D
    vend_agg["delta_vl_d"]  = vend_agg["d_vl_d"] - vend_agg["a_vl_d"]
    vend_agg["delta_pct"]   = (vend_agg["delta_vl_d"] / vend_agg["a_vl_d"].replace(0, float("nan"))) * 100
    vend_agg["delta_mc_d"]  = vend_agg["d_mc_d"] - vend_agg["a_mc_d"]
    vend_agg["delta_mc_pct"]= (vend_agg["delta_mc_d"] / vend_agg["a_mc_d"].replace(0, float("nan"))) * 100
    vend_agg["a_mc_pct"]    = (vend_agg["a_mc"]  / vend_agg["a_vl"].replace(0, float("nan"))) * 100
    vend_agg["d_mc_pct"]    = (vend_agg["d_mc"]  / vend_agg["d_vl"].replace(0, float("nan"))) * 100
    vend_agg["a_cmv_pct"]  = (vend_agg["a_cmv"] / vend_agg["a_vl"].replace(0, float("nan"))) * 100
    vend_agg["d_cmv_pct"]  = (vend_agg["d_cmv"] / vend_agg["d_vl"].replace(0, float("nan"))) * 100
    vend_agg["a_ticket"]   = vend_agg["a_vl"] / vend_agg["a_ped"].replace(0, float("nan"))
    vend_agg["d_ticket"]   = vend_agg["d_vl"] / vend_agg["d_ped"].replace(0, float("nan"))
    vend_agg["clientes_zerados"] = vend_agg["n_cli_a"] - vend_agg["n_cli_d"]
    vend_agg = vend_agg.sort_values("delta_vl_d", ascending=True)

    tot_cart = len(vend_agg)
    cart_negativas = (vend_agg["delta_pct"] < 0).sum()
    cart_positivas = (vend_agg["delta_pct"] > 0).sum()
    maior_queda = vend_agg.sort_values("delta_pct").iloc[0] if len(vend_agg) > 0 else None

    kv1, kv2, kv3, kv4 = st.columns(4)
    kv1.metric("Carteiras com queda",      f"{cart_negativas} / {tot_cart}")
    kv2.metric("Carteiras em crescimento", f"{cart_positivas}")
    if maior_queda is not None:
        kv3.metric("Pior carteira", maior_queda["carteira"][:30], f"{maior_queda['delta_pct']:+.1f}%")
        kv4.metric("Perda diária maior carteira", fmt_brl(abs(maior_queda["delta_vl_d"])))

    vend_csv = vend_agg.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exportar por vendedor (CSV)", vend_csv, "vendedores.csv", "text/csv")
    st.caption("Clique em ▶ para ver os clientes de cada carteira")

    if vend_agg.empty:
        st.info("Nenhuma carteira nos filtros atuais.")
    else:
        _brl = fmt_brl_full
        _pct = fmt_pct
        _pa  = fmt_pct_abs
        _txt = lambda v: str(v) if v is not None else "—"
        _num = lambda v: f"{v:.2f}" if not pd.isna(v) else "—"
        _int = lambda v: str(int(v)) if not pd.isna(v) else "—"

        main_cols_6 = [
            ("carteira",          "Carteira",         _txt, False),
            ("a_vl_d",            "Fat/dia Antes",    _brl, False),
            ("d_vl_d",            "Fat/dia Depois",   _brl, False),
            ("delta_vl_d",        "Δ Fat/dia R$",     _brl, False),
            ("delta_pct",         "Δ Fat %",          _pct, True ),
            ("a_mc_d",            "MC/dia Antes",     _brl, False),
            ("d_mc_d",            "MC/dia Depois",    _brl, False),
            ("delta_mc_d",        "Δ MC/dia R$",      _brl, False),
            ("delta_mc_pct",      "Δ MC %",           _pct, True ),
            ("a_mc_pct",          "MC% Antes",        _pa,  False),
            ("d_mc_pct",          "MC% Depois",       _pa,  False),
            ("n_cli_a",           "Clientes Antes",   _int, False),
            ("n_cli_d",           "Clientes Depois",  _int, False),
            ("clientes_zerados",  "Zeraram",          _int, False),
        ]
        client_cols_6 = [
            ("nome",          "Cliente",         _txt, False),
            ("sigla",         "Sig",             _txt, False),
            ("estado",        "UF",              _txt, False),
            ("a_vl_d",        "Fat/dia Antes",   _brl, False),
            ("d_vl_d",        "Fat/dia Depois",  _brl, False),
            ("delta_pct",     "Δ Fat %",         _pct, True ),
            ("delta_mc_pct",  "Δ MC %",          _pct, True ),
            ("a_margem_pct",  "MC% Antes",       _pa,  False),
            ("d_margem_pct",  "MC% Depois",      _pa,  False),
            ("a_qtde_d",      "Qtde/dia Antes",  _num, False),
            ("d_qtde_d",      "Qtde/dia Depois", _num, False),
        ]
        main_rows_6 = vend_agg[[
            "carteira","a_vl_d","d_vl_d","delta_vl_d","delta_pct",
            "a_mc_d","d_mc_d","delta_mc_d","delta_mc_pct",
            "a_mc_pct","d_mc_pct","n_cli_a","n_cli_d","clientes_zerados",
        ]].to_dict("records")

        def detail_fn_6(row):
            cli_cart = (cli_fil[cli_fil["carteira"] == row["carteira"]]
                        .sort_values("delta_pct", ascending=True))
            cli_rows = cli_cart[[
                "codcli","nome","sigla","estado",
                "a_vl_d","d_vl_d","delta_pct","delta_mc_pct",
                "a_margem_pct","d_margem_pct","a_qtde_d","d_qtde_d",
            ]].to_dict("records")
            return _det_tbl(cli_rows, client_cols_6)

        tot6 = build_total_row(vend_agg, label_col="carteira", label="TOTAL")
        components.html(
            tree_table_html(main_rows_6, detail_fn_6, main_cols_6, total_row=tot6,
                            max_height=980, n_sticky=1, sticky_widths=[175]),
            height=1010, scrolling=False
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 — SIMULADOR LETRA E
# ══════════════════════════════════════════════════════════════════════════════
with tab8:
    st.subheader("📐 Simulador Heurístico — Letra E")
    st.caption(
        "Elasticidade de mercado **assumida** (ajustável) · "
        "Fornecedores **Letra E** · "
        "Desconto configurado **por fornecedor**"
    )

    cf_e = cf_df[cf_df["sigla"] == "E"].copy()

    if cf_e.empty:
        st.warning("Nenhum dado de fornecedor para letra E. Verifique o cli_forn.csv.")
    else:
        forn_agg_e = cf_e.groupby(["codfor", "fantasia"], as_index=False).agg(
            a_vl_d  =("a_vl_d",  "sum"),
            d_vl_d  =("d_vl_d",  "sum"),
            d_cmv_d =("d_cmv_d", "sum"),
            a_mc_d  =("a_mc_d",  "sum"),
            d_mc_d  =("d_mc_d",  "sum"),
            a_qtde  =("a_qtde",  "sum"),
            d_qtde  =("d_qtde",  "sum"),
            n_cli   =("codcli",  "nunique"),
        )
        forn_agg_e["codfor"] = forn_agg_e["codfor"].astype(str).str.strip().str.zfill(5)
        forn_agg_e["delta_pct_f"]  = (
            (forn_agg_e["d_vl_d"] - forn_agg_e["a_vl_d"])
            / forn_agg_e["a_vl_d"].replace(0, float("nan")) * 100
        )
        forn_agg_e["delta_vl_d_r"] = forn_agg_e["d_vl_d"] - forn_agg_e["a_vl_d"]
        forn_agg_e["delta_mc_d_r"] = forn_agg_e["d_mc_d"] - forn_agg_e["a_mc_d"]
        forn_agg_e["delta_mc_pct"] = (
            forn_agg_e["delta_mc_d_r"]
            / forn_agg_e["a_mc_d"].replace(0, float("nan")) * 100
        )

        ft_e = ft_df.copy()
        ft_e["codfor"] = ft_e["codfor"].astype(str).str.strip().str.zfill(5)
        forn_agg_e = forn_agg_e.merge(
            ft_e[["codfor", "pc_acre_e"]].rename(columns={"pc_acre_e": "desc_atual"}),
            on="codfor", how="left"
        )
        forn_agg_e["desc_atual"] = forn_agg_e["desc_atual"].fillna(0.0)

        forn_agg_e["eps_obs"]  = forn_agg_e.apply(_calc_eps_obs, axis=1)
        forn_agg_e["conf_eps"] = forn_agg_e.apply(
            lambda r: _eps_conf_label(
                r["a_qtde"] / N_DIAS_A,
                r["d_qtde"] / N_DIAS_D,
                not pd.isna(r["eps_obs"])
            ), axis=1
        )

        forn_agg_e = forn_agg_e.sort_values("a_vl_d", ascending=False).reset_index(drop=True)
        total_fat_e = forn_agg_e["a_vl_d"].sum()
        forn_agg_e["represent_pct"] = forn_agg_e["a_vl_d"] / total_fat_e * 100
        forn_agg_e["represent_acum"] = forn_agg_e["represent_pct"].cumsum()

        repr_thr_e = st.slider(
            "% de faturamento acumulado a analisar",
            min_value=10, max_value=100, value=80, step=5, key="repr_e",
        )
        forn_agg_e = forn_agg_e[forn_agg_e["represent_acum"].shift(1, fill_value=0) < repr_thr_e].copy()
        st.caption(f"Exibindo **{len(forn_agg_e)} fornecedores** que representam até **{repr_thr_e}%** do faturamento de {PERIODO_A}.")

        rev_ant_e = forn_agg_e["a_vl_d"].sum()
        rev_cur_e = forn_agg_e["d_vl_d"].sum()
        mc_ant_e  = forn_agg_e["a_mc_d"].sum()
        mc_cur_e  = forn_agg_e["d_mc_d"].sum()

        rev_ant_e_total = cf_e.groupby("codfor")["a_vl_d"].sum().sum()
        rev_cur_e_total = cf_e.groupby("codfor")["d_vl_d"].sum().sum()

        ke1, ke2, ke3, ke4, ke5, ke6 = st.columns(6)
        ke1.metric(f"Fat/dia {PERIODO_A} (total E)",   fmt_brl_full(rev_ant_e_total))
        ke2.metric(f"Fat/dia {PERIODO_D} (total E)",   fmt_brl_full(rev_cur_e_total),
                   f"{(rev_cur_e_total/rev_ant_e_total-1)*100:+.1f}%" if rev_ant_e_total > 0 else "—")
        ke3.metric(f"Fat/dia {PERIODO_A} ({repr_thr_e}%)", fmt_brl_full(rev_ant_e))
        ke4.metric(f"Fat/dia {PERIODO_D} ({repr_thr_e}%)",  fmt_brl_full(rev_cur_e),
                   f"{(rev_cur_e/rev_ant_e-1)*100:+.1f}%" if rev_ant_e > 0 else "—")
        ke5.metric(f"MC/dia {PERIODO_A} (total E)",    fmt_brl_full(cf_e.groupby("codfor")["a_mc_d"].sum().sum()))
        ke6.metric(f"MC/dia {PERIODO_D} (total E)",    fmt_brl_full(cf_e.groupby("codfor")["d_mc_d"].sum().sum()))

        st.divider()
        st.markdown("### 🎛️ Elasticidade Assumida")

        _eps_val_e = forn_agg_e.dropna(subset=["eps_obs"])
        if not _eps_val_e.empty:
            _w_e  = _eps_val_e["a_vl_d"].values
            _v_e  = _eps_val_e["eps_obs"].values
            _si_e = np.argsort(_v_e)
            _sv_e = _v_e[_si_e]; _sw_e = _w_e[_si_e]
            _cw_e = np.cumsum(_sw_e)
            _med_e = float(_sv_e[np.searchsorted(_cw_e, _cw_e[-1] / 2)])
            st.info(
                f"📊 **ε observado calculado para {len(_eps_val_e)} de "
                f"{len(forn_agg_e)} fornecedores** · "
                f"**Mediana ponderada: ε = {_med_e:.1f}**"
            )
        else:
            st.warning("Nenhum fornecedor com dados suficientes para calcular ε observado.")

        eps_e = st.slider(
            "Elasticidade (ε) assumida — Letra E",
            min_value=-15.0, max_value=-0.1, value=-2.0, step=0.1, key="eps_e",
        )

        forn_agg_e["sug_delta"] = forn_agg_e.apply(
            lambda row: _opt_delta(row["desc_atual"], row["d_vl_d"], row["d_vl_d"] - row["d_mc_d"], eps_e), axis=1
        )
        forn_agg_e["sug_delta_obs"] = forn_agg_e.apply(
            lambda row: (
                _opt_delta(row["desc_atual"], row["d_vl_d"], row["d_vl_d"] - row["d_mc_d"], row["eps_obs"])
                if not pd.isna(row["eps_obs"]) else float("nan")
            ), axis=1
        )
        forn_agg_e["desc_final_sug"] = forn_agg_e["desc_atual"] - forn_agg_e["sug_delta"]

        st.divider()
        st.markdown("### 📋 Descontos por Fornecedor → Nova Letra E")

        disc_e = forn_agg_e[[
            "codfor", "fantasia",
            "a_vl_d", "d_vl_d", "delta_vl_d_r", "delta_pct_f",
            "a_mc_d", "d_mc_d", "delta_mc_d_r", "delta_mc_pct",
            "n_cli", "eps_obs", "conf_eps", "desc_atual",
            "sug_delta", "sug_delta_obs", "desc_final_sug",
            "represent_pct", "represent_acum",
        ]].copy()
        disc_e.columns = [
            "Cód", "Fornecedor",
            "Fat/dia Antes", "Fat/dia Atual", "Δ Fat/dia R$", "Δ Fat %",
            "MC/dia Antes", "MC/dia Atual", "Δ MC/dia R$", "Δ MC %",
            "Clientes", "ε Obs", "Confiança ε", "Desc Atual %",
            "Δ Sug slider (pp)", "Δ Sug ε Obs (pp)", "Desc Final Sug %",
            "Represent. %", "Acum. %",
        ]
        disc_e["Δ Desc (pp)"] = 0.0
        disc_e = disc_e.sort_values("Fat/dia Atual", ascending=False).reset_index(drop=True)

        if "my_deltas_e" not in st.session_state:
            st.session_state["my_deltas_e"] = {}
        for _ri, _rc in st.session_state.get("disc_edit_e", {}).get("edited_rows", {}).items():
            if "Δ Desc (pp)" in _rc and int(_ri) < len(disc_e):
                _cf = str(disc_e["Cód"].iat[int(_ri)]).strip()
                try:
                    _dv = float(_rc["Δ Desc (pp)"])
                except (TypeError, ValueError):
                    continue
                if _dv != 0:
                    st.session_state["my_deltas_e"][_cf] = _dv
                else:
                    st.session_state["my_deltas_e"].pop(_cf, None)
        disc_e["Δ Desc (pp)"] = disc_e["Cód"].map(
            lambda c: st.session_state["my_deltas_e"].get(str(c).strip(), 0.0)
        )
        disc_e["Desc Final %"] = disc_e["Desc Atual %"] - disc_e["Δ Desc (pp)"]

        edited_e = st.data_editor(
            disc_e,
            column_config={
                "Cód":               st.column_config.TextColumn("Cód", disabled=True, width="small"),
                "Fornecedor":        st.column_config.TextColumn("Fornecedor", disabled=True),
                "Fat/dia Antes":     st.column_config.NumberColumn("Fat/dia Antes",    disabled=True, format="R$ %.0f"),
                "Fat/dia Atual":     st.column_config.NumberColumn("Fat/dia Atual",    disabled=True, format="R$ %.0f"),
                "Δ Fat/dia R$":      st.column_config.NumberColumn("Δ Fat/dia R$",     disabled=True, format="R$ %.0f"),
                "Δ Fat %":           st.column_config.NumberColumn("Δ Fat %",          disabled=True, format="%.1f%%"),
                "MC/dia Antes":      st.column_config.NumberColumn("MC/dia Antes",     disabled=True, format="R$ %.0f"),
                "MC/dia Atual":      st.column_config.NumberColumn("MC/dia Atual",     disabled=True, format="R$ %.0f"),
                "Δ MC/dia R$":       st.column_config.NumberColumn("Δ MC/dia R$",      disabled=True, format="R$ %.0f"),
                "Δ MC %":            st.column_config.NumberColumn("Δ MC %",           disabled=True, format="%.1f%%"),
                "Clientes":          st.column_config.NumberColumn("Clientes",         disabled=True, width="small"),
                "ε Obs":             st.column_config.NumberColumn("ε Obs 📊",         disabled=True, format="%.2f"),
                "Confiança ε":       st.column_config.TextColumn("Confiança",          disabled=True, width="small"),
                "Desc Atual %":      st.column_config.NumberColumn("Desc Atual %",     disabled=True, format="%.1f%%"),
                "Δ Sug slider (pp)": st.column_config.NumberColumn("Δ Sug slider 💡",  disabled=True, format="+%.1f pp"),
                "Δ Sug ε Obs (pp)":  st.column_config.NumberColumn("Δ Sug ε Obs 📊",  disabled=True, format="+%.1f pp"),
                "Desc Final Sug %":  st.column_config.NumberColumn("Desc Final Sug %", disabled=True, format="%.1f%%"),
                "Δ Desc (pp)":       st.column_config.NumberColumn(
                    "Δ Desc (pp) ✏️", min_value=-20.0, max_value=20.0, step=0.5, format="%.1f pp",
                ),
                "Desc Final %":      st.column_config.NumberColumn("Desc Final % ✅",  disabled=True, format="%.1f%%"),
                "Acum. %":           st.column_config.NumberColumn("Acum. %",          disabled=True, format="%.1f%%"),
            },
            hide_index=True, key="disc_edit_e",
            height=min(500, 60 + len(disc_e) * 35),
        )

        curr_desc_map_e = dict(zip(forn_agg_e["codfor"].astype(str).str.zfill(5), forn_agg_e["desc_atual"]))
        delta_map_e = {
            str(k).strip(): float(v)
            for k, v in st.session_state.get("my_deltas_e", {}).items()
        }

        proj_e = forn_agg_e.copy()
        proj_e["codfor_k"]  = proj_e["codfor"].astype(str).str.strip().str.zfill(5)
        proj_e["curr_desc"] = proj_e["codfor_k"].map(curr_desc_map_e).fillna(0.0)
        proj_e["delta_pp"]  = proj_e["codfor_k"].map(delta_map_e).fillna(0.0)
        proj_e["new_desc"]  = proj_e["curr_desc"] - proj_e["delta_pp"]
        _denom_e            = (1 + proj_e["curr_desc"] / 100).clip(lower=0.001)
        proj_e["r"]         = ((1 + proj_e["new_desc"] / 100) / _denom_e).clip(lower=0.001)
        proj_e["cost_d"]    = proj_e["d_vl_d"] - proj_e["d_mc_d"]
        proj_e["Rev_new"]   = proj_e["d_vl_d"]  * (proj_e["r"] ** (1 + eps_e))
        proj_e["CMV_new"]   = proj_e["cost_d"]  * (proj_e["r"] ** eps_e)
        proj_e["MC_new"]    = proj_e["Rev_new"] - proj_e["CMV_new"]

        mc_new_e  = proj_e["MC_new"].sum()
        rev_new_e = proj_e["Rev_new"].sum()

        st.divider()
        st.markdown("### 📊 Resultado com os Novos Descontos")
        pr1, pr2, pr3, pr4 = st.columns(4)
        pr1.metric("Fat/dia projetado", fmt_brl_full(rev_new_e),
                   f"{(rev_new_e/rev_cur_e-1)*100:+.1f}% vs atual" if rev_cur_e > 0 else "—")
        pr2.metric("MC/dia projetada",  fmt_brl_full(mc_new_e),
                   f"{mc_new_e-mc_cur_e:+.2f} R$/dia vs atual")
        pr3.metric(f"Fat/dia vs {PERIODO_A}",  fmt_brl_full(rev_new_e - rev_ant_e),
                   f"{(rev_new_e/rev_ant_e-1)*100:+.1f}%" if rev_ant_e > 0 else "—")
        pr4.metric(f"MC/dia vs {PERIODO_A}",   fmt_brl_full(mc_new_e - mc_ant_e),
                   f"{(mc_new_e/mc_ant_e-1)*100:+.1f}%" if mc_ant_e > 0 else "—")

        st.divider()
        st.markdown("### 📈 Sensibilidade — pp Adicionais sobre os Δ Configurados")
        delta_range_e = np.linspace(0, 15, 201)
        mc_sens_e, rev_sens_e = [], []
        for _dd in delta_range_e:
            _mc = 0.0; _rev = 0.0
            for _, row in proj_e.iterrows():
                _new_d    = row["curr_desc"] - row["delta_pp"] - _dd
                _den      = max(1 + row["curr_desc"] / 100, 0.001)
                _r        = max((1 + _new_d / 100) / _den, 0.001)
                _rv       = row["d_vl_d"] * (_r ** (1 + eps_e))
                _cost_row = row["cost_d"] * (_r ** eps_e)
                _mc      += _rv - _cost_row
                _rev     += _rv
            mc_sens_e.append(float(_mc))
            rev_sens_e.append(float(_rev))

        idx_e  = int(np.argmax(mc_sens_e))
        adj_e  = float(delta_range_e[idx_e])
        mc_e   = mc_sens_e[idx_e]
        curva_e = pd.DataFrame({
            "pp adicionais": delta_range_e,
            "MC/dia R$":     mc_sens_e,
            "Fat/dia R$":    rev_sens_e,
        }).set_index("pp adicionais")
        st.markdown(f"**Ótimo com +{adj_e:.1f} pp adicionais** → MC = {fmt_brl_full(mc_e)}")
        st.line_chart(curva_e, color=["#4CAF50", "#2196F3"], height=240)

    st.caption("Modelo heurístico — sazonalidade e outros fatores não são capturados.")


# ── Rodapé ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"Dados até {DATA_FIM_D} · "
    f"Referência: {PERIODO_A} ({N_DIAS_A} dias úteis seg–sex) · "
    f"Atual: {PERIODO_D} ({N_DIAS_D} dias úteis, seg–sex) · "
    "Loja 08 GO"
)