-- Dados iniciais (carga de demonstração). Preços em centavos.

INSERT INTO categoria (id, nome, slug) VALUES
 (1, 'Tradicionais', 'tradicionais'),
 (2, 'Diet',         'diet'),
 (3, 'Salgados',     'salgados'),
 (4, 'Regionais',    'regionais');

INSERT INTO cupcake (categoria_id, nome, descricao, ingredientes, alergenicos, preco_centavos, cor_cobertura) VALUES
 (1, 'Red Velvet',         'Massa aveludada de cacau com cobertura de cream cheese.',               'Farinha de trigo, açúcar, ovos, manteiga, cacau, leitelho, cream cheese, corante alimentício.', 'Glúten, ovos, lactose', 1250, '#c0392b'),
 (1, 'Chocolate Belga',    'Massa de chocolate 54% com ganache e raspas de chocolate.',            'Farinha de trigo, chocolate belga 54%, açúcar, ovos, manteiga, creme de leite.',               'Glúten, ovos, lactose, soja', 1190, '#5d3a1a'),
 (1, 'Baunilha com Morango','Massa de baunilha recheada com geleia de morango da casa.',            'Farinha de trigo, açúcar, ovos, manteiga, fava de baunilha, morango, açúcar.',                 'Glúten, ovos, lactose', 1090, '#f4a6c0'),
 (1, 'Limão Siciliano',    'Massa cítrica com curd de limão e merengue maçaricado.',               'Farinha de trigo, açúcar, ovos, manteiga, limão siciliano, claras.',                         'Glúten, ovos, lactose', 1150, '#f7e07a'),
 (2, 'Chocolate Diet',     'Versão sem açúcar adicionado, adoçada com eritritol.',                 'Farinha de amêndoas, cacau 100%, ovos, eritritol, óleo de coco.',                             'Ovos, oleaginosas', 1390, '#7b4a2a'),
 (2, 'Coco Zero',          'Massa de coco sem açúcar adicionado com cobertura leve.',              'Farinha de coco, ovos, leite de coco, xilitol, coco ralado.',                                 'Ovos', 1350, '#f3efe6'),
 (3, 'Queijo e Ervas',     'Cupcake salgado de queijo coalho com orégano e manjericão.',           'Farinha de trigo, queijo coalho, ovos, leite, orégano, manjericão, fermento.',                'Glúten, ovos, lactose', 990, '#e9c46a'),
 (3, 'Frango com Catupiry','Massa salgada recheada com frango desfiado e requeijão cremoso.',      'Farinha de trigo, frango, requeijão, ovos, leite, cebola, salsinha.',                         'Glúten, ovos, lactose', 1090, '#f1d9a7'),
 (4, 'Cupuaçu',            'Massa amanteigada com creme de cupuaçu da Amazônia.',                  'Farinha de trigo, polpa de cupuaçu, açúcar, ovos, manteiga, creme de leite.',                 'Glúten, ovos, lactose', 1290, '#f6dfa4'),
 (4, 'Açaí com Castanha',  'Cobertura de açaí com farofa crocante de castanha-do-brasil.',         'Farinha de trigo, açaí, açúcar, ovos, manteiga, castanha-do-brasil.',                         'Glúten, ovos, lactose, oleaginosas', 1390, '#5b2a6e'),
 (4, 'Tapioca com Coco',   'Massa leve de tapioca e leite de coco, inspirada no beiju.',           'Goma de tapioca, leite de coco, açúcar, ovos, coco ralado.',                                  'Ovos', 1190, '#fdf6ec');

-- Faixas de CEP de Porto Velho/RO (demonstração).
INSERT INTO zona_entrega (nome, cep_inicio, cep_fim, valor_centavos, prazo_minutos) VALUES
 ('Centro',      76800001, 76803999,  500, 25),
 ('Zona Sul',    76804000, 76820999,  800, 35),
 ('Zona Leste',  76821000, 76829999, 1000, 45),
 ('Zona Norte',  76830000, 76834999, 1200, 50);
