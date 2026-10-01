from baralho import deck, carta,  valores_padrao
from enum import Enum
import secrets

from fastapi import  Response, HTTPException


class turno:
    #disposição dos jogadores na mesa
    def __init__(self, ordem: list[jogador]):
        self.ordem = ordem
        self.posicao = 0

    @property
    def atual(self) -> jogador:
        return self.ordem[self.posicao]

    @property
    def eh_o_ultimo(self) -> bool:
        return self.posicao == len(self.ordem) - 1

    def avancar(self):
        if self.posicao != len(self.ordem) - 1:
            self.posicao += 1

def ordem_a_partir_de(mesa: list[jogador], inicio: int)-> list[jogador]:
    inicio %= len(mesa)
    return mesa[inicio:] + mesa[:inicio]
    
class jogador:
    def __init__(self, id: int, nome: str = "Jogador"):


        self.nome: str = (f"Jogador {id}"if nome == "Jogador" else nome)
        self.id : int = id

        
        self.admin: bool = False
        self.pontos: int = 0
        
        self.mao = deck("Mão")
        self.mao.cartas = [] 
        
        
class jogada:
    turno_jogada: turno # setado na função nova_jogada da rodada
    def __init__(self, turno_jogada: turno):
        self.turno_jogada: turno = turno_jogada
        self.monte: deck = deck() 
        self.vencedor: jogador | None = None

class status_rodada(Enum):
    PALPITES = 1
    JOGADAS = 2
    FINAL = 3


class rodada:
    
    
    def __init__(self, turno_palpites: turno, n_cartas: int):
        self.status: str = status_rodada.PALPITES  
        self.bolo = deck("Bolo")
        self.bolo.construir_deck(valores = valores_especificos)
        self.bolo.embaralhar()
        self.carta_da_rodada = self.bolo.cartas.pop()
        self.jogada_atual: jogada | None = None
        self.jogadas: list[jogada] = []
        self.palpites: dict[jogador, int] = {} # têm uma ordem especifica qu rotaciona a cada rodada
        self.vitorias: dict[jogador, int] = {}
        self.turno_palpites: turno = turno_palpites
        for j in self.turno_palpites.ordem:
            self.vitorias[j] = 0
        self.numero_de_cartas: int = n_cartas
        

    def nova_jogada(self, primeiro_a_jogar: int = 0):
        self.jogada_atual = jogada(turno(ordem_a_partir_de(self.turno_palpites.ordem, primeiro_a_jogar)))

    def ver_palpites(self):
        soma = sum(self.palpites.values())
        palpites = {j.nome: p for j, p in self.palpites.items()}
        return {"palpites": palpites, "soma" : soma}

    def fazer_palpite(self, palpite: int, usuario: jogador):
        
        
        if self.status is not status_rodada.PALPITES:
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
        self.status = status_rodada.JOGADAS
        self.nova_jogada()
        return {"mensagem": "Palpite feito com sucesso, hora de jogar"}


def numero_de_rodadas_valido(jogo, n : int )-> bool:
    if(n <= 0):
        print("Insira um numero inteiro maior que zero")
        return False
    maximo = int( 51 / len(jogo.sessoes))
    if(n > maximo):
        print("Há jogadores demais para essa quantidade de rodadas, o máximo é ", maximo)
        return False
    
    return True


def cartas_na_mesa(j: jogada) -> list[dict]:
    # o monte recebe as cartas na mesma ordem do turno da jogada
    return [{"jogador": jog.nome, "carta": c} for jog, c in zip(j.turno_jogada.ordem, j.monte.cartas)]

def placar_da_rodada(r: rodada) -> list[dict]:
    return [{"nome": j.nome, "palpite": r.palpites.get(j), "vitorias": r.vitorias[j]} for j in r.turno_palpites.ordem]
    

class status_partida(Enum):
    INICIO = 1
    RODADAS = 2
    FINAL = 3

valores_especificos = valores_padrao.copy()
valores_especificos["A"] = 14

class partida:
    def __init__(self):
        self.status: str = status_partida.INICIO
        self.sessoes: dict[str, jogador] = {}
        self.mesa: list[jogador] = [] #disposicao dos jogadores na mesa
        self.numero_de_rodadas: int = 0
        self.rodada_atual: rodada | None = None
        self.rodadas: list[rodada] = []

        self.player_id = 1
        self.aviso: str | None = None

    def nova_rodada(self, n_cartas: int):

        self.rodada_atual = rodada( turno(ordem_a_partir_de(self.mesa, n_cartas - 1)), n_cartas) 
        self.aviso = None
        
        for j in self.mesa:
            j.mao.cartas = []
            j.mao.comprar(self.rodada_atual.bolo, n_cartas)
    
    def reiniciar(self):
        # mantém os jogadores na sala e zera todo o resto
        for j in self.sessoes.values():
            j.pontos = 0
            j.mao.cartas = []
        self.status = status_partida.INICIO
        self.mesa = []
        self.numero_de_rodadas = 0
        self.rodada_atual = None
        self.rodadas = []

        self.aviso = None

    def reiniciar_rodada(self, n_cartas: int):
        self.nova_rodada(n_cartas)

    def entrar(self, nome: str, response: Response, sessao: str | None ):
        
            if sessao is not None and sessao in self.sessoes:
                    print("Jogador ja está no self")
                    return {"mensagem" : "Jogador ja está no self"}
        
            nome_final = f"Jogador {self.player_id}" if nome == "Jogador" else nome
            if nome_final in [j.nome for j in self.sessoes.values()]:
                return {"mensagem" : "Nome ja está em uso, escolha outro"}
            
            if self.status is status_partida.INICIO:
                token = secrets.token_urlsafe(16) # gerando um token aleatorio
                novo_jogador = jogador(self.player_id, nome)
                self.player_id += 1
                
                if not any(j.admin for j in self.sessoes.values()):
                    novo_jogador.admin = True
                self.sessoes[token] = novo_jogador # criando uma correspondencia [token : jogador ]no dicionario sessoes 
                response.set_cookie(key = "sessao", value = token, httponly = True) # configurando o cookie
                print(f"{nome} entrou no self")
                return {"mensagem": f"{nome} entrou no jogo"}
            return {"mensagem": "Jogo já está em andamento, não é possível entrar"}

    def status_completo(self):
        if self.status is status_partida.INICIO:
            return {"status": self.status.name, "mensagem": f"Partida ainda não começou, {len(self.sessoes)} jogador(es) na sala"}
        
        if self.status is status_partida.FINAL:
            return {"status": self.status.name, "mensagem": "Partida encerrada"}
        
        rodada = self.rodada_atual
        numero_rodada = rodada.numero_de_cartas  # a rodada n é jogada com n cartas
        estado = {"status": self.status.name,
                      "rodada": numero_rodada,
                      "total_de_rodadas": self.numero_de_rodadas,
                      "fase": rodada.status.name,
                      "vez_de": None,
                      "aviso": self.aviso
                      }
        
        if rodada.status is status_rodada.PALPITES:
            estado["vez_de"] = rodada.turno_palpites.atual.nome
            estado["mensagem"] = f"Partida está na rodada {numero_rodada}, na fase de palpites, na vez de {rodada.turno_palpites.atual.nome}"
        elif rodada.status is status_rodada.JOGADAS:
            if rodada.jogada_atual is not None and rodada.jogada_atual.turno_jogada.atual is not None:
                estado["vez_de"] = rodada.jogada_atual.turno_jogada.atual.nome
                estado["mensagem"] = f"Partida está na rodada {numero_rodada}, na fase de jogadas, na vez de {rodada.jogada_atual.turno_jogada.atual.nome}"
            else:
                estado["mensagem"] = f"Partida está na rodada {numero_rodada}, na fase de jogadas"
        else:
            estado["mensagem"] = f"Rodada {numero_rodada} encerrada"
        
        return estado

    def iniciar(self, n_rodadas, usuario):
        if usuario.admin is False:
            return {"mensagem" : "Apenas o administrador pode iniciar a partida"}
        if len(self.sessoes) < 2:
            return {"mensagem": "É preciso pelo menos 2 jogadores para inciar a partida"}
        if numero_de_rodadas_valido(self, n_rodadas) is False:
            return {"mensagem": "Numero de rodadas invalido"}
            
        if self.status is status_partida.INICIO:
            self.status = status_partida.RODADAS
            self.numero_de_rodadas = n_rodadas
            self.mesa = list(self.sessoes.values())
            self.nova_rodada(1)
                
            
            return {"mensagem": f"Partida iniciada com {n_rodadas} rodadas"}
        return {"mensagem": "Partida já começou"} 

    def fazer_jogada(self, indice: int, usuario: jogador):
    
        if self.status is not status_partida.RODADAS:
            return {"mensagem": "Partida não está na fase de rodadas"} 
        
        rodada = self.rodada_atual
        
        if rodada.status is not status_rodada.JOGADAS:
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
                j.pontos += rodada.palpites[j] + 1
    
        if len(self.rodadas) != self.numero_de_rodadas:
    
            self.nova_rodada(rodada.numero_de_cartas + 1)
            
            return {"mensagem": mensagem, "resultados": resultados }
    
        self.status = status_partida.FINAL
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
    def encerrar(self, usuario: jogador):
        if not usuario.admin:
            return {"mensagem": "Apenas o administrador pode encerrar a partida"}
        if self.status is status_partida.FINAL:
            return {"mensagem": "A partida já está encerrada"}
        self.status = status_partida.FINAL
        return {"mensagem": "Partida encerrada pelo administrador"}
    
    def nova_partida(self, usuario):
        if not usuario.admin:
            return {"mensagem": "Apenas o administrador pode começar uma nova partida"}
        if self.status is not status_partida.FINAL:
            return {"mensagem": "Encerre a partida atual antes de começar outra"}
        self.reiniciar()
        return {"mensagem": "Nova partida: aguardando jogadores"}

    def sair_da_partida(self, response: Response , sessao: str):
        if sessao is None or sessao not in self.sessoes:
            raise HTTPException(status_code = 401, detail = "Sem sessão válida")
        usuario = self.sessoes[sessao]
        del self.sessoes[sessao]
        response.delete_cookie("sessao")
    
        #quando o ultimo jogador sai a partida volta ao estado inicial 
        if not self.sessoes:
            self.reiniciar()
        
            return {"mensagem": "Você saiu da partida"}
            
        #  quando o admin sai do self, o proximo menor id vira o novo admin
        if usuario.admin:
            novo_admin = min(self.sessoes.values(), key=lambda j: j.id)
            novo_admin.admin = True
    
        if usuario in self.mesa:
            self.mesa.remove(usuario)
            
            if self.status == status_partida.RODADAS:
        
                if (len(self.mesa) < 2):
                    
                    self.status = status_partida.FINAL
                    self.aviso = f"{usuario.nome} saiu da partida e não há jogadores o suficiente para continuar. Fim da partida"
                
                else:
                    
                    self.reiniciar_rodada(self.rodada_atual.numero_de_cartas)
                    self.aviso = f"{usuario.nome} saiu da partida. A rodada {self.rodada_atual.numero_de_cartas} vai ser reiniciada"
    
            
        return {"mensagem": "Você saiu da partida"}
        
