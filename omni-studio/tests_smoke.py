"""Teste de fumaca: percorre projeto -> pipeline -> storyboard -> render -> midia.

Roda offline no provider mock: `python3 tests_smoke.py`.
"""
from __future__ import annotations

import os
import tempfile
import time

os.environ.setdefault("OMNI_PROVIDER", "mock")
os.environ.setdefault("OMNI_STORAGE_DIR", tempfile.mkdtemp(prefix="omni-smoke-"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)
failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"{'ok  ' if condition else 'FALHA'} {label}{'' if condition else ' -> ' + detail}")
    if not condition:
        failures.append(label)


def wait_for(fn, timeout: float = 60.0, interval: float = 0.5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        value = fn()
        if value:
            return value
        time.sleep(interval)
    return None


with client:
    config = client.get("/api/config").json()
    check("config expoe o provider", config["provider"] == "mock", str(config))

    project = client.post("/api/projects", json={"name": "Smoke"}).json()
    check("cria projeto", bool(project["id"]))

    # 1) contexto -> 2) storytelling -> 3) storyboard
    context = {
        "brand": "Contoso",
        "product": "fabrica de migracao para Azure",
        "audience": "CIOs de grandes empresas",
        "problem": "entender sistemas legados manualmente leva meses",
        "turning_point": "mapeamento deterministico antes de construir",
        "value": "governanca ponta a ponta e custo otimizado",
        "cta": "Vamos migrar.",
        "duration_seconds": 30,
        "resolution": "360p",
    }
    pipeline = client.post(f"/api/projects/{project['id']}/pipelines", json=context).json()
    check("pipeline criado", bool(pipeline.get("id")), str(pipeline)[:200])
    check("storytelling em 5 atos", len(pipeline["story"]["acts"]) == 5)
    check("locucao em portugues", all(a["vo"] for a in pipeline["story"]["acts"]))
    segments = pipeline["storyboard"]["segments"]
    check("storyboard com 3 pecas de 10s", len(segments) == 3, f"{len(segments)} pecas")
    check("peca 1 abre a cena", segments[0]["mode"] == "text_to_video")
    check("pecas seguintes estendem", [s["mode"] for s in segments[1:]] == ["extend", "extend"])
    check("prompt tem blocos do template", "ACTION AND CAMERA SEQUENCE" in segments[0]["prompt"])
    check("continuacao explicita", segments[1]["prompt"].startswith("CONTINUATION"))

    # edicao manual do storyboard e regeracao de prompts
    board = pipeline["storyboard"]
    board["segments"][0]["shot_sequence"] = "OPENING SHOT — 107° wide rectilinear view, tabletop push-in."
    client.patch(f"/api/pipelines/{pipeline['id']}", json={"storyboard": board})
    edited = client.post(f"/api/pipelines/{pipeline['id']}/prompts").json()
    check("prompt reflete a edicao", "tabletop push-in" in edited["storyboard"]["segments"][0]["prompt"])

    # 4) resultado final
    accepted = client.post(f"/api/pipelines/{pipeline['id']}/render", json={"resolution": "360p"})
    check("render aceito", accepted.status_code == 202, accepted.text)
    final = wait_for(
        lambda: (lambda p: p if p["status"] in ("completed", "failed") else None)(
            client.get(f"/api/pipelines/{pipeline['id']}").json()
        )
    )
    check("pipeline concluiu", final and final["status"] == "completed", str(final and final.get("error")))
    renders = final["renders"] if final else []
    check("3 pecas renderizadas", len(renders) == 3, f"{len(renders)}")
    check("cena chega a 30s", renders and renders[-1]["cumulative_seconds"] == 30)
    check("encadeamento por parent_id", all(r["parent_id"] for r in renders[1:]))
    if renders:
        media = client.get(f"/api/generations/{renders[0]['id']}/media")
        check("midia servida", media.status_code == 200 and len(media.content) > 0)

    # limite cumulativo de 40s
    too_long = client.post(
        f"/api/projects/{project['id']}/pipelines", json={**context, "duration_seconds": 60}
    ).json()
    check("duracao normalizada ao teto de 40s", too_long["context"]["duration_seconds"] == 40)

    # draft room
    batch = client.post(
        f"/api/projects/{project['id']}/draft-batches",
        json={"prompts": ["variacao A", "variacao B", "variacao C"]},
    ).json()
    check("draft room cria 3 rascunhos em 360p", len(batch) == 3 and batch[0]["resolution"] == "360p")
    done = wait_for(
        lambda: all(
            client.get(f"/api/generations/{g['id']}").json()["status"] == "completed" for g in batch
        )
    )
    check("rascunhos concluem", bool(done))

    # validacoes de dominio
    bad = client.post(
        f"/api/projects/{project['id']}/generations",
        json={"prompt": "x", "mode": "interpolate"},
    )
    check("interpolate exige 2 frames", bad.status_code == 400, bad.text)
    # 30s + 10s = 40s ainda cabe; a extensao seguinte estouraria o teto
    fourth = client.post(
        f"/api/projects/{project['id']}/generations",
        json={"prompt": "x", "mode": "extend", "parent_id": renders[-1]["id"], "resolution": "360p"},
    )
    check("quarta peca chega a 40s", fourth.status_code == 202, fourth.text)
    fourth_id = fourth.json()["id"]
    wait_for(lambda: client.get(f"/api/generations/{fourth_id}").json()["status"] == "completed")
    bad = client.post(
        f"/api/projects/{project['id']}/generations",
        json={"prompt": "x", "mode": "extend", "parent_id": fourth_id, "resolution": "360p"},
    )
    check("extensao alem de 40s e recusada", bad.status_code == 400, bad.text)

print("\n" + ("FALHAS: " + ", ".join(failures) if failures else "Tudo verde."))
raise SystemExit(1 if failures else 0)
