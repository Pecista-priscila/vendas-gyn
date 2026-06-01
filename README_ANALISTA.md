# Para a Analista — Como Continuar Este Projeto

## O que você está recebendo

Esta pasta contém um projeto de análise completo do impacto do reajuste de preços em Goiânia (GYN) feito pelo Gustavo. Inclui um dashboard Streamlit de monitoramento e uma análise de elasticidade de preços que ficou ~90% pronta.

## O que fazer para continuar com o Claude Cowork

**Passo 1 — Abra uma nova sessão no Claude Cowork**

**Passo 2 — Arraste ou anexe os seguintes arquivos para a conversa:**
1. `HANDOFF_CLAUDE.md` ← este é o mais importante, começa por ele
2. `GLOSSARIO_THREAD.md`
3. `elasticidade.csv`
4. `_config.json`

**Passo 3 — Digite para o Claude:**
> "Leia o arquivo HANDOFF_CLAUDE.md que te passei. Esse é o contexto completo de um projeto que preciso continuar. Me confirma onde estamos e qual é o próximo passo."

O Claude vai ler tudo e retomar de onde o Gustavo parou.

---

## O que está pendente

A análise de elasticidade pela Opção C (a mais rigorosa) está quase pronta. Para finalizar, você precisa **confirmar com o Gustavo qual é a estimativa de sazonalidade real dele para Abril vs Março em GYN** — é um único número (ex: "-3%"). Com esse número, o Claude calcula o resultado final em segundos.

---

## Para rodar o dashboard localmente

Veja o `HANDOFF_CLAUDE.md`, seção 5 — tem o passo a passo de instalação e execução.

---

## Documentos de referência disponíveis

| Arquivo | Quando usar |
|---|---|
| `HANDOFF_CLAUDE.md` | Ponto de partida para o Claude continuar o projeto |
| `GLOSSARIO_THREAD.md` | Referência técnica: queries SQL, lógica de dias úteis, bugs já resolvidos |
| `../kaizen_postgres_referencia.md` | Referência do banco de dados da Kaizen (para qualquer consulta SQL) |
| `HANDOFF_ANALISTA.md` | Explicação em linguagem humana de tudo que foi feito |
