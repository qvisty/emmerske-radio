(() => {
  'use strict';
  const D = window.EE;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const audio = $('#audio');
  const COLORS = ['--brick', '--sage', '--mustard', '--sky'];
  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const chColor = (i) => `var(${COLORS[i % COLORS.length]})`;
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
  };
  const fmt = (s) => {
    s = Math.max(0, Math.floor(s || 0));
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), ss = String(s % 60).padStart(2, '0');
    return h ? `${h}:${String(m).padStart(2, '0')}:${ss}` : `${m}:${ss}`;
  };
  const pad = (n) => String(n).padStart(2, '0');
  const enc = (p) => p.split('/').map(encodeURIComponent).join('/');
  const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const duration = () => (isFinite(audio.duration) && audio.duration) || D.duration;
  const chapterAt = (t) => {
    let i = 0;
    for (let k = 0; k < D.chapters.length; k++) if (t >= D.chapters[k].start - 0.05) i = k;
    return i;
  };
  const toast = (msg) => {
    const el = $('#toast'); el.textContent = msg; el.classList.add('show');
    clearTimeout(toast.t); toast.t = setTimeout(() => el.classList.remove('show'), 2200);
  };

  /* ---------- Afspilning ---------- */
  let pendingT = null; // tidspunkt valgt før lydens metadata er indlæst
  const now = () => (pendingT ?? audio.currentTime);
  function seek(t, play = true) {
    endClip();
    t = Math.min(Math.max(0, t), duration() - 0.5);
    if (audio.readyState >= 1) { audio.currentTime = t; pendingT = null; } else { pendingT = t; }
    if (play) audio.play().catch(() => {});
    tick(true);
  }
  function toggle() { endClip(); audio.paused ? audio.play().catch(() => {}) : audio.pause(); }

  /* ---------- Klip: afspil et udsnit og stop af sig selv ---------- */
  let clip = null;
  function endClip() {
    if (!clip) return;
    clip.btn.classList.remove('on'); clip.btn.style.setProperty('--p', 0); clip = null;
  }
  function playClip(btn) {
    if (clip && clip.btn === btn) { audio.paused ? audio.play().catch(() => {}) : audio.pause(); return; }
    seek(+btn.dataset.t, true);
    clip = { btn, t: +btn.dataset.t, end: +btn.dataset.end };
    btn.classList.add('on');
  }
  function clipTick(t) {
    if (!clip) return;
    clip.btn.style.setProperty('--p', Math.min(1, Math.max(0, (t - clip.t) / (clip.end - clip.t))));
    if (t >= clip.end) { audio.pause(); endClip(); }
  }
  document.addEventListener('click', (e) => { const b = e.target.closest('.clip'); if (b) playClip(b); });

  audio.addEventListener('play', () => { document.body.classList.add('playing'); loop(); });
  audio.addEventListener('pause', () => { document.body.classList.remove('playing'); store.set('ee-pos', audio.currentTime); });
  audio.addEventListener('ended', () => document.body.classList.remove('playing'));
  audio.addEventListener('loadedmetadata', () => { if (pendingT !== null) { audio.currentTime = pendingT; pendingT = null; } $('#durTime').textContent = fmt(duration()); drawWave(); });
  audio.addEventListener('seeked', () => tick(true));

  $('#playBtn').onclick = toggle;
  $('#miniPlay').onclick = toggle;
  $('#heroPlay').onclick = () => { toggle(); };
  $('#back15').onclick = () => seek(now() - 15, !audio.paused);
  $('#fwd30').onclick = () => seek(now() + 30, !audio.paused);
  $('#prevCh').onclick = () => {
    const i = chapterAt(now()), c = D.chapters[i];
    seek(now() - c.start > 3 || i === 0 ? c.start : D.chapters[i - 1].start);
  };
  $('#nextCh').onclick = () => { const i = chapterAt(now()); if (i < D.chapters.length - 1) seek(D.chapters[i + 1].start); };

  const speeds = [1, 1.25, 1.5, 2, 0.75];
  $('#speedBtn').onclick = (e) => {
    const i = (speeds.indexOf(audio.playbackRate) + 1) % speeds.length;
    audio.playbackRate = speeds[i];
    e.currentTarget.textContent = String(speeds[i]).replace('.', ',') + '×';
  };
  $('#shareBtn').onclick = async () => {
    const t = Math.floor(now());
    const url = `${location.origin}${location.pathname}#t=${t}`;
    try { await navigator.clipboard.writeText(url); toast(`Link til ${fmt(t)} er kopieret`); }
    catch (e) { history.replaceState(null, '', `#t=${t}`); toast(`Kopiér adressen – den peger på ${fmt(t)}`); }
  };

  /* ---------- Bølgeform ---------- */
  const wave = $('#wave'), canvas = $('#waveCanvas'), ctx = canvas.getContext('2d');
  let hoverX = -1;
  function drawWave() {
    const dpr = window.devicePixelRatio || 1, w = wave.clientWidth, h = wave.clientHeight;
    if (!w) return;
    if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const peaks = D.peaks.length ? D.peaks : new Array(600).fill(0.5);
    const dur = duration(), cur = now() / dur;
    const barW = w < 600 ? 2 : 3, gap = 1, n = Math.floor(w / (barW + gap));
    const cols = COLORS.map(css), faint = css('--line');
    const top = 16, mid = top + (h - top) / 2, amp = (h - top) / 2 - 2;
    for (let i = 0; i < n; i++) {
      const f = i / n, t = f * dur;
      const p = peaks[Math.min(peaks.length - 1, Math.floor(f * peaks.length))];
      const bh = Math.max(1.5, Math.pow(p, 0.8) * amp);
      const ci = chapterAt(t);
      ctx.fillStyle = cols[ci % cols.length];
      ctx.globalAlpha = f <= cur ? 1 : (hoverX >= 0 && i * (barW + gap) <= hoverX ? 0.5 : 0.28);
      ctx.fillRect(i * (barW + gap), mid - bh, barW, bh * 2);
    }
    ctx.globalAlpha = 1;
    // kapitelmarkører
    ctx.font = `600 10px Lexend, sans-serif`; ctx.textBaseline = 'top';
    D.chapters.forEach((c, i) => {
      const x = (c.start / dur) * w;
      ctx.fillStyle = faint; ctx.fillRect(Math.round(x), top - 2, 1, h - top + 2);
      if (w > 520 || i % 2 === 0) { ctx.fillStyle = cols[i % cols.length]; ctx.fillText(pad(c.n), Math.min(x + 3, w - 14), 0); }
    });
    // afspilningshoved
    ctx.fillStyle = css('--ink'); ctx.fillRect(cur * w - 1, top - 2, 2, h - top + 2);
  }
  const posFromEvent = (e) => {
    const r = wave.getBoundingClientRect();
    const x = Math.min(Math.max(0, (e.touches ? e.touches[0].clientX : e.clientX) - r.left), r.width);
    return { x, t: (x / r.width) * duration() };
  };
  let dragging = false;
  wave.addEventListener('pointerdown', (e) => { dragging = true; wave.setPointerCapture(e.pointerId); const p = posFromEvent(e); seek(p.t, !audio.paused || true); });
  wave.addEventListener('pointerup', () => { dragging = false; });
  wave.addEventListener('pointermove', (e) => {
    const p = posFromEvent(e), tip = $('#waveTip'), c = D.chapters[chapterAt(p.t)];
    hoverX = p.x; tip.hidden = false;
    tip.style.left = Math.min(Math.max(p.x, 70), wave.clientWidth - 70) + 'px';
    tip.textContent = `${fmt(p.t)} · ${pad(c.n)} ${c.title}`;
    if (dragging) { seek(p.t, !audio.paused); }
    drawWave();
  });
  wave.addEventListener('pointerleave', () => { hoverX = -1; $('#waveTip').hidden = true; drawWave(); });
  wave.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') { seek(now() - 5, !audio.paused); e.preventDefault(); e.stopPropagation(); }
    if (e.key === 'ArrowRight') { seek(now() + 5, !audio.paused); e.preventDefault(); e.stopPropagation(); }
  });
  new ResizeObserver(drawWave).observe(wave);

  /* ---------- Hero-equalizer ---------- */
  const eq = $('#heroEq');
  const EQN = 14; for (let i = 0; i < EQN; i++) eq.appendChild(document.createElement('i'));
  const eqBars = [...eq.children];
  function drawEq() {
    const t = audio.currentTime, idx = Math.floor((t / duration()) * D.peaks.length);
    eqBars.forEach((b, i) => {
      const p = audio.paused ? 0.1 : (D.peaks[Math.min(D.peaks.length - 1, idx + (i % 3))] || 0.3);
      const wob = audio.paused ? 0 : Math.abs(Math.sin(t * (3 + i * 1.7) + i)) * 0.55;
      b.style.height = Math.max(8, Math.min(100, (p * 0.7 + wob * p + 0.08) * 100)) + '%';
    });
  }

  /* ---------- Kapitler ---------- */
  const list = $('#chapterList');
  list.innerHTML = D.chapters.map((c, i) => `
    <li class="ch reveal" style="--c:${chColor(i)}" data-i="${i}">
      <div class="ch-ico"><svg><use href="#c-${c.icon}"/></svg></div>
      <div class="ch-body">
        <div class="ch-top"><b>${pad(c.n)}</b><span>${fmt(c.start)}</span><span>·</span><span>${fmt(c.end - c.start)}</span></div>
        <h3>${esc(c.title)}</h3>
        <p class="ch-who">${esc(c.who)}</p>
        <p class="ch-desc">${esc(c.desc)}</p>
        <div class="ch-actions">
          <button class="ch-play" data-i="${i}"><svg class="i-play"><use href="#i-play"/></svg><svg class="i-pause"><use href="#i-pause"/></svg><span>Afspil</span></button>
        </div>
      </div>
      <i class="ch-prog"></i>
    </li>`).join('');
  list.addEventListener('click', (e) => {
    const b = e.target.closest('.ch-play'); if (!b) return;
    const i = +b.dataset.i;
    if (chapterAt(now()) === i && now() > D.chapters[i].start + 0.5) toggle();
    else seek(D.chapters[i].start);
  });
  const chEls = $$('.ch', list), chProg = chEls.map((el) => $('.ch-prog', el));

  /* ---------- Stemmer ---------- */
  const initials = (n) => n.split(/\s*&\s*|\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join('');
  $('#people').innerHTML = D.people.map((p, i) => `
    <article class="person reveal" style="--c:${chColor(i + 1)}">
      <div class="avatar" aria-hidden="true">${esc(initials(p.name))}</div>
      <h3>${esc(p.name)}</h3>
      <p class="role">${esc(p.role)}</p>
      <p>${esc(p.bio)}</p>
      <div class="chips">${p.chapters.map((n) => `<button class="chip" data-ch="${n - 1}" title="${esc(D.chapters[n - 1].title)}">▶ Kap. ${n}</button>`).join('')}</div>
    </article>`).join('');
  $('#people').addEventListener('click', (e) => { const b = e.target.closest('.chip'); if (b) seek(D.chapters[+b.dataset.ch].start); });

  /* ---------- Personer i toppen og i fortællingen ---------- */
  const personIdx = (name) => D.people.findIndex((p) => p.name === name);
  $('#heroAvatars').innerHTML = D.people.map((p, i) =>
    `<a class="av" href="#stemmer" style="--c:${chColor(i + 1)}" title="${esc(p.name)} – ${esc(p.role)}">${esc(initials(p.name))}</a>`).join('');
  $$('.act-people').forEach((el) => {
    el.innerHTML = el.dataset.people.split('|').map((n) => {
      const i = personIdx(n), p = D.people[i];
      if (!p) return '';
      return `<button class="pchip" data-ch="${p.chapters[0] - 1}" style="--c:${chColor(i + 1)}" title="Hør ${esc(p.name)} i kapitel ${p.chapters[0]}">
        <span class="av sm">${esc(initials(p.name))}</span><span><strong>${esc(p.name)}</strong><small>${esc(p.role)}</small></span></button>`;
    }).join('');
  });
  document.addEventListener('click', (e) => { const b = e.target.closest('.pchip'); if (b) seek(D.chapters[+b.dataset.ch].start); });

  /* ---------- Citater ---------- */
  $('#quotes').innerHTML = D.quotes.map((q, i) => `
    <figure class="quote reveal ${i === 1 || i === 6 ? 'big' : ''}">
      <blockquote>${esc(q.text)}</blockquote>
      <footer><strong>— ${esc(q.who)}</strong><button class="q-play" data-t="${q.t}"><svg><use href="#i-play"/></svg> Hør ${fmt(q.t)}</button></footer>
    </figure>`).join('');
  $('#quotes').addEventListener('click', (e) => { const b = e.target.closest('.q-play'); if (b) seek(+b.dataset.t - 0.3); });

  /* ---------- Opdatering pr. frame ---------- */
  let lastCh = -1, lastSave = 0, raf = 0;

  function tick(force) {
    const t = now(), dur = duration();
    const ci = chapterAt(t), c = D.chapters[ci];
    $('#curTime').textContent = fmt(t);
    $('#miniTime').textContent = fmt(t);
    $('#miniFill').style.width = (t / dur) * 100 + '%';
    wave.setAttribute('aria-valuenow', Math.floor(t));
    wave.setAttribute('aria-valuetext', `${fmt(t)}, kapitel ${c.n}: ${c.title}`);
    if (ci !== lastCh || force) {
      if (ci !== lastCh) {
        chEls[lastCh]?.classList.remove('active'); chProg[lastCh] && (chProg[lastCh].style.width = '0');
        chEls[ci].classList.add('active');
      }
      lastCh = ci;
      $('#nowNum').textContent = pad(c.n); $('#nowTitle').textContent = c.title; $('#nowWho').textContent = c.who;
      $('#player').style.setProperty('--chc', chColor(ci));
      $('#miniNum').textContent = pad(c.n); $('#miniTitle').textContent = c.title; $('#miniWho').textContent = '· ' + c.who;
      if ('mediaSession' in navigator) {
        navigator.mediaSession.metadata = new MediaMetadata({
          title: `${pad(c.n)} ${c.title}`, artist: c.who, album: 'Emmerske Efterskole i radioen · Radio Globus',
          artwork: [{ src: 'assets/img/skolen.webp', sizes: '820x827', type: 'image/webp' }],
        });
      }
    }
    chProg[ci].style.width = Math.min(100, ((t - c.start) / (c.end - c.start)) * 100) + '%';
    clipTick(t);
    drawWave(); drawEq();
    if (Date.now() - lastSave > 5000 && t > 5) { store.set('ee-pos', t); lastSave = Date.now(); }
  }
  function loop() {
    cancelAnimationFrame(raf);
    const step = () => { tick(); if (!audio.paused) raf = requestAnimationFrame(step); else drawEq(); };
    raf = requestAnimationFrame(step);
  }

  /* ---------- Mini-afspiller ---------- */
  const mini = $('#mini');
  let started = false;
  audio.addEventListener('play', () => { started = true; updateMini(); }, { once: true });
  const playerVisible = { v: true };
  new IntersectionObserver(([e]) => { playerVisible.v = e.isIntersecting; updateMini(); }, { threshold: 0.15 }).observe($('#player'));
  function updateMini() {
    const show = started && !playerVisible.v;
    mini.classList.toggle('show', show); mini.setAttribute('aria-hidden', String(!show));
  }

  /* ---------- Tastatur ---------- */
  document.addEventListener('keydown', (e) => {
    if (e.target.closest('input, textarea, select') || e.metaKey || e.ctrlKey || e.altKey) return;
    if (!$('#lightbox').hidden) return;
    const k = e.key.toLowerCase();
    if (k === ' ' && !e.target.closest('button, a')) { toggle(); e.preventDefault(); }
    else if (k === 'arrowleft' && !e.target.closest('#deck')) { seek(now() - 15, !audio.paused); }
    else if (k === 'arrowright' && !e.target.closest('#deck')) { seek(now() + 30, !audio.paused); }
    else if (k === 'n') $('#nextCh').click();
    else if (k === 'p') $('#prevCh').click();
  });
  if ('mediaSession' in navigator) {
    const ms = navigator.mediaSession;
    ms.setActionHandler('play', () => audio.play());
    ms.setActionHandler('pause', () => audio.pause());
    ms.setActionHandler('previoustrack', () => $('#prevCh').click());
    ms.setActionHandler('nexttrack', () => $('#nextCh').click());
    ms.setActionHandler('seekbackward', () => seek(now() - 15));
    ms.setActionHandler('seekforward', () => seek(now() + 30));
  }

  /* ---------- Deep link / genoptag ---------- */
  function fromHash() {
    const m = location.hash.match(/t=(\d+(?:\.\d+)?)/);
    if (!m) return false;
    const t = +m[1];
    seek(t, false);
    $('#lyt').scrollIntoView();
    toast(`Klar ved ${fmt(t)} – tryk afspil`);
    return true;
  }
  window.addEventListener('hashchange', fromHash);
  if (!fromHash()) {
    const pos = +store.get('ee-pos');
    if (pos > 20 && pos < D.duration - 20) {
      $('#resume').hidden = false; $('#resumeAt').textContent = fmt(pos);
      $('#resumeBtn').onclick = () => { seek(pos); $('#resume').hidden = true; };
    }
  }
  audio.addEventListener('play', () => { $('#resume').hidden = true; }, { once: true });

  /* ---------- Slides ---------- */
  let slide = 0;
  const thumbs = $('#deckThumbs');
  thumbs.innerHTML = D.slides.map((s, i) => `<button data-i="${i}" title="${esc(s)}"><img src="assets/slides/thumb-${pad(i + 1)}.webp" alt="Slide ${i + 1}: ${esc(s)}" loading="lazy" width="480" height="268"></button>`).join('');
  function showSlide(i) {
    slide = (i + D.slides.length) % D.slides.length;
    const img = $('#deckImg');
    img.style.opacity = 0.2;
    const pre = new Image();
    pre.onload = () => { img.src = pre.src; img.style.opacity = 1; };
    pre.src = `assets/slides/slide-${pad(slide + 1)}.webp`;
    img.alt = `Slide ${slide + 1}: ${D.slides[slide]}`;
    $('#deckCount').textContent = `${slide + 1} / ${D.slides.length}`;
    $('#deckTitle').textContent = D.slides[slide];
    $$('button', thumbs).forEach((b, k) => b.classList.toggle('active', k === slide));
    const tb = thumbs.children[slide];
    thumbs.scrollTo({ left: tb.offsetLeft - thumbs.clientWidth / 2 + tb.clientWidth / 2, behavior: 'smooth' });
  }
  thumbs.addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) showSlide(+b.dataset.i); });
  $('#deckPrev').onclick = () => showSlide(slide - 1);
  $('#deckNext').onclick = () => showSlide(slide + 1);
  $('#deckFull').onclick = () => {
    const st = $('#deckStage');
    document.fullscreenElement ? document.exitFullscreen() : st.requestFullscreen?.().catch(() => openLightbox($('#deckImg').src, '', D.slides[slide]));
  };
  $('#deck').addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') { showSlide(slide - 1); e.preventDefault(); }
    if (e.key === 'ArrowRight') { showSlide(slide + 1); e.preventDefault(); }
  });
  $('#deckStage').tabIndex = 0;
  // swipe
  let sx = null;
  $('#deckStage').addEventListener('touchstart', (e) => { sx = e.touches[0].clientX; }, { passive: true });
  $('#deckStage').addEventListener('touchend', (e) => {
    if (sx === null) return; const dx = e.changedTouches[0].clientX - sx;
    if (Math.abs(dx) > 40) showSlide(slide + (dx < 0 ? 1 : -1)); sx = null;
  });
  $('#deckImg').addEventListener('click', () => { if (!document.fullscreenElement) openLightbox($('#deckImg').src, 'Filer/Trivslens%20Arkitektur%20Emmerske%20Efterskole.pdf', D.slides[slide]); });
  showSlide(0);

  /* ---------- Lightbox ---------- */
  const lb = $('#lightbox'), lbScroll = $('#lbScroll');
  let lastFocus = null;
  function openLightbox(src, orig, caption) {
    lastFocus = document.activeElement;
    $('#lbImg').src = src; $('#lbImg').alt = caption; $('#lbCaption').textContent = caption;
    const o = $('#lbOrig'); o.hidden = !orig; if (orig) o.href = orig;
    lbScroll.classList.remove('zoom'); lb.hidden = false; document.body.style.overflow = 'hidden';
    $('#lbClose').focus();
  }
  function closeLightbox() { lb.hidden = true; document.body.style.overflow = ''; lastFocus?.focus(); }
  $('#gallery').addEventListener('click', (e) => {
    const b = e.target.closest('.g-item'); if (b) openLightbox(b.dataset.full, b.dataset.orig, b.dataset.caption);
  });
  document.addEventListener('click', (e) => { const b = e.target.closest('.zoomable'); if (b) openLightbox(b.dataset.full, '', b.dataset.caption); });
  $('#lbClose').onclick = closeLightbox;
  lb.addEventListener('click', (e) => { if (e.target === lb || e.target === lbScroll) closeLightbox(); });
  $('#lbImg').addEventListener('click', (e) => {
    const img = e.currentTarget, r = img.getBoundingClientRect();
    const fx = (e.clientX - r.left) / r.width, fy = (e.clientY - r.top) / r.height;
    lbScroll.classList.toggle('zoom');
    if (lbScroll.classList.contains('zoom')) {
      requestAnimationFrame(() => { lbScroll.scrollLeft = fx * img.scrollWidth - lbScroll.clientWidth / 2; lbScroll.scrollTop = fy * img.scrollHeight - lbScroll.clientHeight / 2; });
    }
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !lb.hidden) closeLightbox(); });

  /* ---------- Downloads ---------- */
  const DL = [
    ['Materialer', [
      ['PDF', 'Trivslens Arkitektur – præsentation', 'Filer/Trivslens Arkitektur Emmerske Efterskole.pdf', '1,4 MB · 12 slides', '--mustard'],
      ['PPTX', 'Trivslens Arkitektur – PowerPoint', 'Filer/Trivslens Arkitektur Emmerske Efterskole.pptx', '12 dias med redigerbare tekstbokse', '--mustard'],
      ['PNG', 'Kapiteloversigt – infografik', 'Filer/Oversigt over radioprogrammet - rettede tider.png', '2 MB', '--mustard'],
      ['PNG', 'Hvor skuldrene sænkes – infografik', 'Filer/Emmerske Efterskole hvor skuldrene sænkes.png', '5 MB', '--mustard'],
      ['PNG', 'Fundament for trivsel – infografik', 'Filer/Emmerske Efterskole Fundament for trivsel.png', '4 MB', '--mustard'],
    ]],
  ];
  $('#downloads').innerHTML = DL.map(([g, items]) => `<p class="dl-group">${g}</p>` + items.map(([type, title, path, meta, col]) => `
    <a class="dl reveal" href="${enc(path)}" download style="--c:var(${col})">
      <span class="dl-type">${type}</span>
      <span class="dl-body"><strong>${esc(title)}</strong><small>${esc(meta)}</small></span>
      <svg><use href="#i-dl"/></svg>
    </a>`).join('')).join('');

  /* ---------- Tema & læsevenlig ---------- */
  const root = document.documentElement;
  const rb = $('#readableBtn');
  rb.setAttribute('aria-pressed', String(root.classList.contains('readable')));
  rb.onclick = () => {
    const on = root.classList.toggle('readable');
    rb.setAttribute('aria-pressed', String(on)); store.set('ee-readable', on ? '1' : '0');
    toast(on ? 'Læsevenlig visning: større tekst og mere luft' : 'Normal visning');
    requestAnimationFrame(drawWave);
  };
  $('#themeBtn').onclick = () => {
    const dark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark'; store.set('ee-theme', root.dataset.theme);
    requestAnimationFrame(drawWave);
  };
  matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', () => requestAnimationFrame(drawWave));

  /* ---------- Nav-markering & reveal ---------- */
  const navLinks = $$('.nav a');
  const secObs = new IntersectionObserver((es) => es.forEach((e) => {
    if (e.isIntersecting) navLinks.forEach((a) => a.classList.toggle('active', a.getAttribute('href') === '#' + e.target.id));
  }), { rootMargin: '-45% 0px -50% 0px' });
  navLinks.forEach((a) => { const s = $(a.getAttribute('href')); if (s) secObs.observe(s); });
  const rev = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); rev.unobserve(e.target); } }), { rootMargin: '0px 0px -8% 0px' });
  $$('.reveal').forEach((el, i) => { el.style.transitionDelay = (i % 6) * 50 + 'ms'; rev.observe(el); });

  document.fonts?.ready.then(drawWave);
  tick(true); drawEq();
})();
