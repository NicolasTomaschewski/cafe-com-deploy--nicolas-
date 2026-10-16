#!/usr/bin/env python3
"""Calcula as métricas DORA da Café com Deploy a partir da API do GitHub.

Fontes:
  - workflow cd.yml (push na main): cada job "production" concluído com sucesso = 1 deploy
  - workflow rollback.yml: cada execução bem-sucedida = 1 recuperação

Uso:
  python scripts/dora.py
  GITHUB_TOKEN=<token> python scripts/dora.py   # opcional, evita limite da API

Sem token, a API pública permite 60 requisições por hora, suficiente para este projeto.
"""

import json
import os
import urllib.request
from datetime import datetime
from statistics import mean

REPO = os.getenv("GITHUB_REPOSITORY", "NicolasTomaschewski/cafe-com-deploy-nicolas")
API = f"https://api.github.com/repos/{REPO}"
TOKEN = os.getenv("GITHUB_TOKEN")


def get(path: str):
    req = urllib.request.Request(
        API + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "dora-cafe-com-deploy"},
    )
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as resposta:
        return json.load(resposta)


def ts(valor: str) -> datetime:
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def fmt(segundos: float) -> str:
    minutos, seg = divmod(int(segundos), 60)
    horas, minutos = divmod(minutos, 60)
    if horas:
        return f"{horas}h{minutos:02d}min"
    return f"{minutos}min{seg:02d}s"


def inicio_da_mudanca(sha: str, fallback: str) -> datetime:
    """Data do primeiro commit do PR que gerou o deploy (início do lead time)."""
    prs = get(f"/commits/{sha}/pulls")
    if not prs:
        return ts(fallback)
    commits = get(f"/pulls/{prs[0]['number']}/commits?per_page=100")
    return min(ts(c["commit"]["author"]["date"]) for c in commits)


def main() -> None:
    deploys = []
    execucoes_com_falha = 0

    runs = get("/actions/workflows/cd.yml/runs?branch=main&event=push&per_page=100")
    for run in runs["workflow_runs"]:
        jobs = get(f"/actions/runs/{run['id']}/jobs?filter=latest")["jobs"]
        prod = next((j for j in jobs if j["name"] == "production"), None)
        if prod and prod["conclusion"] == "success":
            inicio = inicio_da_mudanca(run["head_sha"], run["head_commit"]["timestamp"])
            fim = ts(prod["completed_at"])
            deploys.append((run["head_sha"][:7], inicio, fim))
        elif run["conclusion"] == "failure":
            execucoes_com_falha += 1

    rollbacks = get("/actions/workflows/rollback.yml/runs?per_page=100")["workflow_runs"]
    rollbacks_ok = [r for r in rollbacks if r["conclusion"] == "success"]
    tempos_rec = [
        (ts(r["updated_at"]) - ts(r["run_started_at"])).total_seconds() for r in rollbacks_ok
    ]

    deploys.sort(key=lambda d: d[2])
    leads = [(fim - inicio).total_seconds() for _, inicio, fim in deploys]

    print(f"## Métricas DORA — {REPO}\n")
    print("| SHA | Início da mudança (1º commit do PR) | Em produção | Lead time |")
    print("| --- | --- | --- | --- |")
    for (sha, inicio, fim), lead in zip(deploys, leads):
        print(f"| `{sha}` | {inicio:%d/%m %H:%M} UTC | {fim:%d/%m %H:%M} UTC | {fmt(lead)} |")

    print("\n| Métrica | Valor |")
    print("| --- | --- |")
    print(f"| Deploys em produção | {len(deploys)} |")
    if deploys:
        dias = max((deploys[-1][2] - deploys[0][2]).total_seconds() / 86400, 1)
        print(f"| Frequência de deploy | {len(deploys) / dias:.1f} por dia |")
        print(f"| Lead time médio | {fmt(mean(leads))} |")
        print(f"| Lead time mínimo | {fmt(min(leads))} |")
        taxa = len(rollbacks_ok) / len(deploys) * 100
        print(f"| Rollbacks executados | {len(rollbacks_ok)} |")
        print(f"| Taxa de falha (rollbacks ÷ deploys) | {taxa:.0f}% |")
    print(f"| Execuções do cd com falha | {execucoes_com_falha} |")
    if tempos_rec:
        print(f"| Tempo de recuperação médio | {fmt(mean(tempos_rec))} |")
        print(f"| Tempo de recuperação mínimo | {fmt(min(tempos_rec))} |")


if __name__ == "__main__":
    main()
