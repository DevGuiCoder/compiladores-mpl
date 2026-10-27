# Entrega 3 — implementação, validação e auditoria

Data: 26/10/2026. Repositório existente, sem recriação do projeto.
Commit da implementação verificada em clone limpo: `7da8006`.

## Alterações

| Arquivo | Alteração |
|---|---|
| `mplc/semantica.py` | Substituição do esqueleto pela análise semântica e pelo despejo da tabela |
| `testes/test_semantica.py` | Novo conjunto de 20 testes, com subcasos de generalização e regressão |
| `README.md` | Arquitetura, semântica, execução, limites atuais e proveniência; tabela de tokens e BNF preservadas integralmente |
| `.gitignore` | Retirada da exclusão de `evidencias/`, permitindo versionar as evidências obrigatórias |
| `.gitattributes` | Novo controle de fim de linha LF para `compilar`, `executar` e scripts `.sh` |
| `evidencias/verificacao-3.txt` | Evidência oficial gerada pelo alvo original do Makefile |
| `evidencias/auditoria-e3.md` | Este registro final de resultados e limpeza |

A implementação usa uma lista de escopos com dicionários de símbolos e
referência ao pai. Cada função possui um escopo de parâmetros e outro de
corpo; blocos internos sombreiam nomes externos, cuja resolução é restaurada
ao sair. Duplicações no mesmo escopo e usos de identificadores inexistentes
ou de categoria incompatível são rejeitados.

A primeira passada coleta todas as assinaturas e valida `principal`.
A segunda analisa corpos, declarações, expressões, condições, argumentos e
retornos. A única promoção aceita é `inteiro` para `real`. A garantia de
retorno considera a estrutura: ambos os ramos de `se/senao` precisam retornar;
`se` sem `senao` e `enquanto` não garantem retorno. Não se avaliam condições
constantes. A AST conserva os rótulos anteriores e recebe informações de
tipos e símbolos em `extra`, disponíveis para a futura geração de código.

## Resultados após a limpeza

| Comando | Resultado real | Código de saída |
|---|---|---|
| `make verificar E=1` | 20/20 verificações aprovadas | 0 |
| `make verificar E=2` | 36/36 verificações aprovadas | 0 |
| `make verificar E=3` | 70/70 verificações aprovadas | 0 |
| `make evidencias E=3` | Arquivo gerado; conteúdo termina com 70/70 aprovadas | 0 |
| `python3 -B -m unittest discover -s testes -v` | 20 testes aprovados, incluindo seus subcasos | 0 |
| `make prova E=3` | Clone limpo: 70/70 aprovadas | 0 |
| `make prova` | E1: 20/20; E2: 36/36; E3: 70/70; E4: 70/93 | 2 |

Os dez programas válidos foram aceitos **até a fase semântica**, com os
dez despejos de tabela idênticos aos gabaritos. Os catorze programas
semanticamente inválidos foram recusados, todos na fase e linha esperadas.
As seis recusas léxicas e as seis sintáticas também mantiveram fase, linha
e coluna corretas. O contrato confere apenas a linha nos erros semânticos;
não se afirma igualdade obrigatória das colunas dessa fase.

Os testes adicionais verificam sombreamento de parâmetros e variáveis,
restauração do tipo externo, ausência de vazamento entre blocos e funções,
duplicações, chamadas antecipadas e recursão mútua, aridade, uso de `vazio`,
condições, retornos estruturais e comandos inalcançáveis. Incluem 208
combinações de operadores binários e tipos, além de 64 combinações de
tipos em inicializações, atribuições, argumentos e retornos. Também
conferem independência entre análises, preservação do despejo da AST e
diagnósticos sem saída extra em stdout.

Ambiente efetivamente usado: Windows com Git Bash, GNU Make 4.4.1 e
Python 3.12.12 do MSYS2 em uma pasta temporária. O Makefile, o verificador
e os lançadores originais foram executados sem adaptação ou substituição
das verificações. Os 20 testes também passaram no Python 3.12 nativo.
`PYTHONDONTWRITEBYTECODE=1` impediu recriação dos caches durante as
verificações finais. As ferramentas temporárias não pertencem ao projeto.
Não foi realizada uma execução no serviço Google Cloud Shell.

## Arquivos removidos

Foram removidos somente dez caches de bytecode Python, já ignorados pelo
Git e regeneráveis a partir dos fontes:

```text
__pycache__/verificar.cpython-312.pyc
mplc/__pycache__/__init__.cpython-312.pyc
mplc/__pycache__/erros.cpython-312.pyc
mplc/__pycache__/gerador.cpython-312.pyc
mplc/__pycache__/intermediario.cpython-312.pyc
mplc/__pycache__/lexico.cpython-312.pyc
mplc/__pycache__/principal.cpython-312.pyc
mplc/__pycache__/semantica.cpython-312.pyc
mplc/__pycache__/sintatico.cpython-312.pyc
mplc/__pycache__/vm.cpython-312.pyc
```

Os dois diretórios `__pycache__` correspondentes também foram removidos.
A inspeção dos arquivos versionados, importações, Makefile e referências
não identificou dependência desses caches. Nenhum fonte ou arquivo
versionado anterior foi excluído. Não foram encontrados backups, logs de
depuração, prompts, instruções de agentes ou transcrições dispensáveis
dentro do repositório.

## Arquivos preservados

- Histórico Git anterior, sem reescrita, e permissões `100755` dos lançadores.
- `mplc/lexico.py`, `mplc/sintatico.py`, CLI, erros e interfaces da E4.
- `Makefile`, `verificar.py` e `autoteste.sh`, sem alteração no corretor.
- Corpus completo em `testes/positivos`, `testes/negativos` e `testes/fases`.
- `LINGUAGEM.md`, `CONTRATOS.md`, todos os enunciados de `entregas/` e exemplos.
- `evidencias/verificacao-1.txt` e `evidencias/verificacao-2.txt`, sem regeneração.
- Tabela de tokens e BNF do README, comparadas integralmente com a versão anterior.
- Comentários técnicos úteis e informações de origem acadêmica. O README
  registra explicitamente o auxílio do Codex na E3 e nos testes adicionais.

## Limitação restante

**`make prova` sem filtro não passou.** Ele verifica as quatro entregas.
As 23 provas pendentes são dez despejos de IR, dez execuções positivas e
três erros de execução. A causa é anterior a esta implementação:
`mplc/intermediario.py`, `mplc/gerador.py` e `mplc/vm.py` ainda contêm os
esqueletos da E4. A execução para na ausência de código intermediário.

Essa falha não foi mascarada com alterações no Makefile, no corretor ou
nos testes. A prova específica da E3 passou no clone do commit indicado,
confirmando que sua implementação não depende de arquivos locais esquecidos.
Não há regressões observadas nas Entregas 1 e 2 nem falhas observadas na E3;
isso não constitui validação do corpus oculto ou da execução da E4.
