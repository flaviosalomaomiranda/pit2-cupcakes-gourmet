/* Comportamentos de interface. Tudo é "melhoria progressiva": sem JavaScript o site continua
 * funcionando via formulários; com JavaScript fica mais rápido e com feedback imediato. */
(function () {
  'use strict';
  var U = window.Utils;
  var $ = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };

  function aplicarMascara(sel, fn) {
    $$(sel).forEach(function (el) {
      el.addEventListener('input', function () { el.value = fn(el.value); });
    });
  }
  aplicarMascara('[data-mascara-cep]', U.mascaraCep);
  aplicarMascara('[data-mascara-telefone]', U.mascaraTelefone);
  aplicarMascara('[data-mascara-cartao]', U.mascaraCartao);
  aplicarMascara('[data-mascara-validade]', U.mascaraValidade);

  // Quantidade com botões + e − na página de detalhe
  $$('[data-qtd]').forEach(function (box) {
    var input = $('input', box);
    var min = parseInt(input.min, 10) || 1, max = parseInt(input.max, 10) || 50;
    $('[data-qtd-menos]', box).addEventListener('click', function () { input.value = U.limitarQuantidade(+input.value - 1, min, max); });
    $('[data-qtd-mais]', box).addEventListener('click', function () { input.value = U.limitarQuantidade(+input.value + 1, min, max); });
    input.addEventListener('change', function () { input.value = U.limitarQuantidade(input.value, min, max); });
  });

  // Adicionar ao carrinho sem recarregar a vitrine (atualiza o contador do topo na hora)
  $$('form[data-add-carrinho]').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      if (!window.fetch) return;
      ev.preventDefault();
      var botao = $('button', form);
      botao.disabled = true;
      fetch(form.action, { method: 'POST', body: new FormData(form), credentials: 'same-origin',
                           headers: { 'X-Requested-With': 'fetch' } })
        .then(function (r) { return r.json().then(function (j) { return { r: r, j: j }; }); })
        .then(function (res) {
          if (!res.r.ok) { botao.textContent = res.j.mensagem || 'Não foi possível adicionar'; return; }
          var badge = $('[data-badge]');
          badge.textContent = res.j.total_itens;
          badge.classList.remove('badge--vazio');
          badge.classList.add('badge--pulo');
          setTimeout(function () { badge.classList.remove('badge--pulo'); }, 400);
          botao.textContent = '✓ Adicionado';
          setTimeout(function () { botao.textContent = '+ Adicionar'; }, 1200);
        })
        .catch(function () { form.submit(); })   // fallback: envia do jeito tradicional
        .then(function () { botao.disabled = false; });
    });
  });

  // Busca ao vivo na vitrine: filtra os cards enquanto digita (sem precisar clicar em "Buscar")
  var campoBusca = $('[data-busca-ao-vivo]');
  if (campoBusca) {
    var cards = $$('.card[data-texto]');
    var semResultado = $('[data-sem-resultado]');
    var termoSaida = $('[data-termo]');
    var espera = null;
    var filtrar = function () {
      var termo = campoBusca.value;
      var visiveis = 0;
      cards.forEach(function (c) {
        var ok = U.correspondeBusca(c.getAttribute('data-texto'), termo);
        c.hidden = !ok;
        if (ok) visiveis++;
      });
      semResultado.hidden = visiveis > 0;
      termoSaida.textContent = termo.trim() ? ' para “' + termo.trim() + '”' : '';
      try {
        var url = new URL(window.location.href);
        if (termo.trim()) url.searchParams.set('q', termo.trim()); else url.searchParams.delete('q');
        history.replaceState(null, '', url);
      } catch (e) { /* navegador antigo: só não atualiza o endereço */ }
    };
    campoBusca.addEventListener('input', function () { clearTimeout(espera); espera = setTimeout(filtrar, 120); });
    campoBusca.addEventListener('search', filtrar);   // botão "x" do campo de busca
  }

  // Prévia do frete enquanto digita o CEP
  var formFrete = $('[data-frete]');
  if (formFrete) {
    var campoCep = $('[data-mascara-cep]', formFrete), saida = $('[data-frete-resultado]', formFrete);
    campoCep.addEventListener('input', function () {
      if (!U.cepValido(campoCep.value)) return;
      fetch('/carrinho/api/frete?cep=' + encodeURIComponent(campoCep.value))
        .then(function (r) { return r.json(); })
        .then(function (j) {
          saida.textContent = j.ok ? (j.zona + ': ' + j.valor + ' · até ' + j.prazo + ' min — clique em Calcular para aplicar') : j.mensagem;
          saida.classList.toggle('erro', !j.ok);
        }).catch(function () {});
    });
  }

  // Embalagem presente: mostra/esconde a mensagem e conta caracteres
  var toggle = $('[data-toggle-mensagem]');
  if (toggle) toggle.addEventListener('change', function () { $('[data-mensagem-presente]').hidden = !toggle.checked; });
  $$('[data-contador]').forEach(function (ta) {
    var saida = $('[data-contador-saida]');
    ta.addEventListener('input', function () { saida.textContent = ta.value.length + '/140'; });
  });

  // Checkout: mostra campos do cartão só quando escolhido; evita clique duplo no "Confirmar"
  $$('[data-metodo]').forEach(function (r) {
    r.addEventListener('change', function () { $('[data-cartao]').hidden = r.value !== 'CARTAO' || !r.checked; });
  });
  var formCheckout = $('[data-checkout]');
  if (formCheckout) {
    formCheckout.addEventListener('submit', function (ev) {
      var cartao = $('input[name=metodo][value=CARTAO]', formCheckout).checked;
      var numero = $('#numero_cartao');
      if (cartao && !U.luhnValido(numero.value)) {
        ev.preventDefault();
        numero.setAttribute('aria-invalid', 'true');
        numero.focus();
        alertaInline(numero, 'Número do cartão inválido.');
        return;
      }
      var b = $('[data-enviar]', formCheckout);
      b.disabled = true; b.textContent = 'Processando…';
    });
  }
  function alertaInline(campo, msg) {
    var p = campo.parentNode.querySelector('.erro-inline') || document.createElement('p');
    p.className = 'erro-inline'; p.textContent = msg;
    campo.parentNode.appendChild(p);
  }

  // PIX: copiar código e contagem regressiva de 15 minutos
  var copiar = $('[data-copiar]');
  if (copiar) copiar.addEventListener('click', function () {
    var origem = $('[data-copiar-origem]');
    origem.select();
    var ok = function () { copiar.textContent = '✓ Copiado'; setTimeout(function () { copiar.textContent = 'Copiar código'; }, 1500); };
    if (navigator.clipboard) navigator.clipboard.writeText(origem.value).then(ok, function () { document.execCommand('copy'); ok(); });
    else { document.execCommand('copy'); ok(); }
  });
  var contagem = $('[data-contagem]');
  if (contagem) {
    var fim = parseInt(contagem.getAttribute('data-contagem'), 10) * 1000;
    var tick = function () {
      var resta = (fim - Date.now()) / 1000;
      contagem.textContent = U.formatarContagem(resta);
      if (resta <= 0) { location.reload(); return; }
      setTimeout(tick, 1000);
    };
    tick();
  }

  // Página de acompanhamento atualiza sozinha
  var auto = $('[data-auto-recarregar]');
  if (auto) setTimeout(function () { location.reload(); }, parseInt(auto.getAttribute('data-auto-recarregar'), 10) * 1000);

  // Confirmação antes de ações destrutivas
  $$('form[data-confirmar]').forEach(function (f) {
    f.addEventListener('submit', function (ev) { if (!window.confirm(f.getAttribute('data-confirmar'))) ev.preventDefault(); });
  });

  // Painel: verifica novos pedidos a cada 15 s e toca alerta (o navegador exige 1 clique para liberar som)
  var nav = $('[data-total-pagos]');
  if (nav) {
    var conhecido = parseInt(nav.getAttribute('data-total-pagos'), 10);
    var somLiberado = false, audioCtx = null;
    var botaoSom = $('[data-ativar-som]');
    botaoSom.addEventListener('click', function () {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (Ctx) { audioCtx = audioCtx || new Ctx(); somLiberado = true; bip(); }
      botaoSom.textContent = '🔔 Alerta sonoro ativo'; botaoSom.setAttribute('aria-pressed', 'true');
    });
    function bip() {
      if (!somLiberado || !audioCtx) return;
      [0, 0.25].forEach(function (t) {
        var o = audioCtx.createOscillator(), g = audioCtx.createGain();
        o.frequency.value = 880; o.connect(g); g.connect(audioCtx.destination);
        g.gain.setValueAtTime(0.25, audioCtx.currentTime + t);
        o.start(audioCtx.currentTime + t); o.stop(audioCtx.currentTime + t + 0.18);
      });
    }
    setInterval(function () {
      fetch(nav.getAttribute('data-url-resumo'), { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (j.total_pagos > conhecido) {
            conhecido = j.total_pagos;
            $('[data-novo-pedido]').hidden = false;
            document.title = '🔔 Novo pedido! — Doce Nuvem';
            bip();
          }
        }).catch(function () {});
    }, 15000);
  }
})();
