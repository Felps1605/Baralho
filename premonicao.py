import secrets
import uvicorn
from fastapi import FastAPI, Response, Cookie, Depends, HTTPException

from collections.abc import Iterator
from enum import Enum

from baralho import deck, carta,  valores_padrao

app = FastAPI()

player_id = 1


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
    def __init__(self, nome: str = "Jogador"):

        global player_id

        self.nome: str = (f"Jogador {player_id}"if nome == "Jogador" else nome)
        self.id : int = player_id
        player_id += 1
        
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

    def nova_rodada(self, n_cartas: int):

        self.rodada_atual = rodada( turno(ordem_a_partir_de(jogo.mesa, n_cartas - 1)), n_cartas) 

        for j in jogo.mesa:
            j.mao.comprar(jogo.rodada_atual.bolo, n_cartas)




jogo = partida()

def usuario_atual(sessao: str | None = Cookie(default = None)) -> jogador:
    if sessao is None or sessao not in jogo.sessoes:
        raise HTTPException(status_code = 401, detail = "Sem sessão válida")
    return jogo.sessoes[sessao] #devolve o jogador que possui a chave sessao

@app.post("/entrar")
def entrar(nome: str, response: Response, sessao: str | None = Cookie(default = None)):
    
    if sessao is not None and sessao in jogo.sessoes:
            print("Jogador ja está no jogo")
            return {"mensagem" : "Jogador ja está no jogo"}

    nome_final = f"Jogador {player_id}" if nome == "Jogador" else nome
    if nome_final in [j.nome for j in jogo.sessoes.values()]:
        return {"mensagem" : "Nome ja está em uso, escolha outro"}
    
    if jogo.status is status_partida.INICIO:
        token = secrets.token_urlsafe(16) # gerando um token aleatorio
        novo_jogador = jogador(nome)
        if novo_jogador.id == 1:
            novo_jogador.admin = True
        jogo.sessoes[token] = novo_jogador # criando uma correspondencia [token : jogador ]no dicionario sessoes 
        response.set_cookie(key = "sessao", value = token, httponly = True) # configurando o cookie
        print(f"{nome} entrou no jogo")
        return {"mensagem": f"{nome} entrou no jogo"}
    return {"mensagem": "Jogo já está em andamento, não é possível entrar"}


@app.get("/partida/rodada/mao")
def ver_mao(usuario: jogador = Depends(usuario_atual)):
    return usuario.mao


@app.get("/partida/rodada/palpites")
def ver_palpites(usuario: jogador = Depends(usuario_atual)):
    if jogo.rodada_atual is not None:
        soma = sum(jogo.rodada_atual.palpites.values())
        palpites = {j.nome: p for j, p in jogo.rodada_atual.palpites.items()}
        return {"palpites": palpites, "soma" : soma}
    return {"mensagem": "Não há rodadas e palpites ainda"}

@app.get("/partida/rodada/carta")
def ver_carta_da_rodada(usuario: jogador = Depends(usuario_atual)):
    if jogo.rodada_atual is not None:
        return jogo.rodada_atual.carta_da_rodada
    return {"mensagem": "Não há uma carta da rodada no momento"}

@app.get("/partida/jogadores/")
async def ver_lista_de_jogadores():
    return [{"nome": j.nome, "id": j.id, "pontos": j.pontos} for j in jogo.sessoes.values()]

@app.get("/partida/estado")
def consultar_estado_da_partida():
    if jogo.status is status_partida.INICIO:
        return {"status": jogo.status.name,
                "mensagem": f"Partida ainda não começou, {len(jogo.sessoes)} jogador(es) na sala"}

    if jogo.status is status_partida.FINAL:
        return {"status": jogo.status.name, "mensagem": "Partida encerrada"}

    rodada = jogo.rodada_atual
    numero_rodada = rodada.numero_de_cartas  # a rodada n é jogada com n cartas
    estado = {"status": jogo.status.name,
              "rodada": numero_rodada,
              "total_de_rodadas": jogo.numero_de_rodadas,
              "fase": rodada.status.name,
              "vez_de": None}

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

def numero_de_rodadas_valido(n : int )-> bool:
    if(n <= 0):
        print("Insira um numero inteiro maior que zero")
        return False
    maximo = int( 51 / len(jogo.sessoes))
    if(n > maximo):
        print("Há jogadores demais para essa quantidade de rodadas, o máximo é ", maximo)
        return False
    
    return True


@app.post("/partida/iniciar")
async def iniciar_partida( n_rodadas: int = 10, usuario: jogador = Depends(usuario_atual)):
    if usuario.admin is False:
        return {"mensagem" : "Apenas o administrador pode iniciar a partida"}
    if len(jogo.sessoes) < 2:
        return {"mensagem": "É preciso pelo menos 2 jogadores para inciar a partida"}
    if numero_de_rodadas_valido(n_rodadas) is False:
        return {"mensagem": "Numero de rodadas invalido"}
    
    if jogo.status is status_partida.INICIO:
        jogo.status = status_partida.RODADAS
        jogo.numero_de_rodadas = n_rodadas
        jogo.mesa = list(jogo.sessoes.values())
        jogo.nova_rodada(1)
        
        return {"mensagem": f"Partida iniciada com {n_rodadas} rodadas"}
    return {"mensagem": "Partida já começou"} 



@app.post("/partida/rodada/palpite")
def fazer_palpite(palpite: int, usuario: jogador = Depends(usuario_atual)):
    
    if jogo.status is not status_partida.RODADAS:
        return {"mensagem": "Partida não está na fase de rodadas"} 
    
    rodada = jogo.rodada_atual
    
    if rodada.status is not status_rodada.PALPITES:
        return {"mensagem": "Rodada não está na fase de palpites"} 
    
    if usuario is not rodada.turno_palpites.atual:
        return {"mensagem": "Não é a sua vez de palpitar"} 

    if usuario in rodada.palpites:
            return {"mensagem": "Você já fez seu palpite"} 
    
    if palpite > rodada.numero_de_cartas or palpite < 0:
        return {"mensagem": f"Valor de palpite inválido, precisa ser um numero inteiro entre 0 e {rodada.numero_de_cartas}"}
    

    if not rodada.turno_palpites.eh_o_ultimo : 
        rodada.palpites[usuario] = palpite
        rodada.turno_palpites.avancar()
        return {"mensagem": "Palpite feito com sucesso"}

    #para o ultimo jogador
    soma_dos_palpites = sum(rodada.palpites.values())
    if soma_dos_palpites + palpite == rodada.numero_de_cartas:
        return {"mensagem": f"A soma dos palpites não pode ser igual à quantidade de cartas da rodada, você não pode dar o palpite {palpite}"}

    rodada.palpites[usuario] = palpite
    rodada.status = status_rodada.JOGADAS
    rodada.nova_jogada()
    return {"mensagem": "Palpite feito com sucesso, hora de jogar"}

@app.post("/partida/rodada/jogar")
def fazer_jogada(indice: int, usuario: jogador = Depends(usuario_atual)):
    
    if jogo.status is not status_partida.RODADAS:
        return {"mensagem": "Partida não está na fase de rodadas"} 
    
    rodada = jogo.rodada_atual
    
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
    
    
    jogo.rodadas.append(rodada)
    mensagem = mensagem + "\nFim da rodada\n"
    resultados = { "palpites": {j.nome : p for j, p in rodada.palpites.items()}, "Jogadas ganhas" : {j.nome : p for j, p in rodada.vitorias.items()}}
        
    #codigo pra verificar quem pontuou e distribuir os pontos
    for j in rodada.palpites:
        if rodada.palpites[j] == rodada.vitorias[j]:
            j.pontos += rodada.palpites[j] + 1

    if len(jogo.rodadas) != jogo.numero_de_rodadas:

        jogo.nova_rodada(rodada.numero_de_cartas + 1)
        
        return {"mensagem": mensagem, "resultados": resultados }

    jogo.status = status_partida.FINAL
    mensagem = mensagem + "\nFim da partida\n"
    resultados["pontuações"] = {j.nome: j.pontos for j in jogo.mesa} 
    return {"mensagem": mensagem, "resultados": resultados}


if __name__ == "__main__":
    uvicorn.run("premonicao2:app", host="127.0.0.5", port=8000, reload = True)
