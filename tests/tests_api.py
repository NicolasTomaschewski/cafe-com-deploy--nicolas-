def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_version(client):
    assert "version" in client.get("/version").json()

def test_criar_e_buscar_cafe(client):
    r = client.post("/cafes", json={"nome": "Bourbon Amarelo", "preco": 12.5})
    assert r.status_code == 201
    cafe_id = r.json()["id"]
    assert client.get(f"/cafes/{cafe_id}").json()["nome"] == "Bourbon Amarelo"

def test_listar_cafes(client):
    client.post("/cafes", json={"nome": "Catuaí", "preco": 10})
    assert len(client.get("/cafes").json()) == 1

def test_cafe_inexistente(client):
    assert client.get("/cafes/999").status_code == 404

def test_nome_duplicado(client):
    client.post("/cafes", json={"nome": "Catuaí", "preco": 10})
    assert client.post("/cafes", json={"nome": "Catuaí", "preco": 11}).status_code == 409

def test_preco_negativo_rejeitado(client):
    assert client.post("/cafes", json={"nome": "X", "preco": -1}).status_code == 422

def test_preco_com_desconto(client):
    cafe_id = client.post("/cafes", json={"nome": "Geisha", "preco": 20}).json()["id"]
    assert client.get(f"/cafes/{cafe_id}/preco?desconto=10").json()["preco_final"] == 18.0

def test_desconto_invalido_na_api(client):
    cafe_id = client.post("/cafes", json={"nome": "Geisha", "preco": 20}).json()["id"]
    assert client.get(f"/cafes/{cafe_id}/preco?desconto=80").status_code == 400