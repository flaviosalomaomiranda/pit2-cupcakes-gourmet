"""Carrinho de compras (US04, US06).

O carrinho guarda apenas {id_do_cupcake: quantidade}. Preços NUNCA vêm do navegador:
são sempre buscados no banco na hora de calcular, o que impede adulteração de valores.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import ValidacaoErro


@dataclass(frozen=True)
class LinhaCarrinho:
    cupcake_id: int
    nome: str
    preco_centavos: int
    quantidade: int
    cor_cobertura: str

    @property
    def subtotal_centavos(self) -> int:
        return self.preco_centavos * self.quantidade


class Carrinho:
    def __init__(self, dados: dict | None = None, qtd_max: int = 50):
        self.qtd_max = qtd_max
        self._itens: dict[str, int] = {}
        for chave, qtd in (dados or {}).items():
            try:
                cid, q = int(chave), int(qtd)
            except (TypeError, ValueError):
                continue  # ignora lixo vindo de cookie antigo/adulterado
            if cid > 0 and 0 < q <= qtd_max:
                self._itens[str(cid)] = q

    # ---- leitura -------------------------------------------------------
    def para_dict(self) -> dict[str, int]:
        return dict(self._itens)

    def quantidade_de(self, cupcake_id: int) -> int:
        return self._itens.get(str(cupcake_id), 0)

    @property
    def total_itens(self) -> int:
        return sum(self._itens.values())

    @property
    def vazio(self) -> bool:
        return not self._itens

    def ids(self) -> list[int]:
        return [int(k) for k in self._itens]

    # ---- escrita -------------------------------------------------------
    def _validar_qtd(self, quantidade) -> int:
        try:
            q = int(quantidade)
        except (TypeError, ValueError):
            raise ValidacaoErro("Quantidade inválida.", campo="quantidade")
        if q < 0:
            raise ValidacaoErro("Quantidade não pode ser negativa.", campo="quantidade")
        return q

    def adicionar(self, cupcake_id: int, quantidade=1) -> None:
        q = self._validar_qtd(quantidade)
        if q == 0:
            raise ValidacaoErro("Escolha pelo menos 1 unidade.", campo="quantidade")
        nova = self.quantidade_de(cupcake_id) + q
        if nova > self.qtd_max:
            raise ValidacaoErro(f"Limite de {self.qtd_max} unidades por sabor.", campo="quantidade")
        self._itens[str(cupcake_id)] = nova

    def definir(self, cupcake_id: int, quantidade) -> None:
        """Define a quantidade; zero remove o item (critério de aceite da US04)."""
        q = self._validar_qtd(quantidade)
        if q > self.qtd_max:
            raise ValidacaoErro(f"Limite de {self.qtd_max} unidades por sabor.", campo="quantidade")
        if q == 0:
            self.remover(cupcake_id)
        else:
            self._itens[str(cupcake_id)] = q

    def remover(self, cupcake_id: int) -> None:
        self._itens.pop(str(cupcake_id), None)

    def limpar(self) -> None:
        self._itens.clear()

    # ---- cálculo -------------------------------------------------------
    def montar_linhas(self, produtos: dict[int, dict]) -> list[LinhaCarrinho]:
        """Cruza o carrinho com os produtos ativos do banco. Itens inexistentes/inativos saem."""
        linhas = []
        for cid in self.ids():
            p = produtos.get(cid)
            if p is None:
                self.remover(cid)
                continue
            linhas.append(LinhaCarrinho(cid, p["nome"], p["preco_centavos"], self.quantidade_de(cid), p["cor_cobertura"]))
        return linhas


def calcular_totais(linhas: list[LinhaCarrinho], embalagem_presente: bool, valor_embalagem: int, frete: int | None):
    subtotal = sum(l.subtotal_centavos for l in linhas)
    embalagem = valor_embalagem if embalagem_presente else 0
    frete_val = frete or 0
    return {
        "subtotal": subtotal,
        "embalagem": embalagem,
        "frete": frete_val,
        "total": subtotal + embalagem + frete_val,
    }
