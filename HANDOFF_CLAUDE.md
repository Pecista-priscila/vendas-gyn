# HANDOFF — Kaizen GO Análise Reajuste
## Documento de continuidade para Claude Cowork

> Este arquivo é o ponto de partida para uma nova sessão Claude continuar exatamente de onde a sessão anterior parou.
> Ao ingerir este documento, o Claude deve ter contexto suficiente para continuar sem perguntas.

**Projeto:** Análise do impacto do reajuste de preços em Goiânia (GYN) — Dashboard + Elasticidade  
**Status:** Análise de elasticidade ~90% concluída. Pendência: Opção C com regressão corrigida.  
**Data do último trabalho:** Maio/2026

---

## 1. CONTEXTO DO NEGÓCIO

A Kaizen Autopeças (Grupo Bueno) realizou um **reajuste de preços em massa** em Goiânia a partir de **06/04/2026**. O Gustavo Santos (Gerência de Precificação, Alocação e Aquisições) conduziu uma análise para entender:

1. Como o faturamento, CMV e margem se comportaram após o reajuste (dashboard de monitoramento)
2. Qual é a elasticidade-preço da demanda de autopeças por atacado em GYN (análise econométrica)

---

## 2. ARQUIVOS DO PROJETO

Todos os arquivos estão na **mesma pasta onde este documento está**. Aqui está o que cada um faz:

| Arquivo | O que é |
|---|---|
| `app.py` | Streamlit dashboard (comparativo Março vs Abril, médias diárias) |
| `gerar_dados.py` | Script Python de atualização dos CSVs via banco PostgreSQL |
| `_config.json` | Parâmetros de período (datas, n_dias) lidos pelo app |
| `requirements.txt` | `streamlit>=1.32.0`, `pandas>=2.0.0` |
| `cli_forn.csv` | Vendas diárias por cliente × fornecedor (clientes O e Q de GO) |
| `clientes.csv` | Vendas totais por cliente GO |
| `fornecedores.csv` | Vendas totais por fornecedor × sigla de loja GO |
| `grupos.csv` | Vendas totais por grupo de produto × sigla de loja GO |
| `elasticidade.csv` | Dados por fornecedor-cliente usados na análise de elasticidade Opção C |
| `for_tipo.csv` | Tabela auxiliar de tipo de fornecedor (usada no app, aba de fornecedores) |
| `GLOSSARIO_THREAD.md` | **Referência técnica completa**: todas as queries SQL, lógica de atualização, bugs resolvidos |

Fora dessa pasta, existe também:
- `../kaizen_postgres_referencia.md` — referência do banco PostgreSQL da Kaizen (schemas, tabelas, joins, pitfalls)

---

## 3. BANCO DE DADOS

- Schema: `"D-1"` (com aspas duplas — o nome tem hífen)
- Acesso em Cowork: `ToolSearch: select:mcp__7abdf5bc-da2c-4f94-b0d1-314dc8737601__execute_query`
- Modo: somente SELECT (read-only)

**Tabelas usadas:**

| Tabela | Colunas-chave |
|---|---|
| `"D-1".prod_ped` | `codcli, codfor, cod_pro` (**underscore**, não confundir com `codpro`), `dt_emissao, qtde_ven, preco, prc_com, vl_mc` |
| `"D-1".pedido` | `codcli, codvde, dt_emissao, valor_tot, tot_custo, cancelada, tipped` |
| `"D-1".cliente` | `codcli, sigladesc, cliente, cidade, estado, cd_tipocli` |
| `"D-1".fornec` | `codfor, fornec, fantasia` |
| `"D-1".produto` | `codpro, codgru` |
| `"D-1".grupo` | `codgru, grupo` |

**Filtros obrigatórios:**
- Pedidos válidos em `pedido`: `cancelada = 'N' AND tipped = 'V'`
- Escopo GO: `c.estado = 'GO'` ou `cd_loja = '08'`
- **Excluir I8000**: `codcli <> 'I8000'` — DISTRIBUIDORA KAIZEN LTDA é entidade interna que faz transferências bulk (R$783K em 17/04, R$368K em 21/04). Sem essa exclusão, o faturamento de Abril fica inflado em ~R$1,2M e os cálculos de elasticidade ficam com sinal positivo (errado).

**Lojas:**
- `cd_loja = '08'` → Kaizen Parque Oeste (GYN)
- `cd_loja = '01'` → APENAS a Pecista (CD de BSB) — não representa todo o DF

---

## 4. PERÍODOS E DIAS ÚTEIS

| Parâmetro | Valor atual |
|---|---|
| Período A (referência) | Mar 01–31/2026 (`n_dias_a = 22`) |
| Período D (reajuste) | Abr 06–28/2026 (`n_dias_d = 16`) |
| Início do reajuste | 06/04/2026 |
| D-1 atual | 28/04/2026 |

**Feriados confirmados (excluídos do divisor):**
- 03/04/2026 — Sexta-Feira Santa (confirmado via volume ~0 de pedidos)
- 21/04/2026 — Tiradentes (confirmado via ~57 pedidos vs ~4.500 em dia normal)

O `gerar_dados.py` já tem o Tiradentes no set `FERIADOS`. Para atualizar para novas datas, basta rodar o script — ele calcula D-1 automaticamente.

---

## 5. DASHBOARD STREAMLIT — COMO RODAR E ATUALIZAR

```bash
# Instalar dependências
pip install streamlit pandas psycopg python-dotenv

# Criar .env com credenciais do banco (pedir para Gustavo ou TI)
# DB_HOST=... DB_PORT=5432 DB_NAME=... DB_USER=... DB_PASSWORD=...

# Atualizar dados (roda queries no banco, gera os CSVs)
python gerar_dados.py

# Rodar o dashboard
streamlit run app.py
```

**Arquitetura do app.py:**
- Lê `_config.json` para N_DIAS_A, N_DIAS_D, rótulos de período
- Carrega os 4 CSVs + `for_tipo.csv` via `@st.cache_data`
- CSVs de `clientes/fornecedores/grupos` armazenam **totais** — o app divide por N_DIAS internamente
- `cli_forn.csv` armazena **médias diárias** — o app usa diretamente
- Tabelas expansíveis via `tree_table_html()` — sticky columns com classes explícitas `.sc0`, `.sc1` (não `nth-child` — quebra overflow)
- `.str.strip()` obrigatório nos joins por `codcli`/`codfor` — sem isso, detalhe mostra "Sem dados"

---

## 6. ANÁLISE DE ELASTICIDADE — ESTADO COMPLETO

### Contexto da análise

O Gustavo queria um único número: **a elasticidade-preço da demanda de autopeças em GYN**.

Dados base:
- Loja: `cd_loja = '08'` (Kaizen Parque Oeste)
- Período A: Mar/2026 completo — Período D: Abr 06–28/2026
- Exclusão: `codcli <> 'I8000'`
- Faturamento A (ex-I8000): R$6,26M | Faturamento D (ex-I8000): R$5,43M → Δ = -13,2%

### Sigladesc relevantes

| Sigla | Perfil |
|---|---|
| `O` | Revendedores/balconistas GO — maior volume |
| `Q` | Distribuidores GO |
| `E`, `U`, `N` | Clientes com precificação diferenciada (desconto negociado) — mais sensíveis a preço |

---

### OPÇÃO A — Elasticidade Agregada (Arc Elasticity)

**Cálculo:**
- Preço médio A = Faturamento_A / Qtde_A → Preço médio D = Faturamento_D / Qtde_D
- ΔP% = (P_D - P_A) / P_A × 100
- ΔQ% = (Q_D - Q_A) / Q_A × 100
- Ed = ΔQ% / ΔP%

**Resultados (todos os clientes GO, ex-I8000, n_dias_a=22, n_dias_d=16):**

| Cenário | ΔP% | ΔQ% | Ed |
|---|---|---|---|
| Todos os clientes | +7,73% | -15,94% | **-2,06** |
| Sem diferenciados | +7,61% | -15,62% | **-2,05** |
| Só diferenciados | +8,15% | -16,72% | **-2,05** |

**⚠️ Limitação crítica:** O número é distorcido pelo efeito-mix. Óleo de motor caiu -47,3% em volume — não por causa do preço, mas por outros fatores (sazonalidade, abastecimento). Isso contamina o ΔQ% agregado. **Não usar este número para decisões sem ajuste.**

---

### OPÇÃO B — Mediana por Produto

**Metodologia:** Para cada combinação produto × período com ≥5 unidades em ambos os períodos, calcular Ed individual. Tomar mediana. Isso neutraliza o efeito-mix.

**Resultados:**

| Cenário | Mediana Ed | N produtos |
|---|---|---|
| Todos | **-0,75** | ~1.200 |
| Sem diferenciados (ex O/Q/E/U/N) | **-0,72** | ~800 |
| Só diferenciados (O/Q/E/U/N) | **-0,99** | ~400 |

---

### OPÇÃO C — Regressão WLS Entre Fornecedores (INCOMPLETA — PENDÊNCIA PRINCIPAL)

**Metodologia:** Cada fornecedor teve um ΔP% diferente (alguns aumentaram +15%, outros +3%). Isso cria variação cross-section que permite estimar o efeito puro do preço.

Modelo:
```
ΔQ%_i = α + β × ΔP%_i + ε_i
```
Onde w_i = faturamento no Período A (peso da regressão WLS).

**Resultados da regressão livre (95 fornecedores):**
- β = **-0,5367** (t = -2,68, p < 0,01)
- α = **-8,10%**
- R² = 0,122
- ΔP% médio ponderado = **+7,97%**
- ΔQ% médio ponderado = **-14,07%**

**Problema identificado — intercepto não é sazonalidade pura:**

O Gustavo identificou que α = -8,1% não é a sazonalidade real. A regressão absorveu parte do efeito médio do preço no intercepto:

```
α = S_real + β × ΔP%_médio
-8,10% = S_real + (-0,5367 × 7,97%)
-8,10% = S_real - 4,28%
S_implícito = -3,82%
```

Isso significa que β = -0,54 **subestima** a elasticidade real, porque parte da queda de demanda causada pelo preço ficou capturada no α.

**Solução — Regressão Corrigida (PENDENTE):**

Com a sazonalidade real S conhecida, roda-se a regressão sem intercepto sobre ΔQ_adj:

```python
# Dados disponíveis no elasticidade.csv (colunas: codfor, delta_P_pct, delta_Q_pct, peso)
import numpy as np, pandas as pd

df = pd.read_csv("elasticidade.csv")

# Calcular ΔP% e ΔQ% por fornecedor (agregados, ponderados por receita)
# (o elasticidade.csv tem por cli×forn — precisar agregar por fornecedor)
# Pesos = faturamento período A por fornecedor

S = <VALOR_FORNECIDO_PELO_GUSTAVO>  # ex: -0.03 para -3%

DP = df_forn["delta_P_pct"].values / 100   # já em decimal
DQ = df_forn["delta_Q_pct"].values / 100
W  = df_forn["peso_a"].values               # faturamento março por fornecedor

DQ_adj = DQ - S                             # remove sazonalidade
beta_adj = np.sum(W * DP * DQ_adj) / np.sum(W * DP**2)  # WLS sem intercepto
print(f"β ajustado = {beta_adj:.4f}")
```

**Tabela de sensibilidade (já calculada):**

| S real | β ajustado | Interpretação |
|---|---|---|
| -1% | **-1,20** | Levemente elástico |
| -2% | **-1,15** | Levemente elástico |
| -3% | **-1,11** | Próximo à unitária |
| -4% | **-1,06** | Próximo à unitária |
| -5% | **-1,02** | Quase unitária |
| -6% | **-0,97** | Quase inelástico |

**Próxima ação:** Confirmar com Gustavo qual é a sazonalidade real e calcular β_final.

---

### Resumo consolidado das três opções

| Método | Resultado | Confiabilidade |
|---|---|---|
| A — Agregado | Ed = -2,05 | Baixa (contaminado por mix) |
| B — Mediana produto | Ed = -0,72 a -0,99 | Média (sazonalidade não eliminada) |
| C — Regressão corrigida | Ed = -0,97 a -1,20 | Alta (depende do S fornecido pelo Gustavo) |

**Conclusão provável:** A demanda de autopeças por atacado em GYN é **próxima à unitária** (Ed ≈ -1,0). O reajuste de +8% gerou queda de demanda de ~8%, resultando em receita aproximadamente neutra. Clientes com precificação diferenciada são levemente mais sensíveis.

---

## 7. QUERIES SQL USADAS (resumo — ver GLOSSARIO_THREAD.md para versão completa)

### Verificar feriados suspeitos
```sql
SELECT dt_emissao::date AS dia, COUNT(*) AS pedidos
FROM "D-1".pedido
WHERE dt_emissao::date BETWEEN '2026-04-06' AND '2026-04-30'
  AND cancelada = 'N' AND tipped = 'V'
GROUP BY 1 ORDER BY 1
```

### Faturamento diário de GYN (ex-I8000) — validação
```sql
SELECT dt_emissao::date AS dia,
       SUM(pp.qtde_ven * pp.preco) AS faturamento
FROM "D-1".prod_ped pp
JOIN "D-1".cliente c ON pp.codcli = c.codcli
WHERE c.cd_loja = '08'
  AND pp.codcli <> 'I8000'
  AND pp.dt_emissao::date BETWEEN '2026-04-06' AND '2026-04-28'
GROUP BY 1 ORDER BY 1
```

### Dados para Opção C (variação por fornecedor)
```sql
SELECT pp.codfor, f.fornec, f.fantasia,
    SUM(CASE WHEN pp.dt_emissao::date BETWEEN '2026-03-01' AND '2026-03-31'
        THEN pp.qtde_ven * pp.preco END) / 22.0 AS rec_a_dia,
    SUM(CASE WHEN pp.dt_emissao::date BETWEEN '2026-04-06' AND '2026-04-28'
        THEN pp.qtde_ven * pp.preco END) / 16.0 AS rec_d_dia,
    AVG(CASE WHEN pp.dt_emissao::date BETWEEN '2026-03-01' AND '2026-03-31'
        THEN pp.preco END) AS preco_medio_a,
    AVG(CASE WHEN pp.dt_emissao::date BETWEEN '2026-04-06' AND '2026-04-28'
        THEN pp.preco END) AS preco_medio_d,
    SUM(CASE WHEN pp.dt_emissao::date BETWEEN '2026-03-01' AND '2026-03-31'
        THEN pp.qtde_ven END) / 22.0 AS qtde_a_dia,
    SUM(CASE WHEN pp.dt_emissao::date BETWEEN '2026-04-06' AND '2026-04-28'
        THEN pp.qtde_ven END) / 16.0 AS qtde_d_dia
FROM "D-1".prod_ped pp
JOIN "D-1".cliente c ON pp.codcli = c.codcli
JOIN "D-1".fornec f ON pp.codfor = f.codfor
WHERE c.cd_loja = '08'
  AND pp.codcli <> 'I8000'
  AND (pp.dt_emissao::date BETWEEN '2026-03-01' AND '2026-03-31'
    OR pp.dt_emissao::date BETWEEN '2026-04-06' AND '2026-04-28')
GROUP BY pp.codfor, f.fornec, f.fantasia
HAVING SUM(CASE WHEN pp.dt_emissao::date BETWEEN '2026-03-01' AND '2026-03-31'
    THEN pp.qtde_ven * pp.preco END) > 0
ORDER BY rec_a_dia DESC NULLS LAST
```

---

## 8. PARA O CLAUDE QUE VAI CONTINUAR — CHECKLIST DE BOOT

Ao receber este documento numa nova sessão Cowork, faça:

1. **Confirmar arquivos**: verificar que `app.py`, `gerar_dados.py`, `_config.json`, `elasticidade.csv` e os 4 CSVs estão na mesma pasta
2. **Confirmar acesso ao banco**: `ToolSearch: select:mcp__7abdf5bc-da2c-4f94-b0d1-314dc8737601__execute_query`
3. **Leia o GLOSSARIO_THREAD.md** para detalhes de SQL e lógica de atualização
4. **Leia o kaizen_postgres_referencia.md** para estrutura completa do banco
5. **Tarefa pendente**: perguntar ao usuário qual é a estimativa de sazonalidade S para Abril vs Março em GYN e calcular `β_adj = Σ(W × ΔP × (ΔQ - S)) / Σ(W × ΔP²)`

---

## 9. CONTATOS E RESPONSÁVEL

- **Gustavo Santos** — gustavo@grupobueno.com — é quem tem o número de sazonalidade e o contexto de negócio
- Credenciais do banco PostgreSQL: pedir via TI ou ao Gustavo
