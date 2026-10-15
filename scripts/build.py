#!/usr/bin/env python3
"""Monta o vídeo (HTML do HyperFrames) a partir do projeto.

Uso: python3 build.py <projeto> [--guias]

Lê no projeto: roteiro.md, cenas.json, timing.json (voice.py), words.json (transcribe.py),
audio/mix.wav (music.py) e assets/avatar_intro.mp4 + assets/avatar_final.mp4 (avatar.py).
Gera <projeto>/index.html, hyperframes.json e package.json — pronto para `npx hyperframes render`.

--guias desenha a zona segura por cima (verde = conteúdo, azul = legenda, vermelho = interface dos apps).
Formato do cenas.json: references/cenas.md.
"""
import difflib
import html
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import SKILL_DIR, die, duration, load_config, read_script  # noqa: E402

HF_VERSION = "0.8.159"
THEMES = ("moderno", "caderno", "cinematico")
HL = {"caderno": ("#FFD84D", "#ffffff"), "cinematico": ("rgba(255,210,74,.22)", "rgba(12,18,34,.85)"),
      "moderno": ("rgba(124,58,237,.55)", "rgba(255,255,255,.06)")}
GX, GY = 1280, 2120          # espaçamento das cenas no mapa
WARN = []


# ======================= texto e tempos =======================
def norm(s):
    return re.sub(r"[^\w]", "", s.lower())


def md(s):
    """*palavra* → destaque na cor de acento; resto escapado."""
    return re.sub(r"\*(.+?)\*", r'<span class="a">\1</span>', html.escape(s))


def align(text, words, a, b):
    """Dá tempo a cada palavra do ROTEIRO usando as palavras do whisper na janela [a, b]."""
    toks = text.split()
    ws = [w for w in words if a - 0.3 <= w["s"] <= b + 0.3]
    sm = difflib.SequenceMatcher(None, [norm(t) for t in toks], [norm(w["w"]) for w in ws], autojunk=False)
    times = [None] * len(toks)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            w = ws[blk.b + k]
            times[blk.a + k] = (w["s"], w["e"])
    # palavras sem par (ex.: "três" falado vs "3" transcrito): interpola entre vizinhos
    i = 0
    while i < len(toks):
        if times[i] is None:
            j = i
            while j < len(toks) and times[j] is None:
                j += 1
            t0 = times[i - 1][1] if i > 0 else a
            t1 = times[j][0] if j < len(toks) else b
            step = max(0.05, (t1 - t0) / (j - i + 1))
            for k in range(i, j):
                s = t0 + step * (k - i + 0.5)
                times[k] = (s, s + step * 0.9)
            i = j
        else:
            i += 1
    return [{"w": t, "n": norm(t), "s": round(s, 3), "e": round(e, 3)} for t, (s, e) in zip(toks, times)]


class Anchors:
    def __init__(self, toks):
        self.toks = toks

    def at(self, spec, after=0.0, default=None):
        """'frase' (primeira ocorrência depois de `after`), 'frase+0.3', ou número em segundos."""
        if spec is None:
            return default
        if isinstance(spec, (int, float)):
            return float(spec)
        m = re.match(r"^(.*?)([+-]\d+(?:\.\d+)?)?$", str(spec).strip())
        phrase, off = m.group(1).strip(), float(m.group(2) or 0)
        target = [norm(x) for x in phrase.split() if norm(x)]
        if not target:
            return default
        T = self.toks
        for i in range(len(T)):
            if T[i]["s"] >= after - 0.05 and [t["n"] for t in T[i:i + len(target)]] == target:
                return round(T[i]["s"] + off, 3)
        WARN.append(f"âncora não encontrada: '{phrase}' (depois de {after:.1f}s)")
        return default


# ======================= cenas =======================
class Scene:
    def __init__(self, i, data, t0, t1, A, theme):
        self.i, self.d, self.t0, self.t1, self.A, self.theme = i, data, t0, t1, A, theme
        self.html, self.steps, self.k = [], [], 0

    def id(self, name):
        return f"c{self.i}-{name}"

    def t(self, spec, gap=0.4):
        """Tempo de uma âncora dentro da cena (ou um padrão escalonado se não houver)."""
        self.k += 1
        dflt = self.t0 + 0.5 + gap * (self.k - 1)
        v = self.A.at(spec, self.t0 - 0.2, dflt) if spec is not None else dflt
        return round(min(max(v, self.t0 + 0.2), self.t1 - 0.3), 3)

    def step(self, kind, sel, t, **kw):
        self.steps.append({"k": kind, "s": sel, "t": t, **kw})

    def add(self, s):
        self.html.append(s)

    # --- blocos comuns ---
    def header(self, top_no_num=300):
        d = self.d
        top = top_no_num
        if d.get("numero"):
            self.add(f'<div class="num" id="{self.id("n")}">{html.escape(str(d["numero"]))}</div>')
            self.step("pop", "#" + self.id("n"), round(self.t0 + 0.3, 3))
            top = 420
        if d.get("titulo"):
            self.add(f'<div class="title" id="{self.id("t")}" style="top:{top}px">{md(d["titulo"])}</div>')
            self.step("wipe", "#" + self.id("t"), self.t(d.get("titulo_em")))

    def stamps_side(self, items, tops=(860, 1020)):
        for j, c in enumerate((items or [])[:2]):
            sid = self.id(f"st{j}")
            cls = {"2": " c2", "3": " c3"}.get(str(c.get("cor", "")), "")
            self.add(f'<div class="stamp side-stamp{cls}" id="{sid}" style="top:{tops[j]}px">{html.escape(c["texto"])}</div>')
            self.step("stamp", "#" + sid, self.t(c.get("em")), rot=[4, -3][j])

    def stamp_center(self, c, top=1080):
        if not c:
            return
        sid = self.id("stc")
        cls = {"2": " c2", "3": " c3"}.get(str(c.get("cor", "")), "")
        self.add(f'<div class="stamps" style="top:{top}px"><div class="stamp{cls}" id="{sid}">{html.escape(c["texto"])}</div></div>')
        self.step("stamp", "#" + sid, self.t(c.get("em")), rot=-4)

    def chips(self, items, top):
        if not items:
            return
        inner = ""
        for j, c in enumerate(items):
            cid = self.id(f"ch{j}")
            style = f' style="background:{c["cor"]};color:#fff"' if c.get("cor") else ""
            inner += f'<span class="chip" id="{cid}"{style}>{html.escape(c["texto"])}</span>'
            self.step("pop", "#" + cid, self.t(c.get("em")))
        self.add(f'<div class="chips" style="top:{top}px">{inner}</div>')

    # --- tipos ---
    def r_abertura(self):
        d = self.d
        if d.get("icone"):
            self.add(f'<img class="ab-icon" id="{self.id("ic")}" src="{d["icone"]}" alt="" />')
            self.step("pop", "#" + self.id("ic"), self.t(d.get("icone_em")), d=.55)
        if d.get("imagem"):
            self.add(f'<img class="ab-img" id="{self.id("im")}" src="{d["imagem"]}" alt="" />')
            self.step("wipe", "#" + self.id("im"), self.t(d.get("imagem_em")))
        elif d.get("titulo"):
            self.add(f'<div class="title" id="{self.id("t")}" style="top:600px;text-align:center">{md(d["titulo"])}</div>')
            self.step("wipe", "#" + self.id("t"), self.t(d.get("titulo_em")))
        if d.get("kicker"):
            self.add(f'<div class="ab-kick kick" id="{self.id("k")}">{html.escape(d["kicker"])}</div>')
            self.step("rise", "#" + self.id("k"), self.t(d.get("kicker_em")))
        if d.get("carimbos"):
            inner = ""
            for j, c in enumerate(d["carimbos"][:3]):
                sid = self.id(f"s{j}")
                cls = ["", " c2", " c3"][j]
                inner += f'<div class="stamp{cls}" id="{sid}">{html.escape(c["texto"])}</div>'
                self.step("stamp", "#" + sid, self.t(c.get("em")), rot=[-5, 3, -2][j])
            self.add(f'<div class="stamps" style="top:860px">{inner}</div>')
        if d.get("nota"):
            self.add(f'<div class="ab-note" id="{self.id("nt")}">{html.escape(d["nota"]["texto"])}</div>')
            self.step("wipe", "#" + self.id("nt"), self.t(d["nota"].get("em")))

    def r_passos(self):
        d = self.d
        self.header()
        ps = d.get("passos", [])[:3]
        inner = ""
        for j, p in enumerate(ps):
            if j:
                inner += f'<div class="fa" id="{self.id(f"a{j}")}"></div>'
            hl = ' style="background:var(--hl);color:#141414"' if j == len(ps) - 1 else ""
            inner += f'<div class="fb" id="{self.id(f"p{j}")}"{hl}>{html.escape(p["texto"])}</div>'
            t = self.t(p.get("em"))
            if j:
                self.step("fill", "#" + self.id(f"a{j}"), round(t - 0.2, 3), d=.3)
            self.step("pop", "#" + self.id(f"p{j}"), t)
        self.add(f'<div class="flow">{inner}</div>')
        n = d.get("nota")
        if n:
            lines = "".join(f'<div class="ln mono" id="{self.id(f"l{j}")}">{html.escape(x)}</div>' for j, x in enumerate(n.get("linhas", [])[:4]))
            self.add(f'<div class="box note" id="{self.id("nb")}"><div class="h mono">{html.escape(n.get("titulo", ""))}</div>{lines}</div>')
            t = self.t(n.get("em"))
            self.step("slide", "#" + self.id("nb"), t)
            for j in range(len(n.get("linhas", [])[:4])):
                self.step("slide", "#" + self.id(f"l{j}"), round(t + 0.4 + 0.45 * j, 3), dx=-30)
        self.stamps_side(d.get("carimbos"))

    def r_busca(self):
        d = self.d
        self.header()
        b = d.get("busca")
        if b:
            self.add(f'<div class="box search" id="{self.id("q")}"><b></b><span class="mono" id="{self.id("qt")}"></span></div>')
            t = self.t(b.get("em"))
            self.step("rise", "#" + self.id("q"), t)
            self.step("type", "#" + self.id("qt"), round(t + 0.4, 3), text=b["texto"], d=1.4)
        for j, c in enumerate(d.get("cartoes", [])[:3]):
            cid = self.id(f"c{j}")
            self.add(f'<div class="box card" id="{cid}" style="top:{790 + 110 * j}px">{html.escape(c["texto"])}<span>{html.escape(c.get("meta", ""))}</span></div>')
            self.step("slide", "#" + cid, self.t(c.get("em"), 0.2), dx=140)
            if c.get("destaque_em"):
                self.step("hl", "#" + cid, self.t(c["destaque_em"]), c=HL[self.theme][0])
        self.chips(d.get("chips"), 1115)

    def r_comparar(self):
        d = self.d
        self.header()
        for side, left in (("esquerda", 100), ("direita", 540)):
            c = d.get(side)
            if not c:
                continue
            cid = self.id(side)
            self.add(f'<div class="box cmp" id="{cid}" style="left:{left}px"><div class="ic">{html.escape(c.get("icone", ""))}</div><div class="lb">{html.escape(c.get("rotulo", ""))}</div></div>')
            self.step("rise", "#" + cid, self.t(c.get("em")))
            if c.get("apagar_em"):
                self.step("dim", "#" + cid, self.t(c["apagar_em"]))
        self.chips(d.get("chips"), 930)
        au = d.get("audio")
        if au:
            bars = "".join("<b></b>" for _ in range(14))
            log = "".join(f'<div id="{self.id(f"lg{j}")}">{html.escape(x["texto"])}</div>' for j, x in enumerate(au.get("linhas", [])[:2]))
            self.add(f'<div class="box voice" id="{self.id("v")}"><div class="vn" id="{self.id("vn")}">{bars}</div><div class="vlog mono">{log}</div></div>')
            t = self.t(au.get("em"))
            self.step("slide", "#" + self.id("v"), t)
            self.step("wave", f'#{self.id("vn")} b', round(t + 0.3, 3))
            for j, x in enumerate(au.get("linhas", [])[:2]):
                self.step("fadein", "#" + self.id(f"lg{j}"), self.t(x.get("em")))

    def r_lista(self):
        d = self.d
        if d.get("titulo"):
            self.add(f'<div class="title" id="{self.id("t")}" style="top:300px;font-size:96px">{md(d["titulo"])}</div>')
            self.step("wipe", "#" + self.id("t"), self.t(d.get("titulo_em")))
        for j, it in enumerate(d.get("itens", [])[:4]):
            rid = self.id(f"r{j}")
            chips = ""
            for q, c in enumerate(it.get("chips", [])[:4]):
                chips += f'<span class="chip" id="{rid}-c{q}">{html.escape(c["texto"])}</span>'
            sub = f'<div class="t2">{html.escape(it["sub"])}</div>' if it.get("sub") else ""
            chips_html = f'<div class="chips">{chips}</div>' if chips else ""
            self.add(f'<div class="box row" id="{rid}" style="top:{470 + 170 * j}px"><div class="ic">{html.escape(it.get("icone", "•"))}</div>'
                     f'<div><div class="t1">{html.escape(it["titulo"])}</div>{sub}{chips_html}</div></div>')
            self.step("slide", "#" + rid, self.t(it.get("em")))
            for q, c in enumerate(it.get("chips", [])[:4]):
                self.step("pop", f"#{rid}-c{q}", self.t(c.get("em")))

    def r_terminal(self):
        d = self.d
        self.header()
        top = 560
        out = "".join(f'<div id="{self.id(f"o{j}")}" style="margin-top:18px;color:#7ee2a8">{html.escape(x["texto"])}</div>' for j, x in enumerate(d.get("saida", [])[:3]))
        prog = f'<div class="prog"><b id="{self.id("pb")}"></b></div>' if d.get("progresso") else ""
        self.add(f'<div class="term" id="{self.id("tm")}" style="top:{top}px;height:450px"><div class="bar"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i></div>'
                 f'<div class="body mono"><span class="p">$</span> <span id="{self.id("cmd")}"></span>{prog}{out}</div></div>')
        t = self.t(d.get("em"))
        self.step("rise", "#" + self.id("tm"), round(t - 0.3, 3))
        dur = min(1.6, max(0.5, len(d.get("comando", "")) * 0.03))
        self.step("type", "#" + self.id("cmd"), t, text=d.get("comando", ""), d=dur)
        if prog:
            self.step("fill", "#" + self.id("pb"), round(t + dur + 0.1, 3), d=.9, ease="power1.inOut")
        for j, x in enumerate(d.get("saida", [])[:3]):
            self.step("fadein", "#" + self.id(f"o{j}"), self.t(x.get("em")) if x.get("em") else round(t + dur + 1.1 + 0.4 * j, 3))
        self.stamp_center(d.get("carimbo"), 1060)

    def r_opcoes(self):
        d = self.d
        self.header()
        ops = d.get("opcoes", [])[:4]
        hl, base = HL[self.theme]
        times = []
        for j, o in enumerate(ops):
            oid = self.id(f"o{j}")
            self.add(f'<div class="box opt" id="{oid}" style="top:{500 + 135 * j}px"><span class="r"></span>{html.escape(o["texto"])}</div>')
            times.append(self.t(o.get("em")))
        for j in range(len(ops)):
            self.step("slide", "#" + self.id(f"o{j}"), round(min(times) - 0.4 + 0.1 * j, 3), dx=-140)
            self.step("color", "#" + self.id(f"o{j}"), times[j], c=hl)
            if j + 1 < len(ops):
                self.step("color", "#" + self.id(f"o{j}"), times[j + 1], c=base)
        self.stamp_center(d.get("carimbo"), 1070)

    def r_numero_grande(self):
        d = self.d
        v = str(d.get("valor", ""))
        m = re.match(r"^(\D*)(\d+)(.*)$", v)
        self.add(f'<div class="stat" id="{self.id("s")}"><div class="v" id="{self.id("v")}">{html.escape(v)}</div>'
                 f'<div class="l">{html.escape(d.get("rotulo", ""))}</div>'
                 + (f'<div class="s">{html.escape(d["sub"])}</div>' if d.get("sub") else "") + "</div>")
        t = self.t(d.get("em"))
        self.step("pop", "#" + self.id("s"), round(t - 0.2, 3))
        if m and d.get("contar", True):
            self.step("count", "#" + self.id("v"), round(t - 0.2, 3), to=int(m.group(2)), pre=m.group(1), suf=m.group(3), d=1.0)

    def r_imagem(self):
        d = self.d
        self.header()
        self.add(f'<div class="box shotbox" id="{self.id("b")}"><img id="{self.id("img")}" src="{d["arquivo"]}" alt="" /></div>')
        t = self.t(d.get("em"))
        self.step("rise", "#" + self.id("b"), t, d=.5)
        self.step("kenburns", "#" + self.id("img"), round(t + 0.3, 3), d=max(1.0, self.t1 - t - 0.8))
        if d.get("legenda"):
            self.add(f'<div class="shotcap kick" id="{self.id("lg")}">{html.escape(d["legenda"])}</div>')
            self.step("rise", "#" + self.id("lg"), round(t + 0.5, 3))

    def r_frase(self):
        d = self.d
        inner = ""
        for j, ln in enumerate(d.get("linhas", [])[:4]):
            inner += f'<div class="fl" id="{self.id(f"f{j}")}">{md(ln["texto"])}</div>'
        self.add(f'<div class="frase">{inner}</div>')
        for j, ln in enumerate(d.get("linhas", [])[:4]):
            self.step("wipe" if self.theme == "caderno" else "slam", "#" + self.id(f"f{j}"), self.t(ln.get("em")))

    def render(self):
        fn = getattr(self, "r_" + self.d.get("tipo", ""), None)
        if not fn:
            die(f"cena {self.i + 1}: tipo desconhecido '{self.d.get('tipo')}' (ver references/cenas.md)")
        fn()
        return '<div class="frame"></div>' + "".join(self.html)


# ======================= overlays sobre o avatar =======================
def overlays(items, A, t0, t1, pre):
    out, steps = [], []
    times = [A.at(o.get("em"), t0, t0 + 0.4 + i) for i, o in enumerate(items)]
    for i, o in enumerate(items):
        oid, t = f"{pre}{i}", times[i]
        kind = o.get("tipo", "balao")
        if kind == "balao":
            strike = f'<div class="strike" id="{oid}-x"></div>' if o.get("riscar_em") else ""
            bg = ' style="background:var(--hl);color:#141414"' if o.get("destaque") else ""
            out.append(f'<div class="ov"><div class="bub" id="{oid}"{bg}>{html.escape(o["texto"])}{strike}</div></div>')
            steps.append({"k": "pop", "s": "#" + oid, "t": round(t - 0.1, 3)})
            if strike:
                steps.append({"k": "strike", "s": f"#{oid}-x", "t": A.at(o["riscar_em"], t0, t + 0.8)})
        elif kind == "numeros":
            bs = "".join(f'<b id="{oid}-{j}">{html.escape(str(v))}</b>' for j, v in enumerate(o.get("valores", [])))
            out.append(f'<div class="ov"><div class="big3" id="{oid}">{bs}</div></div>')
            for j in range(len(o.get("valores", []))):
                steps.append({"k": "pop", "s": f"#{oid}-{j}", "t": round(t - 0.1 + 0.25 * j, 3)})
        elif kind == "inscrever":
            out.append(f'<div class="ov"><div class="subbtn" id="{oid}">{html.escape(o.get("texto", "Inscreva-se"))}</div></div>'
                       f'<svg class="cursor" id="{oid}-cur" viewBox="0 0 24 24"><path d="M3 2l17 9-7 2-3 7z" fill="#fff" stroke="#000" stroke-width="1.6"/></svg>')
            steps.append({"k": "pop", "s": "#" + oid, "t": round(t - 0.15, 3)})
            steps.append({"k": "click", "s": "#" + oid, "cur": f"#{oid}-cur", "t": round(t + 0.3, 3)})
        if i + 1 < len(items) and kind != "inscrever":
            steps.append({"k": "fadeout", "s": "#" + oid, "t": round(min(times[i + 1], t1) - 0.35, 3)})
    return "".join(out), steps


# ======================= legendas =======================
def captions(toks, theme, t_end):
    chunks, cur = [], []
    for t in toks:
        cur.append(t)
        if len(cur) == 3 or t["w"][-1] in ".,?!:;":
            chunks.append(cur); cur = []
    if cur:
        chunks.append(cur)
    html_out, steps = [], []
    if theme == "caderno":
        on, offbg, ink, offink = "#FFD84D", "rgba(255,216,77,0)", None, None
    elif theme == "moderno":
        on, offbg, ink, offink = "#7C3AED", "rgba(124,58,237,0)", None, None
    else:
        on, offbg, ink, offink = "rgba(0,0,0,0)", "rgba(0,0,0,0)", "#FFD24A", "#ffffff"
    for ci, ch in enumerate(chunks):
        st = ch[0]["s"]
        en = chunks[ci + 1][0]["s"] if ci + 1 < len(chunks) else ch[-1]["e"] + 0.4
        en = min(en, ch[-1]["e"] + 0.9, t_end)
        if en - st < 0.15:
            continue
        ws = "".join(f'<span class="cw" id="w{ci}_{wi}">{html.escape(w["w"])}</span>' for wi, w in enumerate(ch))
        html_out.append(f'<div class="cap clip" id="cap{ci}" data-start="{st:.2f}" data-duration="{en - st:.2f}" data-track-index="9" data-layout-allow-overlap>'
                        f'<div class="capin" id="capin{ci}">{ws}</div></div>')
        steps.append({"k": "caption", "s": f"#capin{ci}", "t": st})
        for wi, w in enumerate(ch):
            s = {"k": "word", "s": f"#w{ci}_{wi}", "t": w["s"], "on": on, "offbg": offbg,
                 "off": ch[wi + 1]["s"] if wi + 1 < len(ch) else None}
            if ink:
                s.update(ink=ink, offink=offink)
            steps.append(s)
    return "\n".join(html_out), steps


# ======================= montagem =======================
def main():
    if len(sys.argv) < 2:
        die(__doc__)
    proj = Path(sys.argv[1]).resolve(); guias = "--guias" in sys.argv
    cfg = load_config(proj)
    for f in ("timing.json", "words.json", "cenas.json", "audio/mix.wav"):
        if not (proj / f).exists():
            die(f"falta {f} no projeto (veja a ordem dos passos no SKILL.md).")
    timing = json.loads((proj / "timing.json").read_text())
    words = json.loads((proj / "words.json").read_text())
    spec = json.loads((proj / "cenas.json").read_text())
    script = read_script(proj)
    theme = spec.get("estilo") or cfg.get("estilo", "moderno")
    if theme not in THEMES:
        die(f"estilo deve ser um destes: {', '.join(THEMES)}.")
    total = float(timing["total"])

    toks = []
    for part in ("intro", "meio", "final"):
        toks += align(script[part], words, *timing[part])
    A = Anchors(toks)

    # avatar
    av_on = cfg.get("avatar", {}).get("usar", "inicio_e_fim") != "nenhum" and (proj / "assets/avatar_intro.mp4").exists()
    intro_len = min(duration(proj / "assets/avatar_intro.mp4"), timing["intro"][1] + 0.05) if av_on else 0
    f0 = timing["final"][0]
    final_len = min(duration(proj / "assets/avatar_final.mp4"), total - f0) if av_on and (proj / "assets/avatar_final.mp4").exists() else 0
    meio0 = round(max(0.0, intro_len - 0.4), 3) if av_on else 0.0   # entra enquanto o avatar sai

    # cenas
    raw = spec.get("cenas", [])
    if not raw:
        die("cenas.json sem cenas.")
    starts = [meio0]
    for c in raw[1:]:
        s = A.at(c.get("inicio"), starts[-1] + 0.5, None)
        if s is None:
            die(f"âncora de início não encontrada: '{c.get('inicio')}' — use uma frase exata do roteiro.")
        starts.append(round(s - 0.35, 3))
    ends = starts[1:] + [round(f0 - 0.05, 3) if final_len else round(total - 1.8, 3)]
    scenes = []
    for i, c in enumerate(raw):
        sc = Scene(i, c, starts[i], ends[i], A, theme)
        scenes.append((sc.render(), sc))

    canal = cfg.get("canal", {})
    end = spec.get("card_final", {})
    logo = end.get("titulo") or canal.get("nome", "")
    end_t = round(f0 + final_len, 3) if final_len else ends[-1]
    end_html = (f'<div class="frame"></div><div class="end-logo" id="end-l">{md(logo)}</div>'
                f'<div class="end-sub kick" id="end-s">{html.escape(end.get("subtitulo", canal.get("slogan", "")))}</div>'
                + (f'<div class="box end-q" id="end-q">{html.escape(end["pergunta"])}</div>' if end.get("pergunta") else ""))
    end_steps = [{"k": "wipe", "s": "#end-l", "t": round(end_t - 0.1, 3)}, {"k": "rise", "s": "#end-s", "t": round(end_t + 0.2, 3)}]
    if end.get("pergunta"):
        end_steps.append({"k": "pop", "s": "#end-q", "t": round(end_t + 0.4, 3)})

    steps = []
    for _, sc in scenes:
        steps += sc.steps
    steps += end_steps

    # camada de cenas por estilo
    if theme == "caderno":
        n = len(scenes) + 1
        cols = 3
        cells = []
        for i in range(n):
            r, c = divmod(i, cols)
            if r % 2:
                c = cols - 1 - c
            cells.append([c * GX, r * GY])
        rows = (n + cols - 1) // cols
        world = "".join(f'<div class="st" id="st{i}" style="left:{cells[i][0]}px;top:{cells[i][1]}px">{h}</div>' for i, (h, _) in enumerate(scenes))
        world += f'<div class="st" id="st-end" style="left:{cells[-1][0]}px;top:{cells[-1][1]}px">{end_html}</div>'
        layer = (f'<div id="cam"><div id="drift"><div id="world" style="width:{cols * GX}px;height:{rows * GY}px">{world}</div></div></div>')
        cam_starts = starts + [round(f0 - 0.1, 3) if final_len else ends[-1]]
        camera = {"mode": "mapa", "cells": cells, "starts": cam_starts}
    else:
        rng = random.Random(7)
        if theme == "moderno":
            nodes = [(rng.uniform(60, 1020), rng.uniform(80, 1840)) for _ in range(22)]
            lines, pulses = "", ""
            for a_i, (x1, y1) in enumerate(nodes):
                near = sorted(range(len(nodes)), key=lambda j: (nodes[j][0] - x1) ** 2 + (nodes[j][1] - y1) ** 2)[1:3]
                for j in near:
                    if j > a_i:
                        x2, y2 = nodes[j]
                        lines += f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}"/>'
                        if len(pulses) < 2600:
                            pulses += f'<line class="pulse" x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}"/>'
            dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.choice([3, 4, 5])}"/>' for x, y in nodes)
            bg = (f'<div id="aurora"><div class="blob" id="b1"></div><div class="blob" id="b2"></div><div class="blob" id="b3"></div><div class="blob" id="b4"></div></div>'
                  f'<div id="grid"></div><svg id="net" viewBox="0 0 1080 1920">{lines}{pulses}{dots}</svg>')
        parts = "".join(f'<i class="pt" style="left:{rng.uniform(0, 1080):.0f}px;top:{rng.uniform(0, 1920):.0f}px;width:{(z := rng.choice([3, 4, 4, 6, 8]))}px;height:{z}px;opacity:{rng.uniform(.25, .8):.2f}"></i>' for _ in range(70))
        layer = bg if theme == "moderno" else f'<div id="bgfx"></div><div id="floorwrap"><div id="floor"></div></div><div id="floorfade"></div><div id="parts">{parts}</div>'
        cam_list = []
        for i, (h, sc) in enumerate(scenes):
            layer += (f'<section class="scene clip" id="sc{i}" data-start="{sc.t0:.2f}" data-duration="{sc.t1 - sc.t0:.2f}" data-track-index="2">'
                      f'<div class="st" id="st{i}">{h}</div></section>')
            cam_list.append([f"#st{i}", sc.t0, sc.t1])
        layer += f'<section class="scene clip" id="sc-end" data-start="{end_t:.2f}" data-duration="{total - end_t:.2f}" data-track-index="2"><div class="st">{end_html}</div></section>'
        camera = {"mode": "suave" if theme == "moderno" else "cortes", "scenes": cam_list}

    # avatar + overlays
    av_html = ""
    av_plan = {}
    if av_on:
        o1, s1 = overlays(spec.get("intro", []), A, 0, intro_len, "oi")
        av_html += (f'<div id="avl1"><video id="avatar1" src="assets/avatar_intro.mp4" muted playsinline data-start="0" data-duration="{intro_len:.2f}" data-track-index="0"></video></div>'
                    f'<div id="ov1" class="clip" data-start="0" data-duration="{intro_len:.2f}" data-track-index="1">{o1}</div>')
        steps += s1
        av_plan["intro"] = round(intro_len, 3)
        if final_len:
            o2, s2 = overlays(spec.get("final", []), A, f0, f0 + final_len, "of")
            av_html += (f'<div id="avl2"><video id="avatar2" src="assets/avatar_final.mp4" muted playsinline data-start="{f0:.2f}" data-duration="{final_len:.2f}" data-track-index="0"></video></div>'
                        f'<div id="ov2" class="clip" data-start="{f0:.2f}" data-duration="{final_len:.2f}" data-track-index="1">{o2}</div>')
            steps += s2
            av_plan["final"] = [round(f0, 3), round(final_len, 3)]

    cap_html, cap_steps = ("", [])
    if cfg.get("legendas", True):
        cap_html, cap_steps = captions(toks, theme, total)
    steps += cap_steps

    guides = ""
    if guias:
        guides = ('<div style="position:absolute;inset:0;z-index:99;pointer-events:none">'
                  '<div style="position:absolute;left:100px;top:230px;width:830px;height:950px;outline:3px dashed #00c853"></div>'
                  '<div style="position:absolute;left:100px;top:1240px;width:830px;height:160px;outline:3px dashed #2962ff"></div>'
                  '<div style="position:absolute;left:940px;top:700px;width:140px;height:820px;background:rgba(255,0,0,.18)"></div>'
                  '<div style="position:absolute;left:0;top:1500px;width:1080px;height:420px;background:rgba(255,0,0,.18)"></div>'
                  '<div style="position:absolute;left:0;top:0;width:1080px;height:200px;background:rgba(255,0,0,.18)"></div></div>')

    css = (SKILL_DIR / "styles/base.css").read_text() + "\n" + (SKILL_DIR / f"styles/{theme}.css").read_text()
    runtime = (SKILL_DIR / "scripts/runtime.js").read_text()
    plan = {"total": total, "camera": camera, "avatar": av_plan, "steps": steps}
    page = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
{css}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920" data-fps="30">
{layer}
{av_html}
{cap_html}
<div id="scan"></div><div id="flash"></div>
<svg id="grain" viewBox="0 0 1280 2120"><filter id="nz"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="5"/></filter><rect width="1280" height="2120" filter="url(#nz)"/></svg>
{guides}
<audio id="mix" src="audio/mix.wav" data-start="0" data-duration="{total}" data-volume="1"></audio>
</div>
<script>window.PLAN = {json.dumps(plan, ensure_ascii=False)};</script>
<script>
{runtime}
</script>
</body>
</html>
"""
    (proj / "index.html").write_text(page)
    (proj / "hyperframes.json").write_text(json.dumps({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
                                                       "paths": {"assets": "assets"}, "media": {"autoProxy": True}}, indent=2))
    (proj / "package.json").write_text(json.dumps({"name": proj.name.lower(), "private": True, "type": "module",
                                                   "scripts": {"check": f"npx --yes hyperframes@{HF_VERSION} check",
                                                               "render": f"npx --yes hyperframes@{HF_VERSION} render"}}, indent=2))
    (proj / ".hyperframesignore").write_text("audio/raw_*\naudio/intro.*\naudio/meio.*\naudio/final.*\naudio/voz.wav\naudio/premix.wav\naudio/musica.mp3\n*.md\ncenas.json\nwords.json\ntiming.json\navatar_jobs.json\nconfig.json\nsnaps/\n")
    print(f"ok: estilo {theme} · {len(scenes)} cenas · {total:.1f}s · avatar {'sim' if av_on else 'não'}")
    for i, (_, sc) in enumerate(scenes):
        print(f"  cena {i + 1:>2} {sc.d.get('tipo'):<14} {sc.t0:6.2f}s → {sc.t1:6.2f}s")
    for w in WARN:
        print("  AVISO:", w)


if __name__ == "__main__":
    main()
