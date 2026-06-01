# Handoff — Kaizen GO Análise Reajuste
**Projeto:** Dashboard de monitoramento do impacto do reajuste de preços em Goiânia  
**Preparado por:** Gustavo Santos (Gerência de Precificação, Alocação e Aquisições)  
**Data:** Maio/2026  
**Para:** Analista responsável pela continuidade

---

## 1. O que é esse projeto e por que ele existe

A Kaizen Autopeças realizou um **reajuste de preços em massa na praça de Goiânia (GYN)** a partir de **06 de abril de 2026**. O objetivo desse projeto é monitorar — com dados reais do ERP — o que aconteceu com:

- **Faturamento** — quanto vendemos em média por dia útil
- **CMV** — custo da mercadoria vendida
- **Margem de Contribuição (MC)** — faturamento menos CMV
- **Volume** — quantidade de itens vendidos

A comparação é sempre **Março/2026 (referência)** vs **Abril/2026 a partir do dia 06 (período do reajuste)**, usando **médias diárias de dias úteis** para ser uma comparação justa (Março teve 22 dias úteis; Abril começou a ser monitorado a partir do dia 6).

Além do dashboard de monitoramento, foi realizada uma **análise de elasticidade-preço da demanda** para entender se os clientes de GYN são sensíveis a aumento de preço — ou seja, se vendemos menos quando preço sobe e por quanto.

---

## 2. Estrutura de arquivos do projeto

Todo o projeto está na pasta:
```
/sessions/sharp-optimistic-keller/mnt/Claude/kaizen_go_reajuste/
```

| Arquivo | O que é |
|---|---|
| `app.py` | Aplicação Streamlit (dashboard interativo) |
| `gerar_dados.py` | Script Python que busca dados do banco e gera os CSVs |
| `_config.json` | Parâmetros dos períodos (datas, dias úteis) — lido pelo app |
| `requirements.txt` | Dependências Python do Streamlit |
| `cli_forn.csv` | Vendas diárias por cliente × fornecedor (clientes O e Q de GO) |
| `clientes.csv` | Vendas totais por cliente GO — divididas pelo app |
| `fornecedores.csv` | Vendas totais por fornecedor × sigla de loja GO |
| `grupos.csv` | Vendas totais por grupo de produto × sigla de loja GO |
| `elasticidade.csv` | Resultado da análise de elasticidade (Opções A/B/C) |
| `for_tipo.csv` | Tabela auxiliar de tipo de fornecedor (usada no app) |
| `GLOSSARIO_THREAD.md` | Referência técnica completa (SQL, lógica de atualização) |

---

## 3. Como rodar o Streamlit (passo a passo)

### Pré-requisitos
- Python 3.10+ instalado
- Acesso ao banco de dados PostgreSQL da Kaizen (credenciais abaixo)

### Instalar dependências
```bash
cd /caminho/da/pasta/kaizen_go_reajuste
pip install streamlit pandas psycopg python-dotenv
```

### Configurar credenciais do banco
Crie um arquivo `.env` na pasta do projeto com:
```
DB_HOST=<servidor_postgres>
DB_PORT=5432
DB_NAME=<nome_do_banco>
DB_USER=<usuario>
DB_PASSWORD=<senha>
```
Peça as credenciais para o Gustavo ou para a TI — são as mesmas credenciais do banco de dados "D-1" da Kaizen.

### Rodar o dashboard
```bash
streamlit run app.py
```

O browser abre automaticamente em `http://localhost:8501`.

> **Importante:** Os dados que aparecem no dashboard são os CSVs que estão na pasta. O app **não busca dados em tempo real** — ele lê os arquivos CSV. Para ter dados atualizados, é preciso rodar o `gerar_dados.py` (ver seção 4).

---

## 4. Como atualizar os dados

O dashboard mostra dados até **D-1 = 28/04/2026** (última atualização). Para atualizar:

### Passo 1 — Identificar a nova data D-1

D-1 é sempre **ontem** (o banco tem dados até o dia anterior). Confirme quantos dias úteis de segunda a sexta correram entre **06/04/2026** e a nova D-1, excluindo:
- Fins de semana (sáb/dom)
- **21/04/2026 (Tiradentes)** — confirmado como não-útil (apenas ~57 pedidos nesse dia)
- Outros feriados: verificar via query de pedidos por dia (ver abaixo)

**Calendário já mapeado até 28/04:**
```
Abr 06–10 ✓ (5 dias)
Abr 11–12 ✗ (fds)
Abr 13–17 ✓ (5 dias)
Abr 18–19 ✗ (fds)
Abr 20 ✓, Abr 21 ✗ (Tiradentes), Abr 22–24 ✓ (4 dias)
Abr 25–26 ✗ (fds)
Abr 27–28 ✓ (2 dias)
TOTAL até 28/04: 16 dias úteis
```

Para verificar feriados suspeitos, use essa query no banco:
```sql
SELECT dt_emissao::date AS dia, COUNT(*) AS pedidos
FROM "D-1".pedido
WHERE dt_emissao::date BETWEEN '2026-04-06' AND '<nova_data_fim>'
  AND cancelada = 'N' AND tipped = 'V'
GROUP BY 1 ORDER BY 1
```
Dias com menos de ~500 pedidos são suspeitos de feriado — confirme e exclua do divisor.

### Passo 2 — Adicionar feriados ao script e rodar

Abra o `gerar_dados.py` e localize a linha:
```python
FERIADOS: set = set()
```

Adicione os feriados identificados (dias de semana em que a Kaizen não operou):
```python
FERIADOS = {
    datetime.date(2026, 4, 21),   # Tiradentes — já mapeado
    # datetime.date(2026, 5, 1),  # Dia do Trabalho — verificar quando chegar
}
```

Depois rode:
```bash
python gerar_dados.py
```

O script calcula automaticamente D-1 (ontem), conta os dias úteis, roda as 4 queries no banco e gera os CSVs atualizados. Ao final imprime:
```
✅ _config.json atualizado: {...}
🎉 Todos os CSVs atualizados. Reinicie o Streamlit para recarregar.
```

### Passo 3 — Reiniciar o Streamlit

Pare o Streamlit (Ctrl+C no terminal) e rode novamente:
```bash
streamlit run app.py
```

Os novos dados aparecem automaticamente.

---

## 5. O banco de dados — o que você precisa saber

O banco é PostgreSQL. As tabelas ficam no schema **`"D-1"`** (com aspas duplas — o nome tem hífen).

### Tabelas principais usadas

| Tabela | Para que serve |
|---|---|
| `"D-1".prod_ped` | Itens de pedido: produto, fornecedor, preço, custo, MC, quantidade |
| `"D-1".pedido` | Cabeçalho dos pedidos: cliente, vendedor, valor total, custo total |
| `"D-1".cliente` | Cadastro de clientes: cidade, estado, sigladesc (sigla da loja) |
| `"D-1".fornec` | Cadastro de fornecedores |
| `"D-1".produto` | Cadastro de produtos (codpro, grupo) |
| `"D-1".grupo` | Grupos de produtos |
| `"D-1".vendedor` | Cadastro de vendedores |

### Filtros de escopo usados no projeto

- **Clientes de GO:** `c.estado = 'GO'`
- **Pedidos válidos:** `cancelada = 'N' AND tipped = 'V'`
- **Atenção:** Em `prod_ped`, a coluna de produto é **`cod_pro`** (com underscore) — não confundir com `codpro` da tabela `produto`

### Siglas de loja (sigladesc) relevantes

- **O** — Revendedores/Balconistas GO — é a maior parte do volume
- **Q** — Distribuidores GO
- **E, U, N** — Clientes com precificação diferenciada (desconto negociado) — são naturalmente mais sensíveis a preço

### Exclusão importante — cliente I8000

O cliente `codcli = 'I8000'` é a **DISTRIBUIDORA KAIZEN LTDA** — uma entidade interna da empresa que faz transferências bulk entre filiais. Nas análises de elasticidade, esse cliente foi **excluído** porque suas compras (R$783K em 17/04 e R$368K em 21/04) inflavam artificialmente o faturamento de Abril e distorciam todos os cálculos. Para análises de elasticidade, sempre adicione `AND pp.codcli <> 'I8000'`.

---

## 6. A análise de elasticidade — o que foi feito e o que ficou pendente

### Contexto

Além do dashboard de monitoramento, o Gustavo pediu uma análise para responder: **"Quanto a demanda de GYN caiu para cada 1% de aumento de preço?"** Isso é a elasticidade-preço da demanda (Ed).

A análise usou dados de **loja 08 (Kaizen Parque Oeste, GYN)** via `cd_loja = '08'`, comparando Março 2026 vs Abril 06-28/2026, excluindo I8000.

### Os três métodos calculados

**Opção A — Elasticidade agregada simples (arc elasticity)**

Calcula a variação % de faturamento total e quantidade total entre os dois períodos.

- **Resultado (todos os clientes, ex-I8000):** Ed = **-2,09**
- Interpretação: Para cada 1% de aumento de preço, a demanda teria caído ~2,1% — aparentemente elástico
- **Limitação crítica:** Esse número é distorcido pelo "efeito mix". O óleo de motor, por exemplo, caiu -47,3% em volume mas não por causa do preço — foi por outro motivo. Isso contamina o cálculo agregado. **Não use esse número como verdade.**

**Opção B — Mediana por produto (mais robusta)**

Calcula a elasticidade individualmente para cada combinação produto × cliente que teve pelo menos 5 unidades vendidas nos dois períodos, depois tira a mediana.

| Grupo de clientes | Mediana Ed |
|---|---|
| Todos | -0,75 |
| Sem clientes diferenciados (sem O/Q/E/U/N) | -0,72 |
| Só clientes diferenciados | -0,99 |

- **Limitação:** Ainda tem viés de sazonalidade (Abril naturalmente tem demanda diferente de Março, independente do preço)

**Opção C — Regressão WLS entre fornecedores (mais sofisticada)**

Usa o fato de que diferentes fornecedores receberam aumentos de preço diferentes. Roda uma regressão:

`ΔQ% = α + β × ΔP%`

Onde β é o efeito puro do preço sobre a demanda, e α captura o "choque comum" (sazonalidade + outros fatores).

- **Resultado:** β = **-0,54**, α = **-8,1%** (R² = 0,12, 95 fornecedores)
- **Problema identificado:** O α de -8,1% **não é sazonalidade pura**. A regressão absorveu parte do efeito médio do preço no intercepto. A decomposição mostra:
  - ΔP% médio ponderado entre fornecedores = +7,97%
  - α = S (sazonalidade real) + β × ΔP%_médio = S + (-0,54 × 7,97%) = S - 4,3%
  - Portanto S_implícito = -8,1% + 4,3% = **-3,82%**
  - Mas a sazonalidade real pode ser diferente de -3,82%

### O que ficou PENDENTE — Opção C com regressão corrigida

O Gustavo confirmou que a sazonalidade não é -8,1% e que tem o número real de sazonalidade no acompanhamento interno dele. A fórmula para corrigir a regressão é:

```python
# Passo 1: ajustar ΔQ% retirando a sazonalidade conhecida
DQ_adj = DQ - S   # S é a sazonalidade real (ex: -0.03 para -3%)

# Passo 2: regressão WLS sem intercepto (já que removemos a sazonalidade)
beta_final = sum(W * DP * DQ_adj) / sum(W * DP**2)
```

**Tabela de sensibilidade já calculada:**

| S (sazonalidade real) | β ajustado (elasticidade final) |
|---|---|
| -1% | -1,20 |
| -2% | -1,15 |
| -3% | -1,11 |
| -4% | -1,06 |
| -5% | -1,02 |
| -6% | -0,97 |

O intervalo provável está entre -0,97 e -1,20, sugerindo demanda **próxima à unitária** (para cada 1% de aumento de preço, a demanda cai ~1%).

**Para finalizar:** Confirme com o Gustavo qual é a estimativa de sazonalidade dele para Abril vs Março em GYN e aplique a fórmula acima. O arquivo `elasticidade.csv` tem os dados por fornecedor já calculados para alimentar essa regressão.

---

## 7. Como pedir ajuda ao Claude para continuar

Esse projeto foi criado em sessões do Claude Cowork. Para continuar com o Claude, compartilhe este documento e os arquivos da pasta com ele. Diga algo como:

> "Tenho um projeto de análise de elasticidade de preços da Kaizen em GYN. Segue o handoff: [cola o conteúdo deste arquivo]. Preciso [o que você precisa]."

O Claude vai conseguir entender todo o contexto e continuar de onde paramos.

Para atualizar dados via Claude, ele pode rodar as queries diretamente no banco via MCP (ferramenta de banco de dados já configurada) e gerar os CSVs novos sem precisar do Python local.

---

## 8. Resumo executivo dos resultados da elasticidade

Para fins de decisão de negócio, o que foi encontrado:

**Em GYN (Kaizen Parque Oeste), a demanda de autopeças por atacado é próxima à unitária:**
- Método mais simples (A): Ed = -2,09 (superestimado por efeito mix)
- Método mediana por produto (B): Ed entre -0,72 e -0,99 dependendo do grupo
- Método de regressão corrigida (C, pendente): Ed estimado entre -0,97 e -1,20

**Conclusão prática:** Um reajuste de preços de +8% (o que foi feito) deve resultar em queda de demanda entre -8% e -10%. Isso implica que **o reajuste foi aproximadamente neutro em termos de receita total** (o que se ganhou em preço se perdeu em volume). A análise mais detalhada por segmento mostra que clientes com precificação diferenciada (O/Q/E/U/N) são mais sensíveis — Ed próximo de -1,0 — enquanto o restante da base é levemente menos sensível.

---

## 9. Calendário de feriados identificados (para atualizar n_dias_d)

| Data | Feriado | Operar? | Decisão |
|---|---|---|---|
| 03/04/2026 | Sexta-Feira Santa | Não | Excluir (confirmado via volume ~0) |
| 21/04/2026 | Tiradentes | Não | Excluir (confirmado via ~57 pedidos) |
| 01/05/2026 | Dia do Trabalho | Verificar | Confirmar no banco quando passar |

Para verificar qualquer data suspeita:
```sql
SELECT COUNT(*) AS pedidos
FROM "D-1".pedido
WHERE dt_emissao::date = '2026-XX-XX'
  AND cancelada = 'N' AND tipped = 'V'
```
Se retornar menos de ~500, excluir do divisor.

---

## 10. Contatos e acesso

- **Gustavo Santos** — gustavo@grupobueno.com — dúvidas sobre contexto de negócio, sazonalidade real, decisão de continuar análise
- **Banco de dados** — credenciais via TI (schema `"D-1"`, PostgreSQL)
- **Streamlit** — roda localmente; não há deploy em servidor (era uso interno do Gustavo)

---

*Documento gerado em Maio/2026. Para dúvidas técnicas adicionais, consulte o `GLOSSARIO_THREAD.md` na mesma pasta, que tem as queries SQL completas e detalhes de implementação.*
