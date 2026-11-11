#!/usr/bin/env python3
"""Refresh data/versions.json for every tool in data/catalogue.json.
Stdlib only. Sources: GitHub releases/tags Atom feeds (no API rate limit),
GitHub commits Atom (activity), bioconda via api.anaconda.org.
Run from the repo root:  python3 scripts/update_versions.py
"""
import json, re, sys, time, urllib.request, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

UA = {"User-Agent": "seqtools-catalogue-updater"}
A = "{http://www.w3.org/2005/Atom}"

def get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def atom_entries(url, skip_pre=True):
    try:
        root = ET.fromstring(get(url))
    except Exception:
        return []
    out = []
    for e in root.findall(A + "entry"):
        title = (e.findtext(A + "title") or "").strip()
        link = e.find(A + "link")
        href = link.get("href") if link is not None else ""
        tag = href.rstrip("/").split("/")[-1] if "/releases/tag/" in href or "/tree/" in href else title
        if skip_pre and re.search(r"(alpha|beta|rc\d*|dev|pre|nightly|latest)", tag, re.I):
            continue
        out.append({"version": tag, "title": title, "date": (e.findtext(A + "updated") or "")[:10], "href": href})
    return out

def vkey(v):
    """Sortable key from a messy tag: metaMDBG-1.4, quast_5.3.0, 8-0-4, v2.1.2."""
    v = norm(v)
    if re.fullmatch(r"\d+(-\d+)+", v): v = v.replace("-", ".")
    return tuple(int(x) for x in re.findall(r"\d+", v)[:4]) or (-1,)

def atom_first(url, skip_pre=True):
    e = atom_entries(url, skip_pre)
    return e[0] if e else None

def github(repo):
    out = {}
    # releases are not always created in version order (e.g. backported patches),
    # so take the highest version among recent releases, falling back to tags
    cands = [dict(c, kind="release") for c in atom_entries(f"https://github.com/{repo}/releases.atom")]
    if not cands:
        cands = [dict(c, kind="tag") for c in atom_entries(f"https://github.com/{repo}/tags.atom")]
    if cands:
        out["github"] = max(cands, key=lambda c: vkey(c["version"]))
    com = atom_first(f"https://github.com/{repo}/commits.atom", skip_pre=False)
    if com: out["last_commit"] = com["date"]
    return out

def bioconda(pkg):
    try:
        d = json.loads(get(f"https://api.anaconda.org/package/bioconda/{pkg}"))
    except Exception:
        return {}
    v = d.get("latest_version")
    dates = [f.get("upload_time", "")[:10] for f in d.get("files", []) if f.get("version") == v]
    return {"bioconda": {"version": v, "date": min(dates) if dates else ""}}

def norm(v):
    v = (v or "").strip()
    v = re.sub(r"^[^\d]*(?=\d)", "", v)           # drop any prefix before the first digit
    if re.fullmatch(r"\d+(-\d+)+", v): v = v.replace("-", ".")
    return v

def one(t):
    r = {}
    if t.get("repo"): r.update(github(t["repo"]))
    if t.get("bioconda"): r.update(bioconda(t["bioconda"]))
    gh, bc = r.get("github"), r.get("bioconda")
    # prefer GitHub release; use bioconda when it is newer or GitHub is a side crate (e.g. sourmash r0.x)
    if gh and bc and bc.get("version") and vkey(bc["version"]) > vkey(gh["version"]) and t.get("prefer") != "github":
        gh = None
    if gh and gh.get("version"):
        r["version"], r["date"], r["source"] = norm(gh["version"]), gh["date"], "github " + gh.get("kind", "")
    elif bc and bc.get("version"):
        r["version"], r["date"], r["source"] = bc["version"], bc["date"], "bioconda"
    return t["id"], r

def main():
    cat = json.load(open("data/catalogue.json"))
    with ThreadPoolExecutor(8) as ex:
        res = dict(ex.map(one, cat["tools"]))
    missing = [k for k, v in res.items() if not v.get("version")]
    out = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "tools": res}
    json.dump(out, open("data/versions.json", "w"), indent=1)
    print(f"{len(res)-len(missing)}/{len(res)} versioned; no version: {', '.join(missing) or '-'}")

if __name__ == "__main__":
    main()
