# Relatório Final – Atividade 04: Manutenção em Projeto Existente com Agente

**Projeto:** flaskToDo, uma lista de tarefas simples em Flask + SQLite (projeto open source de DogukanUrker)
**Agente:** Claude Code (extensão do VS Code)
**Entrega:** fork com cinco branches cumulativas, `v1.1` a `v1.5`, cada uma com um relatório técnico próprio (`RELATORIO_ATIVIDADE_A.md` a `E.md`)

> Este documento trata da **experiência** de trabalhar com o agente num projeto existente e das dificuldades encontradas. O que foi implementado, como compilar e como testar está nos relatórios técnicos de cada etapa.


---

## 1. Resumo do que aconteceu

Escolhemos um projeto pequeno e fácil de entender (cerca de cinco arquivos de código) e definimos três melhorias na Atividade 03. A cada etapa o trabalho foi pedido em português, em linguagem de produto ("selo colorido", "campo de busca"), sem especificar arquivos nem técnicas:

| Etapa | Pedido | Branch |
|---|---|---|
| A | Prioridade e data de vencimento | `v1.1` |
| B | Categorias e busca | `v1.2` |
| C | Consultas parametrizadas, POST, conexões fechadas e testes | `v1.3` |
| D | "Uma mudança no front end para deixar mais fácil de usar" | `v1.4` |
| E | Versão escura | `v1.5` |

As etapas D e E não estavam no plano original; surgiram durante o trabalho. Ao final o projeto tem 44 testes automatizados passando.

## 2. Familiaridade prévia

- **Flask, SQLite, HTML/CSS/JS:** Alguns membros do grupo já haviam feito projetos que utilizavam essas ferramentas.
- **pytest e testes automatizados:** Todos os membros já haviam utilizado anteriormente.
- **Git e Github:** Todos os membros já estão familiarizados.
- **Trabalho com agentes de código antes desta disciplina:** Todos os membros já utilizam agentes no dia a dia para seus projetos.

## 3. Como foi trabalhar com um projeto que já existia

**O agente leu antes de escrever.** Antes de qualquer alteração ele leu todos os arquivos. Como o projeto é pequeno, deu para entender tudo de uma vez. Isso fez diferença: as decisões seguintes respeitaram o que já existia. Por exemplo, as colunas novas foram adicionadas no fim da tabela porque o template acessava os dados por posição, e o banco existente foi migrado em vez de recriado. Isso preservou as tarefas já cadastradas.

**O código existente tinha defeitos que não pedimos para corrigir.** Ao ler o projeto apareceram problemas que não eram do nosso plano, como um botão de salvar que sempre editava a primeira tarefa, consultas SQL montadas com texto e um `delete` que mexia nos contadores de todas as tabelas. Ficou claro que manutenção não é só acrescentar: o agente precisou decidir o que corrigir e o que apenas registrar. Em geral, o que bloqueava a nossa melhoria foi corrigido, e o resto foi documentado nos relatórios como limitação.

## 4. O que funcionou

- **Pedidos em linguagem de produto funcionaram bem** para etapas bem delimitadas (A, B, C). O agente traduziu "selo colorido" e "tarefas atrasadas em vermelho" em decisões concretas sem precisar de especificação técnica.
- **Fazer em etapas pequenas.** Cada etapa terminava com um relatório e uma verificação, e a seguinte partia de um estado conhecido. Isso reduziu surpresas.
- **Testar sem depender do navegador.** O agente validava cada etapa com o cliente de teste do Flask, usando uma *cópia* do banco, de modo que nossos dados reais nunca foram tocados durante o desenvolvimento.
- **Relatório por etapa.** Pedir um documento a cada etapa obrigou a registrar decisões e limitações no momento em que elas surgiam, e não de memória no final.
- **A etapa C compensou o investimento.** Os testes (36 nessa etapa) passaram a servir de rede de segurança para as etapas D e E, que mexeram bastante em template e CSS.

## 5. O que não funcionou tão bem e dificuldades

### 5.1 Pedido vago produz decisões que não foram nossas
Na etapa D o pedido foi "uma mudança no front end para deixar mais fácil de usar". Sem critério, o agente escolheu sozinho o que melhorar (formulário no topo, confirmação ao excluir, layout de celular etc.). O resultado foi razoável, mas foi **escolha do agente**, registrada como tal no relatório D. Aprendizado: quanto mais aberto o pedido, mais o resultado reflete o agente e menos a nossa intenção. Ter dado um exemplo de "fácil de usar" teria evitado essa dependência.

### 5.2 Ninguém viu a interface funcionando
O agente trabalhou sem navegador. Todo o front end (cores, alinhamento, layout de celular, contraste do tema escuro) foi verificado **apenas olhando o HTML e o CSS gerados**, nunca a tela real. Os testes confirmam que o botão de tema existe e que o CSS define as variáveis, mas não que o resultado fica bonito ou legível. Essa é a maior lacuna de verificação do trabalho e foi sinalizada em cada relatório; Por isso o grupo sempre conferiu manualmente.

### 5.3 Os testes foram escritos pelo mesmo agente que escreveu o código
Isso é um risco real: se o agente entendeu errado um requisito, o código e o teste tendem a repetir o mesmo erro, e a suíte passa mesmo assim. Na prática, os testes que mais falharam foram por problemas **do próprio teste**, e não do app (ver 5.4 e 6.4). Os testes ajudam contra regressões e injeção de SQL, mas não substituem uma revisão humana do que o app deveria fazer.

### 5.4 Erros de ferramenta e de ambiente (ocorreram pequenos, mas custaram tempo)
- **Script grande no terminal falhou na análise do shell.** Um *heredoc* longo com Python foi rejeitado e nada rodou. A solução foi criar os arquivos com a ferramenta de escrita e executar o script a partir de um arquivo, o que acabou sendo mais reprodutível.
- **Console do Windows e acentos.** Um teste falhou ao imprimir um caractere ("ğ", que já estava numa tarefa do banco) por causa da codificação do console. Não era bug do app.
- **Uma correção automática com `sed` apagou uma barra invertida** (`\s` virou `s`), e os mesmos quatro testes continuaram falhando até a correção ser feita diretamente no arquivo.
- **Arquivos mudando por fora.** Em vários momentos o agente foi avisado de que arquivos tinham sido alterados no disco entre uma leitura e uma escrita, e precisou reler antes de editar. Isso protegeu contra sobrescrever mudanças, mas mostra que o agente e o editor estavam mexendo nos mesmos arquivos ao mesmo tempo.

## 6. Inesperado

### 6.1 O banco de dados foi sendo modificado pelo uso
O `todos.db` estava versionado e aparecia como modificado por causa do uso normal do app. Decidimos **não incluí-lo nos commits** das branches, e o app migra o banco sozinho ao iniciar.

### 6.2 Testes quebrados por mudança de formato, não de comportamento
Na etapa D, quatro testes antigos falharam porque o HTML passou a ter atributos em várias linhas e o teste procurava tudo numa linha. O app estava correto; o teste era frágil demais. Foi a prova de que testar o HTML por expressão regular é frágil.

## 7. O que aprendemos

1. Agentes são bons em ler um projeto pequeno e fazer mudanças coerentes com ele, mas **decidem muito quando o pedido é aberto**.
2. Testes automatizados valem mais quando alguém além do autor os revisa, e isso vale também quando o autor é um agente.
3. Manutenção envolve decidir o que **não** mexer: parte do valor foi o agente registrar problemas encontrados em vez de corrigir tudo.
4. Um relatório curto por etapa, escrito na hora, foi mais fiel do que um resumo escrito no fim.

## 8. O que faríamos diferente

- Descrever o resultado esperado de pedidos abertos (como a etapa D), com pelo menos um exemplo.
- Pedir a revisão dos testes por uma segunda pessoa ou por uma segunda passada do agente com a instrução de procurar casos que o primeiro conjunto não cobre.