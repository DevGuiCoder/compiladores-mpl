"""
Entrega 4, terceira metade — a maquina virtual.

Maquina de pilha que le o .mplb (texto) e executa. Tem:
  - uma pilha de operandos, compartilhada entre as chamadas;
  - uma pilha de REGISTROS DE ATIVACAO: cada chamada ganha o seu proprio
    dicionario de locais (parametros, variaveis e temporarios), o endereco
    de retorno e a linha do fonte em que o chamador estava;
  - deteccao de divisao/resto por zero e de estouro de pilha (erro de
    execucao, codigo de saida 2).

O laco e iterativo: a recursao da MPL nao usa a recursao do Python.
"""
from mplc.erros import ErroMPL

LIMITE_CHAMADAS = 10000


class Registro:
    """Registro de ativacao de uma chamada."""
    __slots__ = ('funcao', 'locais', 'retorno', 'linha')

    def __init__(self, funcao, retorno, linha):
        self.funcao = funcao
        self.locais = {}
        self.retorno = retorno    # pc para onde voltar
        self.linha = linha        # linha do chamador, restaurada na volta


def decodificar_texto(lexema):
    corpo, saida, i = lexema[1:-1], [], 0
    escapes = {'n': '\n', 't': '\t', '"': '"', '\\': '\\'}
    while i < len(corpo):
        c = corpo[i]
        if c == '\\' and i + 1 < len(corpo):
            saida.append(escapes.get(corpo[i + 1], corpo[i + 1]))
            i += 2
        else:
            saida.append(c)
            i += 1
    return ''.join(saida)


def carregar(texto):
    """Le o .mplb: devolve instrucoes, rotulos e funcoes."""
    instrucoes, rotulos, funcoes = [], {}, {}
    for bruta in texto.splitlines():
        linha = bruta.strip()
        if not linha or linha.startswith(';'):
            continue
        partes = linha.split(None, 1)
        op = partes[0]
        arg = partes[1] if len(partes) > 1 else None
        if op == 'ROTULO':
            rotulos[arg] = len(instrucoes)
        elif op == 'FUNCAO':
            nomes = arg.split()
            funcoes[nomes[0]] = (len(instrucoes), nomes[1:])
        else:
            instrucoes.append((op, arg))
    return instrucoes, rotulos, funcoes


def formatar(v):
    if isinstance(v, bool):
        return 'verdadeiro' if v else 'falso'
    if isinstance(v, float):
        return f'{v:.6f}'
    return str(v)


def dividir(a, b):
    if isinstance(a, int) and isinstance(b, int):
        q = abs(a) // abs(b)           # trunca em direcao a zero
        return q if (a >= 0) == (b >= 0) else -q
    return a / b


def resto(a, b):
    return a - b * dividir(a, b)       # sinal do dividendo


def executar(texto_mplb, saida):
    """Executa o bytecode. Escreve o que o programa imprimir em `saida`."""
    codigo, rotulos, funcoes = carregar(texto_mplb)
    pilha = []
    quadros = [Registro('<inicio>', None, 1)]
    linha = 1
    pc = 0

    def erro(msg):
        raise ErroMPL('execucao', linha, 1, msg)

    binarias = {
        'SOMA': lambda a, b: a + b,
        'SUB': lambda a, b: a - b,
        'MUL': lambda a, b: a * b,
        'IGUAL': lambda a, b: a == b,
        'DIFERENTE': lambda a, b: a != b,
        'MENOR': lambda a, b: a < b,
        'MENOR_IGUAL': lambda a, b: a <= b,
        'MAIOR': lambda a, b: a > b,
        'MAIOR_IGUAL': lambda a, b: a >= b,
        'E': lambda a, b: a and b,
        'OU': lambda a, b: a or b,
    }

    while True:
        op, arg = codigo[pc]
        pc += 1
        if op == 'CARREGA':
            pilha.append(quadros[-1].locais[arg])
        elif op == 'GUARDA':
            quadros[-1].locais[arg] = pilha.pop()
        elif op == 'EMPILHA_INT':
            pilha.append(int(arg))
        elif op == 'EMPILHA_REAL':
            pilha.append(float(arg))
        elif op == 'EMPILHA_LOG':
            pilha.append(arg == 'verdadeiro')
        elif op == 'EMPILHA_TXT':
            pilha.append(decodificar_texto(arg))
        elif op in binarias:
            b = pilha.pop(); a = pilha.pop()
            pilha.append(binarias[op](a, b))
        elif op in ('DIV', 'RESTO'):
            b = pilha.pop(); a = pilha.pop()
            if b == 0:
                erro('divisao por zero' if op == 'DIV' else 'resto por zero')
            pilha.append(dividir(a, b) if op == 'DIV' else resto(a, b))
        elif op == 'NEG':
            pilha.append(-pilha.pop())
        elif op == 'NAO':
            pilha.append(not pilha.pop())
        elif op == 'PARA_REAL':
            pilha.append(float(pilha.pop()))
        elif op == 'LINHA':
            linha = int(arg)
        elif op == 'DESVIA':
            pc = rotulos[arg]
        elif op == 'DESVIA_SE_FALSO':
            if not pilha.pop():
                pc = rotulos[arg]
        elif op == 'CHAMA':
            nome, n = arg.split()
            if len(quadros) > LIMITE_CHAMADAS:
                erro(f'estouro de pilha ao chamar {nome}')
            inicio, parametros = funcoes[nome]
            n = int(n)
            args = pilha[len(pilha) - n:] if n else []
            del pilha[len(pilha) - n:]
            quadro = Registro(nome, pc, linha)
            quadro.locais.update(zip(parametros, args))
            quadros.append(quadro)
            pc = inicio
        elif op in ('RETORNA', 'RETORNA_VAZIO'):
            # o valor de retorno (se houver) fica no topo da pilha
            quadro = quadros.pop()
            pc, linha = quadro.retorno, quadro.linha
        elif op == 'DESCARTA':
            pilha.pop()
        elif op == 'ESCREVA':
            saida.write(formatar(pilha.pop()) + '\n')
        elif op == 'PARA':
            return
        else:
            erro(f'instrucao desconhecida: {op}')
