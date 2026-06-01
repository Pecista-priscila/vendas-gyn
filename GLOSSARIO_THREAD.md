# Kaizen GO — Análise Reajuste: Glossário da Thread

> Documento de referência para continuidade em novas threads do Claude.  
> Gerado em: 2026-04-29  
> Última atualização dos dados: D-1 = 2026-04-28 (16 dias úteis Abril)

---

## 1. O que é esse projeto

Dashboard Streamlit chamado **"Kaizen GO — Análise Reajuste"** que compara a performance comercial da Kaizen Autopeças em dois períodos:

- **Período A (referência):** Março 2026 completo (01/03 a 31/03)
- **Período D (atual):** Abril 2026 acumulado (06/04 até D-1)

O objetivo é monitorar o impacto de um reajuste de preços (vigente a partir de 06/04/2026) sobre faturamento, CMV, margem de contribuição e volume de itens vendidos — comparando as médias diárias entre os dois períodos.

---

## 2. Localização dos arquivos

Todos os arquivos ficam em:
```
/sessions/sharp-optimistic-keller/mnt/Claude/kaizen_go_reajuste/
```

| Arquivo | Descrição |
|---|---|
| `app.py` | Aplicação Streamlit principal |
| `gerar_dados.py` | Script de atualização dos CSVs via banco de dados |
| `_config.json` | Parâmetros dinâmicos de período e divisores |
| `cli_forn.csv` | Vendas por cliente × fornecedor (médias diárias) |
| `clientes.csv` | Vendas totais por cliente (valores absolutos) |
| `fornecedores.csv` | Vendas totais por fornecedor × sigla (valores absolutos) |
| `grupos.csv` | Vendas totais por grupo de produto × sigla (valores absolutos) |

---

## 3. Estrutura do `_config.json`

```json
{
  "n_dias_a":   22,
  "data_ini_a": "2026-03-01",
  "data_fim_a": "2026-03-31",
  "periodo_a":  "Mar 01-31/2026",
  "n_dias_d":   16,
  "data_ini_d": "2026-04-06",
  "data_fim_d": "2026-04-28",
  "periodo_d":  "Abr 06-28/2026",
  "atualizado_em": "2026-04-29"
}
```

**Como calcular `n_dias_d`:** contar dias úteis (seg–sex) entre `data_ini_d` e `data_fim_d` (inclusive), excluindo feriados. Feriados a excluir já identificados:
- **21/04/2026 (Tiradentes):** confirmado com baixo volume de pedidos (~57 pedidos vs ~4.500 em dia normal). **Excluir do divisor.**

### Calendário de dias úteis Abril 2026 (06/04–28/04)

```
Abr 06 (Seg) ✓   Abr 07 (Ter) ✓   Abr 08 (Qua) ✓   Abr 09 (Qui) ✓   Abr 10 (Sex) ✓
Abr 11 (Sáb) ✗   Abr 12 (Dom) ✗
Abr 13 (Seg) ✓   Abr 14 (Ter) ✓   Abr 15 (Qua) ✓   Abr 16 (Qui) ✓   Abr 17 (Sex) ✓
Abr 18 (Sáb) ✗   Abr 19 (Dom) ✗
Abr 20 (Seg) ✓   Abr 21 (Ter) ✗ TIRADENTES
Abr 22 (Qua) ✓   Abr 23 (Qui) ✓   Abr 24 (Sex) ✓
Abr 25 (Sáb) ✗   Abr 26 (Dom) ✗
Abr 27 (Seg) ✓   Abr 28 (Ter) ✓

Total: 16 dias úteis
```

**Para atualizar no futuro:** continue contando a partir do Abr 29. Próximos dias úteis: 29/04 (Qua), 30/04 (Qui). Verificar se 01/05 (Dia do Trabalho) opera — se não operar, excluir.

---

## 4. Banco de dados PostgreSQL

### Conexão

O banco é acessado via MCP tool: **`mcp__7abdf5bc-da2c-4f94-b0d1-314dc8737601__execute_query`**

Essa tool aceita apenas queries `SELECT` (read-only). Para usar em nova thread, carregue com:
```
ToolSearch: select:mcp__7abdf5bc-da2c-4f94-b0d1-314dc8737601__execute_query
```

### Schema e tabelas utilizadas

Todas as tabelas ficam no schema **`"D-1"`** (com aspas duplas, é um nome de schema com hífen).

| Tabela | Colunas relevantes |
|---|---|
| `"D-1".prod_ped` | `codcli`, `codfor`, `cod_pro` (atenção: **cod_pro**, não codpro), `dt_emissao`, `qtde_ven`, `preco`, `prc_com`, `vl_mc` |
| `"D-1".pedido` | `codcli`, `codvde`, `dt_emissao`, `valor_tot`, `tot_custo`, `cancelada`, `tipped` |
| `"D-1".cliente` | `codcli`, `sigladesc` (sigla da loja), `cliente` (nome), `cidade`, `estado`, `cd_tipocli` |
| `"D-1".fornec` | `codfor`, `fornec` (razão social), `fantasia` |
| `"D-1".produto` | `codpro`, `codgru` |
| `"D-1".grupo` | `codgru`, `grupo` |
| `"D-1".vendedor` | `codvend`, `vendedor` |

### Filtros fixos de escopo

- **Estado:** `c.estado = 'GO'` — apenas clientes de Goiás
- **Siglas das lojas GO:** `O`, `Q` (usado apenas em `cli_forn.csv` — ver abaixo)
- **Pedidos válidos (tabela pedido):** `cancelada = 'N' AND tipped = 'V'`
- **Pedidos válidos (tabela prod_ped):** sem filtro de cancelamento — usa apenas dt_emissao e as siglas

---

## 5. Queries SQL para cada CSV

### Variáveis usadas nas queries

```
ini_a = '2026-03-01'
fim_a = '2026-03-31'
n_dias_a = 22
ini_d = '2026-04-06'
fim_d = '2026-04-28'   ← atualizar a cada novo dia útil
n_dias_d = 16          ← atualizar junto com fim_d
```

---

### 5.1 `cli_forn.csv` — Vendas por cliente × fornecedor (médias diárias)

> Escopo: apenas sigladesc IN ('O','Q') e estado = 'GO'  
> Valores: **já divididos** pelo número de dias (médias diárias por período)

```sql
SELECT pp.codcli, c.sigladesc AS sigla, c.cliente AS nome,
       pp.codfor, f.fornec AS fornecedor, f.fantasia,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.qtde_ven * pp.preco END),0) / {n_dias_a}.0, 2) AS a_vl_d,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.qtde_ven * pp.prc_com END),0) / {n_dias_a}.0, 2) AS a_cmv_d,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.vl_mc END),0) / {n_dias_a}.0, 2) AS a_mc_d,
    COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.qtde_ven END),0) AS a_qtde,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.qtde_ven * pp.preco END),0) / {n_dias_d}.0, 2) AS d_vl_d,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.qtde_ven * pp.prc_com END),0) / {n_dias_d}.0, 2) AS d_cmv_d,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.vl_mc END),0) / {n_dias_d}.0, 2) AS d_mc_d,
    COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.qtde_ven END),0) AS d_qtde
FROM "D-1".prod_ped pp
JOIN "D-1".cliente c ON pp.codcli = c.codcli
JOIN "D-1".fornec  f ON pp.codfor = f.codfor
WHERE c.sigladesc IN ('O','Q') AND c.estado = 'GO'
  AND (pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
    OR pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}')
GROUP BY pp.codcli, c.sigladesc, c.cliente, pp.codfor, f.fornec, f.fantasia
HAVING COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.qtde_ven * pp.preco END),0) > 0
    OR COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.qtde_ven * pp.preco END),0) > 0
ORDER BY pp.codcli, pp.codfor
```

**Colunas do CSV resultante:** `codcli, sigla, nome, codfor, fornecedor, fantasia, a_vl_d, a_cmv_d, a_mc_d, a_qtde, d_vl_d, d_cmv_d, d_mc_d, d_qtde`

---

### 5.2 `clientes.csv` — Vendas totais por cliente

> Escopo: todos os clientes GO (todos os sigladesc)  
> Valores: **totais absolutos** (app.py divide por n_dias internamente)  
> Fonte de MC e qtde: derivada do `cli_forn.csv` (pedido não tem MC por item)

**Query base (pedido):**
```sql
SELECT ped.codcli,
       c.sigladesc AS sigla, c.cliente AS nome,
       c.cidade, c.estado, c.cd_tipocli,
       COALESCE(v.vendedor, 'SEM VENDEDOR') AS carteira,
    ROUND(COALESCE(SUM(CASE WHEN ped.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN ped.valor_tot END),0), 2) AS a_vl,
    ROUND(COALESCE(SUM(CASE WHEN ped.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN ped.tot_custo END),0), 2) AS a_cmv,
    COALESCE(SUM(CASE WHEN ped.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN 1 END),0) AS a_ped,
    ROUND(COALESCE(SUM(CASE WHEN ped.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN ped.valor_tot END),0), 2) AS d_vl,
    ROUND(COALESCE(SUM(CASE WHEN ped.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN ped.tot_custo END),0), 2) AS d_cmv,
    COALESCE(SUM(CASE WHEN ped.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN 1 END),0) AS d_ped
FROM "D-1".pedido ped
JOIN "D-1".cliente c ON ped.codcli = c.codcli
LEFT JOIN "D-1".vendedor v ON ped.codvde = v.codvend
WHERE c.estado = 'GO'
  AND ped.cancelada = 'N' AND ped.tipped = 'V'
  AND (ped.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
    OR ped.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}')
GROUP BY ped.codcli, c.sigladesc, c.cliente, c.cidade, c.estado, c.cd_tipocli, v.vendedor
ORDER BY ped.codcli
```

**Pós-processamento em Python:** agregar por codcli (um cliente pode ter múltiplos vendedores — usar o vendedor com maior a_vl), depois preencher `a_mc`, `d_mc`, `a_qtde`, `d_qtde` multiplicando as médias do `cli_forn.csv` pelos respectivos `n_dias`.

**Colunas do CSV resultante:** `codcli, sigla, nome, cidade, estado, cd_tipocli, carteira, a_vl, a_cmv, a_mc, a_qtde, a_ped, d_vl, d_cmv, d_mc, d_qtde, d_ped`

---

### 5.3 `fornecedores.csv` — Vendas totais por fornecedor × sigla

> Escopo: todos os clientes GO  
> Valores: **totais absolutos** (app.py divide por n_dias)

```sql
SELECT pp.codfor, f.fornec AS fornecedor, f.fantasia,
       c.sigladesc AS sigla,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.qtde_ven * pp.preco END),0), 2) AS a_vl,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.qtde_ven * pp.prc_com END),0), 2) AS a_cmv,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.vl_mc END),0), 2) AS a_mc,
    COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.qtde_ven END),0) AS a_qtde,
    COUNT(DISTINCT CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.codcli END) AS a_cli,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.qtde_ven * pp.preco END),0), 2) AS d_vl,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.qtde_ven * pp.prc_com END),0), 2) AS d_cmv,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.vl_mc END),0), 2) AS d_mc,
    COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.qtde_ven END),0) AS d_qtde,
    COUNT(DISTINCT CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.codcli END) AS d_cli
FROM "D-1".prod_ped pp
JOIN "D-1".cliente c ON pp.codcli = c.codcli
JOIN "D-1".fornec  f ON pp.codfor = f.codfor
WHERE c.estado = 'GO'
  AND (pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
    OR pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}')
GROUP BY pp.codfor, f.fornec, f.fantasia, c.sigladesc
HAVING COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.qtde_ven * pp.preco END),0) > 0
    OR COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.qtde_ven * pp.preco END),0) > 0
ORDER BY pp.codfor, c.sigladesc
```

**Colunas do CSV resultante:** `codfor, fornecedor, fantasia, sigla, a_vl, a_cmv, a_mc, a_qtde, a_cli, d_vl, d_cmv, d_mc, d_qtde, d_cli`

---

### 5.4 `grupos.csv` — Vendas totais por grupo de produto × sigla

> Escopo: todos os clientes GO  
> Valores: **totais absolutos** (app.py divide por n_dias)  
> Join crítico: `prod_ped.cod_pro` → `produto.codpro` → `grupo.codgru`

```sql
SELECT pro.codgru,
       COALESCE(g.grupo, 'SEM GRUPO') AS grupo,
       c.sigladesc AS sigla,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.qtde_ven * pp.preco END),0), 2) AS a_vl,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.qtde_ven * pp.prc_com END),0), 2) AS a_cmv,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.vl_mc END),0), 2) AS a_mc,
    COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.qtde_ven END),0) AS a_qtde,
    COUNT(DISTINCT CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.codcli END) AS a_cli,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.qtde_ven * pp.preco END),0), 2) AS d_vl,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.qtde_ven * pp.prc_com END),0), 2) AS d_cmv,
    ROUND(COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.vl_mc END),0), 2) AS d_mc,
    COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.qtde_ven END),0) AS d_qtde,
    COUNT(DISTINCT CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.codcli END) AS d_cli
FROM "D-1".prod_ped pp
JOIN "D-1".cliente c ON pp.codcli = c.codcli
LEFT JOIN "D-1".produto pro ON pp.cod_pro = pro.codpro
LEFT JOIN "D-1".grupo   g   ON pro.codgru = g.codgru
WHERE c.estado = 'GO'
  AND (pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
    OR pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}')
GROUP BY pro.codgru, g.grupo, c.sigladesc
HAVING COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
                      THEN pp.qtde_ven * pp.preco END),0) > 0
    OR COALESCE(SUM(CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
                      THEN pp.qtde_ven * pp.preco END),0) > 0
ORDER BY pro.codgru, c.sigladesc
```

**Colunas do CSV resultante:** `codgru, grupo, sigla, a_vl, a_cmv, a_mc, a_qtde, a_cli, d_vl, d_cmv, d_mc, d_qtde, d_cli`

---

## 6. Como atualizar os dados (checklist para nova thread)

### Passo 1 — Determinar a nova `fim_d`

- `fim_d` = D-1 (ontem)
- Contar dias úteis entre `2026-04-06` e a nova `fim_d`, excluindo: fins de semana + 21/04 (Tiradentes) + quaisquer outros feriados identificados
- Verificar se há feriados suspeitos: rodar query de contagem de pedidos por dia e comparar com dias adjacentes

```sql
SELECT dt_emissao::date AS dia, COUNT(*) AS pedidos
FROM "D-1".pedido
WHERE dt_emissao::date BETWEEN '2026-04-06' AND '{nova_fim_d}'
  AND cancelada = 'N' AND tipped = 'V'
GROUP BY 1 ORDER BY 1
```

Dias com menos de ~500 pedidos são suspeitos de feriado e devem ser excluídos do divisor.

### Passo 2 — Rodar as 4 queries

Substituir `{fim_d}` e `{n_dias_d}` em todas as 4 queries da seção 5.  
Rodar via `mcp__7abdf5bc-da2c-4f94-b0d1-314dc8737601__execute_query`.

> ⚠️ Os resultados são grandes (>500k chars). O MCP salva em arquivo `.txt` em:  
> `/sessions/sharp-optimistic-keller/mnt/.claude/projects/-sessions-sharp-optimistic-keller/<session_id>/tool-results/`

### Passo 3 — Converter JSON → CSV com Python

Script base:
```python
import json, csv, collections
from pathlib import Path

# Caminhos
BASE_Q = Path("<caminho_dos_tool_results>")
OUT    = Path("/sessions/sharp-optimistic-keller/mnt/Claude/kaizen_go_reajuste")
N_DIAS_A = 22
N_DIAS_D = <novo_valor>

def load(filename):
    with open(BASE_Q / filename, encoding="utf-8") as f:
        return json.load(f)["result"]

def write_csv(path, rows, cols=None):
    cols = cols or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})

# 1. cli_forn.csv → escrever direto
cf_rows = load("arquivo_cli_forn.txt")
write_csv(OUT / "cli_forn.csv", cf_rows)

# 2. clientes.csv → agregação + MC de cli_forn
raw = load("arquivo_clientes_raw.txt")
clients = collections.defaultdict(lambda: {...})  # ver gerar_dados.py para lógica completa
# ... (ver seção 5.2 acima ou gerar_dados.py para a lógica de agregação completa)

# 3. fornecedores.csv → escrever direto
write_csv(OUT / "fornecedores.csv", load("arquivo_fornecedores.txt"))

# 4. grupos.csv → escrever direto
write_csv(OUT / "grupos.csv", load("arquivo_grupos.txt"))

# 5. _config.json
cfg = {
    "n_dias_a": N_DIAS_A, "data_ini_a": "2026-03-01", "data_fim_a": "2026-03-31",
    "periodo_a": "Mar 01-31/2026",
    "n_dias_d": N_DIAS_D, "data_ini_d": "2026-04-06", "data_fim_d": "<nova_fim_d>",
    "periodo_d": f"Abr 06-{nova_fim_d_dd}/2026", "atualizado_em": "<hoje>"
}
with open(OUT / "_config.json", "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
```

### Passo 4 — Reiniciar o Streamlit

Após salvar os CSVs e o `_config.json`, reiniciar o Streamlit para recarregar os dados.

---

## 7. Lógica de métricas no `app.py`

| Métrica | Cálculo no app |
|---|---|
| Faturamento/dia (A) | `a_vl / N_DIAS_A` (clientes/fornec/grupos) ou `a_vl_d` diretamente (cli_forn) |
| Faturamento/dia (D) | `d_vl / N_DIAS_D` (clientes/fornec/grupos) ou `d_vl_d` diretamente (cli_forn) |
| CMV/dia | mesma lógica com `a_cmv` / `d_cmv` |
| MC/dia | mesma lógica com `a_mc` / `d_mc` |
| Delta % | `(D - A) / A * 100` |
| Margem % | `MC / Faturamento * 100` |

**Atenção:** `cli_forn.csv` armazena valores **já divididos** (médias diárias). Os demais CSVs armazenam **totais** e o app divide internamente.

---

## 8. Estrutura do `app.py` — pontos críticos

### Carregamento de config (linhas ~20–41)
```python
_cfg_path = os.path.join(DATA_DIR, "_config.json")
if os.path.exists(_cfg_path):
    with open(_cfg_path, encoding="utf-8") as _f:
        _cfg = json.load(_f)
    N_DIAS_A  = int(_cfg.get("n_dias_a",  22))
    N_DIAS_D  = int(_cfg.get("n_dias_d",   8))
    PERIODO_A = _cfg.get("periodo_a", "Mar 01-31/2026")
    PERIODO_D = _cfg.get("periodo_d", "Abr 06-15/2026")
    DATA_FIM_D = _cfg.get("data_fim_d", "2026-04-15")
    ATUALIZDO  = _cfg.get("atualizado_em", "")
```

### Função `tree_table_html`
- Renderiza tabelas HTML com linhas expansíveis via `components.html`
- Sticky columns via classes CSS explícitas `.sc0`, `.sc1`... (não `nth-child` — quebra overflow)
- Parâmetros: `n_sticky` (qtde de colunas fixas), `sticky_widths` (largura em px de cada coluna fixa)
- Tab Clientes: `n_sticky=5, sticky_widths=[70,190,42,130,34]`
- Tabs Fornecedores/Grupos: `n_sticky=1, sticky_widths=[175]`

### Detail functions — fix de whitespace (crítico)
```python
# Tab 1 (clientes)
_cf_codcli = cf_df["codcli"].str.strip()
def detail_fn_1(row):
    cid = str(row.get("codcli", "")).strip()
    sub = cf_df[_cf_codcli == cid].sort_values("a_vl_d", ascending=False)
    return _det_tbl(sub.to_dict("records"), detail_cols_1)

# Tab 2 (fornecedores)
_cf_codfor = cf_df["codfor"].str.strip()
def detail_fn_2(row):
    fid = str(row.get("codfor", "")).strip()
    sub = cf_df[_cf_codfor == fid].sort_values("delta_pct", ascending=True)
    return _det_tbl(sub.to_dict("records"), detail_cols_2)
```
O `.str.strip()` é essencial — sem ele, o detalhe mostra "Sem dados" por mismatch de whitespace.

---

## 9. Bugs conhecidos e resoluções

| Bug | Causa | Solução |
|---|---|---|
| Scroll horizontal quebrado na Tab Clientes | CSS usava `nth-child` para sticky cols, incompatível com `overflow: auto` | Reescrito para classes explícitas `.sc0`, `.sc1`... |
| "Sem dados" ao expandir cliente | Mismatch de whitespace no codcli/codfor | `.str.strip()` em ambos os lados do filtro |
| Tiradentes inflando o divisor | 21/04 incluso nos dias úteis apesar de feriado | Excluído manualmente; n_dias_d=13 virou 16 após confirmação |
| Join grupos com `codpro` | `prod_ped` usa `cod_pro` (com underscore) | Corrigido para `pp.cod_pro = pro.codpro` |
| fornecedores/grupos com divisor no CSV | App esperava totais; CSV gerava médias | CSVs corrigidos para armazenar totais brutos |

---

## 10. Estado atual dos dados (2026-04-29)

| CSV | Linhas | Período D coberto |
|---|---|---|
| `cli_forn.csv` | 2.144 | Abr 06–28/2026 |
| `clientes.csv` | 2.941 | Abr 06–28/2026 |
| `fornecedores.csv` | 1.141 | Abr 06–28/2026 |
| `grupos.csv` | 3.102 | Abr 06–28/2026 |

`_config.json`: `n_dias_d=16`, `periodo_d="Abr 06-28/2026"`, `atualizado_em="2026-04-29"`
