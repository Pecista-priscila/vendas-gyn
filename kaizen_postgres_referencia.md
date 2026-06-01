# Kaizen Autopeças — Referência PostgreSQL

> Documento de uso interno para qualquer pessoa (ou agente Claude) que precise consultar o banco de dados da Kaizen.  
> Cobre: schemas, tabelas, colunas, joins, regras de negócio embutidas nos dados, armadilhas e padrões de query.  
> Última revisão: 2026-04-29

---

## 1. Como acessar o banco

O banco é acessado via MCP tool. Em sessões Claude/Cowork:

```
ToolSearch: select:mcp__7abdf5bc-da2c-4f94-b0d1-314dc8737601__execute_query
```

A tool aceita apenas queries `SELECT` (read-only). INSERT, UPDATE, DELETE e DDL são bloqueados.

---

## 2. Schemas principais

| Schema | Atualização | Quando usar |
|---|---|---|
| `"D-1"` | Diária — ETL roda à meia-noite | Análises históricas, relatórios de período fechado, métricas consolidadas. Padrão para a maioria das análises. |
| `"H-1"` | Horária — ETL roda a cada 60 min | Quando os dados precisam ser os mais recentes possíveis: estoque atual, pedidos feitos hoje, notas do dia. |
| `"compras"` | Próprio ciclo de atualização | Médias mensais e histórico de preços. Tabelas analíticas pré-calculadas. |
| `"ECOMM"` | Próprio ciclo | Vendas do Mercado Livre. |

**Regra prática:** se a pergunta contém "hoje", "agora" ou "última hora" → use `H-1`. Para qualquer outra análise → use `D-1`.

---

## 3. Lojas

| cd_loja | Nome | Região | Observações |
|---|---|---|---|
| `01` | PECISTA | DF | CD (Centro de Distribuição) + loja física. Também referenciada como "Pecista". **Representa apenas essa loja — não agrega as demais lojas do DF.** |
| `03` | KAIZEN ASA NORTE | DF | |
| `04` | KAIZEN CEILÂNDIA | DF | |
| `05` | KAIZEN GAMA | DF | |
| `06` | KAIZEN SOF | DF | |
| `07` | KAIZEN PLANALTINA | DF | |
| `08` | KAIZEN PARQUE OESTE | GO | Goiânia. |
| `10` | KAIZEN RECIFE | RE | Recife. |
| `VO` | VENDAS ONLINE | — | Loja virtual (ecommerce). Sem estoque físico. Recebe pedidos Marketplace. |

**Lojas do DF:** `01`, `03`, `04`, `05`, `06`, `07` — cada uma com seu próprio `cd_loja`. Filtrar por `cd_loja = '01'` retorna **somente** a Pecista, não o DF como um todo.  
**Lojas do GO:** `08`  
**Recife:** `10`

> ⚠️ **`cd_loja` identifica uma loja individual, nunca uma região.** Para agrupar por região via `cd_loja`, é preciso usar `IN` explicitando todas as lojas — ex: `cd_loja IN ('01','03','04','05','06','07')` para o DF completo. Não existe um código de `cd_loja` que represente "todas as lojas do DF".  
> O agrupamento regional existe apenas em `cd_tploja` (tributos) e `cd_centrod` (médias), conforme seção 4.

### Atenção: tabela `"D-1".lojas` tem colunas em MAIÚSCULAS

A tabela de cadastro de lojas é a única no banco com colunas em maiúsculas. Use aspas duplas:

```sql
SELECT "CD_LOJA", "LOJA" FROM "D-1".lojas
```

---

## 4. Mapeamento de regiões

Vários sistemas de código de região coexistem no banco. Não confundir:

| Contexto | DF | GO | Recife | Natureza |
|---|---|---|---|---|
| `cd_loja` | `'01'` a `'07'` (uma por loja) | `'08'` | `'10'` | **Individual** — identifica uma loja específica, nunca uma região |
| `cd_tploja` (tabela `prd_tipo` — tributos) | `'01'` | `'02'` | `'03'` | **Regional** — um código por região |
| `cd_centrod` (tabela `prd_cd` — médias regionais) | `01` | `08` | `10` | **Regional** — usa o código da loja-âncora da região |
| `regiao` / `uf` (tabelas no schema `compras`) | `'DF'` | `'GO'` | — | **Regional** — string de texto |

### Diferença crítica

`cd_loja` **nunca representa uma região inteira.** Filtrar `cd_loja = '01'` retorna apenas os dados da Pecista (loja 01 / CD de Brasília). Para cobrir o DF completo com `cd_loja`, é obrigatório listar todas as lojas:

```sql
WHERE cd_loja IN ('01', '03', '04', '05', '06', '07')   -- DF completo
WHERE cd_loja = '08'                                      -- GO
WHERE cd_loja = '10'                                      -- Recife
```

`cd_tploja` e `cd_centrod`, por outro lado, são campos de agrupamento regional — um único valor representa toda a região:

```sql
WHERE cd_tploja = '01'     -- todos os produtos tributados na regra do DF
WHERE cd_centrod = '01'    -- média regional do DF (equivale a todas as lojas DF)
```

Para cálculos de tributos (ICMS, ST, IPI) com `prd_tipo`, o join é por `cd_tploja`:
- DF → `cd_tploja = '01'`
- GO → `cd_tploja = '02'`
- Recife → `cd_tploja = '03'`

---

## 5. Alias de colunas — problema recorrente

O mesmo dado aparece com nomes diferentes em tabelas distintas. **Sempre verificar antes de fazer join.**

### Código do produto

| Alias | Tabelas que usam |
|---|---|
| `codpro` | `produto`, `prod_pco`, `compec`, `prd_tipo`, `prod_nfc`, `prod_noc`, `prd_loja` |
| `cod_pro` | `prod_ped`, `media_mensal_regiao`, `media_mensal_loja_recalc`, `historico_preco_mensal` |
| `cd_produto` | `prd_zero` (todas as variantes), `prd_cd`, `estoque`, `prod_ent`, `nfc_pec` |

Exemplo de join correto:
```sql
JOIN "D-1".prod_ped pp ON pp.cod_pro = pro.codpro        -- prod_ped usa cod_pro
JOIN "D-1".prd_zero z  ON z.cd_produto = pro.codpro      -- prd_zero usa cd_produto
```

### Código de loja

| Alias | Tabelas que usam |
|---|---|
| `cd_loja` | Maioria das tabelas transacionais: `prod_pco`, `compec`, `compra`, `prd_loja`, `estoque`, `prod_ent`, `entrada`, `pedido`, `prod_ped`, `venda`, `prd_zero`, `nfc_pec`, `prod_nfc`, `histoper` |
| `loja` | `media_mensal_loja_recalc` (schema `compras`) |
| `"CD_LOJA"` | `lojas` — atenção: maiúscula, requer aspas duplas |

### Código de fornecedor

| Alias | Tabelas que usam |
|---|---|
| `codfor` | `fornec`, `produto`, `prod_pco`, `compec`, `compra`, `prod_nfc`, `notacom`, `prod_noc` |
| `cd_fornece` | `entrada`, `prod_ent`, `nfc_pec` |

---

## 6. Catálogo de tabelas

### 6.1 Presentes em ambos `D-1` e `H-1`

| Tabela | Descrição | Chave(s) relevante(s) |
|---|---|---|
| `compec` | Cabeçalho dos pedidos de compra | `cd_loja`, `numnot`, `codfor` |
| `prod_pco` | Itens dos pedidos de compra | `cd_loja`, `numnot`, `codfor`, `codpro` |
| `compra` | Notas fiscais de compra cadastradas | `cd_loja`, `numnot`, `codfor`, `serie` |
| `prod_nfc` | Itens das notas fiscais de compra | `cd_loja`, `numnot`, `codfor`, `serie`, `codpro` |
| `prd_loja` | Situação atual do produto por loja (estoque, grid) | `cd_loja`, `codpro` |
| `prod_noc` | Itens de notas não conciliadas | `cd_loja`, `codfor`, `serie`, `numnot`, `codpro` |
| `nfc_pec` | Recebimento de produtos (notas chegadas) | `cd_loja`, `cd_fornece`, `sg_serie`, `nu_nota`, `cd_produto` |
| `estoque` | Histórico de movimentações de estoque | `cd_loja`, `cd_produto`, `dt_estoque` |
| `entrada` | Notas de devolução cadastradas | `cd_loja`, `sg_serie`, `nu_nota` |
| `prod_ent` | Itens das devoluções | `cd_loja`, `sg_serie`, `nu_nota`, `cd_produto` |
| `pedido` | Cabeçalho das vendas | `cd_loja`, `nu_nota`, `serie`, `codcli` |
| `venda` | Notas de venda (referência para devoluções) | `cd_loja`, `nu_nota`, `serie`, `codcli` |
| `cliente` | Cadastro de clientes | `codcli` |
| `fornec` | Cadastro de fornecedores | `codfor` |
| `vendedor` | Cadastro de vendedores/operadores | `codvend` |
| `prd_tipo` | Tributos por produto por região | `codpro`, `cd_tploja` |

### 6.2 Apenas em `D-1`

| Tabela | Descrição | Tamanho aprox. |
|---|---|---|
| `produto` | Cadastro de produtos | ~109K linhas |
| `lojas` | Cadastro de lojas | 9 linhas |
| `grupo` | Grupos de produtos | Pequena |
| `prd_cd` | Média mensal e dias de estoque por região | Média |
| `histoper` | Histórico de operações do sistema | ~890K linhas |
| `prd_zero` | Estoque zerado — loja 01 (Pecista) | ~570K linhas |
| `prd_zero_03` | Estoque zerado — loja 03 (Asa Norte) | — |
| `prd_zero_04` | Estoque zerado — loja 04 (Ceilândia) | — |
| `prd_zero_05` | Estoque zerado — loja 05 (Gama) | — |
| `prd_zero_06` | Estoque zerado — loja 06 (SOF) | — |
| `prd_zero_07` | Estoque zerado — loja 07 (Planaltina) | — |
| `prd_zero_08` | Estoque zerado — loja 08 (GO) | — |
| `prod_ped` | Itens das vendas (principal tabela de faturamento) | ~22M linhas |
| `data` | Calendário com marcação de dia útil | ~12.4K linhas |
| `notacom` | Informações de notas fiscais de compra | — |

> **Não existe `prd_zero_10`** (Recife não tem tabela de estoque zerado).

### 6.3 Schema `compras`

| Tabela | Descrição | Tamanho aprox. |
|---|---|---|
| `media_mensal_regiao` | Média mensal de vendas por região (DF/GO), mês a mês | Média |
| `media_mensal_loja_recalc` | Média mensal de vendas por loja, recalculada | ~68M linhas |
| `historico_preco_mensal` | Preço médio 90 dias por região, mês a mês | ~3.6M linhas |

### 6.4 Schema `ECOMM`

| Tabela | Descrição | Tamanho aprox. |
|---|---|---|
| `ml_dre_new` | Vendas do ecommerce Mercado Livre | ~395K linhas |

---

## 7. Detalhamento das tabelas mais usadas

### 7.1 `prod_ped` — Itens de venda (faturamento)

> A tabela mais usada em análises de revenue. ~22M linhas. **Sempre filtrar por `dt_emissao`.**

| Coluna | Tipo | Descrição |
|---|---|---|
| `cd_loja` | varchar | Código da loja |
| `nu_nota` | varchar | Número da nota fiscal |
| `serie` | varchar | Série da nota fiscal |
| `codcli` | varchar | Código do cliente |
| `cod_pro` | varchar | Código do produto (atenção: `cod_pro`, não `codpro`) |
| `codfor` | varchar | Código do fornecedor do produto |
| `codvde` | varchar | Código do vendedor |
| `dt_emissao` | timestamp | Data de emissão do pedido — **filtro obrigatório** |
| `qtde_ven` | numeric | Quantidade vendida |
| `preco` | numeric | Preço de venda unitário |
| `prc_com` | numeric | Preço de compra (custo) unitário |
| `vl_mc` | numeric | Margem de Contribuição em valor do item |
| `vl_cmv` | numeric | CMV do item |
| `tipped` | varchar | Tipo do pedido. Filtrar `tipped = 'V'` para vendas válidas |

**Cálculos derivados:**
- Faturamento do item: `qtde_ven * preco`
- CMV do item: `qtde_ven * prc_com`
- MC do item: `vl_mc` (coluna direta)
- Margem %: `vl_mc / (qtde_ven * preco) * 100`

### 7.2 `pedido` — Cabeçalho das vendas

> ~8M linhas. Complementa `prod_ped` com dados do pedido como um todo.

| Coluna | Tipo | Descrição |
|---|---|---|
| `cd_loja` | varchar | Código da loja |
| `nu_nota` | varchar | Número da nota |
| `serie` | varchar | Série |
| `codcli` | varchar | Código do cliente |
| `codvde` | varchar | Código do vendedor |
| `dt_emissao` | timestamp | Data de emissão |
| `valor_tot` | numeric | Valor total do pedido |
| `tot_custo` | numeric | Custo total do pedido |
| `cancelada` | varchar | `'N'` = ativa, `'S'` = cancelada. **Sempre filtrar `cancelada = 'N'`** |
| `tipped` | varchar | `'V'` = venda válida. **Sempre filtrar `tipped = 'V'`** |
| `forma_pgto` | varchar | Forma de pagamento. `'M'` = Marketplace (ecommerce) |

### 7.3 `cliente` — Cadastro de clientes

> ~230K linhas. Tabela de cadastro, não tem filtro de data necessário.

| Coluna | Tipo | Descrição |
|---|---|---|
| `codcli` | varchar | Código do cliente (chave primária) |
| `cliente` | varchar | Razão social / nome do cliente |
| `sigladesc` | varchar | Sigla da loja/região que atende o cliente. Ex: `'O'`, `'Q'` = lojas GO |
| `cidade` | varchar | Cidade |
| `estado` | varchar | UF do cliente. Ex: `'GO'`, `'DF'` |
| `cd_tipocli` | varchar | Tipo de cliente |
| `codarea` | varchar | Área do cliente. Excluir `codarea = '112'` em vendas líquidas |
| `codcid` | varchar | Código de cidade. Excluir `codcid = '0501'` em vendas líquidas |

**Siglas da loja GO:** `'O'` e `'Q'` — usadas para filtrar apenas clientes de Goiás via `sigladesc`.

### 7.4 `fornec` — Cadastro de fornecedores

> ~7.8K linhas.

| Coluna | Tipo | Descrição |
|---|---|---|
| `codfor` | varchar | Código do fornecedor (chave primária) |
| `fornec` | varchar | Razão social |
| `fantasia` | varchar | Nome fantasia |

### 7.5 `produto` — Cadastro de produtos

> ~109K linhas. Disponível apenas em `D-1`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `codpro` | varchar | Código do produto (chave primária) |
| `codfor` | varchar | Fornecedor principal do produto |
| `codgru` | varchar | Grupo do produto |
| `descri` | varchar | Descrição do produto |

### 7.6 `grupo` — Grupos de produtos

> Pequena. Disponível apenas em `D-1`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `codgru` | varchar | Código do grupo |
| `grupo` | varchar | Descrição do grupo |

**Grupos especiais a excluir em análises de produto físico:**
- `'3404'` — serviços / não é produto físico. Excluir de Venda Perdida, Compras, Chegou.
- `'0058'` — excluir especificamente na métrica Chegou.

### 7.7 `vendedor` — Cadastro de vendedores

| Coluna | Tipo | Descrição |
|---|---|---|
| `codvend` | varchar | Código do vendedor (chave primária) |
| `vendedor` | varchar | Nome do vendedor |

**Vendedores internos/sistema a excluir em vendas líquidas:** `'0100'`, `'0001'`, `'0006'`, `'2319'`

### 7.8 `prd_tipo` — Tributos por produto e região

> Tabela de precificação tributária. Join por `(codpro, cd_tploja)`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `codpro` | varchar | Código do produto |
| `cd_tploja` | varchar | Código do tipo de loja/região (`'01'`=DF, `'02'`=GO, `'03'`=Recife) |
| `p_compra` | numeric | Preço de compra |
| `pc_ipi` | numeric | Percentual de IPI |
| `pc_subtri` | numeric | Percentual de substituição tributária (ST) |
| `pc_royalt` | numeric | Percentual de royalties |

**Fórmula Pre Royal (preço com impostos):**
```sql
ROUND(
  ((p_compra * (1 + pc_ipi / 100)) * (1 + pc_subtri / 100)) + (pc_royalt / 100 * p_compra),
  2
) AS pre_royal
```

### 7.9 `prd_loja` — Situação atual do produto por loja

> ~1.1M linhas. Snapshot do estado atual. Disponível em `D-1` e `H-1`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `cd_loja` | varchar | Código da loja |
| `codpro` | varchar | Código do produto |
| `estoque` | numeric | Quantidade em estoque |
| `preco` | numeric | Preço de venda atual |
| `prc_com` | numeric | Preço de compra atual |

### 7.10 `prd_zero` (e variantes `_03` a `_08`) — Estoque zerado

> Períodos em que o produto ficou sem estoque. Uma tabela por loja.  
> Estrutura idêntica em todas as variantes.

| Coluna | Tipo | Descrição |
|---|---|---|
| `cd_loja` | varchar | Código da loja |
| `cd_produto` | varchar | Código do produto |
| `dt_zerou` | timestamp | Quando o estoque zerou |
| `dt_chegou` | timestamp | Quando o produto chegou. `NULL` = ainda zerado. |

```sql
-- Para consultar zerado em TODAS as lojas DF:
SELECT cd_loja, cd_produto, dt_zerou, dt_chegou FROM "D-1".prd_zero      WHERE cd_loja = '01'
UNION ALL
SELECT cd_loja, cd_produto, dt_zerou, dt_chegou FROM "D-1".prd_zero_03   WHERE cd_loja = '03'
UNION ALL
SELECT cd_loja, cd_produto, dt_zerou, dt_chegou FROM "D-1".prd_zero_04   WHERE cd_loja = '04'
UNION ALL
SELECT cd_loja, cd_produto, dt_zerou, dt_chegou FROM "D-1".prd_zero_05   WHERE cd_loja = '05'
UNION ALL
SELECT cd_loja, cd_produto, dt_zerou, dt_chegou FROM "D-1".prd_zero_06   WHERE cd_loja = '06'
UNION ALL
SELECT cd_loja, cd_produto, dt_zerou, dt_chegou FROM "D-1".prd_zero_07   WHERE cd_loja = '07'
```

### 7.11 `data` — Calendário

> ~12.4K linhas, cobre até 2032. Disponível apenas em `D-1`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `dt_emissao` | timestamp | Data do calendário |
| `dia_util` | text | `'Sim'` ou `'Não'` |

```sql
-- Contar dias úteis em março/2026:
SELECT COUNT(*) FROM "D-1".data
WHERE dt_emissao >= '2026-03-01' AND dt_emissao < '2026-04-01' AND dia_util = 'Sim'
-- Resultado: 22
```

### 7.12 `compec` — Cabeçalho dos pedidos de compra

> ~317K linhas. Disponível em `D-1` e `H-1`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `cd_loja` | varchar | Loja que fez o pedido |
| `numnot` | varchar | Número do pedido |
| `codfor` | varchar | Código do fornecedor |
| `emissao` | timestamp | Data de emissão do pedido |
| `diacom` | integer | Dias de compra considerados. Excluir `diacom = 3` em algumas métricas |
| `diaven` | integer | Dias de venda projetados. Excluir `diaven = 3` em algumas métricas |

### 7.13 `compra` — Notas fiscais de compra

> ~1.2M linhas. Disponível em `D-1` e `H-1`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `cd_loja` | varchar | Loja |
| `numnot` | varchar | Número da nota |
| `codfor` | varchar | Fornecedor |
| `serie` | varchar | Série |
| `emissao` | timestamp | Data de emissão |
| `cadastro` | timestamp | Data de cadastro no sistema. `NULL` = não cadastrada |
| `valortot` | numeric | Valor total da nota |
| `formapgto` | varchar | Forma de pagamento. `'V'` = padrão/à vista |
| `dt_chegou` | timestamp | Data de chegada da mercadoria |

### 7.14 `entrada` — Devoluções recebidas

| Coluna | Tipo | Descrição |
|---|---|---|
| `cd_loja` | varchar | Loja |
| `sg_serie` | varchar | Série da nota |
| `nu_nota` | varchar | Número da nota |
| `in_clifor` | varchar | `'C'` = devolução de cliente, `'F'` = devolução para fornecedor |
| `in_cancela` | varchar | `'N'` = ativa, `'S'` = cancelada |
| `cd_fornece` | varchar | Código do fornecedor |

**Para devoluções de venda:** filtrar `in_clifor = 'C'` e `in_cancela = 'N'`

### 7.15 `prod_ent` — Itens de devolução

| Coluna | Tipo | Descrição |
|---|---|---|
| `cd_loja` | varchar | Loja |
| `sg_serie` | varchar | Série |
| `nu_nota` | varchar | Número da nota |
| `cd_produto` | varchar | Código do produto |
| `cd_cfop` | varchar | CFOP da operação |
| `nu_origem` | varchar | Número da nota de venda original |
| `sg_origem` | varchar | Série da nota de venda original |
| `cd_cliente` | varchar | Código do cliente |
| `qt_item` | numeric | Quantidade devolvida |
| `vl_unitario` | numeric | Valor unitário |

**CFOPs a excluir** para isolar apenas devoluções de venda: `'1949'`, `'2949'`, `'1603'`

### 7.16 `nfc_pec` — Recebimento de produtos (notas chegadas)

| Coluna | Tipo | Descrição |
|---|---|---|
| `cd_loja` | varchar | Loja |
| `cd_fornece` | varchar | Fornecedor |
| `sg_serie` | varchar | Série |
| `nu_nota` | varchar | Número da nota |
| `nu_pedido` | varchar | Número do pedido de compra vinculado |
| `cd_produto` | varchar | Código do produto |
| `nu_item` | varchar | Item na nota |
| `qt_chegou` | bigint | Quantidade recebida |
| `dt_nota` | timestamp | Data da nota |

### 7.17 `notacom` — Informações complementares de notas de compra

| Coluna | Tipo | Descrição |
|---|---|---|
| `cd_loja` | varchar | Loja |
| `numnot` | varchar | Número da nota |
| `serie` | varchar | Série |
| `emissao` | timestamp | Data de emissão |
| `cadastro` | timestamp | Data de cadastro. `NULL` = não cadastrada |
| `codfor` | varchar | Fornecedor |
| `valortot` | numeric | Valor total |
| `formapgto` | varchar | Forma de pagamento |

### 7.18 `prod_noc` — Notas não conciliadas

| Coluna | Tipo | Descrição |
|---|---|---|
| `cd_loja` | varchar | Loja |
| `codfor` | varchar | Fornecedor |
| `serie` | varchar | Série |
| `numnot` | varchar | Número da nota |
| `codpro` | varchar | Código do produto |
| `qtde` | integer | Quantidade |
| `preco` | numeric | Preço |
| `emissao` | timestamp | Data de emissão |

---

## 8. Joins mais comuns

### 8.1 Vendas: `prod_ped` ↔ `pedido`

```sql
FROM "D-1".prod_ped pp
JOIN "D-1".pedido ped
  ON ped.nu_nota = pp.nu_nota
  AND ped.serie  = pp.serie
  AND ped.cd_loja = pp.cd_loja
  AND ped.codcli  = pp.codcli
```

### 8.2 Vendas ↔ produto ↔ fornecedor ↔ grupo

```sql
FROM "D-1".prod_ped pp
JOIN "D-1".cliente  c   ON c.codcli   = pp.codcli
JOIN "D-1".fornec   f   ON f.codfor   = pp.codfor
LEFT JOIN "D-1".produto pro ON pro.codpro = pp.cod_pro     -- atenção: cod_pro
LEFT JOIN "D-1".grupo   g   ON g.codgru   = pro.codgru
```

### 8.3 Devoluções: `prod_ent` ↔ `entrada` ↔ `venda`

```sql
FROM "D-1".prod_ent pe
JOIN "D-1".entrada e
  ON e.cd_loja  = pe.cd_loja
  AND e.sg_serie = pe.sg_serie
  AND e.nu_nota  = pe.nu_nota
JOIN "D-1".venda ven
  ON ven.cd_loja = pe.cd_loja
  AND ven.codcli  = pe.cd_cliente
  AND ven.serie   = pe.sg_origem
  AND ven.nu_nota = pe.nu_origem
```

### 8.4 Pedidos de compra: `prod_pco` ↔ `compec`

```sql
FROM "H-1".prod_pco pp
LEFT JOIN "H-1".compec c
  ON c.cd_loja = pp.cd_loja
  AND c.numnot  = pp.numnot
  AND c.codfor  = pp.codfor
```

### 8.5 Notas fiscais de compra: `compra` ↔ `prod_nfc`

```sql
FROM "H-1".compra a
JOIN "H-1".prod_nfc e
  ON e.numnot  = a.numnot
  AND e.codfor  = a.codfor
  AND e.serie   = a.serie
  AND e.cd_loja = a.cd_loja
```

### 8.6 Tributos por região: `produto` ↔ `prd_tipo`

```sql
FROM "D-1".produto p
JOIN "D-1".prd_tipo t ON t.codpro = p.codpro AND t.cd_tploja = '01'  -- '01'=DF, '02'=GO, '03'=RE
```

---

## 9. Fórmulas de métricas

### 9.1 Faturamento bruto
```sql
SUM(pp.qtde_ven * pp.preco)
```

### 9.2 CMV
```sql
SUM(pp.qtde_ven * pp.prc_com)
```

### 9.3 Margem de Contribuição (MC)
```sql
SUM(pp.vl_mc)
```

### 9.4 Margem de Contribuição %
```sql
ROUND(SUM(pp.vl_mc) / NULLIF(SUM(pp.qtde_ven * pp.preco), 0) * 100, 2)
```

### 9.5 Faturamento médio diário
```sql
ROUND(SUM(pp.qtde_ven * pp.preco) / {n_dias_uteis}.0, 2)
```

### 9.6 Variação percentual entre períodos (delta %)
```sql
ROUND((valor_periodo_d - valor_periodo_a) / NULLIF(valor_periodo_a, 0) * 100, 2)
```

### 9.7 Pre Royal (preço com impostos — `prd_tipo`)
```sql
ROUND(
  ((p_compra * (1 + pc_ipi / 100)) * (1 + pc_subtri / 100)) + (pc_royalt / 100 * p_compra),
  2
) AS pre_royal
```

---

## 10. Exclusões padrão por contexto

| Exclusão | Quando aplicar | Motivo |
|---|---|---|
| `cancelada = 'N'` | Todo filtro em `pedido` | Excluir pedidos cancelados |
| `tipped = 'V'` | Todo filtro em `pedido` e `prod_ped` | Apenas vendas válidas |
| `in_cancela = 'N'` | Todo filtro em `entrada` | Excluir devoluções canceladas |
| `in_clifor = 'C'` | Devoluções de venda | Excluir devoluções para fornecedor |
| `cd_cfop NOT IN ('1949','2949','1603')` | `prod_ent` para devoluções de venda | CFOPs que não são devolução de venda |
| `codgru <> '3404'` | Venda perdida, compras, chegou | Grupo de serviços, não produto físico |
| `codgru <> '0058'` | Métrica Chegou | Grupo específico excluído |
| `codvde NOT IN ('0100','0001','0006','2319')` | Vendas líquidas | Vendedores internos/sistema |
| `codarea <> '112'` | Vendas líquidas em `cliente` | Tipo de cliente excluído |
| `codcid <> '0501'` | Vendas líquidas em `cliente` | Cidade excluída |
| `forma_pgto = 'M'` → `cd_loja = 'VO'` | Vendas líquidas | Pedidos Marketplace atribuídos à loja virtual |
| `formapgto = 'V'` | Primeira Entrada | Notas de compra padrão (à vista) |
| `diacom <> 3` | Compras | Remover pedidos com dias de compra = 3 |
| `diaven <> 3` | Compras | Remover pedidos com dias de venda = 3 |

---

## 11. Dias úteis — referência

### Tabela `"D-1".data`

A forma oficial de contar dias úteis é via tabela `data`:

```sql
SELECT COUNT(*) FROM "D-1".data
WHERE dt_emissao::date BETWEEN '{data_ini}' AND '{data_fim}'
  AND dia_util = 'Sim'
```

### Valores de referência já calculados

| Período | Dias úteis | Observações |
|---|---|---|
| Mar/2026 (01–31) | 22 | Referência para comparação |
| Abr/2026 (06–15) | 8 | |
| Abr/2026 (06–16) | 9 | |
| Abr/2026 (06–17) | 10 | |
| Abr/2026 (06–23) | 13 | Tiradentes (21/04) já excluído |
| Abr/2026 (06–28) | 16 | Tiradentes (21/04) já excluído |

**Feriado confirmado em Abr/2026:** 21/04 (Tiradentes) — verificado por volume de pedidos (~57 pedidos vs ~4.500 em dias normais). Excluir do divisor ao calcular médias diárias.

---

## 12. Volume das tabelas — referência de performance

Sempre filtrar por data em tabelas grandes. Resultados sem filtro podem atingir dezenas de milhões de linhas e causar timeout.

| Tabela | Linhas aprox. | Filtro obrigatório |
|---|---|---|
| `compras.media_mensal_loja_recalc` | ~68M | `month_end` + `loja` + `cod_pro` |
| `"D-1".estoque` | ~32M | `dt_estoque` |
| `"D-1".prod_ped` | ~22M | `dt_emissao` |
| `"D-1".pedido` | ~8M | `dt_emissao` |
| `"D-1".venda` | ~7M | Período quando possível |
| `"H-1".prod_nfc` | ~5.3M | `emissao` |
| `"H-1".prod_pco` | ~3.7M | `emissao` |
| `compras.historico_preco_mensal` | ~3.6M | `mes_ref` ou `regiao` |
| `"H-1".compra` | ~1.2M | `emissao` ou `cadastro` |
| `"D-1".prd_loja` | ~1.1M | Snapshot — OK sem filtro de data |
| `"D-1".histoper` | ~890K | `dt_operaca` |
| `"D-1".prod_ent` | ~800K | `dt_emissao` |
| `"D-1".prd_zero` | ~570K | `dt_zerou` / `dt_chegou` |
| `ECOMM.ml_dre_new` | ~395K | `date_created` |
| `"H-1".compec` | ~317K | `emissao` |
| `"D-1".cliente` | ~230K | Cadastro — OK sem filtro |
| `"D-1".produto` | ~109K | Cadastro — OK sem filtro |
| `"D-1".data` | ~12.4K | Calendário — OK sem filtro |
| `"D-1".lojas` | 9 | — |
| `"D-1".fornec` | ~7.8K | Cadastro — OK sem filtro |

---

## 13. Padrões e templates de query

### 13.1 Template de análise de vendas por período (dois períodos comparativos)

```sql
SELECT 
    <dimensão>,                             -- ex: pp.codfor, c.sigladesc, pro.codgru
    ROUND(COALESCE(SUM(
        CASE WHEN pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
        THEN pp.qtde_ven * pp.preco END
    ), 0) / {n_dias_a}.0, 2)  AS a_vl_d,
    ROUND(COALESCE(SUM(
        CASE WHEN pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}'
        THEN pp.qtde_ven * pp.preco END
    ), 0) / {n_dias_d}.0, 2)  AS d_vl_d
FROM "D-1".prod_ped pp
JOIN "D-1".cliente c ON c.codcli = pp.codcli
WHERE c.estado = 'GO'        -- ou DF, ou sem filtro de estado
  AND (pp.dt_emissao::date BETWEEN '{ini_a}' AND '{fim_a}'
    OR pp.dt_emissao::date BETWEEN '{ini_d}' AND '{fim_d}')
GROUP BY <dimensão>
ORDER BY <dimensão>
```

### 13.2 Template de dias úteis para divisor

```sql
-- Contar dias úteis entre duas datas:
SELECT COUNT(*) AS n_dias
FROM "D-1".data
WHERE dt_emissao::date BETWEEN '2026-04-06' AND '2026-04-28'
  AND dia_util = 'Sim'
```

### 13.3 Template de Pre Royal por região

```sql
WITH precos AS (
  SELECT 'DF' AS regiao, codpro, p_compra, pc_ipi, pc_subtri, pc_royalt,
    ROUND(((p_compra * (1 + pc_ipi/100)) * (1 + pc_subtri/100)) + (pc_royalt/100 * p_compra), 2) AS pre_royal
  FROM "D-1".prd_tipo WHERE cd_tploja = '01'
  UNION ALL
  SELECT 'GO', codpro, p_compra, pc_ipi, pc_subtri, pc_royalt,
    ROUND(((p_compra * (1 + pc_ipi/100)) * (1 + pc_subtri/100)) + (pc_royalt/100 * p_compra), 2)
  FROM "D-1".prd_tipo WHERE cd_tploja = '02'
)
SELECT p.codpro, p.descri, pr.regiao, pr.pre_royal
FROM "D-1".produto p
JOIN precos pr ON pr.codpro = p.codpro
```

### 13.4 Template de volume de pedidos por dia (detectar feriados)

```sql
SELECT dt_emissao::date AS dia, COUNT(*) AS pedidos
FROM "D-1".pedido
WHERE dt_emissao::date BETWEEN '{data_ini}' AND '{data_fim}'
  AND cancelada = 'N' AND tipped = 'V'
GROUP BY 1 ORDER BY 1
-- Dias com < ~500 pedidos são suspeitos de feriado
```

---

## 14. Checklist antes de executar qualquer query

1. ✅ Há filtro de data nas tabelas transacionais (especialmente as com >1M linhas)?
2. ✅ O schema está correto — `D-1` para análise histórica, `H-1` para dados ao vivo?
3. ✅ Os nomes das colunas de produto estão corretos para cada tabela? (`codpro` vs `cod_pro` vs `cd_produto`)
4. ✅ Os nomes das colunas de fornecedor estão corretos? (`codfor` vs `cd_fornece`)
5. ✅ Os joins têm **todas** as chaves compostas necessárias? (muitas tabelas usam 3–4 colunas de chave)
6. ✅ As exclusões padrão para a métrica em questão foram aplicadas?
7. ✅ Para queries exploratórias sem template, há `LIMIT`?
8. ✅ Se usar a tabela `lojas`, as colunas estão entre aspas duplas (`"CD_LOJA"`, `"LOJA"`)?
9. ✅ O join `prod_ped → produto` está usando `pp.cod_pro = pro.codpro` (não `codpro = codpro`)?
10. ✅ Se for análise de ecommerce, a tabela `ECOMM.ml_dre_new` foi considerada junto com `prod_ped`?

---

## 15. Armadilhas conhecidas

| Armadilha | Descrição | Solução |
|---|---|---|
| **`cd_loja = '01'` não representa o DF** | `cd_loja` é sempre individual. `'01'` é só a Pecista/CD, não agrega as demais lojas do DF. Para o DF completo é necessário `IN ('01','03','04','05','06','07')` | Usar `IN` com todas as lojas da região. Agrupamento regional só existe em `cd_tploja` e `cd_centrod` |
| `lojas` com colunas maiúsculas | Única tabela com colunas em CAPS | Usar aspas duplas: `"CD_LOJA"` |
| `prod_ped.cod_pro` vs `produto.codpro` | Join entre as duas tabelas mais usadas tem alias diferente | `pp.cod_pro = pro.codpro` |
| Whitespace em campos varchar | Campos como `codcli`, `codfor` podem ter espaços no início/fim | Usar `.strip()` em Python ou `TRIM()` em SQL ao comparar |
| Feriados no divisor de dias | Tiradentes (21/04), Carnaval, etc. não estão automaticamente excluídos de divisores manuais | Verificar via tabela `data` ou por contagem de pedidos no dia |
| Multi-vendedor por cliente | Tabela `pedido` pode ter múltiplas linhas por cliente (um por vendedor) | Agregar por `codcli` usando o vendedor com maior volume |
| Ecommerce em `pedido` | Pedidos com `forma_pgto = 'M'` são do marketplace e têm `cd_loja = 'VO'` | Incluir ou excluir conforme o escopo da análise |
| `prd_zero` sem variante para Recife | Não existe `prd_zero_10` | Não fazer UNION com tabela inexistente |
| Chaves compostas em joins | Juntar `compra ↔ prod_nfc` exige 4 colunas (`numnot`, `codfor`, `serie`, `cd_loja`) | Sempre verificar PKs antes de fazer join |
| Timeout em tabelas grandes | `estoque` (~32M) e `prod_ped` (~22M) sem filtro de data causam timeout | Filtro de data sempre obrigatório |
