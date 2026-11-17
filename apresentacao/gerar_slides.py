"""Gera o PDF da apresentacao. Dependencia exclusiva: reportlab."""
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

from demonstrar import dados

PASTA = Path(__file__).resolve().parent
DESTINO = PASTA / 'apresentacao-grupo-NN.pdf'
W, H = 960, 540
FUNDO, TINTA, ACENTO = '#F7F5EF', '#172C40', '#087C78'
MUTED = '#526473'


def gerar():
    c = canvas.Canvas(str(DESTINO), pagesize=(W, H))
    c.setTitle('Compilador MPL - Entrega 4')
    c.setAuthor('Luiz Guilherme Silva Caride, Caio Colo, Eduuardo Bishop')
    d = dados()

    def texto(conteudo, x, y, largura, tamanho=20, cor=TINTA, negrito=False):
        estilo = ParagraphStyle('p', fontName='Helvetica-Bold' if negrito else 'Helvetica',
                                fontSize=tamanho, leading=tamanho * 1.3,
                                textColor=HexColor(cor))
        p = Paragraph(conteudo, estilo)
        _, altura = p.wrap(largura, H)
        if y + altura > H - 40:
            raise ValueError('Texto ultrapassa a area util: ' + conteudo)
        p.drawOn(c, x, H - y - altura)
        return altura

    def codigo(conteudo, x, y, tamanho=18):
        c.setFillColor(HexColor(TINTA))
        c.setFont('Courier', tamanho)
        for i, linha in enumerate(conteudo.splitlines()):
            assert c.stringWidth(linha, 'Courier', tamanho) + x < W - 35
            assert y + i * tamanho * 1.35 < H - 45
            c.drawString(x, H - y - tamanho - i * tamanho * 1.35, linha)

    def pagina(titulo, numero, subtitulo=None):
        c.setFillColor(HexColor(FUNDO))
        c.rect(0, 0, W, H, fill=1, stroke=0)
        texto(titulo, 48, 35, 860, 32, negrito=True)
        if subtitulo:
            texto(subtitulo, 48, 85, 860, 16, MUTED)
        c.setStrokeColor(HexColor(ACENTO))
        c.setLineWidth(2)
        c.line(48, H-123, W-48, H-123)
        c.setFont('Helvetica', 10)
        c.setFillColor(HexColor(MUTED))
        c.drawString(48, 20, 'Compiladores / UNISAGRADO / 2026-2')
        c.drawRightString(W-48, 20, str(numero))

    pagina('Compilador MPL em execução', 1, 'Entrega 4 - Código intermediário, geração e máquina virtual')
    texto('Luiz Guilherme Silva Caride<br/>Caio Colo<br/>Eduuardo Bishop', 48, 150, 430, 21)
    texto('Programa: vitrine.mpl', 520, 150, 380, 23, negrito=True)
    texto('Torre de Hanói, conversão de bases,<br/>raiz quadrada e sequência de Collatz.', 520, 197, 380, 20)
    codigo('./compilar exemplos/vitrine.mpl\n./executar exemplos/vitrine.mplb', 48, 320, 23)
    texto('Demonstração ao vivo: compilar, executar e mostrar a saída.', 48, 425, 860, 20, ACENTO)
    c.showPage()

    pagina('Uma expressão: tokens e árvore', 2, 'exemplos/vitrine.mpl, linha 88: n = n * 5 + 1;')
    texto('Léxico', 48, 148, 400, 23, negrito=True)
    codigo(d['tokens'], 48, 190, 17)
    texto('Sintático', 520, 148, 380, 23, negrito=True)
    codigo(d['ast'], 520, 190, 17)
    texto('A multiplicação fica abaixo da soma.<br/>Linha e coluna começam em 1.', 520, 385, 380, 19, ACENTO)
    c.showPage()

    pagina('Escopos, tipos e três endereços', 3, 'A mesma atribuição percorre a análise semântica e a geração do IR')
    texto('Resolução de n', 48, 150, 410, 23, negrito=True)
    texto('Variável inteira declarada na linha 85.<br/><br/>O uso está no escopo 34, dentro do laço. A busca encontra n no escopo pai 33.', 48, 200, 410, 21)
    texto('Código intermediário', 520, 150, 390, 23, negrito=True)
    codigo(d['ir'], 520, 205, 23)
    texto('Cada linha contém no máximo<br/>uma operação.', 520, 330, 380, 21, ACENTO)
    texto('Na primeira iteração: n = 1, t17 = 5, t18 = 6, n = 6.', 48, 435, 860, 21)
    c.showPage()

    pagina('O bytecode e a pilha', 4, 'Trecho real de exemplos/vitrine.mplb')
    codigo(d['vm'].strip().replace('\n  ', '\n'), 48, 150, 18)
    texto('Primeira multiplicação', 480, 155, 420, 24, negrito=True)
    codigo('CARREGA n        [1]\nEMPILHA_INT 5    [1, 5]\nMUL              [5]\nGUARDA t17       []', 480, 210, 18)
    texto('Depois, a VM soma 1 e grava 6 em n.<br/><br/>Cada chamada cria seu próprio registro de locais, preservando a recursão.', 480, 340, 420, 20)
    c.showPage()

    pagina('Caso técnico: divisão antes da conversão', 5, 'Uma regra da linguagem que precisa sobreviver à geração de código')
    codigo('real meio = 7 / 2;\nescreva(meio);', 48, 155, 26)
    texto('Resultado correto', 48, 275, 360, 23, negrito=True)
    texto('3.000000', 48, 320, 360, 42, ACENTO, negrito=True)
    texto('Causa de um resultado incorreto', 490, 155, 410, 23, negrito=True)
    texto('Converter 7 e 2 para real antes de dividir produziria 3.500000.', 490, 202, 410, 21)
    texto('Implementação atual', 490, 293, 410, 23, negrito=True)
    texto('DIV opera sobre dois inteiros.<br/>PARA_REAL converte o resultado 3.<br/><br/>Teste: test_divisao_resto_e_promocao.', 490, 338, 410, 19)
    c.showPage()

    pagina('Problema de entrega identificado na revisão', 6, 'A versão local estava diferente da versão registrada no Git')
    texto('Sintoma', 48, 155, 230, 23, negrito=True)
    texto('A pasta local executava a E4, mas o último commit ainda tinha os esqueletos.', 48, 205, 245, 21)
    texto('Diagnóstico', 355, 155, 230, 23, negrito=True)
    texto('git status mostrou código alterado e arquivos novos. git show HEAD confirmou a versão anterior.', 355, 205, 245, 21)
    texto('Correção', 662, 155, 250, 23, negrito=True)
    texto('Versionar código, evidência e exemplo. Verificar o clone limpo e o fluxo Linux no GitHub.', 662, 205, 250, 21)
    texto('Validação: corpus oficial, testes adicionais e saída exata da vitrine.', 48, 410, 850, 22, ACENTO)
    c.showPage()

    pagina('Parser manual e parser gerado', 7, 'Apoio para perguntas: comparação solicitada no enunciado')
    texto('Implementação do grupo', 48, 155, 410, 24, negrito=True)
    texto('Descida recursiva.<br/><br/>Uma função por nível de precedência.<br/><br/>Laços constroem os binários pela esquerda.<br/><br/>O código cria a AST explicitamente.', 48, 210, 410, 21)
    texto('Com um gerador', 520, 155, 380, 24, negrito=True)
    texto('Regras de gramática descrevem a sintaxe.<br/><br/>A ferramenta gera o reconhecedor.<br/><br/>A construção da AST ainda exige ações ou uma etapa posterior.', 520, 210, 380, 21)
    c.showPage()

    pagina('Preparação para a alteração ao vivo', 8, 'Apoio: localizar as fases afetadas antes de modificar a linguagem')
    linhas = [
        ('**', 'Léxico, precedência, tipos, IR, geração e VM'),
        ('senaose', 'Palavra reservada, parser e estrutura da AST'),
        ('escreva(a, b)', 'Parser, análise dos argumentos e emissão'),
        ('pare', 'Comando, contexto de laço e salto de saída'),
        ('curto-circuito', 'Desvios no IR antes do operando direito'),
    ]
    for i, (recurso, partes) in enumerate(linhas):
        y = 158 + i*57
        texto(escape(recurso), 48, y, 230, 21, negrito=True)
        texto(escape(partes), 300, y, 600, 20)
    texto('Aplicar somente a alteração sorteada e testar o comportamento novo.', 48, 460, 860, 17, ACENTO)
    c.showPage()
    c.save()
    print(DESTINO)


if __name__ == '__main__':
    gerar()
