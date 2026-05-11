from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse

from app.api.routes import (
    auth_routes,
    agenda_routes,
    diario_routes,
    psicologo_routes,
    notificacoes_routes,
    analytics_routes,
)
from app.core.security import verify_api_key

app = FastAPI(title="Cognitive-Front API")

# verify_api_key é aplicado em cada router individualmente.
# A rota "/" e "/docs" ficam livres propositalmente (são só informativas).
_protected = {"dependencies": [Depends(verify_api_key)]}

app.include_router(auth_routes.router, **_protected)
app.include_router(agenda_routes.router, **_protected)
app.include_router(diario_routes.router, **_protected)
app.include_router(psicologo_routes.router, **_protected)
app.include_router(notificacoes_routes.router, **_protected)
app.include_router(analytics_routes.router, **_protected)


@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Cognitive-Front API</title>
            <style>
                body { background-color: #F5F7F6; font-family: 'Segoe UI', sans-serif;
                       display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .container { background: white; padding: 40px; border-radius: 20px;
                             box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; max-width: 400px; }
                h1 { color: #4a4939; }
                .status { color: #92C7A3; font-weight: bold; font-size: 1.2em; margin-bottom: 30px; }
                .btn { background-color: #92C7A3; color: white; padding: 12px 24px;
                       text-decoration: none; border-radius: 25px; font-weight: bold; }
                .btn:hover { background-color: #76a885; }
                p { color: #666; margin-bottom: 30px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div style="font-size:50px">🧠</div>
                <h1>Cognitive-Front API</h1>
                <div class="status">● Sistema Online</div>
                <p>Backend que alimenta o aplicativo Cognitive-Front.</p>
                <a href="/docs" class="btn">Ver Documentação (Swagger)</a>
            </div>
        </body>
    </html>
    """

# Comando para rodar localmente: uvicorn main:app --reload