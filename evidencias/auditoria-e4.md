# Entrega 4 - finalização e validação

Data: 16/11/2026.

## Escopo

Finalização da implementação já existente de código intermediário, geração
de bytecode textual e máquina virtual. Preservados o corretor, o corpus
oficial e os enunciados. O README agora descreve corretamente os operandos
das instruções e aponta para esta auditoria, mantendo a E3 como histórico.

O programa do grupo é `exemplos/vitrine.mpl`, acompanhado de sua saída.
A apresentação tem PDF, fonte editável e roteiro de execução com nomes
informados pelo usuário. O número do grupo continua representado por `NN`.

## Resultados locais

- Python 3.12 no Windows: 27 testes adicionais passaram (20 da semântica e
  7 da geração/execução, incluindo subcasos e todos os programas positivos).
- Verificador E4: 93/93 passaram na revisão inicial, adaptando somente a
  chamada dos lançadores em memória para o Python nativo. O arquivo
  `verificar.py` não foi alterado. Esse teste não prova o ambiente POSIX.
- A execução da vitrine produziu exatamente a saída esperada.

Os testes adicionais da E4 verificam divisão inteira e resto com sinais,
promoção após a divisão, preservação de locais em recursão, nomes que
parecem temporários, sombreamento, conversões de argumento/retorno,
descarte de resultados, avaliação dos dois operandos lógicos e restauração
da linha do chamador no diagnóstico de execução.

## Clone limpo e publicação

Na revisão inicial, o último commit ainda tinha os esqueletos da E4. A
implementação local, a evidência e o programa próprio precisavam entrar no
histórico. A automação `.github/workflows/verificar.yml` valida em Ubuntu
com Python 3.12: `make prova`, os 27 testes, a vitrine e a correspondência
da evidência versionada com a saída real do verificador.

A execução Linux do commit `4ca8c75743ce84b952429ea9a0ee530eaf810e10`
foi concluída com sucesso em 16/11/2026:
[GitHub Actions, execução 43985556714](https://github.com/DevGuiCoder/compiladores-mpl/actions/runs/43985556714).

| Etapa | Resultado observado |
|---|---|
| `make prova` | Aprovado em clone limpo, nas quatro entregas |
| Testes adicionais | Aprovados, 27 testes com subcasos |
| Programa do grupo | Compilação, execução e comparação da saída aprovadas |
| Evidência E4 | Saída atual do verificador idêntica ao arquivo versionado |

O PDF foi renderizado e inspecionado nas oito páginas; o hash do arquivo
local é igual ao do blob publicado. `.gitattributes` o marca como binário
para impedir conversões de fim de linha que poderiam danificar o documento.
A demonstração `apresentacao/demonstrar.py programa` também foi executada
localmente e conferiu a saída esperada.

## Limites

O corpus oculto da disciplina não foi disponibilizado. Os resultados não
substituem a defesa, o ensaio no computador da apresentação ou o envio pelo
formulário acadêmico. O caso de divisão inteira nos slides é uma explicação
técnica, sem atribuir ao grupo uma experiência de depuração não relatada.
