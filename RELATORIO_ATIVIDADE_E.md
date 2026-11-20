# Relatório – Atividade 04 (Parte E): Tema Escuro

Continuação de [A](RELATORIO_ATIVIDADE_A.md) a [D](RELATORIO_ATIVIDADE_D.md). Esta etapa é só de front end; `app.py` e o banco não mudaram.

## 1. Comportamento

- **Automático:** sem escolha salva, a página segue o tema do sistema (`prefers-color-scheme`).
- **Manual:** o botão 🌙/☀️ no cabeçalho alterna entre claro e escuro e **guarda a escolha** no `localStorage` do navegador.
- A escolha manual tem prioridade sobre o sistema.
- A página 404 também respeita o tema.

## 2. O que foi alterado

### `static/css/styles.css`
- Novas variáveis `--bg` e `--surface`; as cores fixas `#fff` (campos, selects, fundo) viraram `var(--surface)` e o `body` ganhou `background-color: var(--bg)`. A parte D já usava variáveis para as demais cores, então a troca de tema é só redefinir variáveis.
- Paleta escura definida em dois lugares com os mesmos valores: `:root[data-theme="dark"]` (escolha manual) e `@media (prefers-color-scheme: dark)` com `:root:not([data-theme="light"])` (automático, a menos que o usuário tenha escolhido claro).
- `color-scheme: light|dark` para que controles nativos (calendário, lista de opções, scrollbar) acompanhem o tema.
- Estilo do botão `.themeToggle`, cor de `::placeholder` e `.summary` alinhado à direita.
- Selos de prioridade e cor de "atrasada" mantêm contraste (vermelho mais claro no escuro).

### `templates/index.html` e `templates/404.html`
- Pequeno script no `<head>` lê `localStorage` e define `data-theme` **antes** da renderização, evitando o "piscar" de tema claro.
- Botão de alternância no cabeçalho (`index.html`).

### `static/js/script.js`
- `toggleTheme()`, `currentTheme()` e `paintThemeButton()`; o ícone mostra ☀️ no escuro e 🌙 no claro. Acesso ao `localStorage` protegido por `try/catch`.

## 3. Como testar

```bash
python -m pytest        # 44 testes
python app.py
```

Manual:
1. Abrir a página com o sistema em tema escuro → já abre escuro; com o sistema claro → abre claro.
2. Clicar em 🌙 → escurece e o ícone vira ☀️; recarregar a página → continua escuro.
3. Clicar em ☀️ → volta ao claro e **continua claro** mesmo com o sistema escuro.
4. Conferir campos, listas, calendário, tarefas atrasadas, concluídas e a página 404 (`/qualquer-coisa`) nos dois temas.

### Testes
3 testes novos (botão e script de tema no `<head>`, 404 com o script, CSS com as duas definições de tema e sem `#fff` fixo). Total: `44 passed`. Os testes verificam o HTML/CSS servido; **a aparência real não foi validada em navegador** neste ambiente (contraste, cores dos controles nativos).

## 4. Processo e observações

- Aproveitou-se o trabalho da parte D (cores em variáveis CSS); só restaram 3 cores fixas a converter.
- Duplicar a paleta escura (manual + automático) é o custo de suportar os dois modos só com CSS; se a paleta mudar, é preciso alterar os dois blocos.
- Limitação: a escolha fica por navegador/dispositivo (`localStorage`), não por usuário, já que o app não tem contas.
- O app desktop (`desktop.py`, via flaskwebgui) usa o navegador local, então segue as mesmas regras.

## 5. Observação acadêmica

Conforme a Atividade 04, este código não deve ser enviado como PR ao projeto original sem contato prévio com os mantenedores.
