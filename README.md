# Compilador MPL — Entrega 3

Trabalho de Compiladores — Ciência da Computação, UNISAGRADO.
Prof. Luiz Ricardo Mantovani da Silva · 2026-2.
Base acadêmica: [compiladores-lab](https://github.com/LuizRMSilva1973/compiladores-lab).

Implementação em Python 3.12, somente com a biblioteca padrão. As Entregas
1, 2 e 3 estão implementadas. Código intermediário, geração de `.mplb` e
máquina virtual ainda são os esqueletos da Entrega 4: compilar um programa
válido sem opção de despejo ainda termina com código 3 (`NaoImplementado`).

## Arquitetura

| Arquivo | Responsabilidade |
|---|---|
| `mplc/lexico.py` | Tokens com lexema, linha e coluna |
| `mplc/sintatico.py` | Parser manual por descida recursiva e AST `No` |
| `mplc/semantica.py` | Assinaturas, escopos, resolução de nomes, tipos e retornos |
| `mplc/principal.py` | CLI e encadeamento das fases |
| `mplc/erros.py` | Diagnósticos `ErroMPL` e marcação de fases pendentes |
| `mplc/intermediario.py`, `gerador.py`, `vm.py` | Interfaces preservadas para a E4 |
| `testes/` | Corpus oficial e testes adicionais em `test_semantica.py` |

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

## Execução e validação

Na raiz do repositório, em Linux/Cloud Shell com Python 3.12, GNU Make,
Git e shell POSIX:

```bash
./compilar --tokens exemplos/ola.mpl
./compilar --ast exemplos/tudo.mpl
./compilar --tabela exemplos/tudo.mpl
make verificar E=1
make verificar E=2
make verificar E=3
python3 -B -m unittest discover -s testes -p 'test_*.py' -v
make evidencias E=3
make prova E=3
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
não commitadas não entram. `make prova` sem `E` verifica as quatro entregas
e também cobrará a E4 ainda pendente. Consulte os resultados reais e as
limitações da validação em [evidencias/auditoria-e3.md](evidencias/auditoria-e3.md).

## Proveniência e entrega

O histórico Git mantém a base do professor e as implementações anteriores.
A implementação da E3, seus testes adicionais e a revisão documental
receberam auxílio do Codex. O grupo deve revisar e compreender o código
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
