from __future__ import annotations
from dominio.baralho import Deck, Carta
from dominio.config import *
from dominio.enums import StatusPartida, StatusRodada
from dominio.jogador import Jogador
from dominio.turno import Turno, ordem_a_partir_de
from dominio.jogada import Jogada
from dominio.rodada import Rodada
import secrets
import time
from fastapi import  Response, HTTPException
from contextlib import asynccontextmanager


def numero_de_rodadas_valido(jogo: Partida, n : int )-> bool:
    if(n <= 0):
        print("Insira um numero inteiro maior que zero")
        return False
    maximo = int( (NUMERO_DE_CARTAS_PADRAO - 1) / len(jogo.sessoes))
    if(n > maximo):
        print("Há jogadores demais para essa quantidade de rodadas, o máximo é ", maximo)
        return False
    
    return True


def cartas_na_mesa(j: Jogada) -> list[dict]:
    # o monte recebe as cartas na mesma ordem do turno da jogada
    return [{"jogador": jog.nome, "carta": c} for jog, c in zip(j.turno_jogada.ordem, j.monte.cartas)]

def placar_da_rodada(r: Rodada) -> list[dict]:
    return [{"nome": j.nome, "palpite": r.palpites.get(j), "vitorias": r.vitorias[j]} for j in r.turno_palpites.ordem]
    

class Partida:
    def __init__(self):
        self.status: str = StatusPartida.INICIO
        self.sessoes: dict[str, Jogador] = {}
        self.mesa: list[Jogador] = [] #disposicao dos jogadores na mesa
        self.numero_de_rodadas: int = 0
        self.rodada_atual: Rodada | None = None
        self.rodadas: list[Rodada] = []

        self.player_id = 1
        self.aviso: str | None = None
        self.eventos: list[dict] = [] # avisos para todos
        self.removidos: dict[str, str] = {} #tokens de quem foi removido e motivo

        self.ultima_atividade: float = time.monotonic() 
    
    def registrar_evento(self, tipo: str, texto: str, jogador_id: int | None = None):
        # tipo: "entrou", "saiu", "expulso", "desconectado", "admin"
        self.eventos.append({"id": len(self.eventos) + 1, "tipo": tipo, "texto": texto, "jogador_id": jogador_id})
        

    def eventos_desde(self, desde: int | None):
        ultimo = len(self.eventos) #indice do ultimo evento
        if desde is None: #primeira requisição, não há eventos
            return {"ultimo": ultimo, "eventos": []}
        return {"ultimo": ultimo, "eventos": self.eventos[desde:]}

    def jogador_da_vez(self) -> Jogador | None:
        r = self.rodada_atual
        if self.status is not StatusPartida.RODADAS or r is None:
            return None
        if r.status is StatusRodada.PALPITES:
            return r.turno_palpites.atual
        if r.status is StatusRodada.JOGADAS and r.jogada_atual:
            return r.jogada_atual.turno_jogada.atual
        return None


    def nova_rodada(self, n_cartas: int):

        self.rodada_atual = Rodada( Turno(ordem_a_partir_de(self.mesa, n_cartas - 1)), n_cartas) 
        self.aviso = None
        
        for j in self.mesa:
            j.mao.cartas = []
            j.mao.comprar(self.rodada_atual.bolo, n_cartas)
    
    def reiniciar(self):
        # mantém os jogadores na sala e zera todo o resto
        for j in self.sessoes.values():
            j.pontos = 0
            j.mao.cartas = []
        self.status = StatusPartida.INICIO
        self.mesa = []
        self.numero_de_rodadas = 0
        self.rodada_atual = None
        self.rodadas = []

        self.aviso = None

    def reiniciar_rodada(self, n_cartas: int):
        self.nova_rodada(n_cartas)

    def entrar(self, nome: str, response: Response, sessao: str | None ):
        
            if sessao is not None and sessao in self.sessoes:
                    print("Jogador ja está na partida")
                    return {"mensagem" : "Jogador ja está na partida"}
            
            if len(self.sessoes) >= MAX_JOGADORES:
                raise HTTPException(409, "Sala cheia")

            nome_final = f"Jogador {self.player_id}" if nome == "Jogador" else nome
            if nome_final in [j.nome for j in self.sessoes.values()]:
                return {"mensagem" : "Nome ja está em uso, escolha outro"}
            
            if len(nome_final) > MAX_TAMANHO_NOME:
                return {"mensagem" : "Nome excede o limite de 20 caracteres"}

            if self.status is StatusPartida.INICIO:
                token = secrets.token_urlsafe(BYTES_TOKEN_SESSAO) # gerando um token aleatorio
                novo_jogador = Jogador(self.player_id, nome)
                self.player_id += 1
                
                if not any(j.admin for j in self.sessoes.values()):
                    novo_jogador.admin = True
                
                self.sessoes[token] = novo_jogador # criando uma correspondencia [token : Jogador ]no dicionario sessoes 
                
                response.set_cookie(key = "sessao",
                                    value = token,
                                    httponly = True,
                                    samesite = COOKIE_SAMESITE,
                                    secure = EM_PRODUCAO,
                                    ) # configurando o cookie
                
                self.registrar_evento("entrou", f"{novo_jogador.nome} entrou na partida", novo_jogador.id)
                
                return {"mensagem": f"{novo_jogador.nome} entrou no jogo"}
            
            return {"mensagem": "Jogo já está em andamento, não é possível entrar"}

    def status_completo(self):
        if self.status is StatusPartida.INICIO:
            return {"status": self.status.name, "mensagem": f"Partida ainda não começou, {len(self.sessoes)} jogador(es) na sala"}
        
        if self.status is StatusPartida.FINAL:
            return {"status": self.status.name, "mensagem": "Partida encerrada", "aviso": self.aviso}
        
        rodada = self.rodada_atual
        numero_rodada = rodada.numero_de_cartas  # a rodada n é jogada com n cartas
        estado = {"status": self.status.name,
                      "rodada": numero_rodada,
                      "total_de_rodadas": self.numero_de_rodadas,
                      "fase": rodada.status.name,
                      "vez_de": None,
                      "aviso": self.aviso
                      }
        jogador_da_vez = self.jogador_da_vez()
        
        if rodada.status is StatusRodada.PALPITES:
            estado["vez_de"] = jogador_da_vez.nome
            estado["mensagem"] = f"Partida está na rodada {numero_rodada}, na fase de palpites, na vez de {jogador_da_vez.nome}"
        elif rodada.status is StatusRodada.JOGADAS:
            if rodada.jogada_atual is not None and rodada.jogada_atual.turno_jogada.atual is not None:
                estado["vez_de"] = jogador_da_vez.nome
                estado["mensagem"] = f"Partida está na rodada {numero_rodada}, na fase de jogadas, na vez de {jogador_da_vez.nome}"
            else:
                estado["mensagem"] = f"Partida está na rodada {numero_rodada}, na fase de jogadas"
        else:
            estado["mensagem"] = f"Rodada {numero_rodada} encerrada"

        if jogador_da_vez and jogador_da_vez.ultima_atividade_turno:
            estado["segundos_restantes"] = max(0, int(LIMITE_TURNO - (time.monotonic() - jogador_da_vez.ultima_atividade_turno)))

        self.ultima_atividade = time.monotonic()
        return estado

    def iniciar(self, n_rodadas, usuario):
        if usuario.admin is False:
            return {"mensagem" : "Apenas o administrador pode iniciar a partida"}
        if len(self.sessoes) < MIN_JOGADORES:
            return {"mensagem": f"É preciso pelo menos {MIN_JOGADORES} jogadores para inciar a partida"}
        if numero_de_rodadas_valido(self, n_rodadas) is False:
            return {"mensagem": "Numero de rodadas invalido"}
            
        if self.status is StatusPartida.INICIO:
            self.status = StatusPartida.RODADAS
            self.numero_de_rodadas = n_rodadas
            self.mesa = list(self.sessoes.values())
            self.nova_rodada(1)
                
            
            return {"mensagem": f"Partida iniciada com {n_rodadas} rodadas"}
        return {"mensagem": "Partida já começou"} 

    
    def fazer_jogada(self, indice: int, usuario: Jogador):
    
        if self.status is not StatusPartida.RODADAS:
            return {"mensagem": "Partida não está na fase de rodadas"} 
        
        rodada = self.rodada_atual
        
        if rodada.status is not StatusRodada.JOGADAS:
            return {"mensagem": "Rodada não está na fase de jogadas"} 
        
        jogada = rodada.jogada_atual
        
        if usuario is not jogada.turno_jogada.atual:
            return {"mensagem": "Não é a sua vez de jogar"} 
    
        if  indice >= len(usuario.mao.cartas) or indice < 0:
            return {"mensagem": f"Índice de carta inválido, precisa ser um numero inteiro entre 0 e {len(usuario.mao.cartas) - 1}"}
        
        usuario.mao.jogar(jogada.monte, indice)
        carta = jogada.monte.cartas[-1] # so pra exibição mesmo
    
        if not jogada.turno_jogada.eh_o_ultimo:
            jogada.turno_jogada.avancar()
            return {"mensagem": f"Carta jogada: {carta.valor_char} de {carta.naipe}"}
        
        indice_maior_carta = jogada.monte.maior_carta(rodada.carta_da_rodada.naipe)
        maior_carta = jogada.monte.cartas[indice_maior_carta]
        jogada.vencedor = jogada.turno_jogada.ordem[indice_maior_carta]
        rodada.vitorias[jogada.vencedor] += 1
            
        mensagem = f"{jogada.vencedor.nome} ganhou a jogada com a carta {maior_carta.valor_char} de {maior_carta.naipe}"
        
        rodada.jogadas.append(jogada)
            
            
        if len(rodada.jogadas) != rodada.numero_de_cartas:
            rodada.nova_jogada(rodada.turno_palpites.ordem.index(jogada.vencedor))
    
                
            return {"mensagem": mensagem}
        
        
        self.rodadas.append(rodada)
        mensagem = mensagem + "\nFim da rodada\n"
        resultados = { "palpites": {j.nome : p for j, p in rodada.palpites.items()}, "Jogadas ganhas" : {j.nome : p for j, p in rodada.vitorias.items()}}
            
        #codigo pra verificar quem pontuou e distribuir os pontos
        for j in rodada.palpites:
            if rodada.palpites[j] == rodada.vitorias[j]:
                j.pontos += rodada.palpites[j] + BONUS_ACERTO_PALPITE
    
        if len(self.rodadas) != self.numero_de_rodadas:
    
            self.nova_rodada(rodada.numero_de_cartas + 1)
            
            return {"mensagem": mensagem, "resultados": resultados }
    
        self.status = StatusPartida.FINAL
        mensagem = mensagem + "\nFim da partida\n"
        resultados["pontuações"] = {j.nome: j.pontos for j in self.mesa} 
        return {"mensagem": mensagem, "resultados": resultados}

    
    def ver_mesa(self):
        r = self.rodada_atual
        if r is None:
            return {"trunfo": None, "jogada_atual": [], "ultima_jogada": None, "placar_rodada": [], "ultima_rodada": None}
        
        # logo que uma rodada nova começa, a última jogada ainda está na rodada anterior
        jogadas_feitas = r.jogadas or (self.rodadas[-1].jogadas if self.rodadas else [])
        ultima_jogada = jogadas_feitas[-1] if jogadas_feitas else None
        ultima_rodada = self.rodadas[-1] if self.rodadas else None
        
        return {
            "trunfo": r.carta_da_rodada,
            "jogada_atual": cartas_na_mesa(r.jogada_atual) if r.jogada_atual else [],
            "ultima_jogada": {"cartas": cartas_na_mesa(ultima_jogada), "vencedor": ultima_jogada.vencedor.nome} if ultima_jogada else None,
            "placar_rodada": placar_da_rodada(r),
            "ultima_rodada": {"numero": ultima_rodada.numero_de_cartas, "placar": placar_da_rodada(ultima_rodada)} if ultima_rodada else None,
            }
    
    def encerrar(self, usuario: Jogador):
        if not usuario.admin:
            return {"mensagem": "Apenas o administrador pode encerrar a partida"}
        if self.status is StatusPartida.FINAL:
            return {"mensagem": "A partida já está encerrada"}
        self.status = StatusPartida.FINAL
        return {"mensagem": "Partida encerrada pelo administrador"}
    
    
    def nova_partida(self, usuario):
        if not usuario.admin:
            return {"mensagem": "Apenas o administrador pode começar uma nova partida"}
        if self.status is not StatusPartida.FINAL:
            return {"mensagem": "Encerre a partida atual antes de começar outra"}
        self.reiniciar()
        return {"mensagem": "Nova partida: aguardando jogadores"}

    

    def remover_jogador(self, token: str, tipo: str, motivo: str, evento: str):
        #motivo: oq o jogador removido ve
        #evento: oq os outros jogadores veem

        if token is None or token not in self.sessoes:
                raise HTTPException(status_code = 401, detail = "Sem sessão válida")
        usuario = self.sessoes[token]
        
        del self.sessoes[token]
        self.removidos[token] = motivo
        self.registrar_evento(tipo, texto = evento, jogador_id = usuario.id)
    
        #quando o ultimo jogador sai a partida volta ao estado inicial 
        if not self.sessoes:
            self.reiniciar()
        
            return {"mensagem": motivo}
            
        #  quando o admin sai do self, o proximo menor id vira o novo admin
        if usuario.admin:
            novo_admin = min(self.sessoes.values(), key=lambda j: j.id)
            novo_admin.admin = True
            self.registrar_evento(tipo = "admin", texto = f"{novo_admin.nome} agora é o administrador", jogador_id = novo_admin.id)
    
        if usuario in self.mesa:
            self.mesa.remove(usuario)
            
            if self.status == StatusPartida.RODADAS:
        
                if (len(self.mesa) < MIN_JOGADORES):
                    
                    self.status = StatusPartida.FINAL
                    self.aviso = f"{evento} e não há jogadores o suficiente para continuar. Fim da partida"
                
                else:
                    
                    self.reiniciar_rodada(self.rodada_atual.numero_de_cartas)
                    self.aviso = f"{evento}. A rodada {self.rodada_atual.numero_de_cartas} vai ser reiniciada"
    
            
        return {"mensagem": motivo} 
    
    
    def sair_da_partida(self, response: Response , sessao: str):
        nome = self.sessoes[sessao].nome if sessao in self.sessoes else ""
        resultado = self.remover_jogador(sessao, tipo = "saiu", motivo = "Você saiu da partida", evento = f"{nome} saiu da partida")
        self.removidos.pop(sessao, None)
        response.delete_cookie("sessao")
        return resultado

      
    def expulsar_jogador(self, administrador: Jogador, id_alvo: int):
        
        if administrador.admin is not True:
            return {"mensagem": "Jogador não tem autorização para expulsar outros jogadores"}
        if administrador.id == id_alvo:
            return {"mensagem": "Você não pode expulsar a si mesmo, use Sair da partida"}
        token = next((t for t, j in self.sessoes.items() if j.id == id_alvo), None)
        if token is None:
            return {"mensagem": "Jogador não encontrado"}
        alvo = self.sessoes[token]
                    
        self.remover_jogador(token, tipo = "expulso", motivo = f"Você foi expulso por {administrador.nome}", evento = f"{alvo.nome} foi expulso por {administrador.nome}")
        return {"mensagem": f"{alvo.nome} foi expulso"}

    def expulsar_inativos(self, LIMITE_TURNO, LIMITE_OFFLINE ):
        agora = time.monotonic()
        a_remover: list[tuple] = []
        for token, j in self.sessoes.items():
            
            if agora - j.ultimo_momento_online > LIMITE_OFFLINE:
                a_remover.append((token, f"Você foi expulso por tempo demais fora da página", f"{j.nome} foi desconectado por ficar tempo demais fora da página"))
            
            elif j is self.jogador_da_vez() and j.ultima_atividade_turno and agora - j.ultima_atividade_turno > LIMITE_TURNO:
                a_remover.append((token, f"Você foi expulso por inatividade", f"{j.nome} foi desconectado por inatividade durante o turno"))
            
        for token, motivo, evento in a_remover:
            self.remover_jogador(token, "desconectado", motivo, evento)