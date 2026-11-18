-- Migração 002 (v1.1) — avaliação de Luiz Cláudio: um CEP de Porto Velho foi recusado.
-- Causa: a faixa "Centro" começava em 76800-001 e deixava de fora 76800-000 (CEP geral da cidade).
UPDATE zona_entrega SET cep_inicio = 76800000 WHERE nome = 'Centro' AND cep_inicio = 76800001;
