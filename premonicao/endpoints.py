
from __future__ import annotations
import uvicorn
from fastapi import FastAPI, Response, Cookie, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import time
import asyncio
import secrets
from contextlib import asynccontextmanager

from classes import Partida, Rodada, Jogada, Turno, Jogador
from premonicao.dominio.enums import StatusPartida, StatusRodada
from premonicao.dominio.config import *

async def vigiar_inativos():
    while True:
        await asyncio.sleep(INTERVALO_VIGIA)
        for codigo, jogo in list(jogos.items()):

            try:
                jogo.expulsar_inativos(LIMITE_TURNO, LIMITE_OFFLINE)
            except Exception as e:
                print("Erro ao expulsar inativos:", repr(e))

            if len(jogo.sessoes) == 0 or time.monotonic() - jogo.ultima_atividade > LIMITE_SALA_INATIVA:
                del jogos[codigo]

@asynccontextmanager
async def lifespan(app):
    tarefa = asyncio.create_task(vigiar_inativos())
    yield
    tarefa.cancel()


app = FastAPI(lifespan = lifespan)


jogos: dict[str, Partida]= {}

def novo_codigo() -> str:
    while True:
        c = "".join(secrets.choice(ALFABETO) for _ in range(TAMANHO_CODIGO_SALA))
        if c not in jogos:
            return c

def sala_atual(codigo: str)-> Partida:
    jogo = jogos.get(codigo.upper())
    if jogo is None:
        raise HTTPException(404, "Sala não encontrada")
    jogo.ultima_atividade = time.monotonic()
    return jogo

def usuario_atual(jogo: Partida = Depends(sala_atual),
                  sessao: str | None = Cookie(default = None)) -> Jogador:
    
    if sessao in jogo.removidos:
        raise HTTPException(status_code = 401, detail = jogo.removidos[sessao]) # ex: "Você foi expulso por ana"
    if sessao is None or sessao not in jogo.sessoes:
        raise HTTPException(status_code = 401, detail = "Sem sessão válida")
    j = jogo.sessoes[sessao]
    j.ultimo_momento_online = time.monotonic()
    return j 


@app.get("/")
def pagina():
    return FileResponse(Path(__file__).parent / "index.html")

@app.get("/config")
def configuracao():
    return {
        "max_tamanho_nome": MAX_TAMANHO_NOME,
        "tamanho_codigo_sala": TAMANHO_CODIGO_SALA,
        "n_rodadas_padrao": N_RODADAS_PADRAO,
        "min_jogadores": MIN_JOGADORES,
        "cartas_para_distribuir": NUMERO_DE_CARTAS_PADRAO - 1,
        "aviso_inatividade": AVISO_INATIVIDADE,
        "intervalo_ms": INTERVALO_MS,
    }


@app.get("/sala/{codigo}/eu")
def quem_sou_eu(usuario: Jogador = Depends(usuario_atual)):
    return {"nome": usuario.nome, "id": usuario.id, "admin": usuario.admin}

@app.post("/sala")
def criar_sala(nome: str, response: Response):
    if(len(jogos) >= MAX_SALAS):
        raise HTTPException(503, "servidor cheio, tente denovo mais tarde")
    if(len(nome) > MAX_TAMANHO_NOME or len(nome) < MIN_TAMANHO_NOME):
        raise HTTPException(422, f"O nome deve ter entre {MIN_TAMANHO_NOME} e {MAX_TAMANHO_NOME} caracteres")
    codigo = novo_codigo()
    jogos[codigo] = Partida()
    resultado = jogos[codigo].entrar(nome, response, None)
    return {"codigo": codigo, "resultado": resultado}


@app.post("/sala/{codigo}/entrar")
def entrar( nome: str, response: Response, jogo: Partida = Depends(sala_atual), sessao: str | None = Cookie(default = None)):
    if(len(nome) > MAX_TAMANHO_NOME or len(nome) < MIN_TAMANHO_NOME):
        raise HTTPException(422, f"O nome deve ter entre {MIN_TAMANHO_NOME} e {MAX_TAMANHO_NOME} caracteres")
    return jogo.entrar(nome, response, sessao)

@app.get("/sala/{codigo}/rodada/mao")
def ver_mao(jogo: Partida = Depends(sala_atual), usuario: Jogador = Depends(usuario_atual)):
    return usuario.mao


@app.get("/sala/{codigo}/rodada/palpites")
def ver_palpites(jogo: Partida = Depends(sala_atual)):
    return jogo.rodada_atual.ver_palpites() if jogo.rodada_atual else {}
    
@app.get("/sala/{codigo}/rodada/carta")
def ver_carta_da_rodada(jogo: Partida = Depends(sala_atual)):
    return jogo.rodada_atual.carta_da_rodada if jogo.rodada_atual else None

@app.get("/sala/{codigo}/jogadores/")
async def ver_lista_de_jogadores(jogo: Partida = Depends(sala_atual)):
    return [{"nome": j.nome, "id": j.id, "pontos": j.pontos} for j in jogo.sessoes.values()]

@app.get("/sala/{codigo}/estado")
def consultar_estado_da_partida(jogo: Partida = Depends(sala_atual)):
   return jogo.status_completo()

@app.post("/sala/{codigo}/iniciar")
async def iniciar_partida( n_rodadas: int = N_RODADAS_PADRAO, jogo: Partida = Depends(sala_atual), usuario: Jogador = Depends(usuario_atual)):
    return jogo.iniciar( n_rodadas, usuario )

@app.post("/sala/{codigo}/rodada/palpite")
def fazer_palpite(palpite: int, jogo: Partida = Depends(sala_atual), usuario: Jogador = Depends(usuario_atual)):
    #provavelmente deveria limpar isso
    return jogo.rodada_atual.fazer_palpite(palpite, usuario) if jogo.status == StatusPartida.RODADAS else {"mensagem": "Só é possível fazer palpites durante a fase de rodadas"}
    
@app.post("/sala/{codigo}/rodada/jogar")
def fazer_jogada(indice: int, jogo: Partida = Depends(sala_atual), usuario: Jogador = Depends(usuario_atual)):
    return jogo.fazer_jogada(indice, usuario) 

@app.post("/sala/{codigo}/rodada/presente")
def presente(presente: bool = False, jogo: Partida = Depends(sala_atual), usuario: Jogador = Depends(usuario_atual)):
    if presente and jogo.jogador_da_vez() is usuario:
        usuario.ultima_atividade_turno = time.monotonic()
    return presente
    
@app.get("/sala/{codigo}/mesa")
def ver_mesa(jogo: Partida = Depends(sala_atual)):
    return jogo.ver_mesa()
   
@app.post("/sala/{codigo}/encerrar")
def encerrar_partida(jogo: Partida = Depends(sala_atual), usuario: Jogador = Depends(usuario_atual)):
    return jogo.encerrar(usuario)

@app.post("/sala/{codigo}/nova")
def nova_partida(jogo: Partida = Depends(sala_atual), usuario: Jogador = Depends(usuario_atual)):
    return jogo.nova_partida(usuario)
    
@app.post("/sala/{codigo}/sair")
def sair_da_partida(response: Response, jogo: Partida = Depends(sala_atual), sessao: str | None = Cookie(default = None)):
    return jogo.sair_da_partida(response, sessao)

@app.post("/sala/{codigo}/expulsar")
def expulsar_jogador(id: int, jogo: Partida = Depends(sala_atual), usuario: Jogador = Depends(usuario_atual)):
    return jogo.expulsar_jogador(usuario, id)

@app.get("/sala/{codigo}/eventos")
def ver_eventos(desde: int | None = None, jogo: Partida = Depends(sala_atual)):
    return jogo.eventos_desde(desde)
    
    

if __name__ == "__main__":
    uvicorn.run("endpoints:app", host = HOST, port = PORTA_PADRAO, reload =RELOAD)