from __future__ import annotations

from dominio.baralho import Deck
from dominio.config import valores_especificos
from dominio.enums import StatusRodada
from dominio.jogada import Jogada
from dominio.jogador import Jogador
from dominio.turno import Turno, ordem_a_partir_de


class Rodada:
    
    
    def __init__(self, turno_palpites: Turno, n_cartas: int):
        self.status: str = StatusRodada.PALPITES  
        self.bolo = Deck("Bolo")
        self.bolo.construir_deck(valores = valores_especificos)
        self.bolo.embaralhar()
        self.carta_da_rodada = self.bolo.cartas.pop()
        self.jogada_atual: Jogada | None = None
        self.jogadas: list[Jogada] = []
        self.palpites: dict[Jogador, int] = {} # têm uma ordem especifica que rotaciona a cada rodada
        self.vitorias: dict[Jogador, int] = {}
        self.turno_palpites: Turno = turno_palpites
        for j in self.turno_palpites.ordem:
            self.vitorias[j] = 0
        self.numero_de_cartas: int = n_cartas
        

    def nova_jogada(self, primeiro_a_jogar: int = 0):
        self.jogada_atual = Jogada(Turno(ordem_a_partir_de(self.turno_palpites.ordem, primeiro_a_jogar)))

    def ver_palpites(self):
        soma = sum(self.palpites.values())
        palpites = {j.nome: p for j, p in self.palpites.items()}
        return {"palpites": palpites, "soma" : soma}

    def fazer_palpite(self, palpite: int, usuario: Jogador):
        
        
        if self.status is not StatusRodada.PALPITES:
            return {"mensagem": "Rodada não está na fase de palpites"} 
            
        if usuario is not self.turno_palpites.atual:
            return {"mensagem": "Não é a sua vez de palpitar"} 

        
        if usuario in self.palpites:
                return {"mensagem": "Você já fez seu palpite"} 
            
        if palpite > self.numero_de_cartas or palpite < 0:
            return {"mensagem": f"Valor de palpite inválido, precisa ser um numero inteiro entre 0 e {self.numero_de_cartas}"}
            
        if not self.turno_palpites.eh_o_ultimo : 
            self.palpites[usuario] = palpite
            self.turno_palpites.avancar()

            return {"mensagem": "Palpite feito com sucesso"}
        
        #para o ultimo jogador
        soma_dos_palpites = sum(self.palpites.values())
        if soma_dos_palpites + palpite == self.numero_de_cartas:
            return {"mensagem": f"A soma dos palpites não pode ser igual à quantidade de cartas da rodada, você não pode dar o palpite {palpite}"}
        
        self.palpites[usuario] = palpite
        self.status = StatusRodada.JOGADAS
        self.nova_jogada()
        return {"mensagem": "Palpite feito com sucesso, hora de jogar"}

