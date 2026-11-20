# Relatório – Atividade 04 (Parte C): Endurecimento e Testes

Continuação de [A](RELATORIO_ATIVIDADE_A.md) e [B](RELATORIO_ATIVIDADE_B.md). Projeto base: **flaskToDo** (Flask + SQLite).
Escopo: consultas parametrizadas, POST no lugar de GET, conexões sempre fechadas e suíte de testes com pytest.

## 1. Problemas do projeto original que motivaram a etapa

| Problema | Onde | Risco |
|---|---|---|
| SQL montado por f-string com texto vindo da URL | `add`, `edit`, `check`, `uncheck`, `delete` | injeção de SQL; aspas no texto quebravam a consulta |
| Alterações via GET (`/delete/3`, `/check/3`) | todas as rotas de escrita | qualquer link, prefetch ou `<img src>` de outro site altera os dados (CSRF trivial) |
| `sqlite3.connect()` sem `close()` | todas as rotas | vazamento de conexões / banco travado |
| `update sqlite_sequence set seq = seq-1` ao excluir | `delete` | decrementava o contador de **todas** as tabelas, causando reutilização de ids (inclusive em `categories`) |
| `editToDo()` lia sempre o primeiro `.todoContent` | `script.js` | salvar edição só funcionava na primeira tarefa |

## 2. O que foi alterado

### `app.py`
- **Consultas 100% parametrizadas** (`?`). Não resta nenhum `f"...sql..."` no arquivo.
- **POST para toda escrita**: `/add`, `/check/<id>`, `/uncheck/<id>`, `/edit/<id>`, `/delete/<id>`, `/meta/<id>`, `/category/add`, `/category/delete/<id>`. Os dados vão no corpo do formulário (texto deixou de ir na URL, o que também elimina problemas com `/`, `?`, `#`, `%`). GET nessas rotas devolve **405**.
- **Gerenciador de contexto `getDb()`**: abre a conexão, faz `commit` se tudo deu certo e **sempre fecha** (`finally`), inclusive quando há exceção.
- Todas as rotas aceitam `next` (campo oculto) e redirecionam por `safeNext()`, então **busca, filtros e ordenação passam a ser preservados** após concluir/excluir/editar (limitação deixada na parte B).
- Entradas de texto passam por `strip()`; vazio é ignorado.
- Removido o `update sqlite_sequence` do `delete`.
- Caminho do banco em `app.config["DATABASE"]` (variável de ambiente `FLASKTODO_DB`, padrão `todos.db`), o que torna a aplicação testável sem tocar no banco real.

### `dbChecker.py`
- O código que rodava no `import` virou a função `initDb(path)`: `CREATE TABLE IF NOT EXISTS` + migrações A e B, idempotente. `app.py` a chama na inicialização. A conexão é fechada com `contextlib.closing`.

### `templates/index.html`, `static/js/script.js`, `static/css/styles.css`
- Links de concluir / reabrir / excluir / remover categoria viraram **formulários POST** (macro `postBtn`) com botões estilizados para parecerem com os ícones anteriores.
- JS: nova `postTo(url, dados)` (formulário oculto) usada por adicionar, editar, alterar metadados e criar categoria. `editToDo(button)` agora usa a **linha do botão clicado** (corrige o bug do primeiro item).

### Testes (novos)
- `tests/conftest.py`: define `FLASKTODO_DB` para um arquivo temporário antes de importar `app`; fixtures `client` (banco novo por teste) e `db` (consulta direta).
- `tests/test_app.py`: **36 testes**.
- `pytest.ini` e `requirements-dev.txt` (`pytest`).

## 3. Como executar e testar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest            # roda os 36 testes
python app.py               # executa a aplicação
```

Os testes usam bancos temporários: o `todos.db` real não é lido nem alterado.

### Cobertura da suíte

| Área | O que é verificado |
|---|---|
| POST vs GET | as 8 rotas de escrita respondem 405 a GET; URLs antigas (`/add/hack`) não criam tarefa; `/` continua em GET |
| CRUD | adicionar, concluir (grava data/hora), reabrir, editar, excluir; texto vazio ou só espaços ignorado; edição atinge a linha certa; ids não são reutilizados |
| Injeção / texto especial | `"; drop table todos; --`, aspas simples, `a/b?c#d`, `100%` são gravados literalmente; HTML é escapado na página; mesmo teste para nomes de categoria |
| Parte A | validação de prioridade/data, atraso só para pendentes vencidas, ordenação por prioridade e vencimento, filtro, atualização via `/meta` |
| Parte B | categorias únicas sem diferenciar maiúsculas, filtro e "sem categoria", categoria inexistente, remover categoria preserva tarefas, busca (case-insensitive e combinada) |
| Segurança | `next` só aceita caminhos locais (`//evil.com` e `http://...` caem em `/`) |
| Conexões | todas as conexões abertas são fechadas, inclusive quando a consulta lança exceção |
| Migração | banco com o esquema original recebe as colunas novas, preserva dados e a migração é idempotente |

Resultado: `36 passed`.

## 4. Processo com o agente

1. Levantamento dos pontos frágeis (tabela da seção 1) antes de editar.
2. Refatoração de `dbChecker.py` primeiro, pois sem ela não havia como testar sem efeitos colaterais no banco real.
3. Reescrita das rotas em bloco, depois adaptação de template/JS/CSS.
4. Escrita dos testes e execução da suíte.

### Inesperado / observações
- Um comando de shell com um script Python grande em *heredoc* falhou na análise sintática do bash (nada foi executado). Os arquivos foram então criados com a ferramenta de escrita e o patch rodou a partir de um arquivo, o que também deixou o processo mais reprodutível.
- Os testes de fechamento de conexão usam um *wrapper* sobre `sqlite3.connect` (via `monkeypatch`) para registrar chamadas a `close()`, em vez de depender de efeitos indiretos.
- A suíte passou de primeira (36/36); a validação visual dos botões-formulário em navegador não foi feita neste ambiente.

### Limitações / decisões
- **Não há token CSRF.** POST elimina o ataque trivial por link/imagem, mas um formulário hospedado em outro site ainda poderia enviar POST. Para uma aplicação local isso foi considerado suficiente; para uso exposto na rede, o ideal é Flask-WTF ou token próprio.
- `app.run(debug=True, host=<ip da máquina>)` do projeto original foi mantido; o modo debug não deve ser usado exposto.
- `app.secret_key` continua sendo gerado a cada execução (não há sessões em uso).
- Ao excluir tarefas os ids deixam de ser reaproveitados (comportamento correto de `AUTOINCREMENT`), diferente do original.
- Não há testes de interface (JavaScript/navegador), apenas de servidor.

## 5. Observação acadêmica

Conforme a Atividade 04, este código não deve ser enviado como PR ao projeto original sem contato prévio com os mantenedores.

> Campos a completar pelo grupo no relatório final: familiaridade prévia com Flask/SQLite/pytest e o que foi aprendido.
