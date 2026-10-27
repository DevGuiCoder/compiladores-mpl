"""Regressao e generalizacao da E3; executar com unittest discover."""
import contextlib
import io
from pathlib import Path
import tempfile
import textwrap
import unittest

from mplc import lexico, semantica, sintatico
from mplc.erros import ErroMPL
from mplc.principal import compilar_ate, main


RAIZ = Path(__file__).resolve().parent
LITERAIS = {'inteiro': '2', 'real': '2.5', 'texto': '"a"', 'logico': 'verdadeiro'}


def analisar(fonte):
    arvore = sintatico.analisar(lexico.analisar(textwrap.dedent(fonte).strip()))
    return arvore, semantica.analisar(arvore)


def principal(comandos):
    return 'funcao vazio principal() {\n' + comandos + '\n}'


class SemanticaTest(unittest.TestCase):
    def recusa(self, fonte, linha=None):
        with self.assertRaises(ErroMPL) as contexto:
            analisar(fonte)
        erro = contexto.exception
        self.assertEqual(erro.fase, 'semantico')
        self.assertGreaterEqual(erro.coluna, 1)
        if linha is not None:
            self.assertEqual(erro.linha, linha)

    def test_corpus_positivo_e_despejos_anteriores(self):
        for fonte in sorted((RAIZ / 'positivos').glob('*.mpl')):
            for modo in ('tokens', 'ast', 'tabela'):
                with self.subTest(programa=fonte.stem, modo=modo):
                    esperado = (RAIZ / 'fases' / f'{fonte.stem}.{modo}').read_text('utf-8')
                    obtido = compilar_ate(fonte.read_text('utf-8'), modo)
                    self.assertEqual('\n'.join(obtido), esperado.rstrip('\n'))

    def test_corpus_negativo_fase_linha_e_coluna(self):
        for fonte in sorted((RAIZ / 'negativos').glob('*.mpl')):
            if fonte.name.startswith('exec-'):
                continue
            with self.subTest(programa=fonte.stem):
                fase, linha, coluna = fonte.with_suffix('.erro').read_text().strip().split('|')
                with self.assertRaises(ErroMPL) as contexto:
                    compilar_ate(fonte.read_text('utf-8'), 'tabela')
                erro = contexto.exception
                self.assertEqual((erro.fase, erro.linha), (fase, int(linha)))
                if fase != 'semantico':
                    self.assertEqual(erro.coluna, int(coluna))

    def test_sombreamento_e_restauracao(self):
        analisar('''
            funcao inteiro f(inteiro x) {
                { texto x = "interno"; escreva(x + "!"); }
                x = x + 1;
                retorne x;
            }
            funcao vazio principal() {
                inteiro x = 3;
                { real x = 1; { logico x = falso; escreva(nao x); } x = 2.5; }
                x = f(x);
            }
        ''')
        self.recusa(principal('inteiro x; { real x; }\nx = 2.5;'), 3)

    def test_corpo_pode_sombrear_parametro(self):
        analisar('funcao texto f(inteiro x) { texto x = "oi"; retorne x; }\n'
                 + principal('escreva(f(2));'))

    def test_escopos_nao_vazam(self):
        casos = [
            '{ inteiro x; }\nescreva(x);',
            'se (verdadeiro) { inteiro x; }\nescreva(x);',
            'enquanto (falso) { inteiro x; }\nescreva(x);',
            'se (verdadeiro) { inteiro x; } senao { escreva(x); }',
            'escreva(x); inteiro x;',
            'x = 1;',
        ]
        for caso in casos:
            with self.subTest(caso=caso):
                self.recusa(principal(caso))
        self.recusa('funcao vazio f() { inteiro x; }\n' + principal('escreva(x);'), 3)

    def test_duplicacoes(self):
        self.recusa(principal('inteiro x;\nreal x;'), 3)
        self.recusa('funcao vazio f(inteiro x, texto x) {}\n' + principal(''), 1)
        self.recusa('funcao vazio f() {}\nfuncao inteiro f(inteiro x) { retorne x; }\n'
                    + principal(''), 2)

    def test_principal_obrigatorio_e_assinatura(self):
        for fonte in ('', 'funcao vazio outra() {}',
                      'funcao inteiro principal() { retorne 1; }',
                      'funcao vazio principal(inteiro x) {}'):
            with self.subTest(fonte=fonte):
                self.recusa(fonte, 1)

    def test_chamadas_antecipadas_e_recursao_mutua(self):
        analisar(principal('escreva(par(8));') + '''
            funcao logico par(inteiro n) {
                se (n == 0) { retorne verdadeiro; } senao { retorne impar(n - 1); }
            }
            funcao logico impar(inteiro n) {
                se (n == 0) { retorne falso; } senao { retorne par(n - 1); }
            }
        ''')

    def test_chamadas_invalidas(self):
        for argumentos in ('', '1, 2', '2.5', 'verdadeiro', '"x"'):
            with self.subTest(argumentos=argumentos):
                self.recusa('funcao inteiro f(inteiro x) { retorne x; }\n'
                            + principal(f'f({argumentos});'), 3)
        self.recusa(principal('inexistente();'), 2)
        self.recusa(principal('inteiro x; x();'), 2)
        self.recusa(principal('escreva(principal);'), 2)

    def test_matriz_conversoes_atribuicao_argumento_retorno(self):
        for destino in LITERAIS:
            for origem, valor in LITERAIS.items():
                fontes = [
                    principal(f'{destino} x = {valor};'),
                    principal(f'{destino} x; x = {valor};'),
                    f'funcao vazio f({destino} x) {{}}\n' + principal(f'f({valor});'),
                    f'funcao {destino} f() {{ retorne {valor}; }}\n' + principal('f();'),
                ]
                for contexto, fonte in enumerate(fontes):
                    with self.subTest(destino=destino, origem=origem, contexto=contexto):
                        if destino == origem or (destino, origem) == ('real', 'inteiro'):
                            analisar(fonte)
                        else:
                            self.recusa(fonte)

    def test_matriz_operadores_binarios(self):
        # Tabela de especificacao independente do despacho do analisador.
        numericos = {
            ('inteiro', 'inteiro'): 'inteiro', ('inteiro', 'real'): 'real',
            ('real', 'inteiro'): 'real', ('real', 'real'): 'real',
        }
        regras = {op: dict(numericos) for op in ('+', '-', '*', '/')}
        regras['+'][('texto', 'texto')] = 'texto'
        regras['%'] = {('inteiro', 'inteiro'): 'inteiro'}
        for op in ('<', '<=', '>', '>=', '==', '!='):
            regras[op] = {par: 'logico' for par in numericos}
        for op in ('==', '!='):
            regras[op].update({('texto', 'texto'): 'logico', ('logico', 'logico'): 'logico'})
        for op in ('e', 'ou'):
            regras[op] = {('logico', 'logico'): 'logico'}
        for op, aceitos in regras.items():
            for a, literal_a in LITERAIS.items():
                for b, literal_b in LITERAIS.items():
                    with self.subTest(op=op, esquerda=a, direita=b):
                        fonte = principal(f'escreva({literal_a} {op} {literal_b});')
                        if (a, b) in aceitos:
                            arvore, _ = analisar(fonte)
                            expressao = arvore.filhos[0].filhos[1].filhos[0].filhos[0]
                            self.assertEqual(expressao.extra['tipo'], aceitos[a, b])
                        else:
                            self.recusa(fonte, 2)

    def test_operadores_unarios(self):
        for op, tipos in (('nao', {'logico'}), ('-', {'inteiro', 'real'})):
            for tipo, valor in LITERAIS.items():
                with self.subTest(op=op, tipo=tipo):
                    fonte = principal(f'escreva({op} {valor});')
                    if tipo in tipos:
                        analisar(fonte)
                    else:
                        self.recusa(fonte, 2)

    def test_condicoes_exigem_logico(self):
        for comando in ('se', 'enquanto'):
            for tipo, valor in LITERAIS.items():
                with self.subTest(comando=comando, tipo=tipo):
                    fonte = principal(f'{comando} ({valor}) {{}}')
                    if tipo == 'logico':
                        analisar(fonte)
                    else:
                        self.recusa(fonte, 2)

    def test_vazio_so_como_comando(self):
        prefixo = 'funcao vazio nada() { retorne; }\n'
        analisar(prefixo + principal('nada();'))
        for comando in ('escreva(nada());', 'escreva(nada() == nada());',
                        'inteiro x = nada();', 'se (nada()) {}',
                        'retorne nada();'):
            with self.subTest(comando=comando):
                self.recusa(prefixo + principal(comando), 3)
        self.recusa(prefixo + 'funcao inteiro f() { retorne nada(); }\n' + principal(''), 2)

    def test_retorno_estrutural(self):
        validos = [
            'retorne 1;', '{ retorne 1; }',
            'se (verdadeiro) { retorne 1; } senao { retorne 2; }',
            'se (falso) { retorne 1; } retorne 2;',
            'enquanto (verdadeiro) { retorne 1; } retorne 2;',
            'se (verdadeiro) { se (falso) { retorne 1; } senao { retorne 2; } } '
            'senao { retorne 3; }',
        ]
        invalidos = [
            '', 'se (verdadeiro) { retorne 1; }',
            'enquanto (verdadeiro) { retorne 1; }',
            'se (verdadeiro) { retorne 1; } senao {}',
            'se (verdadeiro) {} senao { retorne 1; }',
            'se (verdadeiro) { se (verdadeiro) { retorne 1; } } senao { retorne 2; }',
        ]
        for corpo in validos + invalidos:
            with self.subTest(corpo=corpo):
                fonte = f'funcao inteiro f() {{ {corpo} }}\n' + principal('')
                if corpo in validos:
                    analisar(fonte)
                else:
                    self.recusa(fonte, 1)
        self.recusa('funcao inteiro f() { retorne; }\n' + principal(''), 1)

    def test_inacessivel_ainda_e_validado(self):
        self.recusa(principal('retorne;\nescreva(nao_declarada);'), 3)
        self.recusa(principal('se (verdadeiro) { retorne; } senao { escreva(x); }'), 2)

    def test_escopos_vazios_ordem_e_pais(self):
        _, tabela = analisar(principal('se (verdadeiro) {} senao {} enquanto (falso) {} {}'))
        self.assertEqual(semantica.despejar(tabela), [
            'escopo 0 global', '  principal|funcao|vazio()|1',
            'escopo 1 funcao principal pai 0', 'escopo 2 bloco pai 1',
            'escopo 3 bloco pai 2', 'escopo 4 bloco pai 2',
            'escopo 5 bloco pai 2', 'escopo 6 bloco pai 2',
        ])

    def test_analises_independentes_e_ast_preservada(self):
        arvore = sintatico.analisar(lexico.analisar(principal('real x = 7 / 2;')))
        antes = sintatico.despejar(arvore)
        tabela = semantica.despejar(semantica.analisar(arvore))
        self.assertEqual(sintatico.despejar(arvore), antes)
        self.assertEqual(semantica.despejar(semantica.analisar(arvore)), tabela)
        divisao = arvore.filhos[0].filhos[1].filhos[0].filhos[0]
        self.assertEqual(divisao.extra['tipo'], 'inteiro')
        _, nova = analisar(principal(''))
        self.assertEqual(len(nova), 3)

    def test_divisao_zero_e_recursao_nao_sao_erros_semanticos(self):
        analisar(principal('escreva(1 / 0); escreva(1 % 0);'))
        analisar('funcao inteiro f() { retorne f(); }\n' + principal('f();'))

    def test_cli_erro_sem_stdout_e_modos_independentes(self):
        with tempfile.TemporaryDirectory() as pasta:
            fonte = Path(pasta) / 'programa.mpl'
            fonte.write_text(principal('escreva(x);'), encoding='utf-8')
            for modo in ([], ['--tabela'], ['--ast'], ['--tokens']):
                with self.subTest(modo=modo):
                    saida, erros = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erros):
                        codigo = main([*modo, str(fonte)])
                    if modo in ([], ['--tabela']):
                        self.assertEqual(codigo, 1)
                        self.assertEqual(saida.getvalue(), '')
                        self.assertRegex(erros.getvalue(), r'^erro semantico: linha 2, coluna \d+: [^\n]+\n$')
                    else:
                        self.assertEqual(codigo, 0)
                        self.assertEqual(erros.getvalue(), '')
                    self.assertFalse(fonte.with_suffix('.mplb').exists())


if __name__ == '__main__':
    unittest.main()
