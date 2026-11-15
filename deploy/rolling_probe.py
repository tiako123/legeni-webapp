import json, time, urllib.request, collections
c = collections.Counter()
fin = time.time() + 100
while time.time() < fin:
    try:
        r = urllib.request.urlopen("http://legeni-webapp/api/info", timeout=2)
        c[json.loads(r.read())["version"]] += 1
    except Exception:
        c["ERREUR"] += 1
    time.sleep(0.1)
print("RESULTAT", dict(c))
