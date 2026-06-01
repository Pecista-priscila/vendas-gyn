"""
Kaizen GO — Geração de Dados (D-1)
====================================
Atualiza todos os CSVs do dashboard buscando dados até D-1 (ontem).
Execute uma vez por dia antes de abrir o Streamlit.

Requisitos:
    pip install psycopg python-dotenv

Configuração da conexão:
    Crie um arquivo .env na mesma pasta com:
        DB_HOST=...
        DB_PORT=5432
        DB_NAME=...
        DB_USER=...
        DB_PASSWORD=...
    OU defina a variável de ambiente DATABASE_URL=postgresql://user:pass@host:port/db

Período A (referência): Janeiro + Fevereiro + Março/2026 (01/01 a 31/03/2026)
Período D (atual):      Maio/2026 (01/05 a D-1)
"""

import os, json, csv, datetime
from pathlib import Path

# ─── Carregar variáveis de ambiente (.env opcional) ───────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

import psycopg

# ─── Diretório base (mesmo do script) ─────────────────────────────────────────
BASE = Path(__file__).parent

# ─── Conexão ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL") or (
    "host={} port={} dbname={} user={} password={}".format(
        os.environ.get("DB_HOST", "localhost"),
        os.environ.get("DB_PORT", "5432"),
        os.environ.get("DB_NAME", ""),
        os.environ.get("DB_USER", ""),
        os.environ.get("DB_PASSWORD", ""),
    )
)

# ─── Feriados em dias de semana em que a Kaizen não operou ────────────────────
FERIADOS: set = {
    datetime.date(2026, 1, 1),    # Ano Novo
    datetime.date(2026, 3, 3),    # Carnaval (terça)
    datetime.date(2026, 3, 4),    # Quarta de Cinzas
    datetime.date(2026, 4, 3),    # Sexta-Feira Santa
    datetime.date(2026, 4, 21),   # Tiradentes — confirmado (~57 pedidos)
    datetime.date(2026, 5, 1),    # Dia do Trabalho — confirmado (~18 pedidos)
}

def dias_uteis(ini: datetime.date, fim: datetime.date) -> int:
    """Conta dias úteis (seg-sex) excluindo FERIADOS entre ini e fim (inclusive)."""
    n = 0
    d = ini
    while d <= fim:
        if d.weekday() < 5 and d not in FERIADOS:
            n += 1
        d += datetime.timedelta(days=1)
    return n


def gerar(conn):
    hoje   = datetime.date.today()
    fim_d  = hoje - datetime.timedelta(days=1)          # D-1 = ontem
    while fim_d.weekday() >= 5:
        fim_d -= datetime.timedelta(days=1)

    # ── Período A: Janeiro + Fevereiro + Março/2026 ───────────────────────────
    ini_a  = datetime.date(2026, 1, 1)
    fim_a  = datetime.date(2026, 3, 31)

    # ── Período D: Maio/2026 até D-1 ─────────────────────────────────────────
    ini_d  = datetime.date(2026, 5, 1)

    # Se D-1 ainda está em abril ou antes, usa último dia útil de abril
    if fim_d < ini_d:
        print(f"⚠  D-1 ({fim_d}) ainda antes do início do período Maio ({ini_d}). Abortando.")
        return

    # Garante que fim_d não passa de 31/05
    fim_d = min(fim_d, datetime.date(2026, 5, 31))

    n_dias_a  = dias_uteis(ini_a, fim_a)
    n_dias_d  = dias_uteis(ini_d, fim_d)

    periodo_a = f"Jan-Mar {ini_a.year}"
    periodo_d = f"Mai {ini_d.strftime('%d')}-{fim_d.strftime('%d')}/{ini_d.year}"

    print(f"Período A: {periodo_a}  ({n_dias_a} dias úteis)  [{ini_a} → {fim_a}]")
    print(f"Período D: {periodo_d}  ({n_dias_d} dias úteis)  [{ini_d} → {fim_d}]")

    ini_a_s = ini_a.isoformat()
    fim_a_s = fim_a.isoformat()
    ini_d_s = ini_d.isoformat()
    fim_d_s = fim_d.isoformat()

    # Datas de feriados como lista SQL para usar em NOT IN
    feriados_sql = ", ".join(f"'{d.isoformat()}'" for d in FERIADOS)

    cur = conn.cursor()

    # ── 1. cli_forn.csv ───────────────────────────────────────────────────────
    print("\n⏳ Gerando cli_forn.csv …")
    cur.execute(f"""
        SELECT pp.codcli, c.sigladesc AS sigla, c.cliente AS nome,
               pp.codfor, f.fornec AS fornecedor, f.fantasia,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.qtde_ven * pp.preco END),0) / {n_dias_a}.0, 2) AS a_vl_d,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.qtde_ven * pp.prc_com END),0) / {n_dias_a}.0, 2) AS a_cmv_d,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.vl_mc END),0) / {n_dias_a}.0, 2) AS a_mc_d,
            COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.qtde_ven END),0) AS a_qtde,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.qtde_ven * pp.preco END),0) / {n_dias_d}.0, 2) AS d_vl_d,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.qtde_ven * pp.prc_com END),0) / {n_dias_d}.0, 2) AS d_cmv_d,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.vl_mc END),0) / {n_dias_d}.0, 2) AS d_mc_d,
            COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.qtde_ven END),0) AS d_qtde
        FROM "D-1".prod_ped pp
        JOIN "D-1".cliente c ON pp.codcli = c.codcli
        JOIN "D-1".fornec  f ON pp.codfor = f.codfor
        WHERE c.sigladesc IN ('O','Q','E','U') AND c.estado = 'GO'
          AND (pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
            OR (pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                AND pp.dt_emissao::date NOT IN ({feriados_sql})))
        GROUP BY pp.codcli, c.sigladesc, c.cliente, pp.codfor, f.fornec, f.fantasia
        HAVING COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.qtde_ven * pp.preco END),0) > 0
            OR COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              THEN pp.qtde_ven * pp.preco END),0) > 0
        ORDER BY pp.codcli, pp.codfor
    """)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    _write_csv(BASE / "cli_forn.csv", cols, rows)
    print(f"   ✓ {len(rows)} linhas")

    # ── 2. clientes.csv ───────────────────────────────────────────────────────
    print("⏳ Gerando clientes.csv …")
    cur.execute(f"""
        SELECT ped.codcli,
               c.sigladesc AS sigla, c.cliente AS nome,
               c.cidade, c.estado, c.cd_tipocli,
               COALESCE(v.vendedor, 'SEM VENDEDOR') AS carteira,
            ROUND(COALESCE(SUM(CASE WHEN ped.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN ped.valor_tot END),0), 2) AS a_vl,
            ROUND(COALESCE(SUM(CASE WHEN ped.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN ped.tot_custo END),0), 2) AS a_cmv,
            COALESCE(SUM(CASE WHEN ped.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN 1 END),0) AS a_ped,
            ROUND(COALESCE(SUM(CASE WHEN ped.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND ped.dt_emissao::date NOT IN ({feriados_sql})
                              THEN ped.valor_tot END),0), 2) AS d_vl,
            ROUND(COALESCE(SUM(CASE WHEN ped.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND ped.dt_emissao::date NOT IN ({feriados_sql})
                              THEN ped.tot_custo END),0), 2) AS d_cmv,
            COALESCE(SUM(CASE WHEN ped.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND ped.dt_emissao::date NOT IN ({feriados_sql})
                              THEN 1 END),0) AS d_ped
        FROM "D-1".pedido ped
        JOIN "D-1".cliente c ON ped.codcli = c.codcli
        LEFT JOIN "D-1".vendedor v ON ped.codvde = v.codvend
        WHERE c.estado = 'GO'
          AND ped.cancelada = 'N' AND ped.tipped = 'V'
          AND (ped.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
            OR (ped.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                AND ped.dt_emissao::date NOT IN ({feriados_sql})))
        GROUP BY ped.codcli, c.sigladesc, c.cliente, c.cidade, c.estado, c.cd_tipocli, v.vendedor
        ORDER BY ped.codcli
    """)
    rows_cli_raw = cur.fetchall()
    cols_cli_raw = [d[0] for d in cur.description]

    from collections import defaultdict
    clients = defaultdict(lambda: {
        "codcli":None,"sigla":None,"nome":None,"cidade":None,"estado":None,
        "cd_tipocli":None,"carteira":None,"_vl_max":0,
        "a_vl":0,"a_cmv":0,"a_ped":0,"d_vl":0,"d_cmv":0,"d_ped":0,
        "a_mc":0,"a_qtde":0,"d_mc":0,"d_qtde":0
    })
    col_idx = {c: i for i, c in enumerate(cols_cli_raw)}
    for row in rows_cli_raw:
        k   = row[col_idx["codcli"]]
        cl  = clients[k]
        cl["codcli"]     = k
        cl["sigla"]      = row[col_idx["sigla"]] or cl["sigla"]
        cl["nome"]       = row[col_idx["nome"]]
        cl["cidade"]     = row[col_idx["cidade"]]
        cl["estado"]     = row[col_idx["estado"]]
        cl["cd_tipocli"] = row[col_idx["cd_tipocli"]]
        cl["a_vl"]       = round(cl["a_vl"]  + float(row[col_idx["a_vl"]]  or 0), 2)
        cl["a_cmv"]      = round(cl["a_cmv"] + float(row[col_idx["a_cmv"]] or 0), 2)
        cl["a_ped"]      = cl["a_ped"]  + int(row[col_idx["a_ped"]]  or 0)
        cl["d_vl"]       = round(cl["d_vl"]  + float(row[col_idx["d_vl"]]  or 0), 2)
        cl["d_cmv"]      = round(cl["d_cmv"] + float(row[col_idx["d_cmv"]] or 0), 2)
        cl["d_ped"]      = cl["d_ped"]  + int(row[col_idx["d_ped"]]  or 0)
        vl = float(row[col_idx["a_vl"]] or 0)
        if vl >= cl["_vl_max"]:
            cl["carteira"]  = row[col_idx["carteira"]]
            cl["_vl_max"]   = vl

    cf_path = BASE / "cli_forn.csv"
    if cf_path.exists():
        with open(cf_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                k = r["codcli"]
                if k in clients:
                    clients[k]["a_mc"]   = round(clients[k]["a_mc"]   + float(r["a_mc_d"] or 0) * n_dias_a, 2)
                    clients[k]["a_qtde"] = clients[k]["a_qtde"] + int(float(r["a_qtde"] or 0))
                    clients[k]["d_mc"]   = round(clients[k]["d_mc"]   + float(r["d_mc_d"] or 0) * n_dias_d, 2)
                    clients[k]["d_qtde"] = clients[k]["d_qtde"] + int(float(r["d_qtde"] or 0))

    cols_out = ["codcli","sigla","nome","cidade","estado","cd_tipocli","carteira",
                "a_vl","a_cmv","a_mc","a_qtde","a_ped","d_vl","d_cmv","d_mc","d_qtde","d_ped"]
    with open(BASE / "clientes.csv", "w", newline="", encoding="utf-8") as out:
        w = csv.DictWriter(out, fieldnames=cols_out)
        w.writeheader()
        for cl in clients.values():
            w.writerow({c: cl.get(c, 0) for c in cols_out})
    print(f"   ✓ {len(clients)} clientes")

    # ── 3. fornecedores.csv ───────────────────────────────────────────────────
    print("⏳ Gerando fornecedores.csv …")
    cur.execute(f"""
        SELECT pp.codfor, f.fornec AS fornecedor, f.fantasia,
               c.sigladesc AS sigla,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.qtde_ven * pp.preco END),0), 2) AS a_vl,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.qtde_ven * pp.prc_com END),0), 2) AS a_cmv,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.vl_mc END),0), 2) AS a_mc,
            COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.qtde_ven END),0) AS a_qtde,
            COUNT(DISTINCT CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.codcli END) AS a_cli,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.qtde_ven * pp.preco END),0), 2) AS d_vl,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.qtde_ven * pp.prc_com END),0), 2) AS d_cmv,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.vl_mc END),0), 2) AS d_mc,
            COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.qtde_ven END),0) AS d_qtde,
            COUNT(DISTINCT CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.codcli END) AS d_cli
        FROM "D-1".prod_ped pp
        JOIN "D-1".cliente c ON pp.codcli = c.codcli
        JOIN "D-1".fornec  f ON pp.codfor = f.codfor
        WHERE c.estado = 'GO'
          AND (pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
            OR (pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                AND pp.dt_emissao::date NOT IN ({feriados_sql})))
        GROUP BY pp.codfor, f.fornec, f.fantasia, c.sigladesc
        HAVING COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.qtde_ven * pp.preco END),0) > 0
            OR COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              THEN pp.qtde_ven * pp.preco END),0) > 0
        ORDER BY pp.codfor, c.sigladesc
    """)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    _write_csv(BASE / "fornecedores.csv", cols, rows)
    print(f"   ✓ {len(rows)} linhas")

    # ── 4. grupos.csv ─────────────────────────────────────────────────────────
    print("⏳ Gerando grupos.csv …")
    cur.execute(f"""
        SELECT pro.codgru,
               COALESCE(g.grupo, 'SEM GRUPO') AS grupo,
               c.sigladesc AS sigla,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.qtde_ven * pp.preco END),0), 2) AS a_vl,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.qtde_ven * pp.prc_com END),0), 2) AS a_cmv,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.vl_mc END),0), 2) AS a_mc,
            COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.qtde_ven END),0) AS a_qtde,
            COUNT(DISTINCT CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.codcli END) AS a_cli,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.qtde_ven * pp.preco END),0), 2) AS d_vl,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.qtde_ven * pp.prc_com END),0), 2) AS d_cmv,
            ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.vl_mc END),0), 2) AS d_mc,
            COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.qtde_ven END),0) AS d_qtde,
            COUNT(DISTINCT CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              AND pp.dt_emissao::date NOT IN ({feriados_sql})
                              THEN pp.codcli END) AS d_cli
        FROM "D-1".prod_ped pp
        JOIN "D-1".cliente c ON pp.codcli = c.codcli
        LEFT JOIN "D-1".produto pro ON pp.cod_pro = pro.codpro
        LEFT JOIN "D-1".grupo   g   ON pro.codgru = g.codgru
        WHERE c.estado = 'GO'
          AND (pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
            OR (pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                AND pp.dt_emissao::date NOT IN ({feriados_sql})))
        GROUP BY pro.codgru, g.grupo, c.sigladesc
        HAVING COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a_s}' AND '{fim_a_s}'
                              THEN pp.qtde_ven * pp.preco END),0) > 0
            OR COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d_s}' AND '{fim_d_s}'
                              THEN pp.qtde_ven * pp.preco END),0) > 0
        ORDER BY pro.codgru, c.sigladesc
    """)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    _write_csv(BASE / "grupos.csv", cols, rows)
    print(f"   ✓ {len(rows)} linhas")

    # ── 5. for_tipo.csv ───────────────────────────────────────────────────────
    print("⏳ Gerando for_tipo.csv …")
    cur.execute("""
        SELECT tf.cd_fornece AS codfor, f.fornec AS fornecedor,
               tf.pc_acre_k, tf.pc_acre_o, tf.pc_acre_q, tf.pc_acre_n,
               tf.pc_acre_p, tf.pc_acre_b, tf.pc_acre_f, tf.pc_acre_e, tf.pc_acre_u
        FROM "D-1".for_tipo tf
        JOIN "D-1".fornec f ON tf.cd_fornece = f.codfor
        WHERE tf.cd_tploja = '02'
        ORDER BY tf.cd_fornece
    """)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    _write_csv(BASE / "for_tipo.csv", cols, rows)
    print(f"   ✓ {len(rows)} linhas")

    # ── 6. Salvar _config.json ────────────────────────────────────────────────
    cfg = {
        "n_dias_a":   n_dias_a,
        "data_ini_a": ini_a_s,
        "data_fim_a": fim_a_s,
        "periodo_a":  periodo_a,
        "n_dias_d":   n_dias_d,
        "data_ini_d": ini_d_s,
        "data_fim_d": fim_d_s,
        "periodo_d":  periodo_d,
        "atualizado_em": str(hoje),
    }
    with open(BASE / "_config.json", "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"\n✅ _config.json atualizado: {cfg}")


def _write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)


if __name__ == "__main__":
    print(f"🔌 Conectando ao banco …")
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            print("✓ Conectado.\n")
            gerar(conn)
        print("\n🎉 Todos os CSVs atualizados. Reinicie o Streamlit para recarregar.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        raise