# Resultado das avaliações por pares

> Preenchido com as respostas reais dos avaliadores, repassadas ao autor no dia do teste (17/11/2026). Nenhuma avaliação foi inventada. Campos em branco ainda não foram recebidos.

| # | Avaliador | Data | Funcionou | Não funcionou / corrigir | Não testado | Ação tomada (v1.1) |
|---|---|---|---|---|---|---|
| 1 | Nataska Wanssa | 17/11/2026 | | (a) Ao filtrar "Regionais", a busca digitada antes continuava aplicada. (b) A busca não era automática: só filtrava ao clicar em "Buscar". (c) Os regionais tinham imagens iguais às dos outros. (d) Faltavam bebidas: água e Coca normal. | | (a) Trocar de categoria limpa a busca, e há o link "✕ Limpar busca". (b) Busca ao vivo enquanto digita, sem diferenciar acentos e maiúsculas. (c) Cada sabor ganhou um enfeite próprio: açaí com castanha, cupuaçu aberto, coco, morango, limão, chocolate e ervas. (d) Nova categoria **Bebidas** com água sem gás, água com gás, Coca-Cola e Coca-Cola Zero. |
| 2 | Leopoldo Fuji | | | | | |
| 3 | Leonardo Gobbi | 17/11/2026 | | Não gostou do estilo das imagens; preferia fotos mais realistas, porque as ilustrações não estavam atrativas. | | Ilustrações refeitas com volume: gradientes, cobertura em camadas, brilho e sombra. **Fotos reais ficaram no Roadmap (v1.3):** precisam ser fotos dos produtos da própria loja. Usar fotos de banco de imagens mostraria ao cliente um produto que ele não vai receber, o que contraria a US01. |
| 4 | Fernando Miranda | | | | | |
| 5 | Luiz Cláudio | 17/11/2026 | | Digitou um CEP diferente do sugerido no roteiro e o frete foi recusado. | | Causa: a faixa da zona Centro começava em 76800-001 e excluía **76800-000**, o CEP geral de Porto Velho. Faixa corrigida por migração do banco, e a mensagem agora informa os CEPs atendidos ("76800-000 a 76834-999"). CEPs de outras cidades continuam recusados, como manda a regra de negócio (US08). |

## Melhorias incorporadas após as avaliações (versão 1.1)

| Sugestão | Avaliador | Decisão | Evidência |
|---|---|---|---|
| Busca limpa ao trocar de categoria | Nataska | ✅ Feito | `test_v11_trocar_categoria_limpa_a_busca` |
| Busca automática | Nataska | ✅ Feito (filtra enquanto digita) | `tests_front`: busca sem acento; E2E passo 1b; captura `16-busca-ao-vivo-bebidas.png` |
| Imagens diferentes nos regionais | Nataska | ✅ Feito | `test_v11_imagens_diferentes_por_sabor_e_bebida` (15 desenhos distintos) |
| Água e Coca | Nataska | ✅ Feito (categoria Bebidas) | `test_v11_categoria_bebidas_com_agua_e_coca`, `test_v11_bebida_vai_ao_carrinho_e_ao_pedido` |
| Imagens mais atrativas | Leonardo | ✅ Parcial: ilustrações com volume. Fotos reais → Roadmap v1.3 | captura `13-vitrine-desktop.png` |
| CEP de Porto Velho recusado | Luiz Cláudio | ✅ Corrigido | `test_v11_cep_geral_de_porto_velho_e_aceito` |

A atualização foi feita **sem apagar os pedidos dos testadores**: o banco ganhou controle de versão (`PRAGMA user_version`) e migrações em `database/migracoes/`, cobertas por `test_v11_migracao_preserva_pedidos_de_banco_antigo`.
