"""Tabela de simbolos e verificacao semantica da MPL em duas passadas."""
from dataclasses import dataclass, field

from mplc.erros import ErroMPL


NUMERICOS = {'inteiro', 'real'}


@dataclass
class Simbolo:
    nome: str
    categoria: str
    tipo: str
    linha: int
    escopo: int
    parametros: tuple[str, ...] = ()


@dataclass
class Escopo:
    numero: int
    descricao: str
    pai: 'Escopo | None' = None
    simbolos: dict[str, Simbolo] = field(default_factory=dict)

    def buscar(self, nome):
        escopo = self
        while escopo is not None:
            if nome in escopo.simbolos:
                return escopo.simbolos[nome]
            escopo = escopo.pai
        return None


def cabe(destino, origem):
    """A unica promocao implicita e de inteiro para real."""
    return destino == origem or (destino == 'real' and origem == 'inteiro')


def erro(no, mensagem):
    raise ErroMPL('semantico', no.linha, no.coluna, mensagem)


class Analisador:
    def __init__(self):
        self.escopos = [Escopo(0, 'global')]

    def abrir(self, descricao, pai, no):
        escopo = Escopo(len(self.escopos), descricao, pai)
        self.escopos.append(escopo)
        no.extra['escopo'] = escopo.numero
        return escopo

    def declarar(self, no, categoria, escopo, parametros=()):
        nome = no.extra['nome']
        if nome in escopo.simbolos:
            erro(no, f'{nome} ja declarado neste escopo')
        simbolo = Simbolo(nome, categoria, no.extra['tipo'], no.linha,
                          escopo.numero, parametros)
        escopo.simbolos[nome] = simbolo
        no.extra['simbolo'] = simbolo
        return simbolo

    def resolver(self, no, escopo, funcao=False):
        nome = no.extra['nome']
        simbolo = escopo.buscar(nome)
        if simbolo is None:
            erro(no, f'identificador {nome} nao declarado')
        if (simbolo.categoria == 'funcao') != funcao:
            esperado = 'funcao' if funcao else 'variavel'
            erro(no, f'{nome} nao e {esperado}')
        no.extra['simbolo'] = simbolo
        return simbolo

    def analisar(self, arvore):
        global_ = self.escopos[0]
        # Todas as assinaturas existem antes de visitar qualquer corpo.
        for funcao in arvore.filhos:
            parametros = tuple(p.extra['tipo'] for p in funcao.filhos[0].filhos)
            self.declarar(funcao, 'funcao', global_, parametros)

        principal = global_.simbolos.get('principal')
        if principal is None:
            raise ErroMPL('semantico', 1, 1, 'falta a funcao principal')
        if principal.tipo != 'vazio' or principal.parametros:
            no = next(f for f in arvore.filhos if f.extra['nome'] == 'principal')
            erro(no, 'principal deve retornar vazio e nao receber parametros')

        for funcao in arvore.filhos:
            escopo = self.abrir(f'funcao {funcao.extra["nome"]}', global_, funcao)
            for parametro in funcao.filhos[0].filhos:
                self.declarar(parametro, 'parametro', escopo)
            retorna = self.bloco(funcao.filhos[1], escopo, funcao.extra['tipo'])
            if funcao.extra['tipo'] != 'vazio' and not retorna:
                erro(funcao, 'funcao nao garante retorno em todos os caminhos')
        return self.escopos

    def exigir_tipo(self, no, destino, origem):
        if not cabe(destino, origem):
            erro(no, f'esperado {destino}, encontrado {origem}')

    def bloco(self, no, pai, retorno):
        escopo = self.abrir('bloco', pai, no)
        retorna = False
        for comando in no.filhos:
            # Mesmo comandos inalcancaveis devem ter nomes e tipos validos.
            comando_retorna = self.comando(comando, escopo, retorno)
            retorna = retorna or comando_retorna
        return retorna

    def comando(self, no, escopo, retorno):
        especie = no.rotulo.split()[0]
        if especie == 'bloco':
            return self.bloco(no, escopo, retorno)
        if especie == 'declaracao':
            simbolo = self.declarar(no, 'variavel', escopo)
            if no.filhos:
                self.exigir_tipo(no, simbolo.tipo, self.expressao(no.filhos[0], escopo))
        elif especie == 'atribuicao':
            simbolo = self.resolver(no, escopo)
            self.exigir_tipo(no, simbolo.tipo, self.expressao(no.filhos[0], escopo))
        elif especie in {'se', 'enquanto'}:
            condicao = no.filhos[0]
            self.exigir_tipo(condicao, 'logico', self.expressao(condicao, escopo))
            entao = self.bloco(no.filhos[1], escopo, retorno)
            if especie == 'se' and len(no.filhos) == 3:
                senao = self.bloco(no.filhos[2], escopo, retorno)
                return entao and senao
            # Nao se avaliam constantes: um laco pode executar zero vezes,
            # e um se sem senao sempre deixa um caminho sem retorno.
        elif especie == 'escreva':
            self.expressao(no.filhos[0], escopo)
        elif especie == 'chamada':
            self.chamada(no, escopo)
        elif especie == 'retorne':
            if retorno == 'vazio':
                if no.filhos:
                    erro(no, 'funcao vazio nao pode retornar uma expressao')
            else:
                if not no.filhos:
                    erro(no, f'retorno de {retorno} exige uma expressao')
                self.exigir_tipo(no, retorno, self.expressao(no.filhos[0], escopo))
            return True
        else:
            raise ValueError(f'comando desconhecido na AST: {no.rotulo}')
        return False

    def chamada(self, no, escopo):
        simbolo = self.resolver(no, escopo, funcao=True)
        if len(no.filhos) != len(simbolo.parametros):
            erro(no, f'{simbolo.nome} espera {len(simbolo.parametros)} argumento(s), '
                     f'recebeu {len(no.filhos)}')
        for argumento, tipo in zip(no.filhos, simbolo.parametros):
            self.exigir_tipo(argumento, tipo, self.expressao(argumento, escopo))
        no.extra['tipo'] = simbolo.tipo
        return simbolo.tipo

    def expressao(self, no, escopo):
        especie = no.rotulo.split()[0]
        if especie == 'literal':
            tipo = no.extra['tipo']
        elif especie == 'variavel':
            tipo = self.resolver(no, escopo).tipo
        elif especie == 'chamada':
            tipo = self.chamada(no, escopo)
            if tipo == 'vazio':
                erro(no, 'chamada de funcao vazio nao pode ser usada em expressao')
        elif especie == 'unario':
            operando = self.expressao(no.filhos[0], escopo)
            operador = no.extra['operador']
            if operador == 'nao' and operando == 'logico':
                tipo = 'logico'
            elif operador == '-' and operando in NUMERICOS:
                tipo = operando
            else:
                erro(no, f'operador {operador} nao aceita {operando}')
        elif especie == 'binario':
            esquerda = self.expressao(no.filhos[0], escopo)
            direita = self.expressao(no.filhos[1], escopo)
            tipo = self.binario(no, esquerda, direita)
        else:
            raise ValueError(f'expressao desconhecida na AST: {no.rotulo}')
        no.extra['tipo'] = tipo
        return tipo

    def binario(self, no, esquerda, direita):
        operador = no.extra['operador']
        numericos = esquerda in NUMERICOS and direita in NUMERICOS
        if operador == '+' and esquerda == direita == 'texto':
            return 'texto'
        if operador in {'+', '-', '*', '/'} and numericos:
            return 'real' if 'real' in (esquerda, direita) else 'inteiro'
        if operador == '%' and esquerda == direita == 'inteiro':
            return 'inteiro'
        if operador in {'<', '<=', '>', '>='} and numericos:
            return 'logico'
        if operador in {'==', '!='} and (esquerda == direita or numericos):
            return 'logico'
        if operador in {'e', 'ou'} and esquerda == direita == 'logico':
            return 'logico'
        erro(no, f'operador {operador} nao aceita {esquerda} e {direita}')


def analisar(arvore):
    """Valida a AST e devolve os escopos na ordem de abertura."""
    return Analisador().analisar(arvore)


def despejar(tabela):
    """Serializa a tabela conforme CONTRATOS.md, secao 4."""
    linhas = []
    for escopo in tabela:
        cabecalho = f'escopo {escopo.numero} {escopo.descricao}'
        if escopo.pai is not None:
            cabecalho += f' pai {escopo.pai.numero}'
        linhas.append(cabecalho)
        for simbolo in escopo.simbolos.values():
            tipo = simbolo.tipo
            if simbolo.categoria == 'funcao':
                tipo += f'({",".join(simbolo.parametros)})'
            linhas.append(f'  {simbolo.nome}|{simbolo.categoria}|{tipo}|{simbolo.linha}')
    return linhas
