"""Fetch two individually reviewed CC0 model sources, never a complete donor pack.

Sources stay outside public/. Blender processing and runtime placement are separate.
Run: python3 scripts/import-world-reference.py
"""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
import json
import urllib.request

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/reference/world-dressing"
ASSETS = ("fern_02", "planter_pot_clay")
ALLOWED_HOSTS = {"api.polyhaven.com", "polyhaven.com", "dl.polyhaven.org"}
USER_AGENT = "ONSITE-individual-CC0-model-import/1.0"
SUPPLEMENTAL = {
    "fern_02": {
        "textures/fern_02_alpha_1k.png": ("Alpha", "1k", "png"),
    }
}


def fetch(url):
    parsed = urlparse(url)
    assert parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS, url
    assert parsed.username is None and parsed.password is None, url
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        final = urlparse(response.url)
        assert final.scheme == "https" and final.hostname in ALLOWED_HOSTS, response.url
        body = response.read(32 * 1024 * 1024 + 1)
        assert len(body) <= 32 * 1024 * 1024, "Unexpectedly large source"
        return body, {
            "url": url,
            "finalURL": response.url,
            "contentType": response.headers.get("Content-Type"),
            "bytes": len(body),
            "sha256": sha256(body).hexdigest(),
        }


def write_exact(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, f"Preserve changed source: {path}"
    else:
        path.write_bytes(data)


def safe_relative(value):
    path = PurePosixPath(value)
    assert not path.is_absolute() and ".." not in path.parts and ":" not in value, value
    assert "\\" not in value, value
    return path


def append_supplemental(name, directory, source_files, records):
    for relative, selectors in SUPPLEMENTAL.get(name, {}).items():
        if any(item["path"] == relative for item in records):
            continue
        item = source_files
        for selector in selectors:
            item = item[selector]
        data, receipt = fetch(item["url"])
        assert len(data) == item["size"]
        destination = directory / safe_relative(relative)
        write_exact(destination, data)
        with Image.open(destination) as image:
            receipt["dimensions"] = list(image.size)
            receipt["mode"] = image.mode
            image.verify()
        records.append({
            "path": relative,
            **receipt,
            "purpose": "Original upstream opacity mask. The glTF base-colour JPEG has no alpha despite MASK material; combine only in a separate Blender/runtime derivative.",
        })


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "source-manifest.json"
    if manifest_path.exists():
        saved = json.loads(manifest_path.read_text())
        assert tuple(asset["id"] for asset in saved["assets"]) == ASSETS
        for asset in saved["assets"]:
            for item in asset["files"]:
                local = OUT / asset["id"] / safe_relative(item["path"])
                data = local.read_bytes()
                assert len(data) == item["bytes"] and sha256(data).hexdigest() == item["sha256"], local
            for filename, key in (("upstream-info.json", "sourceMetadata"),
                                  ("upstream-files.json", "sourceFileAPI")):
                local = OUT / asset["id"] / filename
                data, expected = local.read_bytes(), asset[key]
                assert len(data) == expected["bytes"] and sha256(data).hexdigest() == expected["sha256"], local
        assert sha256((OUT / "polyhaven-license.html").read_bytes()).hexdigest() == saved["licenceEvidence"]["snapshotSHA256"]
        changed = False
        for asset in saved["assets"]:
            directory = OUT / asset["id"]
            before = len(asset["files"])
            append_supplemental(asset["id"], directory,
                                json.loads((directory / "upstream-files.json").read_text()),
                                asset["files"])
            if len(asset["files"]) != before:
                changed = True
                asset["totalSourceBytes"] = sum(item["bytes"] for item in asset["files"])
        if changed:
            saved["supplementalCheckedUTC"] = datetime.now(timezone.utc).isoformat()
            manifest_path.write_text(json.dumps(saved, indent=2) + "\n")
        print("Existing pinned sources verified; required opacity supplement present. No original overwritten.")
        return
    licence, licence_receipt = fetch("https://polyhaven.com/license")
    assert b"Our assets are all licensed as" in licence and b"CC0" in licence
    # The live page includes changing build data. Preserve the first checked snapshot.
    licence_path = OUT / "polyhaven-license.html"
    if not licence_path.exists():
        licence_path.write_bytes(licence)
    licence_receipt["snapshotPath"] = str(licence_path.relative_to(ROOT))
    licence_receipt["snapshotSHA256"] = sha256(licence_path.read_bytes()).hexdigest()
    records = []
    for name in ASSETS:
        directory = OUT / name
        info_bytes, info_receipt = fetch(f"https://api.polyhaven.com/info/{name}")
        files_bytes, files_receipt = fetch(f"https://api.polyhaven.com/files/{name}")
        info, files = json.loads(info_bytes), json.loads(files_bytes)
        source = files["gltf"]["1k"]["gltf"]
        model_name = f"{name}_1k.gltf"
        model_bytes, model_receipt = fetch(source["url"])
        assert len(model_bytes) == source["size"], name
        model = json.loads(model_bytes)
        includes = source["include"]
        uris = {item["uri"] for key in ("buffers", "images")
                for item in model.get(key, []) if "uri" in item}
        assert all(not uri.startswith("data:") for uri in uris), name
        assert uris == set(includes), (name, "unrecorded or unused dependencies", uris)
        records_for_asset = [{"path": model_name, **model_receipt}]
        write_exact(directory / model_name, model_bytes)
        for rel, item in includes.items():
            relative = safe_relative(rel)
            data, receipt = fetch(item["url"])
            assert len(data) == item["size"], (name, rel, "size mismatch")
            destination = directory.joinpath(*relative.parts)
            write_exact(destination, data)
            if destination.suffix.lower() in (".jpg", ".jpeg", ".png"):
                with Image.open(destination) as image:
                    dimensions = list(image.size)
                    image.verify()
                receipt["dimensions"] = dimensions
            records_for_asset.append({"path": rel, **receipt})
        append_supplemental(name, directory, files, records_for_asset)
        for buffer in model.get("buffers", []):
            assert (directory / buffer["uri"]).stat().st_size == buffer["byteLength"]
        write_exact(directory / "upstream-info.json", info_bytes)
        write_exact(directory / "upstream-files.json", files_bytes)
        records.append({
            "id": name,
            "name": info["name"],
            "authors": info["authors"],
            "source": f"https://polyhaven.com/a/{name}",
            "licence": "CC0-1.0",
            "licenceURL": "https://polyhaven.com/license",
            "licenceTextURL": "https://creativecommons.org/publicdomain/zero/1.0/legalcode",
            "resolution": "1k",
            "localSource": str((directory / model_name).relative_to(ROOT)),
            "modifications": "None. Exact original glTF, buffers and image bytes.",
            "runtimeImport": False,
            "originalCatalogueDimensionsMillimetres": info.get("dimensions"),
            "originalCataloguePolygonCount": info.get("polycount"),
            "actualGLTFTriangles": sum(
                model["accessors"][p["indices"]]["count"] // 3
                for mesh in model["meshes"] for p in mesh["primitives"]
            ),
            "sourceMetadata": info_receipt,
            "sourceFileAPI": files_receipt,
            "files": records_for_asset,
            "totalSourceBytes": sum(f["bytes"] for f in records_for_asset),
        })
    manifest = {
        "checkedUTC": datetime.now(timezone.utc).isoformat(),
        "scope": "Two original CC0 model sources for selective Blender processing; not runtime delivery.",
        "licenceEvidence": licence_receipt,
        "assets": records,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({r["id"]: {"bytes": r["totalSourceBytes"],
                              "triangles": r["actualGLTFTriangles"]}
                      for r in records}, indent=2))


if __name__ == "__main__":
    main()
