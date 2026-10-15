// Runtime de animação do avatar-shorts-solocodando.
// build.py gera window.PLAN (lista de passos) e este arquivo transforma o plano numa timeline GSAP pausada,
// que o HyperFrames percorre quadro a quadro. Tudo é determinístico: só depende do tempo.
(function () {
  const P = window.PLAN, tl = gsap.timeline({ paused: true }), D = P.total;
  const $ = (s) => document.querySelector(s);

  const K = {
    pop: (s) => tl.fromTo(s.s, { scale: .3, opacity: 0 }, { scale: 1, opacity: 1, duration: s.d || .4, ease: "back.out(2.2)" }, s.t),
    rise: (s) => tl.fromTo(s.s, { y: 80, opacity: 0 }, { y: 0, opacity: 1, duration: s.d || .45, ease: "power3.out" }, s.t),
    slide: (s) => tl.fromTo(s.s, { x: s.dx || -120, opacity: 0 }, { x: 0, opacity: 1, duration: .45, ease: "power3.out" }, s.t),
    stamp: (s) => tl.fromTo(s.s, { scale: 2.4, opacity: 0, rotation: (s.rot || -4) * 3 }, { scale: 1, opacity: 1, rotation: s.rot || -4, duration: .3, ease: "power4.out" }, s.t),
    wipe: (s) => tl.fromTo(s.s, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: .6, ease: "power3.out" }, s.t),
    slam: (s) => tl.fromTo(s.s, { scale: 2.4, opacity: 0, filter: "blur(10px)" }, { scale: 1, opacity: 1, filter: "blur(0px)", duration: .35, ease: "expo.out" }, s.t),
    fadein: (s) => tl.fromTo(s.s, { opacity: 0 }, { opacity: 1, duration: s.d || .25 }, s.t),
    fadeout: (s) => tl.to(s.s, { opacity: 0, y: -40, duration: .25 }, s.t),
    fill: (s) => tl.fromTo(s.s, { scaleX: 0 }, { scaleX: 1, duration: s.d || .5, ease: s.ease || "power2.out" }, s.t),
    hl: (s) => { tl.to(s.s, { backgroundColor: s.c, scale: 1.03, duration: .2 }, s.t); tl.to(s.s, { scale: 1, duration: .25 }, s.t + .25); },
    color: (s) => tl.to(s.s, { backgroundColor: s.c, duration: s.d || .12 }, s.t),
    dim: (s) => tl.to(s.s, { opacity: .45, duration: .4 }, s.t),
    kenburns: (s) => tl.fromTo(s.s, { scale: 1.0, y: 0 }, { scale: 1.08, y: -20, duration: s.d, ease: "sine.inOut" }, s.t),
    wave: (s) => document.querySelectorAll(s.s).forEach((el, i) =>
      tl.fromTo(el, { scaleY: .2 }, { scaleY: .35 + ((i * 53) % 10) / 14, duration: .16, yoyo: true, repeat: 9, ease: "sine.inOut" }, s.t + i * .025)),
    type: (s) => { const el = $(s.s), o = { p: 0 };
      tl.to(o, { p: 1, duration: s.d, ease: "none", onUpdate: () => { el.textContent = s.text.slice(0, Math.round(o.p * s.text.length)); } }, s.t); },
    count: (s) => { const el = $(s.s), o = { v: 0 };
      tl.to(o, { v: s.to, duration: s.d || 1, ease: "power2.out", onUpdate: () => { el.textContent = (s.pre || "") + Math.round(o.v) + (s.suf || ""); } }, s.t); },
    swap: (s) => { tl.set(s.a, { opacity: 0 }, s.t); tl.set(s.b, { opacity: 1 }, s.t); },
    blink: (s) => tl.fromTo(s.s, { opacity: 1 }, { opacity: 0, duration: .25, repeat: Math.max(0, Math.floor(s.d / .5) * 2 - 1), yoyo: true, ease: "steps(1)" }, s.t),
    shake: (s) => tl.fromTo(s.s, { x: 0 }, { x: 6, duration: .2, yoyo: true, repeat: 3 }, s.t),
    click: (s) => { tl.fromTo(s.cur, { x: 260, y: 300, opacity: 0 }, { x: 0, y: 0, opacity: 1, duration: .5, ease: "power3.out" }, s.t);
      tl.to(s.s, { scale: .9, duration: .1, yoyo: true, repeat: 1 }, s.t + .55); tl.to(s.s, { backgroundColor: "#8a8a8a", duration: .1 }, s.t + .65); },
    strike: (s) => tl.fromTo(s.s, { scaleX: 0 }, { scaleX: 1, duration: .35, ease: "power2.out" }, s.t),
    caption: (s) => tl.fromTo(s.s, { y: 24, opacity: 0 }, { y: 0, opacity: 1, duration: .16, ease: "power3.out" }, s.t),
    word: (s) => { const on = { backgroundColor: s.on, duration: .06 }, off = { backgroundColor: s.offbg, duration: .08 };
      if (s.ink) { on.color = s.ink; off.color = s.offink; }
      tl.to(s.s, on, s.t); if (s.off != null) tl.to(s.s, off, s.off); },
  };

  // ---------- câmera ----------
  const C = P.camera;
  if (C.mode === "mapa") {
    gsap.set("#world", { x: -C.cells[0][0], y: -C.cells[0][1] });
    let flip = 1;
    C.cells.forEach((c, i) => {
      const a = C.starts[i], next = i + 1 < C.starts.length ? C.starts[i + 1] - .5 : D;
      if (i > 0) {
        flip = -flip;
        tl.to("#drift", { scale: 1, duration: .35, ease: "power2.out" }, a - .5);
        tl.to("#world", { x: -c[0], y: -c[1], duration: 1.0, ease: "power3.inOut" }, a - .5);
        tl.to("#cam", { scale: .5, rotation: flip * 3, duration: .5, ease: "power2.in" }, a - .5);
        tl.to("#cam", { scale: 1, rotation: 0, duration: .5, ease: "power2.out" }, a);
      }
      tl.fromTo("#drift", { scale: 1 }, { scale: 1.012, duration: Math.max(.5, next - a - .9), ease: "sine.inOut", immediateRender: false }, a + .5);
    });
  } else if (C.mode === "suave") {
    // moderno: a cena entra em foco (blur → nítido) com leve zoom, aproxima devagar e sai desfocando; um brilho atravessa no corte
    C.scenes.forEach((sc, i) => {
      const a = sc[1], b = sc[2];
      tl.fromTo(sc[0], { scale: .94, y: 40, opacity: 0, filter: "blur(16px)" }, { scale: 1, y: 0, opacity: 1, filter: "blur(0px)", duration: .55, ease: "power3.out" }, a);
      tl.to(sc[0], { scale: 1.02, duration: Math.max(.3, b - a - .9), ease: "sine.inOut" }, a + .55);
      tl.to(sc[0], { scale: 1.05, y: -30, opacity: 0, filter: "blur(14px)", duration: .35, ease: "power2.in" }, b - .35);
      tl.fromTo("#scan", { opacity: 1, x: -1100 }, { x: 1100, duration: .7, ease: "power2.inOut", immediateRender: false }, b - .3);
    });
    // aurora viva + pulsos de luz na rede neural
    [["#b1", 220, 160], ["#b2", -260, -200], ["#b3", 240, -260], ["#b4", -180, 220]].forEach(([id, dx, dy], i) =>
      tl.fromTo(id, { x: 0, y: 0, scale: 1 }, { x: dx, y: dy, scale: 1.25, duration: D / 2, ease: "sine.inOut", yoyo: true, repeat: 1 }, 0));
    document.querySelectorAll("#net .pulse").forEach((el, i) =>
      tl.fromTo(el, { strokeDashoffset: 624 }, { strokeDashoffset: 0, duration: 2.2, ease: "none", repeat: Math.max(0, Math.floor((D - (i % 7) * .6) / 2.2) - 1) }, (i % 7) * .6));
  } else {
    // cortes: cada cena entra em "chicote" com blur, se aproxima devagar e sai; flash + linhas no corte
    C.scenes.forEach((sc, i) => {
      const dir = i % 2 ? -1 : 1, a = sc[1], b = sc[2];
      tl.fromTo(sc[0], { x: dir * 420, rotationY: -dir * 28, scale: 1.2, filter: "blur(18px)" }, { x: 0, rotationY: 0, scale: 1, filter: "blur(0px)", duration: .45, ease: "expo.out" }, a);
      tl.to(sc[0], { scale: 1.025, duration: Math.max(.3, b - a - .75), ease: "sine.inOut" }, a + .45);
      tl.to(sc[0], { x: -dir * 380, rotationY: dir * 24, scale: 1.15, filter: "blur(16px)", duration: .3, ease: "expo.in" }, b - .3);
      tl.fromTo("#flash", { opacity: .5 }, { opacity: 0, duration: .35, ease: "power2.out", immediateRender: false }, b - .05);
      tl.fromTo("#scan", { opacity: .9, y: -30 }, { opacity: 0, y: 30, duration: .4, ease: "steps(6)", immediateRender: false }, b - .05);
    });
    if ($("#floor")) tl.fromTo("#floor", { backgroundPosition: "0px 0px" }, { backgroundPosition: "0px " + Math.round(D * 90) + "px", duration: D, ease: "none" }, 0);
    if ($("#parts")) tl.fromTo("#parts", { y: 0 }, { y: -600, duration: D, ease: "none" }, 0);
  }

  // ---------- avatar ----------
  const A = P.avatar;
  if (A.intro) {
    tl.fromTo("#avl1", { scale: 1 }, { scale: 1.08, duration: Math.max(.5, A.intro - .8), ease: "sine.inOut" }, 0);
    if (C.mode === "mapa") {
      tl.to("#avl1", { scale: .34, rotation: -6, x: -250, y: -430, boxShadow: "0 0 0 26px #fff, 14px 14px 0 26px #141414", duration: .55, ease: "power3.inOut" }, A.intro - .75);
      tl.to("#avl1", { x: -1100, rotation: -18, duration: .35, ease: "power3.in" }, A.intro - .25);
    } else if (C.mode === "suave") {
      tl.to("#avl1", { scale: .78, y: -60, borderRadius: 60, opacity: 0, filter: "blur(18px)", duration: .6, ease: "power3.in" }, A.intro - .6);
    } else {
      tl.to("#avl1", { scale: 1.9, filter: "brightness(0) blur(10px)", duration: .45, ease: "expo.in" }, A.intro - .45);
      tl.fromTo("#flash", { opacity: .55 }, { opacity: 0, duration: .35, immediateRender: false }, A.intro - .05);
    }
    tl.to("#ov1", { opacity: 0, duration: .25 }, A.intro - .75);
  }
  if (A.final) {
    const f0 = A.final[0], fl = A.final[1];
    if (C.mode === "mapa") {
      tl.fromTo("#avl2", { scale: .34, rotation: 6, x: 250, y: -430, opacity: 0, boxShadow: "0 0 0 26px #fff, 14px 14px 0 26px #141414" }, { opacity: 1, duration: .2 }, f0 - .25);
      tl.to("#avl2", { scale: 1, rotation: 0, x: 0, y: 0, boxShadow: "0 0 0 0px #fff, 0px 0px 0 0px #141414", duration: .6, ease: "power3.inOut" }, f0 - .05);
    } else if (C.mode === "suave") {
      tl.fromTo("#avl2", { scale: .8, y: 60, borderRadius: 60, opacity: 0, filter: "blur(18px)" }, { scale: 1.02, y: 0, borderRadius: 0, opacity: 1, filter: "blur(0px)", duration: .6, ease: "power3.out" }, f0 - .1);
    } else {
      tl.fromTo("#avl2", { scale: 1.6, filter: "blur(14px)" }, { scale: 1.04, filter: "blur(0px)", duration: .6, ease: "expo.out" }, f0);
    }
    tl.to("#avl2", { scale: 1.07, duration: Math.max(.5, fl - 1.2), ease: "sine.inOut" }, f0 + .55);
    tl.to("#avl2", { scale: .34, rotation: -5, y: -1500, opacity: 0, duration: .55, ease: "power3.in" }, f0 + fl - .6);
  }

  // ---------- grão (textura de filme) ----------
  tl.fromTo("#grain", { x: 0, y: 0 }, { x: -80, y: -60, duration: .12, ease: "steps(3)", repeat: Math.floor(D / .12) - 1 }, 0);

  P.steps.forEach((s) => { const f = K[s.k]; if (f) f(s); });
  window.__timelines["main"] = tl;
})();
