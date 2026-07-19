from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from orchestrator.graph import OrchestrationGraph
from orchestrator.state import RequirementCategory, RequirementSpec, RunState, RunStateStore
from orchestrator.tools.model_provider import build_model_provider_from_env


REQUIREMENT_TEXT = "Build a scalable URL shortener service with APIs, persistence, and analytics."


class ScriptedModelProvider:
    def __init__(self, scripted_by_model: dict[str, list[dict]]) -> None:
        self._scripted = {name: list(values) for name, values in scripted_by_model.items()}

    def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        del system_prompt, user_prompt
        model_name = response_model.__name__
        queue = self._scripted.get(model_name)
        if not queue:
            raise RuntimeError(f"No scripted response configured for {model_name}")
        return response_model.model_validate(queue.pop(0))


def _scripted_url_shortener_provider() -> ScriptedModelProvider:
    return ScriptedModelProvider(
        {
            "RequirementSpec": [
                {
                    "raw_text": REQUIREMENT_TEXT,
                    "category": "greenfield",
                    "explicit_requirements": [
                        "Build a scalable URL shortener service",
                        "Include APIs",
                        "Include persistence",
                        "Include analytics",
                    ],
                    "implicit_requirements": [
                        "Use stateless API nodes",
                        "Track redirect events",
                        "Design for horizontal scaling",
                    ],
                    "ambiguities": [
                        "Target throughput and latency SLO are unspecified",
                        "Analytics retention period is unspecified",
                    ],
                    "ambiguity_score": 0.35,
                }
            ],
            "ArchitectureDesign": [
                {
                    "components": ["fastapi-api", "sqlite-store", "analytics-service"],
                    "data_model": (
                        "url_mappings(code TEXT PRIMARY KEY, target_url TEXT, created_at TIMESTAMP), "
                        "click_events(id INTEGER PK, code TEXT, created_at TIMESTAMP)"
                    ),
                    "api_contract_yaml": (
                        "openapi: 3.0.3\n"
                        "info:\n"
                        "  title: URL Shortener API\n"
                        "  version: 1.0.0\n"
                        "paths:\n"
                        "  /api/v1/shorten:\n"
                        "    post:\n"
                        "      summary: Create a short URL\n"
                        "  /api/v1/{code}:\n"
                        "    get:\n"
                        "      summary: Resolve short URL\n"
                        "  /api/v1/analytics/{code}:\n"
                        "    get:\n"
                        "      summary: Fetch click analytics\n"
                    ),
                    "tradeoffs": [
                        "Random IDs vs counters: chose random IDs for easier stateless generation.",
                        "SQLite vs distributed DB: chose SQLite for prototype simplicity.",
                        "Sync analytics vs async pipeline: chose sync writes for clarity in prototype.",
                    ],
                }
            ],
            "TaskDAG": [
                {
                    "tasks": [
                        {
                            "id": "core-001",
                            "title": "Implement persistence and core APIs",
                            "description": "Build SQLite store and shorten/resolve endpoints.",
                            "depends_on": [],
                            "status": "pending",
                            "owned_files": ["app/store.py", "app/main.py", "tests/test_api_core.py"],
                            "output_summary": None,
                            "retry_count": 0,
                        },
                        {
                            "id": "analytics-002",
                            "title": "Add analytics endpoint",
                            "description": "Track clicks and expose analytics API.",
                            "depends_on": ["core-001"],
                            "status": "pending",
                            "owned_files": ["app/analytics.py", "app/main.py", "tests/test_api_analytics.py"],
                            "output_summary": None,
                            "retry_count": 0,
                        },
                    ]
                }
            ],
            "_GeneratedFilesResponse": [
                {
                    "files": {
                        "app/store.py": "from __future__ import annotations\n\nimport sqlite3\nfrom pathlib import Path\n\n\nclass UrlStore:\n    def __init__(self, db_path: str) -> None:\n        self._db_path = db_path\n        self._init_db()\n\n    def _connect(self) -> sqlite3.Connection:\n        return sqlite3.connect(self._db_path)\n\n    def _init_db(self) -> None:\n        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)\n        with self._connect() as conn:\n            conn.execute(\"CREATE TABLE IF NOT EXISTS url_mappings (code TEXT PRIMARY KEY, target_url TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)\")\n            conn.execute(\"CREATE TABLE IF NOT EXISTS click_events (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)\")\n            conn.commit()\n\n    def save_url(self, code: str, target_url: str) -> None:\n        with self._connect() as conn:\n            conn.execute(\"INSERT OR REPLACE INTO url_mappings(code, target_url) VALUES (?, ?)\", (code, target_url))\n            conn.commit()\n\n    def get_url(self, code: str) -> str | None:\n        with self._connect() as conn:\n            row = conn.execute(\"SELECT target_url FROM url_mappings WHERE code = ?\", (code,)).fetchone()\n        return row[0] if row else None\n\n    def record_click(self, code: str) -> None:\n        with self._connect() as conn:\n            conn.execute(\"INSERT INTO click_events(code) VALUES (?)\", (code,))\n            conn.commit()\n\n    def get_click_count(self, code: str) -> int:\n        with self._connect() as conn:\n            row = conn.execute(\"SELECT COUNT(*) FROM click_events WHERE code = ?\", (code,)).fetchone()\n        return int(row[0] if row else 0)\n",
                        "app/main.py": "from __future__ import annotations\n\nimport os\nimport secrets\n\nfrom fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel, HttpUrl\n\nfrom app.store import UrlStore\n\n\nclass ShortenRequest(BaseModel):\n    target_url: HttpUrl\n\n\nclass ShortenResponse(BaseModel):\n    code: str\n    short_url: str\n\n\ndef _new_code() -> str:\n    return secrets.token_urlsafe(6)[:8]\n\n\ndef create_app(db_path: str | None = None) -> FastAPI:\n    app = FastAPI(title=\"URL Shortener\", version=\"1.0.0\")\n    store = UrlStore(db_path or os.getenv(\"URL_SHORTENER_DB\", \"url_shortener.db\"))\n\n    @app.post(\"/api/v1/shorten\", response_model=ShortenResponse, status_code=201)\n    def shorten(payload: ShortenRequest) -> ShortenResponse:\n        code = _new_code()\n        for _ in range(10):\n            if store.get_url(code) is None:\n                break\n            code = _new_code()\n        else:\n            raise HTTPException(status_code=500, detail=\"Failed to generate unique code\")\n\n        store.save_url(code, str(payload.target_url))\n        return ShortenResponse(code=code, short_url=f\"/api/v1/{code}\")\n\n    @app.get(\"/api/v1/{code}\")\n    def resolve(code: str) -> dict[str, str]:\n        target = store.get_url(code)\n        if target is None:\n            raise HTTPException(status_code=404, detail=\"Short code not found\")\n        store.record_click(code)\n        return {\"code\": code, \"target_url\": target}\n\n    return app\n\n\napp = create_app()\n",
                    }
                },
                {
                    "files": {
                        "app/analytics.py": "from __future__ import annotations\n\nfrom app.store import UrlStore\n\n\nclass AnalyticsService:\n    def __init__(self, store: UrlStore) -> None:\n        self._store = store\n\n    def clicks_for(self, code: str) -> int:\n        return self._store.get_click_count(code)\n",
                        "app/main.py": "from __future__ import annotations\n\nimport os\nimport secrets\n\nfrom fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel, HttpUrl\n\nfrom app.analytics import AnalyticsService\nfrom app.store import UrlStore\n\n\nclass ShortenRequest(BaseModel):\n    target_url: HttpUrl\n\n\nclass ShortenResponse(BaseModel):\n    code: str\n    short_url: str\n\n\ndef _new_code() -> str:\n    return secrets.token_urlsafe(6)[:8]\n\n\ndef create_app(db_path: str | None = None) -> FastAPI:\n    app = FastAPI(title=\"URL Shortener\", version=\"1.0.0\")\n    store = UrlStore(db_path or os.getenv(\"URL_SHORTENER_DB\", \"url_shortener.db\"))\n    analytics = AnalyticsService(store)\n\n    @app.post(\"/api/v1/shorten\", response_model=ShortenResponse, status_code=201)\n    def shorten(payload: ShortenRequest) -> ShortenResponse:\n        code = _new_code()\n        for _ in range(10):\n            if store.get_url(code) is None:\n                break\n            code = _new_code()\n        else:\n            raise HTTPException(status_code=500, detail=\"Failed to generate unique code\")\n\n        store.save_url(code, str(payload.target_url))\n        return ShortenResponse(code=code, short_url=f\"/api/v1/{code}\")\n\n    @app.get(\"/api/v1/{code}\")\n    def resolve(code: str) -> dict[str, str]:\n        target = store.get_url(code)\n        if target is None:\n            raise HTTPException(status_code=404, detail=\"Short code not found\")\n        store.record_click(code)\n        return {\"code\": code, \"target_url\": target}\n\n    @app.get(\"/api/v1/analytics/{code}\")\n    def analytics_endpoint(code: str) -> dict[str, int | str]:\n        target = store.get_url(code)\n        if target is None:\n            raise HTTPException(status_code=404, detail=\"Short code not found\")\n        return {\"code\": code, \"clicks\": analytics.clicks_for(code)}\n\n    return app\n\n\napp = create_app()\n",
                    }
                },
            ],
            "_GeneratedTestsResponse": [
                {
                    "files": {
                        "tests/test_api_core.py": "from pathlib import Path\n\nfrom fastapi.testclient import TestClient\n\nfrom app.main import create_app\n\n\ndef test_shorten_and_resolve(tmp_path: Path) -> None:\n    app = create_app(str(tmp_path / \"core.db\"))\n    client = TestClient(app)\n\n    create = client.post(\"/api/v1/shorten\", json={\"target_url\": \"https://example.com/docs\"})\n    assert create.status_code == 201\n    code = create.json()[\"code\"]\n\n    resolve = client.get(f\"/api/v1/{code}\")\n    assert resolve.status_code == 200\n    assert resolve.json()[\"target_url\"] == \"https://example.com/docs\"\n\n\ndef test_resolve_missing_code(tmp_path: Path) -> None:\n    app = create_app(str(tmp_path / \"core.db\"))\n    client = TestClient(app)\n\n    response = client.get(\"/api/v1/does-not-exist\")\n    assert response.status_code == 404\n",
                    }
                },
                {
                    "files": {
                        "tests/test_api_analytics.py": "from pathlib import Path\n\nfrom fastapi.testclient import TestClient\n\nfrom app.main import create_app\n\n\ndef test_analytics_counts_redirects(tmp_path: Path) -> None:\n    app = create_app(str(tmp_path / \"analytics.db\"))\n    client = TestClient(app)\n\n    create = client.post(\"/api/v1/shorten\", json={\"target_url\": \"https://example.com/page\"})\n    assert create.status_code == 201\n    code = create.json()[\"code\"]\n\n    client.get(f\"/api/v1/{code}\")\n    client.get(f\"/api/v1/{code}\")\n\n    analytics = client.get(f\"/api/v1/analytics/{code}\")\n    assert analytics.status_code == 200\n    assert analytics.json()[\"clicks\"] == 2\n",
                    }
                },
            ],
            "_RiskDocsResponse": [
                {
                    "risks": [
                        "SQLite is a prototype persistence choice and not a distributed production data store.",
                        "Random short-code generation has a low collision risk that should be monitored.",
                        "Synchronous click writes may add latency under high traffic.",
                    ],
                    "final_summary": "## Implementation Plan and Rationale\nImplemented requirement analysis, architecture design, and a two-step dependency-aware execution plan for persistence/API first and analytics second.\n\n## Generated Artifacts\n- app/store.py\n- app/main.py\n- app/analytics.py\n- tests/test_api_core.py\n- tests/test_api_analytics.py\n\n## Risks, Trade-offs, and Validation Approach\nTrade-offs include SQLite simplicity vs horizontal DB scale, random IDs vs sequential IDs, and sync analytics writes vs async pipelines. Validation runs pytest, py_compile, and pyflakes after each task with repair retries on failure.\n\n## Assumptions and Limitations\nPrototype scope assumes moderate traffic and single-region execution. Production should externalize persistence and add async analytics processing.",
                }
            ],
        }
    )


def _slugify(text: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:80] or "generated-project"


def _print_review_payload(state: RunState) -> None:
    print("\n" + "=" * 80)
    print(f"Human Approval Required: phase={state.current_phase}, run_id={state.run_id}")
    print("Review payload:")
    print(state.review_payload or "<no payload>")
    print("=" * 80 + "\n")


def _auto_approve(graph: OrchestrationGraph, run_id: str, feedback: str) -> RunState:
    state = graph.store.load(run_id)
    if state is None:
        raise RuntimeError(f"Run state not found for run_id={run_id}")

    _print_review_payload(state)
    state.human_feedback = feedback
    state.awaiting_human = False
    state.status = "running"
    return graph.invoke(state)


def _run_with_auto_approvals(graph: OrchestrationGraph, state: RunState) -> RunState:
    state = graph.invoke(state)

    approvals = 0
    while state.awaiting_human and state.status != "completed":
        approvals += 1
        state = _auto_approve(graph, state.run_id, feedback=f"Auto-approved gate #{approvals}")
        if approvals > 10:
            raise RuntimeError("Too many approval loops; aborting")

    final_state = graph.store.load(state.run_id)
    if final_state is None:
        raise RuntimeError("Final run state not found after execution")
    if final_state.status != "completed":
        raise RuntimeError(f"Run did not complete successfully. status={final_state.status}")
    return final_state


def _copy_artifacts(generated_root: Path, requirement_text: str, run_id: str, target_dir: Path) -> bool:
    slug = _slugify(requirement_text)
    candidates = [
        generated_root / f"{slug}-{run_id[:8]}",
        generated_root / slug,
    ]
    source_dir = next((path for path in candidates if path.exists()), None)
    if source_dir is None:
        return False

    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, target_dir)
    return True


def _run_project_tests(project_dir: Path) -> int:
    print(f"\nRunning generated project tests in: {project_dir}")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=str(project_dir),
        check=False,
        text=True,
        capture_output=True,
    )

    print("\n--- pytest stdout ---")
    print(proc.stdout.strip() or "<empty>")
    print("\n--- pytest stderr ---")
    print(proc.stderr.strip() or "<empty>")
    print(f"\npytest exit code: {proc.returncode}")
    return proc.returncode


def main() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    generated_root = workspace_root / "generated_projects"
    target_project = generated_root / "url-shortener"
    run_project_dir = generated_root / _slugify(REQUIREMENT_TEXT)

    store = RunStateStore(sqlite_path=str((workspace_root / "orchestrator_runs.db").resolve()))

    try:
        model = build_model_provider_from_env()
    except Exception:
        print("Model provider unavailable; falling back to deterministic scripted URL shortener demo provider.")
        model = _scripted_url_shortener_provider()

    graph = OrchestrationGraph(
        model_provider=model,
        store=store,
        repo_root=str(workspace_root),
        generated_root=str(generated_root),
    )

    if run_project_dir.exists():
        shutil.rmtree(run_project_dir)

    run_id = str(uuid4())
    state = RunState(
        run_id=run_id,
        requirement=RequirementSpec(
            raw_text=REQUIREMENT_TEXT,
            category=RequirementCategory.AMBIGUOUS,
            explicit_requirements=[],
            implicit_requirements=[],
            ambiguities=[],
            ambiguity_score=1.0,
        ),
        current_phase="intake",
        status="running",
    )

    print(f"Starting run_id={run_id}")
    final_state = _run_with_auto_approvals(graph, state)
    final_run_id = run_id

    copied = _copy_artifacts(
        generated_root=generated_root,
        requirement_text=REQUIREMENT_TEXT,
        run_id=final_run_id,
        target_dir=target_project,
    )
    if not copied and not isinstance(model, ScriptedModelProvider):
        print("Primary provider run completed without generated artifacts. Retrying once with deterministic scripted provider.")
        model = _scripted_url_shortener_provider()
        graph = OrchestrationGraph(
            model_provider=model,
            store=store,
            repo_root=str(workspace_root),
            generated_root=str(generated_root),
        )
        if run_project_dir.exists():
            shutil.rmtree(run_project_dir)

        final_run_id = str(uuid4())
        retry_state = RunState(
            run_id=final_run_id,
            requirement=RequirementSpec(
                raw_text=REQUIREMENT_TEXT,
                category=RequirementCategory.AMBIGUOUS,
                explicit_requirements=[],
                implicit_requirements=[],
                ambiguities=[],
                ambiguity_score=1.0,
            ),
            current_phase="intake",
            status="running",
        )
        print(f"Retrying run_id={final_run_id} with scripted provider")
        final_state = _run_with_auto_approvals(graph, retry_state)
        copied = _copy_artifacts(
            generated_root=generated_root,
            requirement_text=REQUIREMENT_TEXT,
            run_id=final_run_id,
            target_dir=target_project,
        )

    if not copied:
        raise RuntimeError("Generated project artifacts were not created by either provider run or scripted fallback")

    print(f"Run completed successfully. run_id={final_run_id}")
    print(f"Final status: {final_state.status}")
    print(f"Final artifacts copied to: {target_project}")

    test_exit_code = _run_project_tests(target_project)
    if test_exit_code != 0:
        raise RuntimeError("Generated project tests failed")


if __name__ == "__main__":
    main()
