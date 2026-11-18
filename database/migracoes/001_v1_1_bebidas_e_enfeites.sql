-- Migração 001 (v1.1) — melhorias pedidas na avaliação por pares (Nataska Wanssa):
--   * imagens diferentes por sabor (coluna enfeite) e tipo de ilustração (cupcake/lata/garrafa)
--   * categoria Bebidas com água e Coca-Cola
-- Idempotente: pode rodar mais de uma vez sem duplicar dados.
-- As colunas ilustracao/enfeite são criadas pelo código (db.py) quando o banco é antigo.

INSERT OR IGNORE INTO categoria (id, nome, slug) VALUES (5, 'Bebidas', 'bebidas');
UPDATE cupcake SET enfeite = 'chocolate' WHERE nome IN ('Chocolate Belga', 'Chocolate Diet');
UPDATE cupcake SET enfeite = 'morango'   WHERE nome = 'Baunilha com Morango';
UPDATE cupcake SET enfeite = 'limao'     WHERE nome = 'Limão Siciliano';
UPDATE cupcake SET enfeite = 'ervas'     WHERE categoria_id = 3;
UPDATE cupcake SET enfeite = 'cupuacu'   WHERE nome = 'Cupuaçu';
UPDATE cupcake SET enfeite = 'acai'      WHERE nome = 'Açaí com Castanha';
UPDATE cupcake SET enfeite = 'coco'      WHERE nome IN ('Tapioca com Coco', 'Coco Zero');

INSERT OR IGNORE INTO cupcake (categoria_id, nome, descricao, ingredientes, alergenicos, preco_centavos, cor_cobertura, ilustracao, enfeite) VALUES
 (5, 'Água mineral sem gás 500 ml', 'Água mineral natural gelada.',               'Água mineral natural.',                            '', 400, '#7cc6f2', 'garrafa', 'nenhum'),
 (5, 'Água mineral com gás 500 ml', 'Água mineral gaseificada gelada.',           'Água mineral, gás carbônico.',                     '', 500, '#4fa3d9', 'garrafa', 'nenhum'),
 (5, 'Coca-Cola lata 350 ml',       'Refrigerante de cola tradicional, gelado.',  'Água gaseificada, açúcar, extrato de noz de cola, cafeína, corante caramelo, acidulante.', '', 700, '#d62828', 'lata', 'nenhum'),
 (5, 'Coca-Cola Zero lata 350 ml',  'Refrigerante de cola sem açúcar, gelado.',   'Água gaseificada, extrato de noz de cola, cafeína, corante caramelo, edulcorantes.',      '', 700, '#1f1f1f', 'lata', 'nenhum');
