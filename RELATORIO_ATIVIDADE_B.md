# Relatório – Atividade 04 (Parte B): Categorias e Busca

Continuação de [RELATORIO_ATIVIDADE_A.md](RELATORIO_ATIVIDADE_A.md). Projeto base: **flaskToDo** (Flask + SQLite).
Escopo desta etapa: item **B** do plano. O item C (endurecimento e testes) continua pendente.

## 1. Objetivo

- Criar e remover **categorias**.
- Associar uma categoria (opcional) a cada tarefa.
- **Filtrar por categoria** (todas / sem categoria / uma específica).
- **Campo de busca** no topo, por texto da tarefa.

## 2. Decisões de design

1. **Tabela própria `categories`** (`id`, `name UNIQUE COLLATE NOCASE`) e coluna `categoryId` em `todos`, em vez de guardar o nome na tarefa. Assim renomear/remover é simples e não há duplicatas por maiúsculas ("Casa" = "casa").
2. Coluna adicionada **no fim** de `todos`, como na parte A, mantendo os índices usados pelo template. O `select *` foi trocado por uma lista explícita de colunas, para que a ordem não dependa do schema.
3. **Remover categoria não apaga tarefas**: elas voltam a "sem categoria".
4. **Busca e filtros combinam** (busca + categoria + prioridade + ordenação). Tudo está no mesmo `<form method="get">`, então um controle preserva o valor dos outros.
5. Busca feita em Python (`texto.lower()` contém `q.lower()`), sem `LIKE`, para evitar discussões de escape de `%`/`_` e por o volume de dados ser pequeno.
6. Novas rotas seguem o padrão GET do projeto; a troca para POST é o item C.

## 3. O que foi alterado

### `dbChecker.py`
- `CREATE TABLE IF NOT EXISTS categories (...)`.
- `ALTER TABLE todos ADD COLUMN categoryId INTEGER` somente se ainda não existir (idempotente, preserva dados).

### `app.py`
- `safeNext()`: validação do parâmetro `next` extraída da rota `meta` e reutilizada (só caminhos locais).
- `validCategory()`: converte para `int` e confirma que a categoria existe; qualquer valor inválido vira "sem categoria".
- `index()`: lê `category` (`all` | `none` | id) e `q`; aplica filtros antes da ordenação. As tuplas ganham 2 itens: índice 11 (id da categoria) e 12 (nome).
- `add()` e `meta()` aceitam `category`.
- Novas rotas: `/category/add/<name>` (nome aparado, máx. 30 caracteres, `INSERT OR IGNORE`, aceita `next`) e `/category/delete/<id>`. Todas as consultas novas são parametrizadas e fecham a conexão.

### `templates/index.html`
- Campo de busca e select de categoria na barra de controles.
- Select de categoria no formulário de criação e em cada tarefa (editável, na macro `meta`).
- Seção "Categorias" no rodapé: chips clicáveis (filtram), botão ✖ para remover, campo para criar.

### `static/js/script.js`
- `todo()` e `updateMeta()` enviam `category`; nova `addCategory()` (preserva filtros atuais via `next`).

### `static/css/styles.css`
- Estilos de `.searchBox`, `.categoriesBox`, `.categoryChip` e quebra de linha em `.controls`/`.meta`.

## 4. Como executar e testar

```bash
pip install -r requirements.txt
python app.py        # a migração roda automaticamente no primeiro start
```

Roteiro manual:
1. Em "Categorias", criar *Trabalho* e *Casa*; tentar criar *trabalho* → não duplica.
2. Criar tarefas escolhendo categorias; trocar a categoria de uma tarefa existente pelo select da linha.
3. Filtrar por categoria pelo select ou clicando no chip; testar "sem categoria".
4. Digitar no campo de busca e dar Enter (case-insensitive); combinar com categoria, prioridade e ordenação.
5. Remover uma categoria → as tarefas permanecem e passam a "sem categoria".

Teste automatizado ad hoc executado (Flask test client sobre **cópia** do banco), todos com o resultado esperado:

| Cenário | Resultado |
|---|---|
| Criar "Trabalho", "trabalho", "Casa" e "  " | 2 categorias gravadas (duplicata e vazio ignorados) |
| `?category=1` | só a tarefa dessa categoria |
| `?category=none` | só tarefas sem categoria |
| `?q=LAV` | encontra "lavar" (case-insensitive); `?q=zzz` → vazio |
| `?category=1&q=rel&priority=alta` | filtros combinados |
| `add?category=99` (inexistente) | tarefa criada sem categoria |
| `meta?...&next=/?q=a` | redireciona para `/?q=a` |
| `category/delete/1` | tarefas dessa categoria ficam com `categoryId` nulo |

## 5. Processo com o agente

1. Releitura de `app.py` antes de editar, já que a parte A havia mudado a rota `index`.
2. Implementação em camadas (banco → backend → template/JS/CSS), reaproveitando padrões da parte A (migração idempotente, helpers de validação, `next` seguro).
3. Verificação com script contra cópia do banco, sem tocar em `todos.db`.

### Observações
- Ao criar "trabalho" (duplicata), o `INSERT OR IGNORE` consome um valor de `AUTOINCREMENT`, então "Casa" ficou com id 3 e não 2. É inofensivo, só informativo.
- Um teste inicial usou `category=2` achando que "Casa" tinha esse id; a tarefa ficou corretamente sem categoria, o que acabou validando o tratamento de id inexistente.
- O visual (layout da barra de controles, chips) não foi conferido em navegador neste ambiente.

### Limitações conhecidas
- `check`, `uncheck`, `edit` e `delete` redirecionam para `/`, então perdem busca/filtros ativos (a parte C pode tratar junto com POST).
- A busca cobre apenas o texto da tarefa, não o nome da categoria.
- Não há renomeação de categoria (apenas criar/remover).
- Persistem os problemas originais descritos na parte A (`editToDo()` sempre edita a primeira tarefa, SQL por f-string nas rotas antigas), a serem tratados no item C.

## 6. Observação acadêmica

Conforme a Atividade 04, este código não deve ser enviado como PR ao projeto original sem contato prévio com os mantenedores.
