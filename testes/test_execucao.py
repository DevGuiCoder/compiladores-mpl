"""Regressoes da geracao e da VM, sem depender dos lancadores POSIX."""
import io
from pathlib import Path
import unittest

from mplc.erros import ErroMPL
from mplc.principal import compilar_ate
from mplc.vm import executar


def rodar(fonte):
    saida = io.StringIO()
    executar('\n'.join(compilar_ate(fonte, 'bytecode')), saida)
    return saida.getvalue()


class ExecucaoTest(unittest.TestCase):
    def test_corpus_e_programa_do_grupo(self):
        raiz = Path(__file__).resolve().parents[1]
        fontes = sorted((raiz / 'testes/positivos').glob('*.mpl'))
        fontes.append(raiz / 'exemplos/vitrine.mpl')
        for fonte in fontes:
            with self.subTest(programa=fonte.name):
                self.assertEqual(rodar(fonte.read_text('utf-8')),
                                 fonte.with_suffix('.saida').read_text('utf-8'))

    def test_divisao_resto_e_promocao(self):
        self.assertEqual(rodar('''funcao vazio principal() {
            real x = 7 / 2;
            escreva(x); escreva(-7 / 3); escreva(-7 % 3);
            escreva(7 / -3); escreva(7 % -3); escreva(-7 % -3);
            escreva(7 / 2.0);
        }'''), '3.000000\n-2\n-1\n-2\n1\n-1\n3.500000\n')

    def test_recursao_preserva_locais_e_argumentos(self):
        self.assertEqual(rodar('''
        funcao inteiro soma(inteiro a, inteiro b) { retorne a + b; }
        funcao inteiro f(inteiro n) {
            inteiro salvo = n;
            se (n == 0) { retorne 0; }
            retorne soma(f(n - 1), salvo);
        }
        funcao vazio principal() { escreva(f(6)); }
        '''), '21\n')

    def test_sombreamento_e_nomes_de_temporarios(self):
        self.assertEqual(rodar('''funcao vazio principal() {
            inteiro t0 = 10;
            inteiro x = 2;
            { inteiro x = 3; escreva(x + t0); }
            escreva(x + t0);
        }'''), '13\n12\n')

    def test_promocao_argumento_retorno_e_descarte(self):
        self.assertEqual(rodar('''
        funcao real f(real n) { retorne n; }
        funcao real g() { retorne 7 / 2; }
        funcao vazio principal() { f(8); escreva(f(2)); escreva(g()); }
        '''), '2.000000\n3.000000\n')

    def test_logicos_avaliam_ambos_os_lados(self):
        for expressao in ('falso e (1 / 0 == 0)', 'verdadeiro ou (1 / 0 == 0)'):
            with self.subTest(expressao=expressao), self.assertRaises(ErroMPL) as ctx:
                rodar('funcao vazio principal() { escreva(' + expressao + '); }')
            self.assertEqual(ctx.exception.fase, 'execucao')

    def test_linha_do_chamador_restaurada(self):
        with self.assertRaises(ErroMPL) as ctx:
            rodar('funcao inteiro f() { retorne 1; }\n'
                  'funcao vazio principal() {\n'
                  '  escreva(f() / 0);\n}')
        self.assertEqual((ctx.exception.fase, ctx.exception.linha), ('execucao', 3))


if __name__ == '__main__':
    unittest.main()
