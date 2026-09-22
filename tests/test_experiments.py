"""記録の欠落と再現性の退行を、実際の子プロセスで検出する。"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ExperimentTest(unittest.TestCase):
    def run_experiment(self, config, directory, *, allow_dirty=True, issue=12):
        path = directory / "config.json"
        path.write_text(json.dumps(config))
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/run_experiment.py"),
                "--config",
                str(path),
                *(["--allow-dirty"] if allow_dirty else []),
                *(["--issue", str(issue)] if issue is not None else []),
                "--output-root",
                str(directory / "runs"),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        run = max((directory / "runs").iterdir(), key=lambda p: p.stat().st_mtime_ns)
        return result, run, json.loads((run / "run.json").read_text())

    def test_repeatable_and_recorded(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/raw") as temporary:
            directory = Path(temporary)
            config = json.loads((ROOT / "configs/smoke.json").read_text())
            data = directory / "input.txt"
            data.write_text("入力のハッシュ確認")
            config["inputs"] = [data.relative_to(ROOT).as_posix()]
            first_result, first, manifest = self.run_experiment(config, directory)
            self.assertEqual(first_result.returncode, 0, (first / "run.log").read_text())
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(manifest["issue"], 12)
            self.assertIn("commit", manifest["git"])
            self.assertTrue(json.loads((first / "inputs.json").read_text())[0]["sha256"])
            self.assertTrue((first / "source/uv.lock").is_file())
            self.assertIn("人工データ", (first / "run.log").read_text())
            environment = json.loads((first / "environment.json").read_text())
            self.assertTrue(environment["packages"])
            self.assertEqual(
                environment["uv"],
                subprocess.check_output(["uv", "--version"], text=True).strip(),
            )
            second_result, second, _ = self.run_experiment(config, directory)
            self.assertEqual(second_result.returncode, 0)
            self.assertNotEqual(first, second)
            for name in ("metrics.json", "split.json", "predictions.csv"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())

    def test_child_failure_is_recorded(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/raw") as temporary:
            config = json.loads((ROOT / "configs/smoke.json").read_text())
            config["parameters"]["rows"] = -1
            result, run, manifest = self.run_experiment(config, Path(temporary))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(manifest["status"], "failed")
            self.assertIn("finished_at", manifest)
            self.assertIn("Traceback", (run / "run.log").read_text())
            self.assertIn("scripts/smoke.py", (run / "run.log").read_text())
            self.assertEqual(json.loads((run / "config.json").read_text()), config)

    def test_missing_input_is_recorded(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/raw") as temporary:
            config = json.loads((ROOT / "configs/smoke.json").read_text())
            config["inputs"] = [(Path(temporary) / "missing.csv").relative_to(ROOT).as_posix()]
            result, run, manifest = self.run_experiment(config, Path(temporary))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(manifest["status"], "failed")
            self.assertIn("missing.csv", (run / "run.log").read_text())

    def test_dirty_run_is_rejected(self):
        with (
            tempfile.TemporaryDirectory(dir=ROOT / "data/raw") as temporary,
            tempfile.NamedTemporaryFile(dir=ROOT, prefix="dirty-check-", suffix=".txt"),
        ):
            config = json.loads((ROOT / "configs/smoke.json").read_text())
            result, run, manifest = self.run_experiment(config, Path(temporary), allow_dirty=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(manifest["git"]["dirty"])
            self.assertEqual(manifest["status"], "failed")
            self.assertIn("コミット", manifest["error"])
            self.assertIn("コミット", (run / "run.log").read_text())
            self.assertIn("finished_at", manifest)

    def test_formal_run_requires_issue(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/raw") as temporary:
            config = json.loads((ROOT / "configs/smoke.json").read_text())
            result, _, manifest = self.run_experiment(
                config, Path(temporary), allow_dirty=False, issue=None
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(manifest["status"], "failed")
            self.assertIn("正式実行には --issue", manifest["error"])

    def test_nested_source_is_saved(self):
        with (
            tempfile.TemporaryDirectory(dir=ROOT / "data/raw") as temporary,
            tempfile.TemporaryDirectory(dir=ROOT / "scripts") as source_directory,
        ):
            source = Path(source_directory) / "nested.py"
            source.write_text("# スナップショットの検証用。\n")
            config = json.loads((ROOT / "configs/smoke.json").read_text())
            result, run, _ = self.run_experiment(config, Path(temporary))
            self.assertEqual(result.returncode, 0, (run / "run.log").read_text())
            relative = source.relative_to(ROOT)
            self.assertEqual((run / "source" / relative).read_bytes(), source.read_bytes())
            hashes = json.loads((run / "source.json").read_text())
            self.assertIn(relative.as_posix(), hashes)

    def test_invalid_config_is_recorded(self):
        for updates, message in [
            ({"script": None}, "script は空でない文字列"),
            ({"script": ""}, "script は空でない文字列"),
            ({"inputs": [str(ROOT / "data/raw/train.csv")]}, "相対パス"),
            ({"inputs": ["../outside.csv"]}, "相対パス"),
            ({"inputs": [123]}, "相対パス文字列"),
        ]:
            with self.subTest(updates=updates):
                with tempfile.TemporaryDirectory(dir=ROOT / "data/raw") as temporary:
                    config = json.loads((ROOT / "configs/smoke.json").read_text())
                    config.update(updates)
                    if updates == {"script": None}:
                        del config["script"]
                    result, run, manifest = self.run_experiment(config, Path(temporary))
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(manifest["status"], "failed")
                    self.assertIn(message, manifest["error"])
                    self.assertIn(message, (run / "run.log").read_text())

    def test_input_symlink_outside_repository_is_rejected(self):
        with (
            tempfile.TemporaryDirectory(dir=ROOT / "data/raw") as temporary,
            tempfile.TemporaryDirectory() as outside,
        ):
            target = Path(outside) / "input.txt"
            target.write_text("リポジトリ外のデータ")
            link = Path(temporary) / "input.txt"
            link.symlink_to(target)
            config = json.loads((ROOT / "configs/smoke.json").read_text())
            config["inputs"] = [link.relative_to(ROOT).as_posix()]
            result, _, manifest = self.run_experiment(config, Path(temporary))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("リポジトリ内", manifest["error"])


if __name__ == "__main__":
    unittest.main()
