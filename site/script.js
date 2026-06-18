/* ░░ Optic Vision Pro — animations de défilement (esprit Humaan) ░░
   Révélation d'images par masque, titres montés depuis un masque,
   apparitions en cascade, barre de progression.
   Respecte prefers-reduced-motion. Couleurs inchangées. */

(function () {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ── Barre de progression de défilement ── */
  const progress = document.createElement("div");
  progress.className = "scroll-progress";
  document.body.appendChild(progress);

  if (!reduceMotion) {
    /* ── Titres : montée depuis un masque (wrap du texte dans un span) ── */
    document.querySelectorAll("main .block h2").forEach(function (h) {
      const span = document.createElement("span");
      while (h.firstChild) span.appendChild(h.firstChild);
      h.appendChild(span);
      h.classList.add("line-mask");
    });

    /* ── Images : révélation par masque ── */
    document.querySelectorAll(".shot").forEach(function (fig) {
      fig.classList.add("mask-img");
    });

    /* ── Textes, cartes, etc. : fondu + montée, en cascade ── */
    document.querySelectorAll("main .block > p, .step-head, .callout, .note, .legend, pre, .deps, .zones-layout, .tuto, main .block > .video-figure").forEach(function (el) {
      el.classList.add("reveal");
    });
    document.querySelectorAll(".cards, .flow, .tuto-steps, .two-col, .video-grid").forEach(function (group) {
      const items = group.children;
      for (let i = 0; i < items.length; i++) {
        if (items[i].classList.contains("flow-arrow")) continue;
        items[i].classList.add("reveal");
        items[i].style.transitionDelay = (i % 6) * 95 + "ms";
      }
    });

    /* ── Hero ── */
    const heroText = document.querySelector(".hero-text");
    const heroFig = document.querySelector(".hero-figure");
    if (heroText) heroText.classList.add("reveal", "reveal-left");
    if (heroFig) heroFig.classList.add("reveal", "reveal-zoom");

    /* ── IntersectionObserver : déclenche les animations ── */
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.14, rootMargin: "0px 0px -8% 0px" });

    document.querySelectorAll(".reveal, .mask-img, .line-mask").forEach(function (el) { io.observe(el); });

    // Le hero est déjà visible : on le révèle dès le chargement
    requestAnimationFrame(function () {
      if (heroText) heroText.classList.add("in-view");
      if (heroFig) heroFig.classList.add("in-view");
    });
  }

  /* ── Barre de progression de défilement (handler throttlé en rAF) ── */
  let ticking = false;

  function update() {
    const y = window.scrollY || window.pageYOffset;
    const docH = document.documentElement.scrollHeight - window.innerHeight;
    progress.style.width = (docH > 0 ? (y / docH) * 100 : 0) + "%";
    ticking = false;
  }

  window.addEventListener("scroll", function () {
    if (!ticking) { window.requestAnimationFrame(update); ticking = true; }
  }, { passive: true });

  update();
})();

/* ░░ Scrollytelling immersif : les calques se construisent au défilement ░░ */
(function () {
  "use strict";
  const steps = Array.prototype.slice.call(document.querySelectorAll(".istep"));
  const layers = Array.prototype.slice.call(document.querySelectorAll(".ilayer[data-layer]"));
  const cap = document.querySelector(".stack-cap [data-cap]");
  if (!steps.length || !layers.length) return;

  function activate(step) {
    steps.forEach(function (s) { s.classList.toggle("active", s === step); });

    const wanted = (step.getAttribute("data-layers") || "").split(/\s+/).filter(Boolean);
    layers.forEach(function (l) {
      l.classList.toggle("on", wanted.indexOf(l.getAttribute("data-layer")) !== -1);
    });
    if (cap) cap.textContent = step.getAttribute("data-cap") || "";
  }

  // Une étape devient active quand elle franchit le centre du viewport
  const io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) activate(entry.target);
    });
  }, { rootMargin: "-50% 0px -50% 0px", threshold: 0 });

  steps.forEach(function (s) { io.observe(s); });
  activate(steps[0]); // état initial
})();

/* ░░ Scrollspy : surligne le lien de navigation de la section visible ░░ */
(function () {
  "use strict";
  const links = Array.prototype.slice.call(document.querySelectorAll(".topbar nav a[href^='#']"));
  if (!links.length) return;

  const map = {};
  const targets = [];
  links.forEach(function (a) {
    const id = a.getAttribute("href").slice(1);
    const sec = document.getElementById(id);
    if (sec) { map[id] = a; targets.push(sec); }
  });
  if (!targets.length) return;

  let current = null;
  function setActive(id) {
    if (id === current) return;
    current = id;
    links.forEach(function (a) { a.classList.remove("active"); });
    if (map[id]) map[id].classList.add("active");
  }

  // La section dont le haut a franchi le tiers supérieur du viewport devient active.
  const io = new IntersectionObserver(function (entries) {
    let best = null;
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        if (!best || entry.boundingClientRect.top < best.boundingClientRect.top) best = entry;
      }
    });
    if (best) setActive(best.target.id);
  }, { rootMargin: "-30% 0px -60% 0px", threshold: 0 });

  targets.forEach(function (s) { io.observe(s); });
})();

/* ░░ Vidéos : lecture/pause automatique selon la visibilité (muettes) ░░ */
(function () {
  "use strict";
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const vids = Array.prototype.slice.call(document.querySelectorAll(".video-figure video"));
  if (!vids.length || !("IntersectionObserver" in window)) return;

  const io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      const v = entry.target;
      if (entry.isIntersecting) {
        if (v.preload !== "auto") v.preload = "auto";
        const p = v.play();
        if (p && typeof p.catch === "function") p.catch(function () { /* autoplay bloqué : contrôles dispo */ });
      } else if (!v.paused) {
        v.pause();
      }
    });
  }, { threshold: 0.45 });

  vids.forEach(function (v) { io.observe(v); });
})();
