#!/usr/bin/env python3
"""Compile a release using AIME's real RIME engine in disposable directories."""

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    if args.evidence.exists():
        parser.error("evidence directory already exists")
    cli = args.cli.resolve(strict=True)
    manifest = json.loads((args.package / "manifest.json").read_text())
    dictionary = args.package / manifest["combinedRimeFile"]
    expected = next(item for item in manifest["files"] if item["path"] == manifest["combinedRimeFile"])
    if hashlib.sha256(dictionary.read_bytes()).hexdigest() != expected["sha256"]:
        parser.error("dictionary checksum mismatch")
    args.evidence.mkdir(parents=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="aime-release-rime-") as temporary:
        root = Path(temporary)
        shared, user = root / "shared", root / "user"
        shared.mkdir()
        user.mkdir()
        (shared / "aime_online.dict.yaml").write_bytes(dictionary.read_bytes())
        (shared / "default.yaml").write_text('config_version: "release-test"\nschema_list:\n  - schema: aime_release_test\nmenu:\n  page_size: 9\n')
        (shared / "aime.yaml").write_text('config_version: "release-test"\n')
        # Original minimal test schema; never installs or changes the active IME.
        (shared / "aime_release_test.schema.yaml").write_text('''schema:
  schema_id: aime_release_test
  name: AIME release verification
  version: "1"
engine:
  processors: [speller, selector, navigator, express_editor]
  segmentors: [abc_segmentor, fallback_segmentor]
  translators: [script_translator]
speller:
  alphabet: abcdefghijklmnopqrstuvwxyz0123456789
  delimiter: " '"
translator:
  dictionary: aime_online
  enable_user_dict: false
  enable_sentence: false
''')
        cases = [("deepseek", "DeepSeek"), ("zhinengti", "智能体"), ("songchigan", "松弛感")]
        for index, (keys, word) in enumerate(cases):
            command = [str(cli), "bench", "--user-dir", str(user), "--shared-dir", str(shared),
                       "--schema", "aime_release_test", "--keys", keys,
                       "--iterations", "1", "--print-candidates", "--verbose"]
            if index:
                command.append("--no-deploy")
            process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, timeout=60)
            (args.evidence / f"rime-{index + 1}.log").write_text(process.stdout + "\n" + process.stderr)
            candidates = [line.partition(". ")[2].split("  ")[0]
                          for line in process.stdout.splitlines() if ". " in line]
            passed = process.returncode == 0 and word in candidates
            results.append({"keys": keys, "expectedCandidate": word, "candidates": candidates,
                            "exitCode": process.returncode, "passes": passed})
            if not passed:
                raise RuntimeError(f"RIME verification failed for {keys}; see log {index + 1}")
        compiled = sorted(p.name for p in (user / "build").glob("aime_online.*"))
    report = {"sourceCommit": manifest["sourceCommit"], "version": manifest["version"],
              "uniqueDictionaryEntries": manifest["uniqueEntries"],
              "dictionarySHA256": expected["sha256"],
              "cliSHA256": hashlib.sha256(cli.read_bytes()).hexdigest(),
              "isolatedTemporaryWorkspace": True, "compiledFiles": compiled, "cases": results}
    (args.evidence / "rime-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
