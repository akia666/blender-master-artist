import importlib.util
from pathlib import Path
import tempfile
import subprocess
import unittest

spec = importlib.util.spec_from_file_location("privacy_audit", Path(__file__).resolve().parents[1] / "scripts/privacy_audit.py")
privacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(privacy)


class PrivacyTests(unittest.TestCase):
    def test_detects_secrets_paths_and_sensitive_files_without_echoing_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret = "ghp_" + "x" * 32
            personal = "C:" + "/Users/" + "example-person/private"
            (root / "leak.txt").write_text(secret + "\n" + personal)
            (root / ".env").write_text("sensitive configuration")
            (root / "model.blend").write_bytes(b"BLENDER")
            result = privacy.audit(root, all_files=True)
            rules = {f["rule"] for f in result["findings"]}
            self.assertTrue({"service_token", "personal_windows_path", "sensitive_filename",
                             "asset_requires_license_and_metadata_review"} <= rules)
            self.assertNotIn(secret, str(result))

    def test_relative_paths_and_clean_text_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "README.md").write_text("Use outputs/model.blend and relative paths.")
            self.assertEqual(privacy.audit(directory)["status"], "pass")

    def test_force_tracked_ignored_output_is_still_a_publication_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            try:
                subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            except (OSError, subprocess.CalledProcessError):
                self.skipTest("Git unavailable; other privacy checks still run")
            (root / ".gitignore").write_text("outputs/\n")
            (root / "outputs").mkdir()
            (root / "outputs/leak.txt").write_text("ghp_" + "x" * 32)
            subprocess.run(["git", "-C", str(root), "add", "--force", "outputs/leak.txt"],
                           check=True, capture_output=True)
            result = privacy.audit(root)
            self.assertTrue(any(f["rule"] == "service_token" for f in result["findings"]))
