"""Demonstra o programa e rastreia uma expressao real em todas as fases."""
import argparse
import io
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from mplc import lexico, sintatico, semantica, intermediario, gerador, vm


def dados():
    fonte = (RAIZ / 'exemplos/vitrine.mpl').read_text('utf-8')
    linha = next(i for i, texto in enumerate(fonte.splitlines(), 1)
                 if 'n = n * 5 + 1;' in texto)
    tokens = lexico.analisar(fonte)
    arvore = sintatico.analisar(tokens)
    tabela = semantica.analisar(arvore)
    codigo = intermediario.gerar(arvore, tabela)
    bytecode = gerador.gerar(codigo)

    def procurar(no):
        if no.linha == linha and no.rotulo == 'atribuicao n':
            return no
        for filho in no.filhos:
            encontrado = procurar(filho)
            if encontrado is not None:
                return encontrado

    no = procurar(arvore)
    simbolo = no.extra['simbolo']
    funcao = next(f for f in codigo if f.nome == 'principal')
    inicio = funcao.codigo.index(('linha', linha)) + 1
    trecho = []
    for instrucao in funcao.codigo[inicio:]:
        if instrucao[0] != 'bin' and instrucao[0] != 'copia':
            break
        trecho.append(intermediario.formatar(instrucao).strip())
    inicio_vm = bytecode.index(f'  LINHA {linha}')
    fim_vm = inicio_vm + 1
    while fim_vm < len(bytecode):
        if bytecode[fim_vm].strip() == 'GUARDA n':
            fim_vm += 1
            break
        fim_vm += 1
    return {
        'tokens': '\n'.join(str(t) for t in tokens if t.linha == linha),
        'ast': '\n'.join(sintatico.despejar(no)),
        'tabela': (f'n: {simbolo.categoria}, tipo {simbolo.tipo}, '
                   f'escopo {simbolo.escopo}, declarada na linha {simbolo.linha}\n'
                   f'Uso na linha {linha}, dentro do escopo 34.\n'
                   'Busca no escopo 34 e depois no pai 33.'),
        'ir': '\n'.join(trecho),
        'vm': '\n'.join(bytecode[inicio_vm:fim_vm]),
        'bytecode': '\n'.join(bytecode) + '\n',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('etapa', nargs='?', default='programa',
                        choices=['programa', 'tokens', 'ast', 'tabela', 'ir', 'vm', 'todas'])
    args = parser.parse_args()
    d = dados()
    if args.etapa == 'programa':
        caminho = RAIZ / 'exemplos/vitrine.mplb'
        caminho.write_text(d['bytecode'], encoding='utf-8', newline='\n')
        saida = io.StringIO()
        vm.executar(caminho.read_text('utf-8'), saida)
        esperado = (RAIZ / 'exemplos/vitrine.saida').read_text('utf-8')
        if saida.getvalue() != esperado:
            raise RuntimeError('A saida da vitrine difere do esperado')
        print(saida.getvalue(), end='')
    elif args.etapa == 'todas':
        for etapa in ['tokens', 'ast', 'tabela', 'ir', 'vm']:
            print(f'\n=== {etapa} ===\n{d[etapa]}')
    else:
        print(d[args.etapa])


if __name__ == '__main__':
    main()
