# 1. Escopo revisado (Kaizen sobre o PIT I)

## 1.1 Identificação

| Item | Valor |
|---|---|
| Sistema | **Doce Nuvem Cupcakes Gourmet**: loja virtual de cupcakes |
| Origem | Projeto Integrador Transdisciplinar em Engenharia de Software I (Loja de Cupcakes Gourmet) |
| Autor | Flavio (RGM 46724478) |
| Tipo | Aplicação web responsiva (*mobile-first*), usável no celular e no computador |
| Stack | Python 3 + Flask (MVC) · SQLite 3 · HTML5/CSS3/JavaScript |

## 1.2 Problema

O cliente (loja de cupcakes gourmet) já teve um aplicativo anterior que "não funcionava". As reclamações dos clientes foram tantas que ele tirou o app do ar e a imagem da marca sofreu. Ele precisa de um canal de vendas on-line confiável, focado em quatro pilares do briefing: **vitrine virtual, pedido eletrônico, pagamento e entrega**.

## 1.3 Objetivo do MVP do PIT II

Entregar um produto funcional e testado que permita:

1. ao **cliente**: ver o cardápio, filtrar, montar o carrinho, pedir embalagem presente, calcular o frete pelo CEP, pagar (PIX ou cartão) e acompanhar o pedido;
2. ao **lojista**: receber os pedidos pagos num painel com alerta e avançar o status até a entrega.

## 1.4 O que mudou desde o PIT I (ciclo de melhoria contínua)

| # | No PIT I | No PIT II | Motivo |
|---|---|---|---|
| K1 | "Aplicativo mobile" | Web app responsivo *mobile-first* | Um código só atende celular e PC, sem instalação nem loja de apps. Custo e manutenção menores. |
| K2 | Login/cadastro na entrada (Splash → Login → Home) | Compra como **convidado**; o login fica só para o lojista | Pedir cadastro antes de comprar aumenta o abandono, e o cadastro de cliente não estava no backlog de alta prioridade. |
| K3 | Pagamento real via gateway | Pagamento **simulado** com formato real: PIX Copia e Cola no padrão EMV/BR Code com CRC16, e cartão com validação de Luhn, validade e CVV | Um gateway real exige CNPJ e contrato. A troca fica isolada em `services/pagamento.py` (ver Roadmap). |
| K4 | Classe `Pedido` sem histórico | Nova entidade **HistoricoStatus** | Atender a US09 (linha do tempo com horários) e auditar quem mudou o quê. |
| K5 | Frete "consultar base de entrega" (vago) | Entidade **ZonaEntrega** com faixa de CEP, valor e prazo | Deixar a regra de negócio testável e configurável. |
| K6 | Valores monetários sem tipo definido | Tudo em **centavos (INTEGER)**, com `CHECK` de total no banco | Evita erros de arredondamento com ponto flutuante. |
| K7 | Endereço só no cadastro do cliente | Endereço **copiado no pedido** | Se o cliente se mudar, o pedido antigo continua correto. |
| K8 | Sem regras de transição de status | **Máquina de estados** (o status não pula etapas nem volta) | Evita erros do lojista e conflitos entre duas abas abertas. |
| K9 | Não havia requisitos de segurança | CSRF, CSP, hash de senha, limite de tentativas de login, cartão nunca salvo | Segurança desde o projeto. |
| K10 | 10 histórias | 12 histórias (US11 painel com alerta, US12 busca) | Detalhamento do critério de aceite da US10 e da US02. |

## 1.5 Histórias de usuário revisadas

| ID | Como… | Quero… | Para… | Prioridade | Pontos | Status no MVP |
|---|---|---|---|---|---|---|
| US01 | cliente | ver o catálogo com imagens padronizadas, nome e preço | me interessar pelos produtos | A | 3 | ✅ Entregue |
| US02 | cliente | filtrar por categoria (tradicional, diet, salgado, regional) | achar rápido o que desejo | B | 2 | ✅ Entregue |
| US03 | cliente | ler descrição, ingredientes e alergênicos | evitar problemas com alergias | B | 2 | ✅ Entregue |
| US04 | cliente | adicionar vários sabores, alterar com + e − e remover | fazer um pedido único | A | 5 | ✅ Entregue |
| US05 | cliente | pedir embalagem presente com mensagem | enviar como lembrancinha | B | 3 | ✅ Entregue |
| US06 | cliente | ver subtotal + embalagem + frete = total antes de pagar | ter clareza do gasto | A | 2 | ✅ Entregue |
| US07 | cliente | pagar via PIX ou cartão de forma segura | ter rapidez e flexibilidade | A | 8 | ✅ Entregue (gateway simulado) |
| US08 | cliente | informar o CEP e ver valor e prazo da entrega | decidir antes de pagar | A | 3 | ✅ Entregue |
| US09 | cliente | acompanhar o status (recebido → em preparo → saiu → entregue) | me programar para receber | C | 3 | ✅ Entregue |
| US10 | lojista | ver os pedidos pagos organizados num painel | separar e despachar rápido | A | 5 | ✅ Entregue |
| US11 | lojista | ser avisado com som quando chegar pedido pago | não perder pedidos | B | 2 | ✅ Entregue |
| US12 | cliente | buscar por nome ou ingrediente | encontrar um sabor específico | C | 1 | ✅ Entregue |

### Critérios de aceite (resumo) e onde são verificados

| História | Critérios de aceite | Teste automatizado |
|---|---|---|
| US01 | Imagens quadradas e leves (SVG ≈1 KB); nome e preço em cada card | `test_us01_*`, `test_imagem_svg_do_cupcake` |
| US02/US12 | Filtro por categoria; categoria inválida mostra "Todos"; busca sem resultado mostra mensagem | `test_us02_*` |
| US04 | Contador do topo atualiza na hora; + e −; quantidade 0 remove; carrinho vazio mostra "Ver cupcakes"; máximo de 50 por sabor | `test_us04_*`, E2E |
| US05 | Embalagem soma R$ 5,00; mensagem de até 140 caracteres | `test_us05_*`, `test_mensagem_presente_limite` |
| US06 | Total = subtotal + embalagem + frete; recalcula ao mudar a quantidade | `test_calcular_totais_*`, `test_banco_rejeita_total_inconsistente` |
| US07 | PIX com QR Code e Copia e Cola válidos por 15 min; aprovação automática na confirmação do banco; cartão não é salvo; recusa com mensagem clara e volta à escolha do pagamento | `test_uc04_*`, `test_pix_*`, `test_luhn` |
| US08 | Máscara 00000-000; valor e prazo; fora da área: "Desculpe, ainda não entregamos nesta região." | `test_us08_*`, `test_calcular_frete_*` |
| US09 | Linha do tempo com horário de cada etapa; atualização automática | `test_us09_*`, `test_us10_lojista_avanca_status_ate_entregue` |
| US10/US11 | Destaque para nome, endereço, itens e presente; botões de avanço; alerta sonoro e visual | `test_us10_*`, E2E |

## 1.6 Fora do escopo do MVP (vai para o Roadmap)

Cadastro e login de cliente, gateway de pagamento real, cadastro de produtos pelo painel, rastreio por GPS, cupons de desconto, notificações por WhatsApp/e-mail.

## 1.7 Requisitos não funcionais

| ID | Requisito | Como foi atendido |
|---|---|---|
| RNF01 Desempenho | Rodar bem em celular simples e conexão 3G | Sem frameworks no front: CSS ≈10 KB, JS ≈8 KB, imagens SVG ≈1 KB e com cache. Fontes do sistema, sem download. |
| RNF02 Usabilidade | Funcionar com uma mão no celular | Botões com no mínimo 44 px, campos com teclado numérico (`inputmode`), mensagens de erro no próprio campo |
| RNF03 Acessibilidade | Navegável por teclado e leitor de tela | HTML semântico, `aria-live`, `aria-invalid`, link "pular para o conteúdo", foco visível, `prefers-reduced-motion` |
| RNF04 Segurança | Proteger dados e transações | CSRF em todo POST; CSP restritiva; SQL parametrizado; senha em hash; limite de 5 tentativas de login; cartão nunca armazenado |
| RNF05 Confiabilidade | Pedido nunca fica pela metade | Criação transacional (commit/rollback) e restrições `CHECK`/`FK` no banco |
| RNF06 Manutenibilidade | Fácil de evoluir | MVC, regras puras isoladas em `services/`, 111 testes automatizados, cobertura de 93% |
| RNF07 Degradação graciosa | Funcionar mesmo com o JavaScript desligado | Tudo funciona por formulários; o JS só acelera |
