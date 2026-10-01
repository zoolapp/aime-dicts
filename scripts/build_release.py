#!/usr/bin/env python3
"""Build an offline dictionary release from one pinned Git commit (stdlib only)."""

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_FEEDS = 100
MAX_BYTES = 4 * 1024 * 1024
MAX_ROWS = 100_000
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
AUTHOR = "Luo Lei and contributors"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def git_bytes(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def read_blob(repo, revision, path):
    data = git_bytes(repo, "show", f"{revision}:{path}")
    if len(data) > MAX_BYTES:
        raise ValueError(f"source too large: {path}")
    return data


def parse_rows(data, path):
    rows, seen = [], set()
    for number, line in enumerate(data.decode("utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 3:
            raise ValueError(f"{path}:{number}: expected three columns")
        word, code, weight = fields
        if (not word or word != word.strip() or len(word) > 32
                or any(ord(c) < 32 for c in word)
                or not re.fullmatch(r"[a-z0-9]+(?: [a-z0-9]+)*", code)
                or not re.fullmatch(r"[0-9]{1,3}", weight)
                or not 1 <= int(weight) <= 100):
            raise ValueError(f"{path}:{number}: invalid word, code or weight")
        key = (word, code)
        if key in seen:
            raise ValueError(f"{path}:{number}: duplicate word/code")
        seen.add(key)
        rows.append((word, code, int(weight)))
        if len(rows) > MAX_ROWS:
            raise ValueError(f"too many rows: {path}")
    if not rows:
        raise ValueError(f"empty feed: {path}")
    return rows


def row_bytes(rows):
    return "".join(f"{word}\t{code}\t{weight}\n" for word, code, weight in rows).encode("utf-8")


def dictionary(name, version, revision, rows):
    header = (f"# AIME vocabulary; CC BY 4.0; {AUTHOR}\n"
              f"# Source commit: {revision}\n# License: {LICENSE_URL}\n"
              f"---\nname: {name}\nversion: {json.dumps(version)}\n"
              "sort: by_weight\nuse_preset_vocabulary: false\n...\n")
    return header.encode("utf-8") + row_bytes(rows)


def build(repo, revision, version, output, repository=None):
    if repository is not None and not re.fullmatch(r"https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9._-]+", repository):
        raise ValueError("repository must be a GitHub HTTPS repository URL")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", version):
        raise ValueError("version must be 1–64 safe ASCII characters")
    commit = git_bytes(repo, "rev-parse", "--verify", "--end-of-options",
                       revision + "^{commit}").decode().strip()
    index_data = read_blob(repo, commit, "index.json")
    index = json.loads(index_data)
    feeds = index.get("feeds")
    if not isinstance(feeds, list) or not 1 <= len(feeds) <= MAX_FEEDS:
        raise ValueError("catalog must contain 1–100 feeds")
    license_data = read_blob(repo, commit, "LICENSE")
    if LICENSE_URL not in license_data.decode() or AUTHOR not in license_data.decode():
        raise ValueError("source license/attribution requires review")
    files = {"LICENSE": license_data}
    source = {"commit": commit, "repository": repository, "publicationStatus": "public" if repository else "pending",
              "index": {"path": "index.json", "sha256": digest(index_data)}, "feeds": []}
    manifest = {"formatVersion": 1, "version": version, "sourceCommit": commit,
                "author": AUTHOR, "license": "CC-BY-4.0", "licenseURL": LICENSE_URL,
                "feeds": [], "mergePolicy": "same text/code: highest weight; first occurrence order"}
    combined, ids, total = {}, set(), 0
    for feed in feeds:
        if not isinstance(feed, dict):
            raise ValueError("feed must be an object")
        feed_id = feed.get("id")
        if not isinstance(feed_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", feed_id):
            raise ValueError("invalid feed id")
        if feed_id in ids:
            raise ValueError("duplicate feed id")
        ids.add(feed_id)
        path = f"feeds/{feed_id}.txt"
        if feed.get("path") != path:
            raise ValueError("feed path must match id under feeds/")
        if (not isinstance(feed.get("name"), str) or not feed["name"].strip()
                or len(feed["name"]) > 80 or any(ord(c) < 32 for c in feed["name"])):
            raise ValueError("feed name required")
        data = read_blob(repo, commit, path)
        if feed.get("sha256") is not None and feed["sha256"] != digest(data):
            raise ValueError(f"catalog checksum mismatch: {path}")
        if feed.get("size") is not None and feed["size"] != len(data):
            raise ValueError(f"catalog size mismatch: {path}")
        rows = parse_rows(data, path)
        if type(feed.get("entries")) is not int or feed["entries"] != len(rows):
            raise ValueError(f"catalog count mismatch: {path}")
        header = (f"# {feed['name']} — AIME {version}\n# {AUTHOR}; CC BY 4.0\n"
                  f"# License: {LICENSE_URL}\n# Source commit: {commit}\n")
        files[path] = header.encode("utf-8") + row_bytes(rows)
        name = "aime_" + feed_id.replace("-", "_")
        dict_path = f"rime/{name}.dict.yaml"
        files[dict_path] = dictionary(name, version, commit, rows)
        source["feeds"].append({"path": path, "sha256": digest(data)})
        manifest["feeds"].append({"id": feed_id, "name": feed["name"],
                                  "entries": len(rows), "textFile": path, "rimeFile": dict_path})
        total += len(rows)
        for word, code, weight in rows:
            key = (word, code)
            combined[key] = max(weight, combined.get(key, 0))
    merged = [(word, code, weight) for (word, code), weight in combined.items()]
    files["rime/aime_online.dict.yaml"] = dictionary("aime_online", version, commit, merged)
    manifest.update({"totalFeedEntries": total, "uniqueEntries": len(merged),
                     "mergedDuplicates": total - len(merged),
                     "combinedRimeFile": "rime/aime_online.dict.yaml"})
    files["SOURCE.json"] = json_bytes(source)
    files["ATTRIBUTION.txt"] = (
        f"AIME vocabulary {version}\nCopyright (c) 2026 {AUTHOR}\n"
        f"License: CC BY 4.0 — {LICENSE_URL}\nSource Git commit: {commit}\n"
        f"Public repository: {repository or 'pending company organization confirmation.'}\n"
        "Changes: normalized release headers; converted TXT rows to RIME dictionaries;\n"
        "combined dictionary merges equal text/code pairs using the highest weight.\n"
        "Individual feeds preserve all source rows and weights. Brand names do not imply endorsement.\n"
    ).encode("utf-8")
    manifest["files"] = [{"path": path, "bytes": len(data), "sha256": digest(data)}
                         for path, data in sorted(files.items())]
    files["manifest.json"] = json_bytes(manifest)
    files["SHA256SUMS"] = "".join(f"{digest(data)}  {path}\n" for path, data in sorted(files.items())).encode()
    output = Path(output)
    if output.exists():
        raise ValueError("output already exists; use a fresh directory")
    output.mkdir(parents=True)
    for path, data in sorted(files.items()):
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    archive = output / f"aime-vocabulary-{version}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as bundle:
        for path, data in sorted(files.items()):
            info = zipfile.ZipInfo(path, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data)
    sha = digest(archive.read_bytes())
    archive.with_suffix(".zip.sha256").write_text(f"{sha}  {archive.name}\n", encoding="utf-8")
    return {"archive": str(archive), "sha256": sha, "sourceCommit": commit,
            "totalFeedEntries": total, "uniqueEntries": len(merged)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository", help="Verified public GitHub source repository URL")
    args = parser.parse_args()
    try:
        print(json.dumps(build(ROOT, args.revision, args.version, args.output, args.repository), ensure_ascii=False, indent=2))
    except (ValueError, UnicodeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"release failed: {error}\n")


if __name__ == "__main__":
    main()
