"""
Entrega 4, segunda metade — geracao do codigo executavel (.mplb).

Traduz o codigo de tres enderecos para uma maquina de PILHA. O .mplb e texto:
uma instrucao por linha, opcode em maiusculas seguido dos operandos
documentados (CHAMA recebe nome e aridade; FUNCAO, nome e parametros).
Linhas que comecam com ';' sao comentarios. O conjunto de
instrucoes esta documentado no README.

Exemplo: `t2 = n * t1` vira

    CARREGA n
    CARREGA t1
    MUL
    GUARDA t2
"""
from mplc.intermediario import Const

OPERACOES = {
    '+': 'SOMA', '-': 'SUB', '*': 'MUL', '/': 'DIV', '%': 'RESTO',
    '==': 'IGUAL', '!=': 'DIFERENTE', '<': 'MENOR', '<=': 'MENOR_IGUAL',
    '>': 'MAIOR', '>=': 'MAIOR_IGUAL', 'e': 'E', 'ou': 'OU',
}
UNARIAS = {'-': 'NEG', 'nao': 'NAO'}
EMPILHA = {'inteiro': 'EMPILHA_INT', 'real': 'EMPILHA_REAL',
           'logico': 'EMPILHA_LOG', 'texto': 'EMPILHA_TXT'}


def empilhar(operando, saida):
    if isinstance(operando, Const):
        saida.append(f'  {EMPILHA[operando.tipo]} {operando.texto}')
    else:
        saida.append(f'  CARREGA {operando}')


def gerar(codigo_intermediario):
    """Devolve as linhas do arquivo .mplb."""
    s = ['; MPL bytecode - maquina de pilha', '; ponto de entrada',
         '  CHAMA principal 0', '  PARA', '']
    tipos = {f.nome: f.tipo for f in codigo_intermediario}
    for f in codigo_intermediario:
        nomes = ' '.join(n for n, _ in f.parametros)
        s.append(f'; funcao {f.nome} {f.tipo}')
        s.append(f'FUNCAO {f.nome}' + (f' {nomes}' if nomes else ''))
        for instr in f.codigo:
            k = instr[0]
            if k == 'linha':
                s.append(f'  LINHA {instr[1]}')
            elif k == 'copia':
                empilhar(instr[2], s)
                s.append(f'  GUARDA {instr[1]}')
            elif k == 'bin':
                empilhar(instr[3], s)
                empilhar(instr[4], s)
                s.append(f'  {OPERACOES[instr[2]]}')
                s.append(f'  GUARDA {instr[1]}')
            elif k == 'un':
                empilhar(instr[3], s)
                s.append(f'  {UNARIAS[instr[2]]}')
                s.append(f'  GUARDA {instr[1]}')
            elif k == 'real':
                empilhar(instr[2], s)
                s.append('  PARA_REAL')
                s.append(f'  GUARDA {instr[1]}')
            elif k == 'rotulo':
                s.append(f'ROTULO {instr[1]}')
            elif k == 'desvie':
                s.append(f'  DESVIA {instr[1]}')
            elif k == 'seFalso':
                empilhar(instr[1], s)
                s.append(f'  DESVIA_SE_FALSO {instr[2]}')
            elif k == 'chama':
                destino, nome, args = instr[1], instr[2], instr[3]
                for a in args:
                    empilhar(a, s)
                s.append(f'  CHAMA {nome} {len(args)}')
                if destino:
                    s.append(f'  GUARDA {destino}')
                elif tipos[nome] != 'vazio':
                    s.append('  DESCARTA')
            elif k == 'retorne':
                if instr[1] is None:
                    s.append('  RETORNA_VAZIO')
                else:
                    empilhar(instr[1], s)
                    s.append('  RETORNA')
            elif k == 'escreva':
                empilhar(instr[1], s)
                s.append('  ESCREVA')
            else:
                raise ValueError(instr)
        s.append('')
    return s
