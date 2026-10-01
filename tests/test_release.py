"""Acceptance checks for pinned source, deterministic archives and unsafe input."""

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("release", Path(__file__).resolve().parents[1] / "scripts/build_release.py")
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aime-dictionary-test-")
        self.root = Path(self.temp.name)
        self.repo = self.root / "source"
        self.repo.mkdir()
        self.git("init", "-q")
        (self.repo / "feeds").mkdir()
        (self.repo / "LICENSE").write_text(f"{release.AUTHOR}\n{release.LICENSE_URL}\n")
        self.write_catalog()
        (self.repo / "feeds/first.txt").write_text("智能体\tzhi neng ti\t40\nDeepSeek\tdeepseek\t98\n")
        (self.repo / "feeds/second.txt").write_text("智能体\tzhi neng ti\t95\n松弛感\tsong chi gan\t90\n")
        self.commit()

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    def commit(self):
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")

    def write_catalog(self, mutation=None):
        data = {"feeds": [{"id": name, "name": name, "path": f"feeds/{name}.txt", "entries": 2}
                          for name in ["first", "second"]]}
        if mutation:
            mutation(data)
        (self.repo / "index.json").write_text(json.dumps(data))

    def test_reproducible_pinned_archive_and_checksums(self):
        one = release.build(self.repo, "HEAD", "2026-10-01", self.root / "one")
        # An uncommitted feed must not contaminate the pinned release.
        (self.repo / "feeds/first.txt").write_text("dirty malformed source")
        two = release.build(self.repo, "HEAD", "2026-10-01", self.root / "two")
        self.assertEqual(Path(one["archive"]).read_bytes(), Path(two["archive"]).read_bytes())
        self.assertEqual(one["totalFeedEntries"], 4)
        self.assertEqual(one["uniqueEntries"], 3)
        with zipfile.ZipFile(one["archive"]) as bundle:
            manifest = json.loads(bundle.read("manifest.json"))
            self.assertIn(b"zhi neng ti\t95", bundle.read("rime/aime_online.dict.yaml"))
            self.assertIn(b"zhi neng ti\t40", bundle.read("feeds/first.txt"))
            self.assertNotIn(b"dirty", bundle.read("feeds/first.txt"))
            for line in bundle.read("SHA256SUMS").decode().splitlines():
                expected, path = line.split("  ")
                self.assertEqual(hashlib.sha256(bundle.read(path)).hexdigest(), expected)
            for entry in manifest["files"]:
                data = bundle.read(entry["path"])
                self.assertEqual(len(data), entry["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
            self.assertEqual(json.loads(bundle.read("SOURCE.json"))["commit"], one["sourceCommit"])
            for info in bundle.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertFalse(info.filename.startswith("/"))
                self.assertNotIn("..", Path(info.filename).parts)

    def test_rejects_catalog_traversal_count_and_duplicate_ids(self):
        mutations = [lambda d: d["feeds"][0].update(path="../LICENSE"),
                     lambda d: d["feeds"][0].update(entries=3),
                     lambda d: d["feeds"].append(d["feeds"][0]),
                     lambda d: d["feeds"][0].update(name="name\ninjected row"),
                     lambda d: d.update(feeds=[None]),
                     lambda d: d.update(feeds=d["feeds"] * 51)]
        for index, mutation in enumerate(mutations):
            self.write_catalog(mutation)
            self.commit()
            with self.assertRaises(ValueError):
                release.build(self.repo, "HEAD", "v1", self.root / f"invalid-{index}")
            self.assertFalse((self.root / f"invalid-{index}").exists())

    def test_rejects_malformed_or_duplicate_rows(self):
        bad = ["词\tci\t101", "词\tci  yu\t80", "词\tci\t1\n词\tci\t2", "词\tci", "词\tci\t-1"]
        for data in bad:
            with self.subTest(data=data), self.assertRaises(ValueError):
                release.parse_rows(data.encode(), "fixture")

    def test_does_not_replace_existing_output(self):
        target = self.root / "existing"
        target.mkdir()
        (target / "keep").write_text("unchanged")
        with self.assertRaises(ValueError):
            release.build(self.repo, "HEAD", "v1", target)
        self.assertEqual((target / "keep").read_text(), "unchanged")

    def test_rejects_version_traversal(self):
        with self.assertRaises(ValueError):
            release.build(self.repo, "HEAD", "../../escape", self.root / "invalid")

    def test_public_provenance_and_catalog_integrity(self):
        repository = "https://github.com/zoolapp/aime-dicts"
        result = release.build(self.repo, "HEAD", "v1", self.root / "public", repository)
        with zipfile.ZipFile(result["archive"]) as bundle:
            source = json.loads(bundle.read("SOURCE.json"))
            self.assertEqual(source["repository"], repository)
            self.assertEqual(source["publicationStatus"], "public")
            self.assertIn(repository.encode(), bundle.read("ATTRIBUTION.txt"))
        for index, mutation in enumerate([
            lambda d: d["feeds"][0].update(sha256="0" * 64),
            lambda d: d["feeds"][0].update(size=1),
        ]):
            self.write_catalog(mutation)
            self.commit()
            with self.assertRaises(ValueError):
                release.build(self.repo, "HEAD", "v1", self.root / f"integrity-{index}")
        with self.assertRaises(ValueError):
            release.build(self.repo, "HEAD", "v1", self.root / "invalid-url", "file:///private")


if __name__ == "__main__":
    unittest.main()
