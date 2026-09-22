"""Python スクリプトを実行し、設定・環境・ログ・終了状態を保存する。"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import traceback
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(UTC).isoformat()


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"Git 情報を取得できません: {result.stderr.strip()}")
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--issue", type=int, help="対応する Issue 番号")
    parser.add_argument("--allow-dirty", action="store_true", help="開発中の動作確認用")
    parser.add_argument("--output-root", type=Path, default=ROOT / "runs")
    args = parser.parse_args()
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:12]
    output = args.output_root.resolve() / run_id
    output.mkdir(parents=True)
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "issue": args.issue,
        "status": "running",
        "started_at": now(),
        "argv": sys.argv,
        "allow_dirty": args.allow_dirty,
    }
    write_json(output / "run.json", manifest)
    code = 1
    child = None
    with (output / "run.log").open("w", buffering=1) as log:
        try:
            shutil.copyfile(args.config, output / "config.original.json")
            config = json.loads(args.config.read_text())
            write_json(output / "config.json", config)
            if not isinstance(config, dict):
                raise ValueError("設定は JSON オブジェクトで指定してください。")
            if not isinstance(config.get("script"), str) or not config["script"].strip():
                raise ValueError("script は空でない文字列で指定してください。")
            if not isinstance(config.get("seed"), int) or isinstance(config["seed"], bool):
                raise ValueError("seed は整数で指定してください。")
            if not 0 <= config["seed"] < 2**32:
                raise ValueError("seed は 0 以上 2**32 未満で指定してください。")
            if not isinstance(config.get("inputs"), list):
                raise ValueError("inputs に入力ファイルの一覧を指定してください。")
            for item in config["inputs"]:
                if not isinstance(item, str) or not item.strip():
                    raise ValueError("inputs の各要素は空でない相対パス文字列にしてください。")
                path = Path(item)
                if path.is_absolute() or not (ROOT / path).resolve().is_relative_to(ROOT):
                    raise ValueError("inputs はリポジトリ内を指す相対パスで指定してください。")
            if not isinstance(config.get("parameters"), dict):
                raise ValueError("parameters はオブジェクトで指定してください。")
            script = (ROOT / config["script"]).resolve()
            if not script.is_relative_to(ROOT / "scripts") or not script.is_file():
                raise ValueError("script は scripts/ 内の Python ファイルを指定してください。")
            if script.suffix != ".py" or script == Path(__file__).resolve():
                raise ValueError("実験用 Python スクリプトを指定してください。")
            status = git("status", "--porcelain", "--untracked-files=all")
            manifest["git"] = {
                "commit": git("rev-parse", "HEAD"),
                "branch": git("branch", "--show-current"),
                "dirty": bool(status),
                "status": status,
            }
            write_json(output / "run.json", manifest)
            if args.issue is not None and args.issue <= 0:
                raise ValueError("--issue は正の整数で指定してください。")
            if not args.allow_dirty and args.issue is None:
                raise ValueError("正式実行には --issue で Issue 番号を指定してください。")
            if status and not args.allow_dirty:
                raise ValueError(
                    "変更をコミットしてください。動作確認のみ --allow-dirty を使えます。"
                )
            environment = {
                "uv": subprocess.check_output(["uv", "--version"], text=True).strip(),
                "python": sys.version,
                "executable": sys.executable,
                "platform": platform.platform(),
                "machine": platform.machine(),
                "packages": sorted(
                    [
                        {"name": d.metadata["Name"], "version": d.version}
                        for d in importlib.metadata.distributions()
                    ],
                    key=lambda d: d["name"],
                ),
                "threads": 1,
                "pythonhashseed": str(config["seed"]),
            }
            write_json(output / "environment.json", environment)
            inputs = []
            for item in config["inputs"]:
                path = (ROOT / item).resolve()
                inputs.append({"path": item, "sha256": sha256(path), "bytes": path.stat().st_size})
            write_json(output / "inputs.json", inputs)
            snapshot = output / "source"
            snapshot.mkdir()
            # 開発中でも確認に使ったスクリプトと依存定義を残す。
            paths = sorted((ROOT / "scripts").rglob("*.py"))
            paths += [ROOT / name for name in ("pyproject.toml", "uv.lock", ".python-version")]
            hashes = {}
            for path in paths:
                if not path.resolve().is_relative_to(ROOT):
                    raise ValueError(f"ソースがリポジトリ外を参照しています: {path}")
                relative = path.relative_to(ROOT)
                destination = snapshot / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
                hashes[str(relative)] = sha256(path)
            write_json(output / "source.json", hashes)
            command = [
                sys.executable,
                "-u",
                str(script),
                "--config",
                str(output / "config.json"),
                "--output-dir",
                str(output),
            ]
            manifest["command"] = command
            write_json(output / "run.json", manifest)
            env = os.environ.copy()
            env.update(
                {
                    name: "1"
                    for name in (
                        "OMP_NUM_THREADS",
                        "OPENBLAS_NUM_THREADS",
                        "MKL_NUM_THREADS",
                        "NUMEXPR_NUM_THREADS",
                        "VECLIB_MAXIMUM_THREADS",
                    )
                }
            )
            env["PYTHONHASHSEED"] = str(config["seed"])
            print(f"実験開始: {run_id}", file=log)
            # ファイルに直接接続し、標準出力・標準エラーを実行中も継続保存する。
            child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=log)
            code = child.wait()
            if code != 0:
                raise RuntimeError(f"実験スクリプトが終了コード {code} で失敗しました。")
            metrics = json.loads((output / "metrics.json").read_text())
            if not isinstance(metrics, dict):
                raise ValueError("metrics.json はオブジェクトで出力してください。")
            manifest["status"] = "completed"
        except BaseException as exc:
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            code = 130 if isinstance(exc, KeyboardInterrupt) else (code or 1)
            manifest["status"] = "interrupted" if code == 130 else "failed"
            manifest["error"] = str(exc)
            traceback.print_exc(file=log)
        finally:
            manifest["exit_code"] = code
            manifest["finished_at"] = now()
            manifest["artifacts"] = sorted(
                str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()
            )
            write_json(output / "run.json", manifest)
    print(f"{manifest['status']}: {output}")
    return code


if __name__ == "__main__":
    sys.exit(main())
