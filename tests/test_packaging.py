import importlib.util
from pathlib import Path
import tempfile
import unittest


def load_script(name):
    path = Path(__file__).resolve().parents[1] / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackagingTests(unittest.TestCase):
    def test_skill_bundle_is_self_contained_and_never_overwrites(self):
        installer = load_script("install_skill")
        checker = load_script("check_skills")
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "blender-master-artist"
            installer.install_bundle(source, target)
            self.assertEqual(checker.check(target)["status"], "pass")
            self.assertTrue((target / "bma/blender_runtime.py").is_file())
            self.assertFalse((target / "outputs").exists())
            with self.assertRaises(FileExistsError):
                installer.install_bundle(source, target)
