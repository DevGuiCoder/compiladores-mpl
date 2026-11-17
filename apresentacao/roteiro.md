# Demonstração e defesa do compilador MPL

Integrantes: Luiz Guilherme Silva Caride, Caio Colo e Eduuardo Bishop.

O número do grupo não foi informado. Antes de enviar o PDF ao professor,
substituam `NN` no nome `apresentacao-grupo-NN.pdf` pelo número correto.
Os nomes foram preservados conforme informados pelo grupo.

## Cinco minutos de apresentação

| Tempo | Responsável sugerido | Demonstração |
|---|---|---|
| 0:00 a 0:30 | Luiz Guilherme | Compilar e executar a vitrine, slide 1 |
| 0:30 a 1:30 | Luiz Guilherme | Linha 88, tokens e AST, slide 2 |
| 1:30 a 2:30 | Caio | Escopo de `n`, tipo e três endereços, slide 3 |
| 2:30 a 3:30 | Eduuardo | Abrir `.mplb`, acompanhar a pilha, slide 4 |
| 3:30 a 4:30 | Eduuardo | Divisão inteira e conversão, slide 5 |
| 4:30 a 5:00 | Caio | Problema real de empacotamento e validação, slide 6 |

Os slides 7 e 8 são apoio para perguntas e preparação da alteração ao vivo.
Ensaiem para que todos falem e para respeitar os cinco minutos.

## Comandos na raiz do repositório

Em Linux/Cloud Shell, com Python 3.12, Git e Make:

```sh
make prova
python3 -B -m unittest discover -s testes -p 'test_*.py' -v
./compilar exemplos/vitrine.mpl
./executar exemplos/vitrine.mplb
python3 apresentacao/demonstrar.py tokens
python3 apresentacao/demonstrar.py ast
python3 apresentacao/demonstrar.py tabela
python3 apresentacao/demonstrar.py ir
python3 apresentacao/demonstrar.py vm
```

`demonstrar.py` usa os módulos reais do compilador e extrai a atribuição
`n = n * 5 + 1;` de `vitrine.mpl`; não substitui as saídas por exemplos
decorados. O comando `python3 apresentacao/demonstrar.py programa` gera o
`.mplb`, executa a VM e compara a saída com `vitrine.saida`.
Abram também `exemplos/vitrine.mplb` no editor para mostrar o arquivo completo.

No Windows, com Python instalado, substituam `python3` pelo executável Python
3.12 disponível. A demonstração dispensa os lançadores POSIX:

```powershell
python -B apresentacao/demonstrar.py programa
python -B apresentacao/demonstrar.py todas
```

Se `python` abrir a Microsoft Store, usem o caminho do executável instalado
ou corrijam o PATH antes do ensaio. A verificação oficial com `make prova`
deve ser feita no ambiente Linux configurado na automação do repositório.

## O que explicar em cada fase

- Léxico: linha e coluna começam em 1; `n` na coluna 5 e `*` na coluna 11.
- Sintático: `+` é a raiz da expressão e `*` está abaixo, à esquerda.
- Semântico: `n` é inteiro, declarado na linha 85 no escopo 33. O uso no
  bloco do laço (34) resolve esse mesmo símbolo no pai.
- Intermediário: `t17 = n * 5`, `t18 = t17 + 1`, `n = t18`.
- VM: carregar operandos, multiplicar, guardar temporário, somar e atribuir.
  Na primeira iteração, `n = 1` passa a `6`.

## Relato técnico com honestidade

O slide 5 apresenta um caso técnico reproduzível, não uma afirmação de que
o grupo sofreu esse bug: `real meio = 7 / 2;` precisa produzir `3.000000`.
Promover os operandos antes da divisão produziria incorretamente `3.500000`.
O código atual executa a divisão inteira antes de `PARA_REAL`.

O slide 6 registra o defeito de entrega realmente constatado nesta revisão:
a pasta local tinha a E4 implementada, mas o último commit ainda continha
os esqueletos. O diagnóstico foi comparar `git status` e `git show HEAD`;
a correção é versionar os arquivos e validar o clone publicado.

O enunciado pede o defeito mais difícil enfrentado pelo grupo. Se houver
outro episódio real, substituam esse relato por sintoma, diagnóstico,
correção e teste. Não apresentem um exemplo hipotético como experiência real.

## Preparação para a alteração ao vivo

| Alteração sorteada | Partes a localizar |
|---|---|
| `**` | Léxico: operador duplo; parser: precedência e associatividade; semântica: tipos; IR, gerador e VM: operação |
| `senaose` | Palavra reservada no léxico; condicional no parser; AST compatível com semântica e IR |
| `escreva(a, b)` | Lista de argumentos no parser; validação e emissão de todos os filhos |
| `pare` | Novo comando, validação de contexto de laço e salto ao rótulo de saída |
| Curto-circuito | Emissão de desvios no IR antes de avaliar o operando direito |

Não implementem esses recursos antes do sorteio: por exemplo, a linguagem
atual exige avaliar os dois lados de `e` e `ou`.

Parser manual: uma função por nível de precedência, laços para associar
binários à esquerda. Um gerador recebe regras de gramática e produz o
reconhecedor, exigindo ainda ações para construir a AST. Comparem o controle
explícito do parser atual com a geração automática, sem afirmar que usaram
ANTLR, PLY ou yacc no projeto.

## PDF e edição

`gerar_slides.py` é o fonte editável do PDF. A biblioteca ReportLab é usada
somente para o material de apresentação; o compilador não depende dela.

```sh
python3 -m pip install reportlab
python3 apresentacao/gerar_slides.py
```

## Entrega acadêmica

A publicação no GitHub não envia o trabalho ao formulário da disciplina.
Confiram o número do grupo, enviem o repositório e a evidência no espaço da
E4 e entreguem o PDF no espaço da apresentação até as 23h59 do dia anterior.
Testem o ambiente no computador que será usado em aula e revisem o código.
