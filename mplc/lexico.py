"""
Entrega 1 — analise lexica.

Transformar o texto do programa numa lista de tokens.

O que voces tem que devolver: uma lista de Token. O ultimo elemento e sempre
um token FIM_ARQUIVO. A regra de posicao dele esta em CONTRATOS.md, secao 7.

Leiam antes: LINGUAGEM.md secao 2, e CONTRATOS.md secao 2.
"""
from mplc.erros import ErroMPL


class Token:
    __slots__ = ('tipo', 'lexema', 'linha', 'coluna')

    def __init__(self, tipo, lexema, linha, coluna):
        self.tipo = tipo          # 'ID', 'INTEIRO', 'MAIS', ... (a lista esta no contrato)
        self.lexema = lexema      # o texto exato como apareceu no fonte
        self.linha = linha
        self.coluna = coluna      # a coluna do PRIMEIRO caractere do token

    def __str__(self):
        # esta e a linha que o --tokens imprime; nao mexam no formato
        return f"{self.linha},{self.coluna},{self.tipo},{self.lexema}"


def analisar(fonte):
    """Recebe o texto do programa. Devolve a lista de Token."""
    palavras = {
        'funcao': 'FUNCAO',
        'retorne': 'RETORNE',
        'se': 'SE',
        'senao': 'SENAO',
        'enquanto': 'ENQUANTO',
        'escreva': 'ESCREVA',
        'inteiro': 'TIPO_INTEIRO',
        'real': 'TIPO_REAL',
        'logico': 'TIPO_LOGICO',
        'texto': 'TIPO_TEXTO',
        'vazio': 'TIPO_VAZIO',
        'verdadeiro': 'LOGICO',
        'falso': 'LOGICO',
        'e': 'E',
        'ou': 'OU',
        'nao': 'NAO',
    }
    duplos = {
        '==': 'IGUAL',
        '!=': 'DIFERENTE',
        '<=': 'MENOR_IGUAL',
        '>=': 'MAIOR_IGUAL',
    }
    simples = {
        '+': 'MAIS',
        '-': 'MENOS',
        '*': 'VEZES',
        '/': 'DIVIDE',
        '%': 'RESTO',
        '<': 'MENOR',
        '>': 'MAIOR',
        '=': 'ATRIBUI',
        '(': 'ABRE_PAR',
        ')': 'FECHA_PAR',
        '{': 'ABRE_CHAVE',
        '}': 'FECHA_CHAVE',
        ',': 'VIRGULA',
        ';': 'PONTO_VIRGULA',
    }

    tokens = []
    indice = 0
    linha = 1
    coluna = 1
    tamanho = len(fonte)

    def avancar():
        """Consome um caractere e atualiza a posicao do proximo."""
        nonlocal indice, linha, coluna
        caractere = fonte[indice]
        indice += 1
        if caractere == '\n':
            linha += 1
            coluna = 1
        elif caractere == '\r':
            # A abertura normal de arquivos do Python converte CRLF para LF,
            # mas tratar CR e CRLF aqui torna analisar() correto por si so.
            if indice < tamanho and fonte[indice] == '\n':
                indice += 1
            linha += 1
            coluna = 1
        else:
            coluna += 1
        return caractere

    def erro(l, c, mensagem):
        raise ErroMPL('lexico', l, c, mensagem)

    while indice < tamanho:
        atual = fonte[indice]

        if atual in ' \t':
            avancar()
            continue
        if atual in '\r\n':
            avancar()
            continue

        inicio = indice
        linha_inicio = linha
        coluna_inicio = coluna

        # Comentario de linha.
        if fonte.startswith('//', indice):
            avancar()
            avancar()
            while indice < tamanho and fonte[indice] not in '\r\n':
                avancar()
            continue

        # Comentario de bloco, sem aninhamento.
        if fonte.startswith('/*', indice):
            avancar()
            avancar()
            while indice < tamanho and not fonte.startswith('*/', indice):
                avancar()
            if indice == tamanho:
                erro(linha_inicio, coluna_inicio, 'comentario de bloco nao terminado')
            avancar()
            avancar()
            continue

        # Identificadores ASCII e palavras reservadas.
        if atual == '_' or 'a' <= atual <= 'z' or 'A' <= atual <= 'Z':
            avancar()
            while indice < tamanho:
                c = fonte[indice]
                if c == '_' or 'a' <= c <= 'z' or 'A' <= c <= 'Z' or '0' <= c <= '9':
                    avancar()
                else:
                    break
            lexema = fonte[inicio:indice]
            tokens.append(Token(palavras.get(lexema, 'ID'), lexema,
                                linha_inicio, coluna_inicio))
            continue

        # Inteiros e reais. O ponto so pertence ao numero quando ha digitos
        # dos dois lados; se vier depois de digitos sem uma parte fracionaria,
        # ele proprio e o caractere que estragou o token.
        if '0' <= atual <= '9':
            while indice < tamanho and '0' <= fonte[indice] <= '9':
                avancar()
            tipo = 'INTEIRO'
            if indice < tamanho and fonte[indice] == '.':
                ponto_linha, ponto_coluna = linha, coluna
                avancar()
                if indice == tamanho or not ('0' <= fonte[indice] <= '9'):
                    erro(ponto_linha, ponto_coluna,
                         'numero real exige digitos depois do ponto')
                tipo = 'REAL'
                while indice < tamanho and '0' <= fonte[indice] <= '9':
                    avancar()
            tokens.append(Token(tipo, fonte[inicio:indice],
                                linha_inicio, coluna_inicio))
            continue

        # Textos ficam com aspas e escapes exatamente como no fonte.
        if atual == '"':
            avancar()
            while indice < tamanho:
                c = fonte[indice]
                if c == '"':
                    avancar()
                    tokens.append(Token('TEXTO', fonte[inicio:indice],
                                        linha_inicio, coluna_inicio))
                    break
                if c in '\r\n':
                    erro(linha_inicio, coluna_inicio, 'texto nao terminado')
                if c == '\\':
                    escape_linha, escape_coluna = linha, coluna
                    avancar()
                    if indice == tamanho or fonte[indice] not in 'nt"\\':
                        erro(escape_linha, escape_coluna, 'escape invalido em texto')
                    avancar()
                    continue
                avancar()
            else:
                erro(linha_inicio, coluna_inicio, 'texto nao terminado')
            continue

        # Operadores de dois caracteres precisam ser tentados primeiro.
        par = fonte[indice:indice + 2]
        if par in duplos:
            avancar()
            avancar()
            tokens.append(Token(duplos[par], par, linha_inicio, coluna_inicio))
            continue
        if atual in simples:
            avancar()
            tokens.append(Token(simples[atual], atual, linha_inicio, coluna_inicio))
            continue

        # Um ponto nunca e token da MPL, inclusive no caso .5.
        if atual == '.':
            erro(linha_inicio, coluna_inicio,
                 'numero real exige digitos antes do ponto')
        erro(linha_inicio, coluna_inicio, f'caractere inesperado {atual!r}')

    tokens.append(Token('FIM_ARQUIVO', '', linha, coluna))
    return tokens
