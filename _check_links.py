"""Static check: every internal link target of the frontend must match a declared route; every API path used by the
frontend must exist (same method) in the backend OpenAPI."""
import json, re, urllib.request
from pathlib import Path

SRC = Path("../frontend/src")
app = (SRC / "App.tsx").read_text(encoding="utf-8")

# ---- routes declared in App.tsx (nested routes are resolved against their parent path); one <Route> per line
routes, stack = set(), []
for line in app.splitlines():
    t = line.strip()
    if t.startswith("</Route>"):
        stack.pop()
        continue
    if not t.startswith("<Route"):
        continue
    selfclose = t.endswith("/>")
    p = re.search(r'path="([^"]*)"', t)
    idx = bool(re.search(r"<Route\s+index\b", t))
    base = stack[-1] if stack else ""
    full = base
    if p:
        full = p.group(1) if p.group(1).startswith("/") else (base.rstrip("/") + "/" + p.group(1))
    if p or idx:
        routes.add(full or "/")
    if not selfclose:
        stack.append(full)
routes = {r for r in routes if r != ""}
print(f"{len(routes)} routes déclarées :", ", ".join(sorted(routes)))


def matches(target: str) -> bool:
    t = target.split("?")[0].split("#")[0].rstrip("/") or "/"
    for r in routes:
        rx = "^" + re.sub(r":[^/]+", "[^/]+", r.rstrip("/") or "/") + "$"
        if re.match(rx, t):
            return True
    return False


# ---- internal link targets
found = {}
patterns = [
    r'\bto=(?:"|\{[`"\'])(/[^"`\'}]*)',            # <Link to="/x"> / to={`/x`}
    r'\b(?:nav|navigate)\(\s*[`"\'](/[^"`\']*)',    # nav("/x")
    r'\bhref=(?:"|\{[`"\'])(/[^"`\'}]*)',
    r'\bto:\s*[`"\'](/[^"`\']*)',                    # tab definitions { to: "/x" }
    r'\bpath:\s*[`"\'](/[^"`\']*)',
    r'return\s+[`"\'](/[^"`\']*)[`"\']',             # homeFor() style
    r':\s*[`"\'](/(?:espace|equipe|admin|direction|formations|connexion|inscription|recuperation|comparaison)[^"`\']*)[`"\']',
]
for f in SRC.rglob("*.ts*"):
    txt = f.read_text(encoding="utf-8")
    for pat in patterns:
        for m in re.finditer(pat, txt):
            tgt = m.group(1)
            if tgt.startswith("/api"):
                continue
            found.setdefault(tgt, set()).add(f.relative_to(SRC).as_posix())

bad = {}
for tgt, files in sorted(found.items()):
    probe = re.sub(r"\$\{[^}]*\}", "1", tgt)  # template parts -> an id
    if not matches(probe):
        bad[tgt] = sorted(files)
print(f"{len(found)} cibles de liens internes trouvées dans le code")
for t, fs in bad.items():
    print("  LIEN SANS ROUTE :", t, "<-", ", ".join(fs))
if not bad:
    print("  OK : toutes les cibles correspondent à une route déclarée")

# ---- external links
ext = {}
for f in SRC.rglob("*.ts*"):
    for m in re.finditer(r'(?:href|src)=["\'](https?://[^"\']+)', f.read_text(encoding="utf-8")):
        ext.setdefault(m.group(1), set()).add(f.name)
print(f"{len(ext)} liens externes dans le code")
for u, fs in ext.items():
    print("  externe :", u, "<-", ", ".join(sorted(fs)))

# ---- API paths used by api.ts vs backend OpenAPI
spec = json.load(urllib.request.urlopen("http://localhost:8000/openapi.json", timeout=20))
ops = {(m.upper(), re.sub(r"\{[^}]+\}", "{}", p)) for p, v in spec["paths"].items() for m in v}
api = (SRC / "lib" / "api.ts").read_text(encoding="utf-8")
missing, count = [], 0
for m in re.finditer(r'request(?:<[^()]*?>)?\(\s*([`"\'])(/[^`"\']*)\1\s*(?:,\s*([^)]*))?\)', api):
    path = re.sub(r"\$\{[^}]*\}", "{}", m.group(2)).split("?")[0]
    rest = m.group(3) or ""
    jm = re.search(r'json\("(\w+)"', rest) or re.search(r'method:\s*"(\w+)"', rest)
    method = jm.group(1) if jm else "GET"
    count += 1
    if (method, "/api" + path.rstrip("/")) not in ops and (method, "/api" + path) not in ops and (method, path.rstrip("/")) not in ops:
        missing.append((method, path))
# generic catalogue helpers use /${resource}: check them for every real resource
RES = ["programs", "specialties", "curricula", "subjects", "admission-conditions", "fees", "payment-terms"]
OFFICIAL = ["admission-conditions", "fees", "payment-terms"]
generic = {("GET", "/{}"): [("GET", f"/{r}") for r in RES], ("POST", "/{}"): [("POST", f"/{r}") for r in RES],
           ("PATCH", "/{}/{}"): [("PATCH", f"/{r}/{{}}") for r in RES], ("DELETE", "/{}/{}"): [("DELETE", f"/{r}/{{}}") for r in RES],
           ("POST", "/{}/{}/{}"): [("POST", f"/{r}/{{}}/{a}") for r in OFFICIAL for a in ("publish", "archive", "draft")]}
still = []
for key in list(missing):
    if key in generic:
        missing.remove(key)
        count += len(generic[key]) - 1
        still += [c for c in generic[key] if (c[0], "/api" + c[1]) not in ops]
missing += still
print(f"{count} appels API analysés dans api.ts")
for mth, p in missing:
    print("  APPEL SANS ENDPOINT :", mth, p)
if not missing:
    print("  OK : chaque appel a un endpoint correspondant dans l'API")
