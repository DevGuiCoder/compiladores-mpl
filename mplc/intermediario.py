"""
Entrega 4, primeira metade — codigo de tres enderecos.

A AST anotada pela semantica vira uma lista de funcoes, cada uma com uma
lista de instrucoes em que ha NO MAXIMO UM OPERADOR. Expressoes compostas
sao quebradas com temporarios (t0, t1, ...).

Instrucoes (tuplas), e como aparecem no --ir:

  ('linha', n)                  ; linha n         (marca o comando do fonte)
  ('copia', d, a)               d = a
  ('bin', d, op, a, b)          d = a op b
  ('un', d, op, a)              d = op a          (op: -, nao)
  ('real', d, a)                d = paraReal a    (promocao inteiro -> real)
  ('rotulo', L)                 L:
  ('desvie', L)                 desvie L
  ('seFalso', a, L)             seFalso a desvie L
  ('chama', d|None, f, args)    d = chama f a, b  /  chama f a, b
  ('retorne', a|None)           retorne a  /  retorne
  ('escreva', a)                escreva a

Operandos: str (nome de variavel ou temporario) ou Const (literal).
Cada simbolo da semantica vira um nome unico dentro da funcao; um nome
sombreado ganha o sufixo @<escopo> (ex.: x@5), que nao colide com nenhum
identificador da MPL.
"""
import re

PADROES = {'inteiro': '0', 'real': '0.0', 'logico': 'falso', 'texto': '""'}


class Const:
    def __init__(self, tipo, texto):
        self.tipo = tipo      # 'inteiro', 'real', 'logico', 'texto'
        self.texto = texto    # forma do fonte: 42, 3.5, verdadeiro, "a\n"

    def __str__(self):
        return self.texto


class Funcao:
    def __init__(self, nome, tipo, parametros):
        self.nome = nome
        self.tipo = tipo
        self.parametros = parametros   # [(nome_ir, tipo)]
        self.codigo = []


class Gerador:
    def __init__(self):
        self.rotulos = 0

    def novo_rotulo(self):
        r = f'L{self.rotulos}'
        self.rotulos += 1
        return r

    def novo_temp(self):
        t = f't{self.temps}'
        self.temps += 1
        return t

    def emitir(self, *instr):
        self.funcao.codigo.append(instr)

    def nome(self, simbolo):
        chave = id(simbolo)
        if chave not in self.nomes:
            base = simbolo.nome
            if re.match(r'(e|ou|nao)(?![a-zA-Z_])', base):
                # e1, ou2... pareceriam os operadores e/ou/nao no --ir
                base = f'_{base}@{simbolo.escopo}'
            elif base in self.usados or re.fullmatch(r't\d+', base):
                base = f'{simbolo.nome}@{simbolo.escopo}'
            self.usados.add(base)
            self.nomes[chave] = base
        return self.nomes[chave]

    # ------------------------------------------------------------------
    def programa(self, arvore):
        funcoes = []
        for no in arvore.filhos:
            self.temps = 0
            self.nomes = {}
            self.usados = set()
            params = [(self.nome(p.extra['simbolo']), p.extra['tipo'])
                      for p in no.filhos[0].filhos]
            self.funcao = Funcao(no.extra['nome'], no.extra['tipo'], params)
            self.tipo_retorno = no.extra['tipo']
            self.bloco(no.filhos[1])
            ultimo = self.funcao.codigo[-1] if self.funcao.codigo else None
            if not ultimo or ultimo[0] != 'retorne':
                self.emitir('retorne', None)
            funcoes.append(self.funcao)
        return funcoes

    def bloco(self, no):
        for comando in no.filhos:
            self.comando(comando)

    def converter(self, operando, destino, origem):
        """Aplica a unica promocao implicita: inteiro -> real."""
        if destino == 'real' and origem == 'inteiro':
            if isinstance(operando, Const):
                return Const('real', operando.texto + '.0')
            t = self.novo_temp()
            self.emitir('real', t, operando)
            return t
        return operando

    def comando(self, no):
        especie = no.rotulo.split()[0]
        if especie == 'bloco':
            self.bloco(no)
            return
        if especie != 'enquanto':      # o enquanto marca a linha no rotulo
            self.emitir('linha', no.linha)
        if especie == 'declaracao':
            simbolo = no.extra['simbolo']
            if no.filhos:
                valor = self.expressao(no.filhos[0])
                valor = self.converter(valor, simbolo.tipo, no.filhos[0].extra['tipo'])
            else:
                valor = Const(simbolo.tipo, PADROES[simbolo.tipo])
            self.emitir('copia', self.nome(simbolo), valor)
        elif especie == 'atribuicao':
            simbolo = no.extra['simbolo']
            valor = self.expressao(no.filhos[0])
            valor = self.converter(valor, simbolo.tipo, no.filhos[0].extra['tipo'])
            self.emitir('copia', self.nome(simbolo), valor)
        elif especie == 'se':
            cond = self.expressao(no.filhos[0])
            senao = self.novo_rotulo()
            self.emitir('seFalso', cond, senao)
            self.bloco(no.filhos[1])
            if len(no.filhos) == 3:
                fim = self.novo_rotulo()
                self.emitir('desvie', fim)
                self.emitir('rotulo', senao)
                self.bloco(no.filhos[2])
                self.emitir('rotulo', fim)
            else:
                self.emitir('rotulo', senao)
        elif especie == 'enquanto':
            inicio, fim = self.novo_rotulo(), self.novo_rotulo()
            self.emitir('rotulo', inicio)
            self.emitir('linha', no.linha)
            cond = self.expressao(no.filhos[0])
            self.emitir('seFalso', cond, fim)
            self.bloco(no.filhos[1])
            self.emitir('desvie', inicio)
            self.emitir('rotulo', fim)
        elif especie == 'escreva':
            self.emitir('escreva', self.expressao(no.filhos[0]))
        elif especie == 'chamada':
            self.chamada(no, com_destino=False)
        elif especie == 'retorne':
            if no.filhos:
                valor = self.expressao(no.filhos[0])
                valor = self.converter(valor, self.tipo_retorno, no.filhos[0].extra['tipo'])
                self.emitir('retorne', valor)
            else:
                self.emitir('retorne', None)
        else:
            raise ValueError(f'comando desconhecido: {no.rotulo}')

    def chamada(self, no, com_destino=True):
        simbolo = no.extra['simbolo']
        args = []
        for arg, tipo in zip(no.filhos, simbolo.parametros):
            valor = self.expressao(arg)
            args.append(self.converter(valor, tipo, arg.extra['tipo']))
        destino = self.novo_temp() if com_destino else None
        self.emitir('chama', destino, simbolo.nome, args)
        return destino

    def expressao(self, no):
        especie = no.rotulo.split()[0]
        if especie == 'literal':
            return Const(no.extra['tipo'], no.extra['valor'])
        if especie == 'variavel':
            return self.nome(no.extra['simbolo'])
        if especie == 'chamada':
            return self.chamada(no)
        if especie == 'unario':
            a = self.expressao(no.filhos[0])
            t = self.novo_temp()
            self.emitir('un', t, no.extra['operador'], a)
            return t
        if especie == 'binario':
            op = no.extra['operador']
            esq, dir_ = no.filhos
            a = self.expressao(esq)
            b = self.expressao(dir_)
            te, td = esq.extra['tipo'], dir_.extra['tipo']
            if op not in ('e', 'ou', '%') and 'real' in (te, td) and te != td:
                a = self.converter(a, 'real', te)
                b = self.converter(b, 'real', td)
            t = self.novo_temp()
            self.emitir('bin', t, op, a, b)
            return t
        raise ValueError(f'expressao desconhecida: {no.rotulo}')


def gerar(arvore, tabela):
    """Devolve o codigo de tres enderecos (lista de Funcao)."""
    return Gerador().programa(arvore)


def formatar(instr):
    k = instr[0]
    if k == 'linha':
        return f'  ; linha {instr[1]}'
    if k == 'copia':
        return f'  {instr[1]} = {instr[2]}'
    if k == 'bin':
        return f'  {instr[1]} = {instr[3]} {instr[2]} {instr[4]}'
    if k == 'un':
        return f'  {instr[1]} = {instr[2]} {instr[3]}'
    if k == 'real':
        return f'  {instr[1]} = paraReal {instr[2]}'
    if k == 'rotulo':
        return f'{instr[1]}:'
    if k == 'desvie':
        return f'  desvie {instr[1]}'
    if k == 'seFalso':
        return f'  seFalso {instr[1]} desvie {instr[2]}'
    if k == 'chama':
        args = ', '.join(str(a) for a in instr[3])
        chamada = f'chama {instr[2]}' + (f' {args}' if args else '')
        return f'  {instr[1]} = {chamada}' if instr[1] else f'  {chamada}'
    if k == 'retorne':
        return '  retorne' + (f' {instr[1]}' if instr[1] is not None else '')
    if k == 'escreva':
        return f'  escreva {instr[1]}'
    raise ValueError(instr)


def despejar(codigo):
    """Devolve as linhas do --ir."""
    linhas = []
    for f in codigo:
        params = ', '.join(f'{n} {t}' for n, t in f.parametros)
        linhas.append(f'funcao {f.nome} {f.tipo} ({params})')
        linhas.extend(formatar(i) for i in f.codigo)
        linhas.append('fim')
        linhas.append('')
    return linhas[:-1]
