/* Funções puras do front-end (sem DOM) — testadas com `node --test tests_front`.
 * Funcionam no navegador (window.Utils) e no Node (module.exports). */
(function (raiz) {
  'use strict';

  function soDigitos(texto) {
    return String(texto == null ? '' : texto).replace(/\D/g, '');
  }

  /** '76801000' -> '76801-000' (máscara progressiva enquanto digita) */
  function mascaraCep(texto) {
    var d = soDigitos(texto).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
  }

  function cepValido(texto) {
    return soDigitos(texto).length === 8;
  }

  /** '69999990000' -> '(69) 99999-0000' ; '6932210000' -> '(69) 3221-0000' */
  function mascaraTelefone(texto) {
    var d = soDigitos(texto).slice(0, 11);
    if (d.length <= 2) return d.length ? '(' + d : '';
    var ddd = '(' + d.slice(0, 2) + ') ';
    var resto = d.slice(2);
    if (d.length <= 6) return ddd + resto;
    var corte = d.length === 11 ? 5 : 4;
    return ddd + resto.slice(0, corte) + '-' + resto.slice(corte);
  }

  /** agrupa de 4 em 4: '4111111111111111' -> '4111 1111 1111 1111' */
  function mascaraCartao(texto) {
    var d = soDigitos(texto).slice(0, 19);
    return d.replace(/(.{4})/g, '$1 ').trim();
  }

  function mascaraValidade(texto) {
    var d = soDigitos(texto).slice(0, 4);
    return d.length > 2 ? d.slice(0, 2) + '/' + d.slice(2) : d;
  }

  function luhnValido(texto) {
    var d = soDigitos(texto);
    if (d.length < 13) return false;
    var soma = 0;
    for (var i = 0; i < d.length; i++) {
      var n = parseInt(d.charAt(d.length - 1 - i), 10);
      if (i % 2 === 1) { n *= 2; if (n > 9) n -= 9; }
      soma += n;
    }
    return soma % 10 === 0;
  }

  /** limita a quantidade ao intervalo [min, max]; valores inválidos viram min */
  function limitarQuantidade(valor, min, max) {
    var n = parseInt(valor, 10);
    if (isNaN(n)) return min;
    return Math.min(max, Math.max(min, n));
  }

  /** segundos -> 'MM:SS' (nunca negativo) */
  function formatarContagem(segundos) {
    var s = Math.max(0, Math.floor(segundos));
    var m = Math.floor(s / 60);
    var r = s % 60;
    return (m < 10 ? '0' : '') + m + ':' + (r < 10 ? '0' : '') + r;
  }

  /** 1250 -> 'R$ 12,50' (mesma regra do back-end) */
  function formatarBRL(centavos) {
    var negativo = centavos < 0;
    var c = Math.abs(Math.round(centavos));
    var reais = Math.floor(c / 100).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    var cents = (c % 100).toString();
    if (cents.length < 2) cents = '0' + cents;
    return (negativo ? '-' : '') + 'R$ ' + reais + ',' + cents;
  }

  /** minúsculas e sem acento: 'Açaí' -> 'acai' */
  function normalizarTexto(texto) {
    return String(texto == null ? '' : texto).toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, ' ').trim();
  }

  /** busca ao vivo: todas as palavras digitadas precisam aparecer no texto (sem acento, sem maiúsculas) */
  function correspondeBusca(texto, termo) {
    var alvo = normalizarTexto(texto);
    var palavras = normalizarTexto(termo).split(' ').filter(Boolean);
    for (var i = 0; i < palavras.length; i++) if (alvo.indexOf(palavras[i]) === -1) return false;
    return true;
  }

  var api = {
    normalizarTexto: normalizarTexto, correspondeBusca: correspondeBusca,
    soDigitos: soDigitos, mascaraCep: mascaraCep, cepValido: cepValido,
    mascaraTelefone: mascaraTelefone, mascaraCartao: mascaraCartao, mascaraValidade: mascaraValidade,
    luhnValido: luhnValido, limitarQuantidade: limitarQuantidade, formatarContagem: formatarContagem,
    formatarBRL: formatarBRL
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else raiz.Utils = api;
})(this);
