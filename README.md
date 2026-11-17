# Compilador MPL — Entrega 4

Trabalho de Compiladores — Ciência da Computação, UNISAGRADO.
Prof. Luiz Ricardo Mantovani da Silva · 2026-2.
Base acadêmica: [compiladores-lab](https://github.com/LuizRMSilva1973/compiladores-lab).

Integrantes: Luiz Guilherme Silva Caride, Caio Colo e Eduuardo Bishop.

Implementação em Python 3.12, somente com a biblioteca padrão. As quatro
entregas estão implementadas: análise léxica, sintática e semântica,
código de três endereços, geração do `.mplb` (texto legível) e a máquina
virtual de pilha que o executa.

## Arquitetura

| Arquivo | Responsabilidade |
|---|---|
| `mplc/lexico.py` | Tokens com lexema, linha e coluna |
| `mplc/sintatico.py` | Parser manual por descida recursiva e AST `No` |
| `mplc/semantica.py` | Assinaturas, escopos, resolução de nomes, tipos e retornos |
| `mplc/principal.py` | CLI e encadeamento das fases |
| `mplc/erros.py` | Diagnósticos `ErroMPL` e marcação de fases pendentes |
| `mplc/intermediario.py` | Código de três endereços (`--ir`) |
| `mplc/gerador.py` | Tradução do três endereços para o `.mplb` de pilha |
| `mplc/vm.py` | Máquina virtual de pilha com registros de ativação |
| `testes/` | Corpus oficial e testes adicionais de semântica e execução |

As regras normativas estão em [LINGUAGEM.md](LINGUAGEM.md), os formatos em
[CONTRATOS.md](CONTRATOS.md) e os critérios em [entregas/](entregas/).
O corretor e o corpus oficial são preservados. A tabela de tokens e a
BNF abaixo também são requisitos das entregas anteriores.

## Entrega 3 — análise semântica

### Representação dos escopos

Os escopos são dicionários encadeados pela referência ao pai, mantidos em
uma lista na ordem de abertura para produzir um despejo determinístico.
O escopo global contém as funções, cada função abre um escopo de parâmetros
e outro para o corpo, e cada bloco interno, inclusive vazio, cria um escopo;
ao encerrar a visita ao bloco, a análise retoma o escopo pai.
A busca percorre o escopo atual e seus pais, permitindo que uma declaração
interna sombreie a externa e que a externa volte a ser encontrada ao sair.
Cada uso de identificador na AST referencia o símbolo resolvido, que registra
seu escopo e tipo, permitindo associar posições de memória a símbolos distintos na E4
sem confundir variáveis de mesmo nome nem repetir a resolução de nomes.

### Declarações, tipos e retornos

Um símbolo registra nome, categoria, tipo, linha, número do escopo e, para
funções, a tupla dos tipos dos parâmetros. Uma declaração duplicada é
recusada no mesmo escopo; parâmetros podem ser sombreados no bloco do corpo.
Os corpos são percorridos em ordem, de modo que declarações locais
posteriores não ficam disponíveis antecipadamente. A declaração entra na
tabela antes da análise do seu inicializador.

A primeira passada registra todas as assinaturas e rejeita funções
repetidas, sem sobrecarga. Confere também a existência de `principal`,
com retorno `vazio` e sem parâmetros. A segunda passada percorre cada
corpo, insere parâmetros e variáveis, resolve identificadores e valida
expressões e comandos. Assim, chamadas antecipadas e recursão mútua são
aceitas semanticamente. Chamadas exigem um símbolo de função, a quantidade
correta de argumentos e tipos compatíveis.

Só há promoção implícita de `inteiro` para `real`, em inicializações,
atribuições, argumentos, retornos e operações numéricas compatíveis.
`+` também aceita dois textos; `%` exige inteiros; comparações de ordem
exigem números; igualdade aceita tipos iguais ou números compatíveis;
operadores lógicos e condições exigem `logico`. Chamadas de retorno
`vazio` só são permitidas como comando. A análise anota `tipo`, `simbolo`
e `escopo` em `No.extra`, conforme o nó, sem mudar os rótulos do `--ast`.
O tipo de `7 / 2` continua `inteiro`, mesmo ao atribuí-lo a uma variável
`real`; a promoção não altera o tipo dos operandos da divisão.

A garantia de retorno é estrutural: `retorne` garante retorno, um bloco
garante se algum de seus comandos garante, e `se/senao` exige garantia
nos dois ramos. `se` sem `senao` e `enquanto` não garantem retorno, mesmo
com condição literal `verdadeiro`. Não se avaliam condições constantes.
Comandos após um retorno também são verificados para detectar nomes e
tipos inválidos. Funções não vazias sem garantia são diagnosticadas na
linha da declaração da função.

A análise para no primeiro erro encontrado: primeiro as assinaturas e a
entrada do programa, depois os corpos em ordem de fonte, com expressões
da esquerda para a direita. Diagnósticos usam as posições da AST e o
formato de `ErroMPL`; a CLI os envia a stderr com código 1. A ausência de
`principal` é ancorada em linha 1, coluna 1. Não há mensagens de depuração
em stdout. Divisão por zero é assunto da execução, não desta fase.

## Entrega 4 — código intermediário, geração e máquina virtual

```bash
./compilar --ir exemplos/vitrine.mpl          # código de três endereços
./compilar exemplos/vitrine.mpl               # grava exemplos/vitrine.mplb
./executar exemplos/vitrine.mplb              # roda na VM
make verificar E=4
```

### Código de três endereços (`mplc/intermediario.py`)

A AST anotada pela semântica é percorrida e cada expressão composta é
quebrada com temporários `t0, t1, ...`, de modo que **cada linha tem no
máximo um operador** (`t2 = t0 + t1`). As formas são: `d = a`,
`d = a op b`, `d = op a`, `d = paraReal a`, `L:`, `desvie L`,
`seFalso a desvie L`, `d = chama f a, b`, `retorne a` e `escreva a`.
Linhas `; linha N` marcam o comando do fonte, para os erros de execução.

Cada símbolo resolvido pela E3 vira um nome único dentro da função; um nome
sombreado ganha o sufixo `@escopo` (`x@5`), que não colide com nenhum
identificador da MPL. A promoção `inteiro → real` é uma instrução explícita
(`paraReal`), emitida **depois** da operação inteira: em `real x = 7 / 2;`
a divisão inteira dá `3` e só então vira `3.000000`.

### Máquina virtual (`mplc/vm.py`)

Máquina de pilha com uma pilha de operandos e uma pilha de **registros de
ativação**. Cada `CHAMA` cria um registro novo com seus próprios locais
(parâmetros, variáveis e temporários), o endereço de retorno e a linha do
chamador; `RETORNA` o descarta. Por isso a recursão direta e a mútua
funcionam: `fatorial(5)` não sobrescreve o `n` de `fatorial(4)`. O laço da
VM é iterativo (não usa a recursão do Python). Mais de 10000 chamadas
aninhadas é estouro de pilha.

A divisão inteira trunca em direção a zero e o resto é calculado como
`a - b * (a / b)`, o que dá ao resto o sinal do dividendo (`-7 % 3 = -1`),
em vez do `%` do Python. Divisão ou resto por zero e estouro de pilha
terminam com `erro execucao: linha L, ...` e código de saída 2.

### Formato do `.mplb`

Texto, uma instrução por linha: opcode em maiúsculas seguido dos operandos
documentados abaixo. `CHAMA` recebe nome e aridade; `FUNCAO` recebe nome e
parâmetros. Linhas começando com `;` são comentários. O arquivo começa com
`CHAMA principal 0` / `PARA`, seguido das funções. Exemplo (`t2 = n * t1`):

```
  CARREGA n
  CARREGA t1
  MUL
  GUARDA t2
```

### Conjunto de instruções da VM

| Instrução | O que faz com a pilha |
|---|---|
| `FUNCAO f p1 p2 ...` | pseudo-instrução: marca o início de `f` e os nomes dos parâmetros; não mexe na pilha |
| `ROTULO L` | pseudo-instrução: marca um destino de desvio; não mexe na pilha |
| `EMPILHA_INT n` | empilha o inteiro `n` |
| `EMPILHA_REAL x` | empilha o real `x` |
| `EMPILHA_LOG v` | empilha `verdadeiro` ou `falso` |
| `EMPILHA_TXT "s"` | empilha o texto `s` (escapes `\n \t \" \\` decodificados) |
| `CARREGA x` | empilha o valor do local `x` do registro de ativação atual |
| `GUARDA x` | desempilha o topo e grava no local `x` do registro atual |
| `DESCARTA` | desempilha o topo e o joga fora (resultado de chamada usada como comando) |
| `SOMA` | desempilha `b` e `a`, empilha `a + b` (números ou concatenação de textos) |
| `SUB` | desempilha `b` e `a`, empilha `a - b` |
| `MUL` | desempilha `b` e `a`, empilha `a * b` |
| `DIV` | desempilha `b` e `a`, empilha `a / b` (inteira truncada para zero se os dois forem inteiros); `b = 0` é erro de execução |
| `RESTO` | desempilha `b` e `a`, empilha o resto com o sinal do dividendo; `b = 0` é erro de execução |
| `NEG` | desempilha `a`, empilha `-a` |
| `PARA_REAL` | desempilha um inteiro, empilha o mesmo valor como real |
| `IGUAL` | desempilha `b` e `a`, empilha `a == b` |
| `DIFERENTE` | desempilha `b` e `a`, empilha `a != b` |
| `MENOR` | desempilha `b` e `a`, empilha `a < b` |
| `MENOR_IGUAL` | desempilha `b` e `a`, empilha `a <= b` |
| `MAIOR` | desempilha `b` e `a`, empilha `a > b` |
| `MAIOR_IGUAL` | desempilha `b` e `a`, empilha `a >= b` |
| `E` | desempilha `b` e `a` (já avaliados, sem curto-circuito), empilha `a e b` |
| `OU` | desempilha `b` e `a`, empilha `a ou b` |
| `NAO` | desempilha `a`, empilha `nao a` |
| `DESVIA L` | não mexe na pilha; continua no rótulo `L` |
| `DESVIA_SE_FALSO L` | desempilha a condição; se for `falso`, continua no rótulo `L` |
| `CHAMA f n` | desempilha os `n` argumentos, cria um registro de ativação para `f` com eles nos parâmetros e salta para `f` |
| `RETORNA` | deixa o valor de retorno no topo, descarta o registro atual e volta ao chamador |
| `RETORNA_VAZIO` | não mexe na pilha; descarta o registro atual e volta ao chamador |
| `ESCREVA` | desempilha o topo e o imprime no formato da seção 4.5 (real com 6 casas, `verdadeiro`/`falso`) |
| `LINHA n` | não mexe na pilha; registra a linha do fonte em execução (para mensagens de erro) |
| `PARA` | encerra a máquina |

### Programa do grupo: `exemplos/vitrine.mpl`

Como a MPL não converte número em texto, o programa primeiro escreve essa
conversão na própria MPL (`naBase`, recursiva, para qualquer base de 2 a
10) e depois a usa para mostrar a Torre de Hanói com 3 discos (recursão em
função `vazio`), a contagem de movimentos (`2^n - 1`, recursiva), números em
binário e octal, raiz quadrada pelo método de Newton (reais e promoção de
argumento `raiz(10)`), os passos de Collatz de 27 e as duas armadilhas da
divisão. A saída esperada está em `exemplos/vitrine.saida`.

## Execução e validação

Na raiz do repositório, em Linux/Cloud Shell com Python 3.12, GNU Make,
Git e shell POSIX:

```bash
./compilar --tokens exemplos/ola.mpl
./compilar --ast exemplos/tudo.mpl
./compilar --tabela exemplos/tudo.mpl
./compilar --ir exemplos/tudo.mpl
./compilar exemplos/tudo.mpl && ./executar exemplos/tudo.mplb
make verificar E=1
make verificar E=2
make verificar E=3
make verificar E=4
python3 -B -m unittest discover -s testes -p 'test_*.py' -v
make evidencias E=4
make prova E=4
make prova
```

`--tokens`, `--ast` e `--tabela` param na fase pedida e não geram `.mplb`.
O verificador da E3 confere os dez programas válidos e os catorze erros
semânticos, além das entregas anteriores. Os testes adicionais cobrem
sombreamento e restauração, escopos vazios, chamadas antecipadas, recursão,
matrizes de operadores e conversões, retornos estruturais e a CLI.

`make evidencias E=3` grava `evidencias/verificacao-3.txt`. As evidências
fazem parte da entrega e devem ser versionadas. `make prova E=3` verifica
a entrega atual em um clone temporário do **último commit**; alterações
não commitadas não entram. `make prova` sem `E` verifica as quatro entregas.
`make evidencias E=4` grava `evidencias/verificacao-4.txt`. Consulte os resultados reais e as
limitações da validação em [evidencias/auditoria-e4.md](evidencias/auditoria-e4.md).
A auditoria da E3 permanece como registro histórico daquela entrega.

A automação em `.github/workflows/verificar.yml` executa as quatro entregas,
os testes adicionais e o programa do grupo em um clone Linux. O roteiro de
demonstração está em [apresentacao/roteiro.md](apresentacao/roteiro.md), junto
dos [slides em PDF](apresentacao/apresentacao-grupo-NN.pdf). Substitua `NN`
pelo número do grupo antes de enviar o PDF à disciplina.

## Proveniência e entrega

O histórico Git mantém a base do professor e as implementações anteriores.
A implementação da E3, seus testes adicionais e a revisão documental
receberam auxílio do Codex. A finalização da E4, os testes de execução,
a automação e o material de apresentação também receberam esse auxílio.
O grupo deve revisar e compreender o código
para a defesa e as alterações ao vivo previstas no enunciado; esta nota
não substitui as regras acadêmicas em [entregas/APRESENTACAO.md](entregas/APRESENTACAO.md).

Para entregar, envie o repositório do grupo e a evidência correspondente
pelo formulário da [página do trabalho](https://profluiz.mantovanitec.com/disciplinas/aulas/compiladores/trabalho.html).
Preserve os enunciados, os testes e as evidências das entregas anteriores.

## Tabela de tokens

O analisador léxico percorre o fonte uma vez, mantendo linha e coluna a partir
de 1. As expressões abaixo usam a notação usual de expressões regulares; nos
casos de operadores, delimitadores e palavras reservadas, o reconhecimento é
literal.

| Token(s) | Forma reconhecida |
|---|---|
| `ID` | `[A-Za-z_][A-Za-z0-9_]*`, desde que não seja palavra reservada |
| `INTEIRO` | `[0-9]+` |
| `REAL` | `[0-9]+\.[0-9]+` |
| `TEXTO` | `"([^"\\\r\n]|\\[nt"\\])*"` |
| `LOGICO` | `verdadeiro` ou `falso` |
| `FUNCAO`, `RETORNE`, `SE`, `SENAO`, `ENQUANTO`, `ESCREVA` | `funcao`, `retorne`, `se`, `senao`, `enquanto`, `escreva` |
| `TIPO_INTEIRO`, `TIPO_REAL`, `TIPO_LOGICO`, `TIPO_TEXTO`, `TIPO_VAZIO` | `inteiro`, `real`, `logico`, `texto`, `vazio` |
| `E`, `OU`, `NAO` | `e`, `ou`, `nao` |
| `MAIS`, `MENOS`, `VEZES`, `DIVIDE`, `RESTO` | `+`, `-`, `*`, `/`, `%` |
| `IGUAL`, `DIFERENTE`, `MENOR`, `MENOR_IGUAL`, `MAIOR`, `MAIOR_IGUAL` | `==`, `!=`, `<`, `<=`, `>`, `>=` |
| `ATRIBUI` | `=` |
| `ABRE_PAR`, `FECHA_PAR`, `ABRE_CHAVE`, `FECHA_CHAVE` | `(`, `)`, `{`, `}` |
| `VIRGULA`, `PONTO_VIRGULA` | `,`, `;` |
| `FIM_ARQUIVO` | fim da entrada; lexema vazio |

Espaços (`[ \t\r\n]+`) e comentários de linha (`//` até a quebra) ou de
bloco (`/*` até o primeiro `*/`) são consumidos sem produzir token. Os
operadores de dois caracteres são tentados antes dos de um caractere. Em
textos, apenas `\n`, `\t`, `\"` e `\\` são escapes válidos; o lexema conserva
aspas e escapes exatamente como escritos.

## Gramática BNF da análise sintática

Os nomes em maiúsculas são tokens da tabela anterior. `ε` representa a
sequência vazia.

```bnf
<programa> ::= <funcao> <programa> | ε

<funcao> ::= FUNCAO <tipo-retorno> ID ABRE_PAR <parametros-op> FECHA_PAR <bloco>
<tipo-retorno> ::= <tipo> | TIPO_VAZIO
<tipo> ::= TIPO_INTEIRO | TIPO_REAL | TIPO_LOGICO | TIPO_TEXTO
<parametros-op> ::= <parametros> | ε
<parametros> ::= <parametro> <parametros-cauda>
<parametros-cauda> ::= VIRGULA <parametro> <parametros-cauda> | ε
<parametro> ::= <tipo> ID

<bloco> ::= ABRE_CHAVE <comandos> FECHA_CHAVE
<comandos> ::= <comando> <comandos> | ε
<comando> ::= <declaracao>
            | ID <comando-id>
            | SE ABRE_PAR <expressao> FECHA_PAR <bloco> <senao-op>
            | ENQUANTO ABRE_PAR <expressao> FECHA_PAR <bloco>
            | ESCREVA ABRE_PAR <expressao> FECHA_PAR PONTO_VIRGULA
            | RETORNE <expressao-op> PONTO_VIRGULA
            | <bloco>
<declaracao> ::= <tipo> ID <inicializador-op> PONTO_VIRGULA
<inicializador-op> ::= ATRIBUI <expressao> | ε
<comando-id> ::= ATRIBUI <expressao> PONTO_VIRGULA
               | ABRE_PAR <argumentos-op> FECHA_PAR PONTO_VIRGULA
<senao-op> ::= SENAO <bloco> | ε
<expressao-op> ::= <expressao> | ε

<expressao> ::= <e-ou> <ou-cauda>
<ou-cauda> ::= OU <e-ou> <ou-cauda> | ε
<e-ou> ::= <igualdade> <e-cauda>
<e-cauda> ::= E <igualdade> <e-cauda> | ε
<igualdade> ::= <relacional> <igualdade-cauda>
<igualdade-cauda> ::= <op-igualdade> <relacional> <igualdade-cauda> | ε
<op-igualdade> ::= IGUAL | DIFERENTE
<relacional> ::= <aditiva> <relacional-cauda>
<relacional-cauda> ::= <op-relacional> <aditiva> <relacional-cauda> | ε
<op-relacional> ::= MENOR | MENOR_IGUAL | MAIOR | MAIOR_IGUAL
<aditiva> ::= <multiplicativa> <aditiva-cauda>
<aditiva-cauda> ::= <op-aditivo> <multiplicativa> <aditiva-cauda> | ε
<op-aditivo> ::= MAIS | MENOS
<multiplicativa> ::= <unaria> <multiplicativa-cauda>
<multiplicativa-cauda> ::= <op-multiplicativo> <unaria> <multiplicativa-cauda> | ε
<op-multiplicativo> ::= VEZES | DIVIDE | RESTO
<unaria> ::= NAO <unaria> | MENOS <unaria> | <primaria>
<primaria> ::= INTEIRO | REAL | LOGICO | TEXTO
             | ID <chamada-op>
             | ABRE_PAR <expressao> FECHA_PAR
<chamada-op> ::= ABRE_PAR <argumentos-op> FECHA_PAR | ε
<argumentos-op> ::= <argumentos> | ε
<argumentos> ::= <expressao> <argumentos-cauda>
<argumentos-cauda> ::= VIRGULA <expressao> <argumentos-cauda> | ε
```

A ordem das produções de expressão vai da precedência mais fraca (`ou`) à
mais forte (chamada e parênteses). No código, cada produção `*-cauda` é um
laço que acumula a árvore pela esquerda, portanto todos os binários são
associativos à esquerda. `<unaria>` chama a si mesma, tornando `nao` e o
menos unário associativos à direita.

---
