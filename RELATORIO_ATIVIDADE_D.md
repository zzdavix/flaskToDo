# Relatório – Atividade 04 (Parte D): Melhorias de Usabilidade no Front End

Continuação de [A](RELATORIO_ATIVIDADE_A.md), [B](RELATORIO_ATIVIDADE_B.md) e [C](RELATORIO_ATIVIDADE_C.md).
Pedido original: "uma mudança no front end, para deixar mais fácil de utilizar". Como o pedido era aberto, o agente levantou os pontos de atrito da interface atual e escolheu o conjunto abaixo (decisão registrada aqui para o grupo poder ajustar).

## 1. Problemas de usabilidade identificados

| Problema | Impacto |
|---|---|
| Campo de nova tarefa no **fim** da página; Enter não adiciona | com a lista longa, era preciso rolar até o fim e clicar no botão |
| Botão "salvar" invisível até focar o texto | difícil descobrir que a tarefa é editável; Enter não salvava |
| Linha de tarefa com muitos controles espremidos (selo, selects, data, hora, lixeira) | confuso, quebrava em telas pequenas |
| Excluir sem confirmação | perda acidental de dados (um clique no ícone) |
| Sem mensagem quando a lista está vazia ou o filtro não acha nada | parece que o app está quebrado |
| Sem contagem de tarefas e sem "limpar filtros" | difícil saber o estado atual |
| Sem layout para celular (o repositório tem `images/mobile.jpeg`) | controles estourando a tela |
| Sem `<meta viewport>`, `lang` nem rótulos de acessibilidade | zoom ruim no celular; leitores de tela sem contexto |

## 2. O que foi alterado

### `templates/index.html` (reescrito)
- Documento HTML completo (`doctype`, `lang="pt-BR"`, `charset`, `viewport`).
- **Formulário de adicionar no topo**, como `<form method="post">` nativo: **Enter adiciona**, campo com `autofocus`, `required` e placeholder; prioridade, categoria e vencimento em linha de opções com rótulos.
- Cabeçalho com **resumo** ("2 pendentes · 1 concluída").
- Cada tarefa agora tem **duas linhas**: principal (concluir, texto, salvar, data de criação, lixeira) e secundária de **metadados** (prioridade, categoria, vencimento, "atrasada").
- O **selo de prioridade virou o próprio seletor** (uma pílula colorida clicável), eliminando o par selo + select duplicado.
- Seções "Concluídas" e "Categorias" com títulos; **estado vazio** com dica e, quando há filtro ativo, mensagem própria e link **limpar filtros**.
- **Confirmação** (`confirm`) ao excluir tarefa e ao remover categoria (avisa que as tarefas são mantidas).
- Criar categoria também é formulário nativo (Enter funciona); chip da categoria filtrada fica destacado.
- `aria-label`/`title` em botões e campos.

### `static/js/script.js`
- Removidas `todo()` e `addCategory()` (substituídas pelos formulários nativos).
- `markDirty()`: o botão **salvar aparece quando o texto é alterado**; **Enter salva** a edição.
- Atalho **`/`** foca o campo de busca.

### `static/css/styles.css` (reescrito, mantendo paleta e página 404)
- Variáveis CSS para as cores; `box-sizing`; largura máxima do conteúdo.
- Hover/foco da linha, texto editável com sublinhado ao passar o mouse, concluídas esmaecidas.
- `@media (max-width: 640px)`: fonte menor, container largo, linha quebrando em duas e botão de adicionar em coluna.
- Cores dos selos ajustadas (âmbar e verde mais escuros) para melhor contraste do texto branco.

### O que **não** mudou
Rotas, banco e regras de negócio (nenhuma alteração em `app.py` ou `dbChecker.py`).

## 3. Como testar

```bash
python -m pytest        # 41 testes
python app.py           # e abrir no navegador
```

Roteiro manual:
1. Abrir a página: o cursor já está no campo de nova tarefa; digitar e **Enter** adiciona.
2. Alterar o texto de uma tarefa: aparece **💾 salvar**; clicar ou dar Enter salva (na linha correta).
3. Trocar prioridade pela pílula colorida, categoria e vencimento na linha de baixo.
4. Clicar em 🗑️ → pede confirmação; Cancelar mantém a tarefa.
5. Buscar algo inexistente → mensagem + "limpar filtros"; apagar tudo → mensagem de lista vazia.
6. Teclar `/` fora de um campo → foca a busca.
7. Reduzir a janela abaixo de ~640 px (ou abrir no celular) → layout em coluna.

### Testes
Foram adicionados 5 testes de renderização (estado vazio e resumo, contagens, "limpar filtros", formulário POST nativo com autofocus e as duas confirmações). Também foi ajustado o regex do helper `titles()` dos testes, pois o `<input>` passou a ter atributos em várias linhas. Resultado: `41 passed`.

## 4. Processo com o agente

1. Releitura de template, CSS e JS, listando fricções reais de uso antes de desenhar.
2. Como o pedido era amplo, optou-se por **melhorias de baixo risco que não mexem no backend**; mudanças maiores (tema escuro, drag-and-drop, edição inline sem recarregar, AJAX) foram deixadas de fora de propósito.
3. Reescrita de template e CSS por inteiro (os acréscimos das partes A–C tinham deixado regras sobrepostas, como `.notCompletedToDos *` forçando `display:flex` em todos os filhos).
4. Execução da suíte; 4 testes antigos falharam por causa do regex de teste, não do app, e foram corrigidos.

### Inesperado / observações
- Um `sed` para corrigir o regex consumiu a barra invertida (`\s` virou `s`) e deixou os mesmos 4 testes falhando; foi corrigido com edição direta do arquivo.
- **A validação visual não foi feita**: não houve navegador neste ambiente. Os testes verificam o HTML gerado, mas não o aparência real (alinhamento, cores, layout mobile). Recomenda-se conferir manualmente pelo roteiro acima.

### Limitações
- Alterar prioridade/categoria/vencimento continua recarregando a página (POST + redirect); não há atualização sem recarga.
- A confirmação usa o `confirm()` nativo do navegador (simples, mas fora do estilo do app).
- O atalho `/` não funciona em campos de formulário, por design.

## 5. Observação acadêmica

Conforme a Atividade 04, este código não deve ser enviado como PR ao projeto original sem contato prévio com os mantenedores.
