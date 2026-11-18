# 5. Dicionário de dados

> Gerado automaticamente a partir de `database/schema.sql` por `scripts/gerar_dicionario_dados.py`.
> Convenções: valores monetários em **centavos** (INTEGER); datas em texto ISO-8601 UTC; booleanos como INTEGER 0/1 (padrão do SQLite).

## categoria

Agrupamento de cupcakes usado nos filtros da vitrine (US02).

| Coluna | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id` | INTEGER | Não | PK | Identificador da categoria. |
| `nome` | TEXT | Não | UNIQUE, CHECK | Nome exibido no filtro (ex.: Tradicionais). |
| `slug` | TEXT | Não | UNIQUE, CHECK | Identificador usado na URL (?categoria=diet); só letras minúsculas. |

## cupcake

Produto do cardápio exibido na vitrine (US01, US03). Desde a v1.1 inclui bebidas.

| Coluna | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id` | INTEGER | Não | PK | Identificador do cupcake. |
| `categoria_id` | INTEGER | Não | FK → categoria | Categoria à qual o cupcake pertence. |
| `nome` | TEXT | Não | UNIQUE, CHECK | Nome comercial do sabor. |
| `descricao` | TEXT | Não | CHECK | Texto de apresentação do produto. |
| `ingredientes` | TEXT | Não | CHECK | Lista de ingredientes (US03 — evitar problemas com alergias). |
| `alergenicos` | TEXT | Não | DEFAULT '' | Alergênicos declarados (glúten, ovos, lactose…). |
| `preco_centavos` | INTEGER | Não | CHECK | Preço unitário em centavos (R$ 12,50 = 1250). |
| `cor_cobertura` | TEXT | Não | CHECK, DEFAULT '#f4a6c0' | Cor hexadecimal usada na ilustração do produto. |
| `ilustracao` | TEXT | Não | CHECK, DEFAULT 'cupcake' | Tipo de desenho do produto: cupcake, lata ou garrafa (v1.1, bebidas). |
| `enfeite` | TEXT | Não | DEFAULT 'cereja' | Enfeite desenhado no topo do cupcake (cereja, açaí, cupuaçu, coco…), para cada sabor ter imagem própria (v1.1). |
| `ativo` | INTEGER | Não | CHECK, DEFAULT 1 | 1 = aparece na vitrine; 0 = fora do cardápio (exclusão lógica). |

Restrições de tabela: `CHECK (enfeite IN ('cereja','morango','chocolate','limao','ervas','acai','cupuacu','coco','nenhum'))`

Índices: `ix_cupcake_categoria`

## zona_entrega

Faixa de CEPs atendida, com valor e prazo do frete (US08).

| Coluna | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id` | INTEGER | Não | PK | Identificador da zona. |
| `nome` | TEXT | Não | UNIQUE | Nome da região (ex.: Zona Sul). |
| `cep_inicio` | INTEGER | Não | CHECK | Primeiro CEP da faixa (8 dígitos, sem hífen). |
| `cep_fim` | INTEGER | Não | CHECK | Último CEP da faixa (deve ser ≥ cep_inicio). |
| `valor_centavos` | INTEGER | Não | CHECK | Valor do frete em centavos. |
| `prazo_minutos` | INTEGER | Não | CHECK | Prazo estimado de entrega em minutos. |

Restrições de tabela: `CHECK (cep_inicio <= cep_fim)`

## cliente

Pessoa que realiza o pedido (compra como convidado no MVP).

| Coluna | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id` | INTEGER | Não | PK | Identificador do cliente. |
| `nome` | TEXT | Não | CHECK | Nome completo. |
| `telefone` | TEXT | Não | CHECK | Celular/telefone só com dígitos (DDD + número). |
| `email` | TEXT | Não | CHECK | E-mail em minúsculas. |
| `criado_em` | TEXT | Não | DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')) | Data/hora de cadastro (UTC, ISO-8601). |

Índices: `ix_cliente_email`

## pedido

Cabeçalho do pedido, com endereço e valores congelados no momento da compra.

| Coluna | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id` | INTEGER | Não | PK | Identificador interno. |
| `codigo` | TEXT | Não | UNIQUE, CHECK | Código público de 8 caracteres usado pelo cliente para acompanhar. |
| `cliente_id` | INTEGER | Não | FK → cliente | Cliente que fez o pedido. |
| `zona_entrega_id` | INTEGER | Não | FK → zona_entrega | Zona de entrega usada no cálculo do frete. |
| `status` | TEXT | Não | DEFAULT 'AGUARDANDO_PAGAMENTO' | Situação atual: AGUARDANDO_PAGAMENTO, RECEBIDO, EM_PREPARO, SAIU_PARA_ENTREGA, ENTREGUE, CANCELADO. |
| `embalagem_presente` | INTEGER | Não | CHECK, DEFAULT 0 | 1 = cliente pediu caixa presente (US05). |
| `mensagem_presente` | TEXT | Não | CHECK, DEFAULT '' | Texto do cartão do presente (até 140 caracteres). |
| `cep` | INTEGER | Não | — | CEP de entrega (8 dígitos). |
| `logradouro` | TEXT | Não | CHECK | Rua/avenida de entrega. |
| `numero` | TEXT | Não | CHECK | Número do endereço. |
| `bairro` | TEXT | Não | CHECK | Bairro de entrega. |
| `complemento` | TEXT | Não | DEFAULT '' | Complemento (opcional). |
| `subtotal_centavos` | INTEGER | Não | CHECK | Soma dos itens. |
| `embalagem_centavos` | INTEGER | Não | CHECK, DEFAULT 0 | Valor da embalagem presente (0 se não pediu). |
| `frete_centavos` | INTEGER | Não | CHECK | Valor do frete. |
| `total_centavos` | INTEGER | Não | — | Total = subtotal + embalagem + frete (garantido por CHECK). |
| `criado_em` | TEXT | Não | DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')) | Data/hora de criação (UTC). |
| `atualizado_em` | TEXT | Não | DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')) | Data/hora da última mudança de status (UTC). |

Restrições de tabela: `CHECK (status IN ('AGUARDANDO_PAGAMENTO','RECEBIDO','EM_PREPARO'`; `CHECK (total_centavos = subtotal_centavos + embalagem_centavos + frete_centavos)`

Índices: `ix_pedido_status`; `ix_pedido_cliente`

## item_pedido

Itens do pedido (associativa Pedido × Cupcake).

| Coluna | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id` | INTEGER | Não | PK | Identificador do item. |
| `pedido_id` | INTEGER | Não | FK → pedido | Pedido ao qual o item pertence. |
| `cupcake_id` | INTEGER | Não | FK → cupcake | Cupcake vendido. |
| `quantidade` | INTEGER | Não | CHECK | Quantidade (1 a 50 por sabor). |
| `preco_unitario_centavos` | INTEGER | Não | CHECK | Preço do cupcake no momento da compra (não muda se o cardápio mudar). |
| `subtotal_centavos` | INTEGER | Não | — | quantidade × preço unitário (garantido por CHECK). |

Restrições de tabela: `UNIQUE (pedido_id, cupcake_id)`; `CHECK (subtotal_centavos = quantidade * preco_unitario_centavos)`

## pagamento

Pagamento do pedido (1:1). Nunca guarda o número completo do cartão (US07).

| Coluna | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id` | INTEGER | Não | PK | Identificador do pagamento. |
| `pedido_id` | INTEGER | Não | FK → pedido, UNIQUE | Pedido pago (único: um pagamento por pedido). |
| `metodo` | TEXT | Não | CHECK | PIX ou CARTAO. |
| `status` | TEXT | Não | DEFAULT 'PENDENTE' | PENDENTE, APROVADO, RECUSADO ou EXPIRADO. |
| `codigo_pix` | TEXT | Sim | — | Código PIX Copia e Cola (obrigatório se PIX; nulo se cartão). |
| `cartao_final` | TEXT | Sim | CHECK | Apenas os 4 últimos dígitos do cartão. |
| `motivo_recusa` | TEXT | Não | DEFAULT '' | Mensagem devolvida pelo gateway em caso de recusa. |
| `expira_em` | TEXT | Sim | — | Prazo de validade do PIX (15 minutos após a criação). |
| `atualizado_em` | TEXT | Não | DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')) | Data/hora da última mudança (UTC). |

Restrições de tabela: `CHECK (status IN ('PENDENTE', 'APROVADO', 'RECUSADO', 'EXPIRADO'))`; `CHECK ((metodo = 'PIX' AND codigo_pix IS NOT NULL) OR (metodo = 'CARTAO' AND codigo_pix IS NULL))`

## historico_status

Linha do tempo de cada pedido, exibida no acompanhamento (US09).

| Coluna | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id` | INTEGER | Não | PK | Identificador do registro. |
| `pedido_id` | INTEGER | Não | FK → pedido | Pedido. |
| `status` | TEXT | Não | — | Status alcançado. |
| `data_hora` | TEXT | Não | DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')) | Momento em que o status foi alcançado (UTC). |

Índices: `ix_historico_pedido`

## usuario_admin

Usuário do painel do lojista (US10).

| Coluna | Tipo | Nulo? | Restrições | Descrição |
|---|---|---|---|---|
| `id` | INTEGER | Não | PK | Identificador do usuário. |
| `usuario` | TEXT | Não | UNIQUE, CHECK | Login do lojista. |
| `senha_hash` | TEXT | Não | — | Hash da senha (PBKDF2/scrypt do Werkzeug). A senha em texto nunca é gravada. |
