import json, time, urllib.request, collections
c = collections.Counter()
t0 = time.time()
errs = []
started = False
fin = t0 + 110
while time.time() < fin:
    try:
        r = urllib.request.urlopen("http://legeni-webapp/api/info", timeout=2)
        started = True
        c[json.loads(r.read())["version"]] += 1
    except Exception as e:
        if started:
            c["ERREUR"] += 1
            errs.append((round(time.time() - t0, 1), type(e).__name__))
    time.sleep(0.1)
print("RESULTAT", dict(c))
print("ERREURS (secondes, type)", errs)
