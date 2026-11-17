// vitrine.mpl — o programa que o grupo apresenta na Entrega 4.
//
// A MPL nao converte numero em texto, entao a primeira coisa que este
// programa faz e ESCREVER essa conversao na propria MPL, com recursao.
// Depois usa ela para mostrar: Torre de Hanoi (recursao com funcao vazio),
// conversao para binario, raiz quadrada por Newton (real), a sequencia de
// Collatz (laco + resto) e as duas armadilhas da divisao inteira.

funcao texto digito(inteiro d) {
  se (d == 0) { retorne "0"; }
  se (d == 1) { retorne "1"; }
  se (d == 2) { retorne "2"; }
  se (d == 3) { retorne "3"; }
  se (d == 4) { retorne "4"; }
  se (d == 5) { retorne "5"; }
  se (d == 6) { retorne "6"; }
  se (d == 7) { retorne "7"; }
  se (d == 8) { retorne "8"; }
  retorne "9";
}

// inteiro -> texto, em qualquer base de 2 a 10
funcao texto naBase(inteiro n, inteiro base) {
  se (n < 0) {
    retorne "-" + naBase(-n, base);
  }
  se (n < base) {
    retorne digito(n);
  }
  retorne naBase(n / base, base) + digito(n % base);
}

funcao texto paraTexto(inteiro n) {
  retorne naBase(n, 10);
}

// Torre de Hanoi: move n discos de 'de' para 'para' usando 'via'
funcao vazio hanoi(inteiro n, texto de, texto para, texto via) {
  se (n == 0) {
    retorne;
  }
  hanoi(n - 1, de, via, para);
  escreva("  disco " + paraTexto(n) + ": " + de + " -> " + para);
  hanoi(n - 1, via, para, de);
}

funcao inteiro movimentos(inteiro n) {
  se (n == 0) {
    retorne 0;
  }
  retorne 2 * movimentos(n - 1) + 1;
}

// raiz quadrada pelo metodo de Newton
funcao real raiz(real x) {
  real r = x;
  inteiro i = 0;
  enquanto (i < 20) {
    r = (r + x / r) / 2.0;
    i = i + 1;
  }
  retorne r;
}

// quantos passos ate chegar em 1
funcao inteiro collatz(inteiro n) {
  inteiro passos = 0;
  enquanto (n != 1) {
    se (n % 2 == 0) {
      n = n / 2;
    } senao {
      n = 3 * n + 1;
    }
    passos = passos + 1;
  }
  retorne passos;
}

funcao vazio principal() {
  escreva("== Torre de Hanoi com 3 discos ==");
  hanoi(3, "A", "C", "B");
  escreva("total: " + paraTexto(movimentos(3)) + " movimentos (com 10 discos seriam " + paraTexto(movimentos(10)) + ")");

  escreva("== Numeros em outras bases ==");
  inteiro n = 1;
  enquanto (n <= 200) {
    escreva(paraTexto(n) + " = " + naBase(n, 2) + " (base 2) = " + naBase(n, 8) + " (base 8)");
    n = n * 5 + 1;
  }

  escreva("== Raiz quadrada por Newton ==");
  escreva(raiz(2.0));
  escreva(raiz(10));

  escreva("== Collatz ==");
  escreva("27 chega a 1 em " + paraTexto(collatz(27)) + " passos");

  escreva("== As armadilhas da divisao ==");
  real meio = 7 / 2;
  escreva(meio);
  escreva("-7 / 2 = " + paraTexto(-7 / 2) + "   e   -7 % 3 = " + paraTexto(-7 % 3));
}
