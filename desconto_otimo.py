"""
Kaizen GO — Calculadora de Desconto Ótimo por Fornecedor
Lê o CSV/Excel exportado do simulador E e calcula o desconto que maximiza a MC.
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="Desconto Ótimo — Kaizen GO", page_icon="🎯", layout="wide")
st.title("🎯 Calculadora de Desconto Ótimo por Fornecedor")
st.caption("Faça upload do arquivo exportado do simulador (letra E ou O). Colunas esperadas: Fat/dia Antes, Fat/dia Atual, MC/dia Atual, Desc Atual %, ε Obs.")

# ── Upload do arquivo ─────────────────────────────────────────────────────────
arquivo = st.file_uploader("📂 Selecione o arquivo da análise de fornecedores", type=["csv", "xlsx"])

if arquivo is None:
    st.info("Aguardando upload do arquivo...")
    st.stop()

# ── Leitura do arquivo ────────────────────────────────────────────────────────
try:
    if arquivo.name.endswith('.xlsx'):
        df = pd.read_excel(arquivo, header=0)
    else:
        df = pd.read_csv(arquivo, sep=None, engine='python')
    df.columns = [c.lstrip('\ufeff').strip() for c in df.columns]
except Exception as e:
    st.error(f"Erro ao ler o arquivo: {e}")
    st.stop()

# ── Verificar colunas necessárias ─────────────────────────────────────────────
colunas_necessarias = ['Fornecedor', 'Fat/dia Atual', 'MC/dia Atual', 'Desc Atual %', 'ε Obs']
faltando = [c for c in colunas_necessarias if c not in df.columns]
if faltando:
    st.error(f"Colunas não encontradas: {faltando}")
    st.write("Colunas disponíveis:", df.columns.tolist())
    st.stop()

# ── Converter numéricos ───────────────────────────────────────────────────────
for col in ['Fat/dia Atual', 'MC/dia Atual', 'Desc Atual %', 'ε Obs', 'Fat/dia Antes', 'MC/dia Antes']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

df = df.dropna(subset=['Fornecedor', 'Fat/dia Atual', 'MC/dia Atual', 'Desc Atual %'])

# ── Sidebar: parâmetros ───────────────────────────────────────────────────────
st.sidebar.title("⚙️ Parâmetros")
usar_margem_minima = st.sidebar.checkbox("Aplicar margem mínima", value=False)
if usar_margem_minima:
    margem_minima = st.sidebar.number_input(
        "Margem mínima aceitável (%)", min_value=0.0, max_value=30.0, value=5.0, step=0.5,
        help="Descontos que levem a margem abaixo deste valor serão ignorados."
    )
else:
    margem_minima = -999.0  # sem restrição
eps_padrao = st.sidebar.slider(
    "ε padrão (quando não calculado)", min_value=-15.0, max_value=-0.1, value=-2.0, step=0.1,
    help="Elasticidade assumida para fornecedores sem ε calculado."
)
max_pp = st.sidebar.number_input(
    "Máximo de pp a testar", min_value=1.0, max_value=20.0, value=15.0, step=1.0,
    help="Testa de -X pp (reduzir desconto / subir preço) até +X pp (aumentar desconto)."
)

# ── Função de cálculo ─────────────────────────────────────────────────────────
def opt_delta(desc_atual, fat_d, mc_d, eps, margem_min_pct, max_pp=15.0, n=601):
    """
    Testa de -max_pp até +max_pp de delta de desconto.
    Positivo = mais desconto (preço cai), negativo = menos desconto (preço sobe).
    Retorna o delta que maximiza MC respeitando margem mínima.
    """
    custo_d = fat_d - mc_d
    if fat_d <= 0 or custo_d < 0 or eps >= 0:
        return 0.0, fat_d, mc_d

    # CORREÇÃO 1: testa de -max_pp até +max_pp (inclui redução de desconto)
    deltas = np.linspace(-max_pp, max_pp, n)
    denom = max(1.0 + desc_atual / 100.0, 0.001)

    melhor_delta = 0.0
    melhor_mc = mc_d
    melhor_fat = fat_d

    for delta in deltas:
        novo_desc = desc_atual - delta
        r = max((1.0 + novo_desc / 100.0) / denom, 0.001)
        fat_novo = fat_d * (r ** (1.0 + eps))
        mc_novo = fat_d * (r ** (1.0 + eps)) - custo_d * (r ** eps)
        margem_nova = mc_novo / fat_novo * 100 if fat_novo > 0 else 0

        if margem_nova >= margem_min_pct and mc_novo > melhor_mc:
            melhor_delta = delta
            melhor_mc = mc_novo
            melhor_fat = fat_novo

    return melhor_delta, melhor_fat, melhor_mc


# ── Calcular para cada fornecedor ─────────────────────────────────────────────
resultados = []
for _, row in df.iterrows():
    forn = row['Fornecedor']
    fat_d = row['Fat/dia Atual']
    mc_d = row['MC/dia Atual']
    desc_atual = row['Desc Atual %']
    eps = row['ε Obs'] if pd.notna(row['ε Obs']) else eps_padrao
    tem_eps = pd.notna(row['ε Obs'])

    margem_atual = mc_d / fat_d * 100 if fat_d > 0 else 0

        # Só calcula desconto ótimo se tiver ε real calculado
    if tem_eps:
        delta_otimo, fat_otimo, mc_otima = opt_delta(
            desc_atual, fat_d, mc_d, eps, margem_minima, max_pp
        )
    else:
        delta_otimo, fat_otimo, mc_otima = 0.0, fat_d, mc_d

    desc_otimo = desc_atual - delta_otimo
    margem_otima = mc_otima / fat_otimo * 100 if fat_otimo > 0 else 0
    ganho_mc = mc_otima - mc_d

    # Classificar ação sugerida
    if abs(delta_otimo) < 0.05:
        acao = "manter"
    elif delta_otimo > 0:
        acao = "↑ mais desconto"
    else:
        acao = "↓ menos desconto"

    resultados.append({
        'Fornecedor':        forn,
        'Fat/dia Antes': row.get('Fat/dia Antes', None),
        'Fat/dia Atual':     fat_d,
        'MC/dia Atual':      mc_d,
        'Margem Atual %':    margem_atual,
        'Desc Atual %':      desc_atual,
        'ε Obs':             row['ε Obs'] if tem_eps else None,
        'ε Usado':           eps,
        'Tem ε':             tem_eps,
        'Δ Desc Ótimo (pp)': delta_otimo,
        'Ação':              acao,
        'Desc Ótimo %':      desc_otimo,
        'Fat/dia Ótimo':     fat_otimo,
        'MC/dia Ótima':      mc_otima,
        'Margem Ótima %':    margem_otima,
        'Ganho MC/dia':      ganho_mc,
    })

res = pd.DataFrame(resultados)

# ── KPIs gerais ───────────────────────────────────────────────────────────────
st.divider()
st.markdown("### 📊 Resumo Geral")

GANHO_MIN = 1.0  # CORREÇÃO 2: só conta ganho real acima de R$1

mc_atual_total  = res['MC/dia Atual'].sum()
mc_otima_total  = res['MC/dia Ótima'].sum()
ganho_total     = mc_otima_total - mc_atual_total
fat_atual_total = res['Fat/dia Atual'].sum()
fat_otimo_total = res['Fat/dia Ótimo'].sum()
n_com_eps       = int(res['Tem ε'].sum())
# CORREÇÃO 3: conta só ganho > R$1
n_com_ganho     = int((res['Ganho MC/dia'] > GANHO_MIN).sum())
n_subir_preco   = int((res['Δ Desc Ótimo (pp)'] < -0.05).sum())
n_mais_desc     = int((res['Δ Desc Ótimo (pp)'] > 0.05).sum())

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("MC/dia Atual",        f"R$ {mc_atual_total:,.0f}".replace(",","."))
k2.metric("MC/dia Ótima",        f"R$ {mc_otima_total:,.0f}".replace(",","."),
          f"+R$ {ganho_total:,.0f}/dia".replace(",","."))
k3.metric("Fat/dia Atual",       f"R$ {fat_atual_total:,.0f}".replace(",","."))
k4.metric("Fornec. com ganho",   f"{n_com_ganho} de {len(res)}")
k5.metric("Sugerem ↓ desconto",  f"{n_subir_preco}")
k6.metric("Sugerem ↑ desconto",  f"{n_mais_desc}")

# ── Tabela de resultados ──────────────────────────────────────────────────────
st.divider()
st.markdown("### 📋 Desconto Ótimo por Fornecedor")
st.caption(f"Margem mínima: {margem_minima}% · ε padrão: {eps_padrao} (quando não calculado) · Intervalo testado: -{max_pp:.0f} pp a +{max_pp:.0f} pp")

disp = res[[
    'Fornecedor', 'Fat/dia Atual', 'MC/dia Atual', 'Margem Atual %',
    'Desc Atual %', 'ε Obs', 'Δ Desc Ótimo (pp)', 'Ação', 'Desc Ótimo %',
    'MC/dia Ótima', 'Margem Ótima %', 'Ganho MC/dia'
]].copy().sort_values('Ganho MC/dia', ascending=False)

def cor_ganho(v):
    try:
        fv = float(v)
        if fv > GANHO_MIN:   return 'background-color:#c6efce; color:#0b5e1e; font-weight:bold'
        if fv < -GANHO_MIN:  return 'background-color:#ffd6d6; color:#6b0000'
    except: pass
    return ''

def cor_acao(v):
    if v == '↓ menos desconto': return 'color:#006600; font-weight:bold'
    if v == '↑ mais desconto':  return 'color:#003399; font-weight:bold'
    return 'color:#888888'

fmt = {
    'Fat/dia Atual':      lambda v: f"R$ {v:,.0f}".replace(",",".") if pd.notna(v) else "—",
    'MC/dia Atual':       lambda v: f"R$ {v:,.0f}".replace(",",".") if pd.notna(v) else "—",
    'Margem Atual %':     lambda v: f"{v:.1f}%" if pd.notna(v) else "—",
    'Desc Atual %':       lambda v: f"{v:.1f}%" if pd.notna(v) else "—",
    'ε Obs':              lambda v: f"{v:.2f}" if pd.notna(v) else "—",
    'Δ Desc Ótimo (pp)':  lambda v: f"{v:+.1f} pp" if pd.notna(v) else "—",
    'Desc Ótimo %':       lambda v: f"{v:.1f}%" if pd.notna(v) else "—",
    'MC/dia Ótima':       lambda v: f"R$ {v:,.0f}".replace(",",".") if pd.notna(v) else "—",
    'Margem Ótima %':     lambda v: f"{v:.1f}%" if pd.notna(v) else "—",
    'Ganho MC/dia':       lambda v: f"R$ {v:+,.0f}".replace(",",".") if pd.notna(v) else "—",
}

st.dataframe(
    disp.style.format(fmt, na_rep="—")
        .map(cor_ganho, subset=['Ganho MC/dia'])
        .map(cor_acao,  subset=['Ação']),
    use_container_width=True,
    height=min(600, 60 + len(disp) * 35)
)

# ── Exportar Excel ────────────────────────────────────────────────────────────
st.divider()
st.markdown("### ⬇️ Exportar Resultado")

def gerar_excel(df_res):
    wb = Workbook()
    ws = wb.active
    ws.title = "Desconto Ótimo"
    cols = list(df_res.columns)

    for ci, col in enumerate(cols, 1):
        cell = ws.cell(row=1, column=ci, value=col)
        cell.font = Font(bold=True, color='FFFFFF', name='Arial', size=9)
        cell.fill = PatternFill('solid', start_color='2F4F8F')
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[1].height = 40

    for ri, row in enumerate(df_res.itertuples(index=False), 2):
        for ci, val in enumerate(row, 1):
            v = round(float(val), 2) if isinstance(val, float) and not pd.isna(val) else (val if pd.notna(val) else None)
            cell = ws.cell(row=ri, column=ci, value=v)
            cell.font = Font(name='Arial', size=9)
            cell.alignment = Alignment(horizontal='center')
            col_name = cols[ci - 1]
            if col_name == 'Ganho MC/dia' and isinstance(val, float) and not pd.isna(val):
                cor = 'C6EFCE' if val > GANHO_MIN else ('FFD6D6' if val < -GANHO_MIN else 'FFFFFF')
                cell.fill = PatternFill('solid', start_color=cor)

    ws.column_dimensions['A'].width = 20
    for ci in range(2, len(cols) + 1):
        ws.column_dimensions[get_column_letter(ci)].width = 14

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

excel_buf = gerar_excel(res)
st.download_button(
    "⬇️ Baixar Excel com desconto ótimo",
    excel_buf,
    "desconto_otimo_fornecedores.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)