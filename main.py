import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.db.database import engine, Base
from app.routers import pagos, tesoreria

Base.metadata.create_all(bind=engine)

app = FastAPI(docs_url=None, redoc_url=None)

app.include_router(pagos.router)
app.include_router(tesoreria.router)


@app.get("/openapi.json", include_in_schema=False)
def get_openapi():
    return FileResponse(os.path.join(os.path.dirname(__file__), "openapi.json"))
