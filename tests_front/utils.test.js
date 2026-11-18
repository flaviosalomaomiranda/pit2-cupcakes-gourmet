// TESTES UNITÁRIOS DO FRONT-END — executar com:  node --test tests_front
// Usa apenas o executor de testes nativo do Node.js (sem dependências).
const test = require('node:test');
const assert = require('node:assert/strict');
const U = require('../app/static/js/utils.js');

test('máscara de CEP é progressiva e limita a 8 dígitos', () => {
  assert.equal(U.mascaraCep('768'), '768');
  assert.equal(U.mascaraCep('768010'), '76801-0');
  assert.equal(U.mascaraCep('76801000'), '76801-000');
  assert.equal(U.mascaraCep('76801-0009999'), '76801-000');
  assert.equal(U.mascaraCep('ab76c801d000'), '76801-000');
});

test('validação de CEP', () => {
  assert.equal(U.cepValido('76801-000'), true);
  assert.equal(U.cepValido('7680'), false);
  assert.equal(U.cepValido(null), false);
});

test('máscara de telefone fixo e celular', () => {
  assert.equal(U.mascaraTelefone(''), '');
  assert.equal(U.mascaraTelefone('6'), '(6');
  assert.equal(U.mascaraTelefone('6932210000'), '(69) 3221-0000');
  assert.equal(U.mascaraTelefone('69999990000'), '(69) 99999-0000');
  assert.equal(U.mascaraTelefone('699999900001234'), '(69) 99999-0000');
});

test('máscara de cartão agrupa de 4 em 4', () => {
  assert.equal(U.mascaraCartao('4111111111111111'), '4111 1111 1111 1111');
  assert.equal(U.mascaraCartao('41111'), '4111 1');
});

test('máscara de validade MM/AA', () => {
  assert.equal(U.mascaraValidade('1'), '1');
  assert.equal(U.mascaraValidade('1235'), '12/35');
  assert.equal(U.mascaraValidade('12/3599'), '12/35');
});

test('algoritmo de Luhn igual ao do back-end', () => {
  assert.equal(U.luhnValido('4111 1111 1111 1111'), true);
  assert.equal(U.luhnValido('4000000000000002'), true);
  assert.equal(U.luhnValido('4111111111111112'), false);
  assert.equal(U.luhnValido('123'), false);
});

test('quantidade fica entre mínimo e máximo', () => {
  assert.equal(U.limitarQuantidade(0, 1, 50), 1);
  assert.equal(U.limitarQuantidade(51, 1, 50), 50);
  assert.equal(U.limitarQuantidade('7', 1, 50), 7);
  assert.equal(U.limitarQuantidade('abc', 1, 50), 1);
});

test('contagem regressiva do PIX', () => {
  assert.equal(U.formatarContagem(900), '15:00');
  assert.equal(U.formatarContagem(61.9), '01:01');
  assert.equal(U.formatarContagem(-5), '00:00');
});

test('formatação de moeda igual ao back-end', () => {
  assert.equal(U.formatarBRL(1250), 'R$ 12,50');
  assert.equal(U.formatarBRL(5), 'R$ 0,05');
  assert.equal(U.formatarBRL(123456), 'R$ 1.234,56');
  assert.equal(U.formatarBRL(-990), '-R$ 9,90');
});

test('busca ao vivo ignora acentos e maiúsculas (avaliação Nataska)', () => {
  assert.equal(U.normalizarTexto('  Açaí  com CASTANHA '), 'acai com castanha');
  assert.equal(U.correspondeBusca('Açaí com Castanha Regionais', 'acai'), true);
  assert.equal(U.correspondeBusca('Cupuaçu Regionais', 'CUPUACU'), true);
  assert.equal(U.correspondeBusca('Coca-Cola lata 350 ml Bebidas', 'coca lata'), true);
  assert.equal(U.correspondeBusca('Red Velvet', 'coca'), false);
  assert.equal(U.correspondeBusca('Qualquer coisa', '   '), true);
});
