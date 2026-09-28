"""
Entrega 2 — analise sintatica.

Transformar a lista de tokens numa arvore.

Sugestao forte: descida recursiva, uma funcao por nivel de precedencia, na
ordem da secao 3.3 da especificacao. E como voces vao enxergar a precedencia
virar formato de arvore.

Gerador de parser (ANTLR, PLY, yacc) esta proibido nesta entrega e na
anterior — o objetivo e entender, e o gerador esconde exatamente a parte
que esta sendo ensinada.

Leiam antes: LINGUAGEM.md secoes 3 a 5, e CONTRATOS.md secao 3.
"""
from decimal import Decimal

from mplc.erros import ErroMPL


class No:
    """Um no da arvore. O rotulo e o que sai no --ast."""

    def __init__(self, rotulo, filhos=None, linha=0, coluna=0, **extra):
        self.rotulo = rotulo      # 'binario +', 'literal inteiro 1', 'bloco', ...
        self.filhos = filhos or []
        self.linha = linha
        self.coluna = coluna
        self.extra = extra        # o que a semantica quiser pendurar depois


def analisar(tokens):
    """Recebe a lista de Token. Devolve a raiz da arvore (um No 'programa')."""
    return Parser(tokens).programa()


TIPOS = {
    'TIPO_INTEIRO': 'inteiro',
    'TIPO_REAL': 'real',
    'TIPO_LOGICO': 'logico',
    'TIPO_TEXTO': 'texto',
}
TIPOS_RETORNO = {**TIPOS, 'TIPO_VAZIO': 'vazio'}


class Parser:
    """Parser manual por descida recursiva para a MPL."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.indice = 0

    @property
    def atual(self):
        return self.tokens[self.indice]

    def conferir(self, *tipos):
        return self.atual.tipo in tipos

    def avancar(self):
        token = self.atual
        if token.tipo != 'FIM_ARQUIVO':
            self.indice += 1
        return token

    def aceitar(self, *tipos):
        if self.conferir(*tipos):
            return self.avancar()
        return None

    def exigir(self, tipo, descricao=None):
        if self.conferir(tipo):
            return self.avancar()
        esperado = descricao or tipo
        self.erro(f'esperado {esperado}, encontrado {self.atual.lexema or "fim do arquivo"}')

    def erro(self, mensagem):
        token = self.atual
        raise ErroMPL('sintatico', token.linha, token.coluna, mensagem)

    def consumir_tipo(self, retorno=False):
        permitidos = TIPOS_RETORNO if retorno else TIPOS
        if self.atual.tipo not in permitidos:
            self.erro('esperado um tipo')
        token = self.avancar()
        return permitidos[token.tipo], token

    def programa(self):
        funcoes = []
        primeiro = self.atual
        while not self.conferir('FIM_ARQUIVO'):
            if not self.conferir('FUNCAO'):
                self.erro('esperado funcao ou fim do arquivo')
            funcoes.append(self.funcao())
        self.exigir('FIM_ARQUIVO')
        return No('programa', funcoes, primeiro.linha, primeiro.coluna)

    def funcao(self):
        inicio = self.exigir('FUNCAO', 'funcao')
        tipo, _ = self.consumir_tipo(retorno=True)
        nome = self.exigir('ID', 'nome da funcao')
        self.exigir('ABRE_PAR', "'('")

        parametros = []
        if not self.conferir('FECHA_PAR'):
            while True:
                tipo_parametro, tipo_token = self.consumir_tipo()
                nome_parametro = self.exigir('ID', 'nome do parametro')
                parametros.append(No(
                    f'parametro {nome_parametro.lexema} {tipo_parametro}',
                    linha=tipo_token.linha,
                    coluna=tipo_token.coluna,
                    nome=nome_parametro.lexema,
                    tipo=tipo_parametro,
                ))
                if not self.aceitar('VIRGULA'):
                    break
        self.exigir('FECHA_PAR', "')'")
        corpo = self.bloco()
        lista = No('parametros', parametros, nome.linha, nome.coluna)
        return No(
            f'funcao {nome.lexema} {tipo}',
            [lista, corpo],
            inicio.linha,
            inicio.coluna,
            nome=nome.lexema,
            tipo=tipo,
        )

    def bloco(self):
        inicio = self.exigir('ABRE_CHAVE', "'{'")
        comandos = []
        while not self.conferir('FECHA_CHAVE'):
            if self.conferir('FIM_ARQUIVO'):
                self.erro("esperado '}' antes do fim do arquivo")
            comandos.append(self.comando())
        self.exigir('FECHA_CHAVE')
        return No('bloco', comandos, inicio.linha, inicio.coluna)

    def comando(self):
        if self.conferir(*TIPOS):
            return self.declaracao()
        if self.conferir('ID'):
            return self.atribuicao_ou_chamada()
        if self.conferir('SE'):
            return self.condicional()
        if self.conferir('ENQUANTO'):
            return self.repeticao()
        if self.conferir('ESCREVA'):
            return self.escrita()
        if self.conferir('RETORNE'):
            return self.retorno()
        if self.conferir('ABRE_CHAVE'):
            return self.bloco()
        self.erro('esperado um comando')

    def declaracao(self):
        tipo, inicio = self.consumir_tipo()
        nome = self.exigir('ID', 'nome da variavel')
        filhos = []
        if self.aceitar('ATRIBUI'):
            filhos.append(self.expressao())
        self.exigir('PONTO_VIRGULA', "';'")
        return No(
            f'declaracao {nome.lexema} {tipo}',
            filhos,
            inicio.linha,
            inicio.coluna,
            nome=nome.lexema,
            tipo=tipo,
        )

    def atribuicao_ou_chamada(self):
        nome = self.exigir('ID')
        if self.aceitar('ATRIBUI'):
            valor = self.expressao()
            self.exigir('PONTO_VIRGULA', "';'")
            return No(
                f'atribuicao {nome.lexema}',
                [valor],
                nome.linha,
                nome.coluna,
                nome=nome.lexema,
            )
        if self.conferir('ABRE_PAR'):
            chamada = self.chamada(nome)
            self.exigir('PONTO_VIRGULA', "';'")
            return chamada
        self.erro("esperado '=' ou '(' depois do identificador")

    def condicional(self):
        inicio = self.exigir('SE')
        self.exigir('ABRE_PAR', "'('")
        condicao = self.expressao()
        self.exigir('FECHA_PAR', "')'")
        entao = self.bloco()
        filhos = [condicao, entao]
        if self.aceitar('SENAO'):
            filhos.append(self.bloco())
        return No('se', filhos, inicio.linha, inicio.coluna)

    def repeticao(self):
        inicio = self.exigir('ENQUANTO')
        self.exigir('ABRE_PAR', "'('")
        condicao = self.expressao()
        self.exigir('FECHA_PAR', "')'")
        corpo = self.bloco()
        return No('enquanto', [condicao, corpo], inicio.linha, inicio.coluna)

    def escrita(self):
        inicio = self.exigir('ESCREVA')
        self.exigir('ABRE_PAR', "'('")
        valor = self.expressao()
        self.exigir('FECHA_PAR', "')'")
        self.exigir('PONTO_VIRGULA', "';'")
        return No('escreva', [valor], inicio.linha, inicio.coluna)

    def retorno(self):
        inicio = self.exigir('RETORNE')
        filhos = []
        if not self.conferir('PONTO_VIRGULA'):
            filhos.append(self.expressao())
        self.exigir('PONTO_VIRGULA', "';'")
        return No('retorne', filhos, inicio.linha, inicio.coluna)

    def chamada(self, nome):
        self.exigir('ABRE_PAR')
        argumentos = []
        if not self.conferir('FECHA_PAR'):
            while True:
                argumentos.append(self.expressao())
                if not self.aceitar('VIRGULA'):
                    break
        self.exigir('FECHA_PAR', "')'")
        return No(
            f'chamada {nome.lexema}',
            argumentos,
            nome.linha,
            nome.coluna,
            nome=nome.lexema,
        )

    # Cada metodo abaixo representa um nivel de precedencia. Os operadores
    # binarios usam lacos, o que os torna associativos a esquerda.
    def expressao(self):
        return self.ou()

    def ou(self):
        return self.binarios(self.e, 'OU')

    def e(self):
        return self.binarios(self.igualdade, 'E')

    def igualdade(self):
        return self.binarios(self.relacional, 'IGUAL', 'DIFERENTE')

    def relacional(self):
        return self.binarios(
            self.aditiva, 'MENOR', 'MENOR_IGUAL', 'MAIOR', 'MAIOR_IGUAL'
        )

    def aditiva(self):
        return self.binarios(self.multiplicativa, 'MAIS', 'MENOS')

    def multiplicativa(self):
        return self.binarios(self.unaria, 'VEZES', 'DIVIDE', 'RESTO')

    def binarios(self, proximo_nivel, *operadores):
        esquerda = proximo_nivel()
        while self.conferir(*operadores):
            operador = self.avancar()
            direita = proximo_nivel()
            esquerda = No(
                f'binario {operador.lexema}',
                [esquerda, direita],
                operador.linha,
                operador.coluna,
                operador=operador.lexema,
            )
        return esquerda

    def unaria(self):
        if self.conferir('NAO', 'MENOS'):
            operador = self.avancar()
            # A chamada recursiva neste mesmo nivel da associatividade a direita.
            operando = self.unaria()
            return No(
                f'unario {operador.lexema}',
                [operando],
                operador.linha,
                operador.coluna,
                operador=operador.lexema,
            )
        return self.primaria()

    def primaria(self):
        if self.conferir('INTEIRO'):
            token = self.avancar()
            return No(
                f'literal inteiro {token.lexema}',
                linha=token.linha,
                coluna=token.coluna,
                tipo='inteiro',
                valor=token.lexema,
            )
        if self.conferir('REAL'):
            token = self.avancar()
            valor = format(Decimal(token.lexema), '.6f')
            return No(
                f'literal real {valor}',
                linha=token.linha,
                coluna=token.coluna,
                tipo='real',
                valor=token.lexema,
            )
        if self.conferir('LOGICO'):
            token = self.avancar()
            return No(
                f'literal logico {token.lexema}',
                linha=token.linha,
                coluna=token.coluna,
                tipo='logico',
                valor=token.lexema,
            )
        if self.conferir('TEXTO'):
            token = self.avancar()
            return No(
                f'literal texto {token.lexema}',
                linha=token.linha,
                coluna=token.coluna,
                tipo='texto',
                valor=token.lexema,
            )
        if self.conferir('ID'):
            nome = self.avancar()
            if self.conferir('ABRE_PAR'):
                return self.chamada(nome)
            return No(
                f'variavel {nome.lexema}',
                linha=nome.linha,
                coluna=nome.coluna,
                nome=nome.lexema,
            )
        if self.aceitar('ABRE_PAR'):
            valor = self.expressao()
            self.exigir('FECHA_PAR', "')'")
            return valor
        self.erro('esperado uma expressao')


def despejar(no, nivel=0, saida=None):
    """Imprime a arvore no formato do --ast. Ja esta pronto: dois espacos por nivel."""
    saida = saida if saida is not None else []
    saida.append('  ' * nivel + no.rotulo)
    for f in no.filhos:
        despejar(f, nivel + 1, saida)
    return saida
