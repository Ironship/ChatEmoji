"""Builds the release ZIP and installs the addon into a game folder.

    python tools/package.py --zip dist                 ChatEmoji-<version>.zip + .sha256 in dist/
    python tools/package.py --install <AddOns\\ChatEmoji>   copy the shipped files, drop stale ones
    python tools/package.py --check                    list what ships and check the TOC

What ships is every file in the repository except the `ignore:` entries of .pkgmeta (the same file
the CurseForge packager reads), so the ZIP matches what CurseForge builds. The ZIP is reproducible:
sorted names, fixed timestamps (the last commit time), LF files from a clean tree.
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALWAYS_IGNORED = {".git", ".pkgmeta", "dist"}


def ignored():
    names = set(ALWAYS_IGNORED)
    path = os.path.join(ROOT, ".pkgmeta")
    section = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip()
        if re.match(r"^\S.*:$", line):
            section = line[:-1]
        elif section == "ignore" and line.strip().startswith("- "):
            names.add(line.strip()[2:].strip())
    return names


def shipped_files():
    skip = ignored()
    files = []
    for base, dirs, names in os.walk(ROOT):
        rel_base = os.path.relpath(base, ROOT).replace("\\", "/")
        rel_base = "" if rel_base == "." else rel_base
        dirs[:] = sorted(d for d in dirs if (rel_base + "/" + d).lstrip("/") not in skip)
        for name in sorted(names):
            rel = (rel_base + "/" + name).lstrip("/")
            if rel not in skip:
                files.append(rel)
    return sorted(files)


def toc_info():
    text = open(os.path.join(ROOT, "ChatEmoji.toc"), encoding="utf-8").read()
    version = re.search(r"^## Version:\s*(\S+)", text, re.M).group(1)
    interfaces = re.search(r"^## Interface:\s*(.+)$", text, re.M).group(1)
    listed = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
    return version, [i.strip() for i in interfaces.split(",")], listed


def check():
    version, interfaces, listed = toc_info()
    files = set(shipped_files())
    problems = []
    for f in listed:
        if f not in files:
            problems.append("TOC lists %s, which does not ship" % f)
    for i in interfaces:
        if not re.fullmatch(r"\d{5,6}", i):
            problems.append("bad Interface number %r" % i)
    top = re.search(r"^## (\S+)", open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read(), re.M)
    if not top or top.group(1) != version:
        problems.append("CHANGELOG.md top entry %r does not match TOC version %s" % (top and top.group(1), version))
    for p in problems:
        print("PROBLEM:", p)
    print("version %s, interfaces %s, %d files ship" % (version, ", ".join(interfaces), len(files)))
    return 1 if problems else 0


def commit_time():
    env = os.environ.get("SOURCE_DATE_EPOCH")
    if env:
        return int(env)
    out = subprocess.run(["git", "log", "-1", "--format=%ct"], cwd=ROOT, capture_output=True, text=True)
    return int(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip() else 315532800


def build_zip(outdir, allow_dirty):
    version, _, _ = toc_info()
    if not allow_dirty:
        st = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
        if st.stdout.strip():
            sys.exit("working tree is not clean (use --allow-dirty to build anyway):\n" + st.stdout)
    import time
    t = time.gmtime(max(commit_time(), 315532800))[:6]
    os.makedirs(outdir, exist_ok=True)
    name = "ChatEmoji-%s.zip" % version
    path = os.path.join(outdir, name)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in shipped_files():
            info = zipfile.ZipInfo("ChatEmoji/" + rel, date_time=t)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, open(os.path.join(ROOT, rel), "rb").read())
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    with open(path + ".sha256", "w", newline="\n") as f:  # LF, so `sha256sum -c` works everywhere
        f.write("%s  %s\n" % (digest, name))
    print(path, digest)


def install(dest):
    files = shipped_files()
    os.makedirs(dest, exist_ok=True)
    keep = set(files)
    for base, dirs, names in os.walk(dest, topdown=False):
        for n in names:
            rel = os.path.relpath(os.path.join(base, n), dest).replace("\\", "/")
            if rel not in keep:
                os.remove(os.path.join(base, n))
        if base != dest and not os.listdir(base):
            os.rmdir(base)
    for rel in files:
        target = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        src = os.path.join(ROOT, rel)
        if not os.path.exists(target) or open(src, "rb").read() != open(target, "rb").read():
            shutil.copyfile(src, target)
    print("%d files in %s" % (len(files), dest))
    print("toc files:", [f for f in os.listdir(dest) if f.endswith(".toc")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", metavar="DIR")
    ap.add_argument("--install", metavar="DIR")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--allow-dirty", action="store_true")
    a = ap.parse_args()
    if a.check:
        sys.exit(check())
    if a.zip:
        if check():
            sys.exit(1)
        build_zip(a.zip, a.allow_dirty)
    if a.install:
        install(a.install)


if __name__ == "__main__":
    main()
