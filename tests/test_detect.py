"""Tests for stack detection."""

from __future__ import annotations

from pathlib import Path

from specced import detect


def _mk(root: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root


def test_detect_python_fastapi(tmp_path: Path) -> None:
    _mk(
        tmp_path,
        {
            "pyproject.toml": '[project]\ndependencies=["fastapi"]\n[tool.ruff]\n[tool.pytest.ini_options]\n'
        },
    )
    d = detect.detect(tmp_path)
    assert "python" in d["languages"]
    assert "fastapi" in d["frameworks"]
    assert "ruff" in d["tools"]
    assert d["suggested_preset"] == "python-fastapi"


def test_detect_generic_python(tmp_path: Path) -> None:
    _mk(tmp_path, {"pyproject.toml": '[project]\ndependencies=["click"]\n'})
    assert detect.detect(tmp_path)["suggested_preset"] == "python"


def test_detect_go(tmp_path: Path) -> None:
    _mk(tmp_path, {"go.mod": "module example.com/x\n"})
    assert detect.detect(tmp_path)["suggested_preset"] == "go"


def test_detect_node_next(tmp_path: Path) -> None:
    _mk(
        tmp_path,
        {
            "package.json": '{"dependencies":{"next":"15"},"scripts":{"lint":"next lint","build":"next build"}}'
        },
    )
    d = detect.detect(tmp_path)
    assert "node" in d["languages"]
    assert d["suggested_preset"] == "node-next"
    assert d["suggested_verification"]["lint"] == "npm run lint"


def test_detect_svelte(tmp_path: Path) -> None:
    _mk(tmp_path, {"package.json": '{"dependencies":{"svelte":"4","@sveltejs/kit":"2"}}'})
    assert detect.detect(tmp_path)["suggested_preset"] == "node-svelte"


def test_detect_monorepo_with_db(tmp_path: Path) -> None:
    _mk(
        tmp_path,
        {
            "backend/pyproject.toml": '[project]\ndependencies=["fastapi","alembic"]\n',
            "frontend/package.json": '{"dependencies":{"next":"15"}}',
            "docker-compose.yml": "services:\n  db: { image: postgres:16 }\n  cache: { image: redis:7 }\n",
            ".github/workflows/ci.yml": "name: ci\n",
        },
    )
    d = detect.detect(tmp_path)
    assert {"backend", "frontend"}.issubset(set(d["tracks"]))
    assert d["monorepo"] is True
    assert "postgres" in d["infra"]["databases"]
    assert "postgres" in d["suggested_mcp"]
    assert "github" in d["suggested_mcp"]  # .github present


def test_detect_supabase(tmp_path: Path) -> None:
    _mk(tmp_path, {"pyproject.toml": "[project]\n", "supabase/config.toml": "x=1\n"})
    d = detect.detect(tmp_path)
    assert d["infra"]["supabase"] is True
    assert "supabase" in d["suggested_mcp"]


def test_detect_django(tmp_path: Path) -> None:
    _mk(tmp_path, {"pyproject.toml": '[project]\ndependencies=["django"]\n'})
    assert detect.detect(tmp_path)["suggested_preset"] == "python-django"


def test_detect_rust(tmp_path: Path) -> None:
    _mk(tmp_path, {"Cargo.toml": '[package]\nname = "x"\n'})
    d = detect.detect(tmp_path)
    assert "rust" in d["languages"]
    assert d["suggested_preset"] == "rust"


def test_detect_node_react_vite(tmp_path: Path) -> None:
    _mk(
        tmp_path, {"package.json": '{"dependencies":{"react":"19"},"devDependencies":{"vite":"5"}}'}
    )
    assert detect.detect(tmp_path)["suggested_preset"] == "node-react"


def test_detect_node_express(tmp_path: Path) -> None:
    _mk(tmp_path, {"package.json": '{"dependencies":{"express":"4"}}'})
    assert detect.detect(tmp_path)["suggested_preset"] == "node-express"


def test_detect_java_spring(tmp_path: Path) -> None:
    _mk(
        tmp_path,
        {"pom.xml": "<project><dependencies>org.springframework.boot</dependencies></project>"},
    )
    d = detect.detect(tmp_path)
    assert "java" in d["languages"]
    assert "spring" in d["frameworks"]
    assert d["suggested_preset"] == "java-spring"


def test_detect_java_without_spring_has_no_preset(tmp_path: Path) -> None:
    _mk(tmp_path, {"pom.xml": "<project><groupId>x</groupId></project>"})
    d = detect.detect(tmp_path)
    assert "java" in d["languages"]
    assert d["suggested_preset"] is None


def test_detect_ruby_rails(tmp_path: Path) -> None:
    _mk(tmp_path, {"Gemfile": "gem 'rails', '~> 7.1'\n"})
    d = detect.detect(tmp_path)
    assert "ruby" in d["languages"]
    assert d["suggested_preset"] == "ruby-rails"


def test_detect_tauri(tmp_path: Path) -> None:
    _mk(
        tmp_path,
        {
            "package.json": '{"dependencies":{"next":"16","@tauri-apps/api":"2"}}',
            "src-tauri/Cargo.toml": '[package]\nname = "app"\n',
        },
    )
    d = detect.detect(tmp_path)
    assert "rust" in d["languages"]
    assert "tauri" in d["frameworks"]
    assert d["suggested_preset"] == "tauri"
    assert "src-tauri" in d["tracks"]


def test_detect_next_app_dir_is_not_a_track(tmp_path: Path) -> None:
    _mk(
        tmp_path,
        {
            "package.json": '{"dependencies":{"next":"16"}}',
            "app/page.tsx": "export default function P() {}\n",
        },
    )
    d = detect.detect(tmp_path)
    assert "app" not in d["tracks"]  # Next.js router dir, not a monorepo track


def test_detect_compose_in_deploy_subdir(tmp_path: Path) -> None:
    _mk(
        tmp_path,
        {
            "go.mod": "module example.com/x\n",
            "deploy/docker-compose/docker-compose.yml": (
                "services:\n  db: { image: postgres:16 }\n  vec: { image: qdrant/qdrant:v1.11.0 }\n"
            ),
        },
    )
    d = detect.detect(tmp_path)
    assert "postgres" in d["infra"]["databases"]
    assert "qdrant" in d["infra"]["databases"]
    assert "postgres" in d["suggested_mcp"]
    assert "qdrant" in d["suggested_mcp"]


def test_detect_empty_repo(tmp_path: Path) -> None:
    d = detect.detect(tmp_path)
    assert d["suggested_preset"] is None
    assert d["suggested_mcp"] == ["context7"]
