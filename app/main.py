import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Cafe

app = FastAPI(title="Café com Deploy")

DB = Annotated[Session, Depends(get_db)]


def preco_com_desconto(preco: float, pct: float) -> float:
    """Regra de negócio: desconto entre 0% e o máximo configurado."""
    maximo = float(os.getenv("DESCONTO_MAXIMO", "100"))
    if not 0 <= pct <= maximo:
        raise ValueError("desconto inválido")
    return round(preco * (1 - pct / 100), 2)


class CafeIn(BaseModel):
    nome: str = Field(min_length=1, max_length=80)
    preco: float = Field(gt=0)


def para_dict(c: Cafe) -> dict:
    return {"id": c.id, "nome": c.nome, "preco": c.preco}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": os.getenv("APP_VERSION", "dev")}


@app.get("/cafes")
def listar_cafes(db: DB):
    return [para_dict(c) for c in db.scalars(select(Cafe).order_by(Cafe.id))]


@app.post("/cafes", status_code=201)
def criar_cafe(dados: CafeIn, db: DB):
    cafe = Cafe(nome=dados.nome, preco=dados.preco)
    db.add(cafe)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "café já cadastrado") from None
    db.refresh(cafe)
    return para_dict(cafe)


@app.get("/cafes/{cafe_id}")
def buscar_cafe(cafe_id: int, db: DB):
    cafe = db.get(Cafe, cafe_id)
    if cafe is None:
        raise HTTPException(404, "café não encontrado")
    return para_dict(cafe)


@app.get("/cafes/{cafe_id}/preco")
def preco_cafe(cafe_id: int, db: DB, desconto: float = 0):
    cafe = buscar_cafe(cafe_id, db)
    try:
        final = preco_com_desconto(cafe["preco"], desconto)
    except ValueError:
        raise HTTPException(400, "desconto inválido") from None
    return {**cafe, "desconto": desconto, "preco_final": final}