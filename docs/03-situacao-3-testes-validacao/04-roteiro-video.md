# Roteiro do vídeo (≈5 minutos, narrado)

> O material pede, em um ponto, "até 5 minutos" e, em outro, "no mínimo 5 minutos". Mire em **5:00 a 5:30**. Grave a tela com o Xbox Game Bar (Win+G), o OBS ou o Clipchamp, com o microfone ligado.

| Tempo | Tela | O que falar |
|---|---|---|
| 0:00–0:30 | README no GitHub | "Sou o Flavio, RGM 46724478. Este é o Doce Nuvem Cupcakes, a continuação do meu Projeto Integrador I. Lá eu planejei uma loja virtual de cupcakes, e aqui está o sistema funcionando, feito em Python com Flask no padrão MVC, banco SQLite e front em HTML, CSS e JavaScript." |
| 0:30–1:00 | Pasta `docs/` e imagem dos casos de uso | "Revisei a documentação do PIT I: escopo, UML, IHC e banco. As principais mudanças foram trocar o app nativo por um site responsivo, criar o histórico de status e as zonas de frete e guardar os valores em centavos." |
| 1:00–2:15 | Celular ou janela estreita: vitrine → filtro → detalhe → carrinho | Mostrar o filtro, os ingredientes, o + e −, a embalagem presente, o CEP recusado e depois o aceito. "Repare que o contador do carrinho atualiza na hora." |
| 2:15–3:00 | Checkout com e-mail errado → PIX → simular confirmação | "Se eu erro o e-mail, o sistema destaca o campo e não apaga o que digitei. No PIX, ele gera um código no padrão oficial do Banco Central, válido por 15 minutos." |
| 3:00–3:40 | Painel `/admin` | "No painel, o lojista recebe o pedido com alerta sonoro, vê que é presente e avança o status." Depois, mostrar a linha do tempo atualizada no cliente. |
| 3:40–4:30 | Terminal rodando `python -m pytest tests -v` | "São 121 testes automatizados: unitários, de integração e de sistema no navegador, todos passando, com 93% de cobertura. Os testes acharam um defeito real: o campo do cartão tinha o mesmo nome do número da casa. Corrigi e documentei no laudo." |
| 4:30–5:15 | `03-resultado-avaliacoes.md` | "Cinco pessoas testaram. [Cite 1 ou 2 sugestões reais e o que você mudou.]" |
| 5:15–5:30 | Roadmap | "Próximos passos: gateway de pagamento real, cadastro de clientes e PostgreSQL. Obrigado!" |
