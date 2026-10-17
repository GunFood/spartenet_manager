"""SparteNet Manager – QR-Code (ohne Zusatzpakete, nach ISO/IEC 18004)"""
from .plan import *  # noqa: F401,F403 – alle Namen der vorherigen Module


# =============================================================== QR-Code (ohne Zusatzpakete, nach ISO/IEC 18004)
_ECC_PRO_BLOCK = {  # Fehlerkorrektur-Codewörter je Block, Stufe M, Version 1–20
    "M": (-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26)}
_BLOECKE = {"M": (-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16)}


def _gf_mul(x, y):
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_divisor(grad):
    erg = [0] * (grad - 1) + [1]
    wurzel = 1
    for _ in range(grad):
        for j in range(grad):
            erg[j] = _gf_mul(erg[j], wurzel)
            if j + 1 < grad:
                erg[j] ^= erg[j + 1]
        wurzel = _gf_mul(wurzel, 0x02)
    return erg


def _rs_rest(daten, divisor):
    erg = [0] * len(divisor)
    for b in daten:
        f = b ^ erg.pop(0)
        erg.append(0)
        for i, c in enumerate(divisor):
            erg[i] ^= _gf_mul(c, f)
    return erg


def _roh_module(v):
    r = (16 * v + 128) * v + 64
    if v >= 2:
        n = v // 7 + 2
        r -= (25 * n - 10) * n - 55
        if v >= 7:
            r -= 36
    return r


def qr_matrix(text, ecl="M"):
    daten = text.encode("utf-8")
    for v in range(1, 21):
        nutz = _roh_module(v) // 8 - _ECC_PRO_BLOCK[ecl][v] * _BLOECKE[ecl][v]
        zbits = 8 if v <= 9 else 16
        if 4 + zbits + len(daten) * 8 <= nutz * 8:
            break
    else:
        raise ValueError("Text zu lang für QR-Code")
    bits = [0, 1, 0, 0] + [(len(daten) >> i) & 1 for i in reversed(range(zbits))]
    for b in daten:
        bits += [(b >> i) & 1 for i in reversed(range(8))]
    bits += [0] * min(4, nutz * 8 - len(bits))
    bits += [0] * (-len(bits) % 8)
    cw = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = 0xEC
    while len(cw) < nutz:
        cw.append(pad); pad ^= 0xEC ^ 0x11
    # Fehlerkorrektur und Verschachtelung
    nb, eccl = _BLOECKE[ecl][v], _ECC_PRO_BLOCK[ecl][v]
    roh = _roh_module(v) // 8
    kurz = nb - roh % nb
    kurzlen = roh // nb
    div = _rs_divisor(eccl)
    bloecke, k = [], 0
    for i in range(nb):
        dl = kurzlen - eccl + (0 if i < kurz else 1)
        dat = cw[k:k + dl]; k += dl
        ecc = _rs_rest(dat, div)
        if i < kurz:
            dat = dat + [0]
        bloecke.append(dat + ecc)
    folge = []
    for i in range(len(bloecke[0])):
        for j, blk in enumerate(bloecke):
            if i != kurzlen - eccl or j >= kurz:
                folge.append(blk[i])
    n = v * 4 + 17
    mod = [[False] * n for _ in range(n)]
    fkt = [[False] * n for _ in range(n)]

    def setze(x, y, w):
        mod[y][x] = w; fkt[y][x] = True
    for i in range(n):
        setze(6, i, i % 2 == 0); setze(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                x, y = cx + dx, cy + dy
                if 0 <= x < n and 0 <= y < n:
                    setze(x, y, max(abs(dx), abs(dy)) not in (2, 4))
    if v > 1:
        na = v // 7 + 2
        schritt = (v * 8 + na * 3 + 5) // (na * 4 - 4) * 2
        pos = [6] + sorted(n - 7 - i * schritt for i in range(na - 1))
        for i, a in enumerate(pos):
            for j, b in enumerate(pos):
                if (i == 0 and j == 0) or (i == 0 and j == na - 1) or (i == na - 1 and j == 0):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        setze(a + dx, b + dy, max(abs(dx), abs(dy)) != 1)

    def format_bits(maske):
        d = (0 << 3) | maske          # Stufe M = 00
        r = d
        for _ in range(10):
            r = (r << 1) ^ ((r >> 9) * 0x537)
        b = ((d << 10) | r) ^ 0x5412
        for i in range(6):
            setze(8, i, (b >> i) & 1)
        setze(8, 7, (b >> 6) & 1); setze(8, 8, (b >> 7) & 1); setze(7, 8, (b >> 8) & 1)
        for i in range(9, 15):
            setze(14 - i, 8, (b >> i) & 1)
        for i in range(8):
            setze(n - 1 - i, 8, (b >> i) & 1)
        for i in range(8, 15):
            setze(8, n - 15 + i, (b >> i) & 1)
        setze(8, n - 8, True)
    format_bits(0)
    if v >= 7:
        r = v
        for _ in range(12):
            r = (r << 1) ^ ((r >> 11) * 0x1F25)
        b = (v << 12) | r
        for i in range(18):
            w = (b >> i) & 1
            a, c = n - 11 + i % 3, i // 3
            setze(a, c, w); setze(c, a, w)
    i = 0
    rechts = n - 1
    while rechts >= 1:
        if rechts == 6:
            rechts = 5
        for vert in range(n):
            for j in range(2):
                x = rechts - j
                hoch = ((rechts + 1) & 2) == 0
                y = n - 1 - vert if hoch else vert
                if not fkt[y][x] and i < len(folge) * 8:
                    mod[y][x] = bool((folge[i >> 3] >> (7 - (i & 7))) & 1)
                    i += 1
        rechts -= 2
    masken = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0, lambda x, y: (x + y) % 3 == 0,
              lambda x, y: (x // 3 + y // 2) % 2 == 0, lambda x, y: x * y % 2 + x * y % 3 == 0,
              lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0, lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0]

    def anwenden(m):
        for y in range(n):
            for x in range(n):
                if not fkt[y][x] and masken[m](x, y):
                    mod[y][x] = not mod[y][x]

    def strafe():
        s = 0
        for zeilen in (mod, list(map(list, zip(*mod)))):
            for z in zeilen:
                lauf, farbe = 0, None
                for w in z:
                    if w == farbe:
                        lauf += 1
                    else:
                        if lauf >= 5:
                            s += 3 + lauf - 5
                        farbe, lauf = w, 1
                if lauf >= 5:
                    s += 3 + lauf - 5
        for y in range(n - 1):
            for x in range(n - 1):
                if mod[y][x] == mod[y][x + 1] == mod[y + 1][x] == mod[y + 1][x + 1]:
                    s += 3
        dunkel = sum(sum(z) for z in mod)
        s += abs(dunkel * 20 - n * n * 10) // (n * n) * 10
        return s
    beste, best_s = 0, None
    for m in range(8):
        anwenden(m); format_bits(m)
        p = strafe()
        if best_s is None or p < best_s:
            beste, best_s = m, p
        anwenden(m)
    anwenden(beste); format_bits(beste)
    return mod


def qr_svg(text, rand=4, farbe="#000000", hintergrund="#ffffff"):
    m = qr_matrix(text)
    n = len(m) + 2 * rand
    pfad = "".join(f"M{x + rand},{y + rand}h1v1h-1z" for y, z in enumerate(m) for x, w in enumerate(z) if w)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges">'
            f'<rect width="{n}" height="{n}" fill="{hintergrund}"/><path d="{pfad}" fill="{farbe}"/></svg>')


def qr_kontrast_ok(farbe, hintergrund):
    hell = lambda c: (0.2126 * int(c[1:3], 16) + 0.7152 * int(c[3:5], 16) + 0.0722 * int(c[5:7], 16)) / 255
    return hell(hintergrund) - hell(farbe) >= 0.45


def wlan_qr_text(ssid, pw):
    esc = lambda s: re.sub(r'([\\;,:"])', r"\\\1", s)
    if not pw:   # offenes Netz (Gast-WLAN mit Voucher-Anmeldung)
        return f"WIFI:T:nopass;S:{esc(ssid)};;"
    return f"WIFI:T:WPA;S:{esc(ssid)};P:{esc(pw)};;"

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
