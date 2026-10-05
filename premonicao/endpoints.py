
import uvicorn
from fastapi import FastAPI, Response, Cookie, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import time
import asyncio
from contextlib import asynccontextmanager

from classes import partida, rodada, jogada, turno, jogador, status_partida, status_rodada, LIMITE_TURNO, LIMITE_OFFLINE




async def vigiar_inativos():
    while True:
        await asyncio.sleep(5)
        try:
            jogo.expulsar_inativos(LIMITE_TURNO, LIMITE_OFFLINE)
        except Exception as e:
            print("Erro ao expulsar inativos:", repr(e))

@asynccontextmanager
async def lifespan(app):
    tarefa = asyncio.create_task(vigiar_inativos())
    yield
    tarefa.cancel()


app = FastAPI(lifespan = lifespan)

jogo = partida()


def usuario_atual(sessao: str | None = Cookie(default = None)) -> jogador:
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



@app.get("/eu")
def quem_sou_eu(usuario: jogador = Depends(usuario_atual)):
    return {"nome": usuario.nome, "id": usuario.id, "admin": usuario.admin}



@app.post("/partida/entrar")
def entrar(nome: str, response: Response, sessao: str | None = Cookie(default = None)):
    return jogo.entrar(nome, response, sessao)

@app.get("/partida/rodada/mao")
def ver_mao(usuario: jogador = Depends(usuario_atual)):
    return usuario.mao


@app.get("/partida/rodada/palpites")
def ver_palpites():
    return jogo.rodada_atual.ver_palpites() if jogo.rodada_atual else {}
    
@app.get("/partida/rodada/carta")
def ver_carta_da_rodada():
    return jogo.rodada_atual.carta_da_rodada if jogo.rodada_atual else None

@app.get("/partida/jogadores/")
async def ver_lista_de_jogadores():
    return [{"nome": j.nome, "id": j.id, "pontos": j.pontos} for j in jogo.sessoes.values()]

@app.get("/partida/estado")
def consultar_estado_da_partida():
   return jogo.status_completo()

@app.post("/partida/iniciar")
async def iniciar_partida( n_rodadas: int = 10, usuario: jogador = Depends(usuario_atual)):
    return jogo.iniciar( n_rodadas, usuario )

@app.post("/partida/rodada/palpite")
def fazer_palpite(palpite: int, usuario: jogador = Depends(usuario_atual)):
    #provavelmente deveria limpar isso
    return jogo.rodada_atual.fazer_palpite(palpite, usuario) if jogo.status == status_partida.RODADAS else {"mensagem": "Só é possível fazer palpites durante a fase de rodadas"}
    
@app.post("/partida/rodada/jogar")
def fazer_jogada(indice: int, usuario: jogador = Depends(usuario_atual)):
    return jogo.fazer_jogada(indice, usuario) 

@app.post("/partida/rodada/presente")
def presente(presente: bool = False, usuario: jogador = Depends(usuario_atual)):
    if presente and jogo.jogador_da_vez() is usuario:
        usuario.ultima_atividade_turno = time.monotonic()
    return presente
    
@app.get("/partida/mesa")
def ver_mesa():
    return jogo.ver_mesa()
   
@app.post("/partida/encerrar")
def encerrar_partida(usuario: jogador = Depends(usuario_atual)):
    return jogo.encerrar(usuario)

@app.post("/partida/nova")
def nova_partida(usuario: jogador = Depends(usuario_atual)):
    return jogo.nova_partida(usuario)
    
@app.post("/partida/sair")
def sair_da_partida(response: Response, sessao: str | None = Cookie(default = None)):
    return jogo.sair_da_partida(response, sessao)

@app.post("/partida/expulsar")
def expulsar_jogador(id: int, usuario: jogador = Depends(usuario_atual)):
    return jogo.expulsar_jogador(usuario, id)

@app.get("/partida/eventos")
def ver_eventos(desde: int | None = None):
    return jogo.eventos_desde(desde)
    
    

if __name__ == "__main__":
    uvicorn.run("endpoints:app", host= "0.0.0.0", port=8000, reload = True)