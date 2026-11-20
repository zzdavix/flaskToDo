# Relatório – Atividade 04 (Parte A): Prioridade e Data de Vencimento

Projeto base: **flaskToDo** (lista de tarefas em Flask + SQLite, projeto open source de DogukanUrker).
Escopo desta etapa: item **A** do plano da Atividade 03. Os itens B (categorias e busca) e C (endurecimento e testes) ficam para etapas seguintes.

## 1. Objetivo da melhoria

- Novos campos por tarefa: **prioridade** (alta / média / baixa) e **data de vencimento** (opcional).
- Selo colorido de prioridade.
- Tarefas atrasadas (vencimento no passado e ainda pendentes) destacadas em vermelho.
- Ordenação (criação, prioridade, vencimento) e filtro por prioridade.

## 2. Entendimento do projeto original

| Arquivo | Papel |
|---|---|
| `app.py` | Rotas Flask (`/`, `/add`, `/check`, `/uncheck`, `/edit`, `/delete`), SQL com f-strings, conexões sem `close()` |
| `dbChecker.py` | Executado no `import`; cria `todos.db` e a tabela se não existirem |
| `templates/index.html` | Lista renderizada acessando colunas por **índice** (`todo[4]` = status etc.) |
| `static/js/script.js` | Navega por GET para `/add/<texto>` e `/edit/<id>/<texto>` |
| `static/css/styles.css` | Estilo |

Pontos que condicionaram o design:

1. O template usa índices posicionais. Por isso as colunas novas foram **adicionadas no fim** da tabela, mantendo os índices 0–6 intactos.
2. O banco `todos.db` já existe e é versionado: foi necessária uma **migração não destrutiva**.
3. As operações são feitas via GET (será tratado na etapa C). Para manter consistência e não antecipar o escopo C, as novas ações seguem o mesmo padrão GET.

## 3. O que foi alterado

### `dbChecker.py`
- Migração idempotente: consulta `PRAGMA table_info(todos)` e executa `ALTER TABLE ... ADD COLUMN` para `priority TEXT DEFAULT 'media'` e `dueDate TEXT` somente se faltarem. Tarefas antigas ficam com prioridade média e sem vencimento.
- O `connection.close()` passou a ficar fora do `try`, ao final, para valer nos dois caminhos.

### `app.py`
- Helpers `validPriority`, `validDueDate` (aceita só `AAAA-MM-DD` válido, senão `None`) e `formatDue` (exibe `dd/mm/aaaa`).
- `index()`: lê `?sort=created|priority|due` e `?priority=all|alta|media|baixa`; calcula `overdue` (`dueDate < hoje` e status `False`); filtra e ordena em Python. Cada linha vira uma tupla estendida: índices 7 (prioridade), 8 (vencimento ISO), 9 (vencimento formatado), 10 (atrasada?).
- `add()`: aceita `?priority=` e `?due=`; o INSERT desta rota agora é **parametrizado** (`?`) e fecha a conexão.
- Nova rota `meta(id)` (`/meta/<id>?priority=&due=&next=`): altera prioridade/vencimento de uma tarefa existente, com UPDATE parametrizado. O parâmetro `next` só é aceito se for caminho local (começa com `/` e não com `//`), evitando *open redirect*.
- Regras de ordenação: *prioridade* = alta→baixa, depois vencimento mais próximo; *vencimento* = mais próximo primeiro, sem data por último, desempate por prioridade.

### `templates/index.html`
- Barra de controles (selects de ordenação e filtro, enviados por GET ao mudar).
- Macro `meta(todo)` reutilizada nas listas de pendentes e concluídas: selo colorido, select de prioridade e campo de data editáveis.
- Classe `overdue` nas pendentes atrasadas + etiqueta "atrasada".
- Formulário de criação com select de prioridade e campo de data.

### `static/js/script.js`
- `todo()` envia prioridade e vencimento e passou a usar `encodeURIComponent` no texto (antes, `?`, `#` ou `/` no texto quebravam a rota).
- Nova `updateMeta(el)` chama `/meta/<id>` preservando a ordenação/filtro atuais via `next`.

### `static/css/styles.css`
- Selos `.badge-alta` (vermelho), `.badge-media` (âmbar), `.badge-baixa` (verde); estilo de `.overdue`, `.overdueTag`, `.controls` e `.meta`.

## 4. Como executar e testar

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python app.py                   # ou python desktop.py
```
A migração roda sozinha no primeiro start (via `import dbChecker`).

Roteiro de teste manual:
1. Criar tarefa com prioridade **alta** e vencimento no passado → aparece com selo vermelho, linha em vermelho e etiqueta "atrasada".
2. Criar tarefas **média** e **baixa**, com e sem data → selos âmbar/verde.
3. Trocar ordenação para *prioridade* e *vencimento* → ordem conforme as regras acima.
4. Filtrar por prioridade → apenas as tarefas daquela prioridade; a ordenação escolhida é mantida (é o mesmo formulário).
5. Alterar prioridade/data de uma tarefa existente → persiste e a página volta com o filtro/ordenação atuais.
6. Concluir uma tarefa atrasada → deixa de ser vermelha.

Teste automatizado ad hoc executado nesta etapa (Flask test client sobre **cópia** do banco): criação com valores válidos e inválidos (`priority=xx`, `due=lixo` → caem em `media`/sem data), as quatro visões (`/`, `sort=priority`, `sort=due`, `priority=alta`), contagem de etiquetas de atraso e `next=//evil.com` → redireciona para `/`. Todos os resultados foram os esperados. A suíte formal com pytest é o item C.

## 5. Processo de desenvolvimento com o agente

1. **Leitura** de todos os arquivos (o projeto é pequeno: ~5 arquivos de código) antes de qualquer edição.
2. **Decisões de design** guiadas pelo código existente: colunas no fim da tabela, migração idempotente, filtro/ordenação no servidor.
3. **Implementação** em camadas: banco → backend → template → JS → CSS.
4. **Verificação**: execução contra cópia do banco para não alterar o `todos.db` real.

### O que funcionou
- Projeto pequeno permitiu entender tudo de uma vez.
- A abordagem de migração via `PRAGMA table_info` preservou os dados existentes.
- Teste via Flask test client dispensou subir servidor/navegador.

### Inesperado / problemas
- Primeira execução de teste falhou por `UnicodeEncodeError` ao imprimir no console Windows (cp1252) uma tarefa existente com "ğ" — problema do console, não do código; resolvido com `PYTHONIOENCODING=utf-8`.
- Não foi possível validar o visual (cores, alinhamento) em navegador neste ambiente; a validação visual fica para o grupo.

### Limitações conhecidas (herdadas, não corrigidas de propósito)
- `editToDo()` sempre lê o **primeiro** `.todoContent`/`.todoID` da página, então salvar edição de texto só funciona de fato para a primeira tarefa. Bug original, fora do escopo.
- As demais rotas (`check`, `uncheck`, `edit`, `delete`) continuam com SQL por f-string, GET e conexões não fechadas → item **C**.
- `delete` decrementa `sqlite_sequence` de todas as tabelas, podendo reutilizar IDs. Também original.
- A comparação de "atrasada" usa a data do servidor e considera atrasada só a partir do dia seguinte ao vencimento.

## 6. Observações sobre uso acadêmico

Conforme a Atividade 04, este código **não** deve ser enviado como PR ao projeto original sem contato prévio com os mantenedores.

> Campos a completar pelo grupo: familiaridade prévia com Flask/SQLite/Jinja, e o que foi aprendido.
