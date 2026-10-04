/* ===== レシピ帳 ===== */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var STORE_KEY = "recipebook.v1";
  var THEME_KEY = "recipebook.theme";

  function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }
  function nowISO() { return new Date().toISOString(); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  var CATS = { dish: "🍳 料理", dessert: "🍰 デザート", drink: "🥤 ドリンク" };
  var PAPER_W = 760, PAPER_H0 = 1100, GROW = 380;

  function ing(name, qty) { return { id: uid(), name: name || "", qty: qty || "" }; }

  function seedRecipes() {
    return [
      { id: uid(), title: "基本のオムレツ", category: "dish", updatedAt: Date.now(),
        ingredients: [ing("卵", "2個"), ing("牛乳", "大さじ1"), ing("塩", "少々"), ing("バター", "10g")],
        strokes: [], paperH: PAPER_H0 },
      { id: uid(), title: "しっとりガトーショコラ", category: "dessert", updatedAt: Date.now() - 1,
        ingredients: [ing("チョコレート", "100g"), ing("無塩バター", "80g"), ing("卵", "2個"), ing("砂糖", "60g"), ing("薄力粉", "30g")],
        strokes: [], paperH: PAPER_H0 },
      { id: uid(), title: "自家製レモネード", category: "drink", updatedAt: Date.now() - 2,
        ingredients: [ing("レモン", "2個"), ing("はちみつ", "大さじ3"), ing("炭酸水", "300ml")],
        strokes: [], paperH: PAPER_H0 }
    ];
  }

  function load() {
    try {
      var raw = localStorage.getItem(STORE_KEY);
      if (raw) { var d = JSON.parse(raw); if (d && Array.isArray(d.recipes)) return d; }
    } catch (e) {}
    return { recipes: seedRecipes() };
  }
  var storageOK = true;
  function save() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(db)); storageOK = true; }
    catch (e) { storageOK = false; toast("保存できませんでした（端末の空き容量をご確認ください）"); }
  }
  var db = load();

  /* ---------- library ---------- */
  var libView = $("#libView"), edView = $("#edView");
  var libFilter = "all", libQ = "";

  function showLibrary() {
    current = null;
    edView.hidden = true; libView.hidden = false;
    renderLibrary();
    window.scrollTo(0, 0);
  }
  function renderLibrary() {
    var grid = $("#grid");
    var q = libQ.trim().toLowerCase();
    var list = db.recipes.slice()
      .filter(function (r) { return libFilter === "all" || r.category === libFilter; })
      .filter(function (r) { return !q || String(r.title).toLowerCase().indexOf(q) >= 0; })
      .sort(function (a, b) { return b.updatedAt - a.updatedAt; });
    grid.innerHTML = "";
    list.forEach(function (r) {
      var card = document.createElement("button");
      card.className = "card"; card.type = "button";
      var n = r.ingredients.filter(function (x) { return x.name.trim(); }).length;
      card.innerHTML =
        '<div class="ctop ' + r.category + '"></div>' +
        '<div class="cbody">' +
          '<div class="cname">' + esc(r.title || "（名称未設定）") + '</div>' +
          '<div class="cmeta"><span class="tag ' + r.category + '">' + CATS[r.category].split(" ")[0] + '</span><span>材料 ' + n + '</span></div>' +
        '</div>';
      card.addEventListener("click", function () { openRecipe(r.id); });
      grid.appendChild(card);
    });
    if (!list.length) {
      var e = document.createElement("p"); e.className = "empty";
      e.textContent = q || libFilter !== "all" ? "見つかりませんでした" : "レシピがありません。右下の＋から作りましょう。";
      grid.appendChild(e);
    }
  }
  $("#catChips").addEventListener("click", function (e) {
    var b = e.target.closest(".chip"); if (!b) return;
    libFilter = b.dataset.cat;
    Array.prototype.forEach.call($("#catChips").children, function (c) { c.classList.toggle("on", c === b); });
    renderLibrary();
  });
  $("#q").addEventListener("input", function () { libQ = this.value; renderLibrary(); });
  $("#addBtn").addEventListener("click", function () { newRecipe(); });

  function newRecipe() {
    var r = { id: uid(), title: "", category: "dish", updatedAt: Date.now(),
      ingredients: [ing(), ing()], strokes: [], paperH: PAPER_H0 };
    db.recipes.push(r); save();
    openRecipe(r.id, true);
  }

  /* ---------- editor state ---------- */
  var current = null, mode = "type", pen = "ink", penWide = false, erasing = false, fingerDraw = false;
  var PEN_COLORS = { ink: "#2B2520", red: "#C0392B", pencil: "#8A7F6E", highlight: "#FFD400" };

  function openRecipe(id, focusTitle) {
    current = db.recipes.filter(function (r) { return r.id === id; })[0];
    if (!current) { showLibrary(); return; }
    mode = "type"; erasing = false;
    libView.hidden = true; edView.hidden = false;
    $("#titleIn").value = current.title;
    setCategory(current.category, true);
    renderIngredients();
    setMode("type");
    setupCanvas();
    window.scrollTo(0, 0);
    if (focusTitle) setTimeout(function () { $("#titleIn").focus(); }, 60);
  }
  function touch() { if (current) { current.updatedAt = Date.now(); save(); } }

  $("#backBtn").addEventListener("click", function () { showLibrary(); });
  $("#titleIn").addEventListener("input", function () { if (current) { current.title = this.value; touch(); } });

  function setCategory(cat, silent) {
    current.category = cat;
    Array.prototype.forEach.call($("#catPicker").children, function (c) { c.classList.toggle("on", c.dataset.cat === cat); });
    if (!silent) touch();
  }
  $("#catPicker").addEventListener("click", function (e) {
    var b = e.target.closest(".chip"); if (!b || !current) return;
    setCategory(b.dataset.cat);
  });

  /* ---------- ingredients ---------- */
  function renderIngredients() {
    var list = $("#ingList"); list.innerHTML = "";
    current.ingredients.forEach(function (x, i) {
      var row = document.createElement("div"); row.className = "ing-row";
      row.innerHTML =
        '<input type="text" placeholder="材料名" value="' + esc(x.name) + '" data-i="' + i + '" data-f="name">' +
        '<input type="text" class="qty" placeholder="分量" value="' + esc(x.qty) + '" data-i="' + i + '" data-f="qty">' +
        '<button class="ing-del" data-i="' + i + '" aria-label="この材料を削除">×</button>';
      list.appendChild(row);
    });
  }
  $("#ingList").addEventListener("input", function (e) {
    var el = e.target; if (!current || !el.dataset) return;
    var i = el.dataset.i, f = el.dataset.f; if (i === undefined) return;
    current.ingredients[+i][f] = el.value; touch();
  });
  $("#ingList").addEventListener("click", function (e) {
    var b = e.target.closest(".ing-del"); if (!b || !current) return;
    current.ingredients.splice(+b.dataset.i, 1); touch(); renderIngredients();
  });
  $("#addIngBtn").addEventListener("click", function () {
    if (!current) return;
    current.ingredients.push(ing()); touch(); renderIngredients();
    var inputs = document.querySelectorAll('#ingList input[data-f="name"]');
    if (inputs.length) inputs[inputs.length - 1].focus();
  });

  /* ---------- mode / pen tools ---------- */
  function setMode(m) {
    mode = m;
    Array.prototype.forEach.call(document.querySelectorAll(".seg-btn"), function (b) { b.classList.toggle("on", b.dataset.mode === m); });
    $("#pentools").hidden = m !== "draw";
    $("#paper").classList.toggle("mode-draw", m === "draw");
    $("#paper").classList.toggle("mode-type", m === "type");
  }
  document.querySelector(".seg").addEventListener("click", function (e) {
    var b = e.target.closest(".seg-btn"); if (!b) return; setMode(b.dataset.mode);
  });
  $("#swatches").addEventListener("click", function (e) {
    var b = e.target.closest(".sw"); if (!b) return;
    pen = b.dataset.pen; erasing = false; $("#eraserBtn").classList.remove("on");
    Array.prototype.forEach.call($("#swatches").children, function (c) { c.classList.toggle("on", c === b); });
  });
  $("#widthBtn").addEventListener("click", function () {
    penWide = !penWide; this.textContent = penWide ? "太" : "細";
  });
  $("#eraserBtn").addEventListener("click", function () {
    erasing = !erasing; this.classList.toggle("on", erasing);
    $("#paper").classList.toggle("erasing", erasing);
  });
  $("#undoBtn").addEventListener("click", function () {
    if (!current || !current.strokes.length) return;
    current.strokes.pop(); touch(); redraw();
  });
  $("#fingerBtn").addEventListener("click", function () {
    fingerDraw = !fingerDraw; this.classList.toggle("on", fingerDraw);
    this.textContent = fingerDraw ? "✍️ 指ON" : "✍️ 指OFF";
  });
  $("#growBtn").addEventListener("click", function () {
    if (!current) return;
    current.paperH = (current.paperH || PAPER_H0) + GROW; touch(); setupCanvas();
  });

  /* ---------- more sheet ---------- */
  function openMore() { $("#moreBackdrop").hidden = false; $("#moreSheet").hidden = false; }
  function closeMore() { $("#moreBackdrop").hidden = true; $("#moreSheet").hidden = true; }
  $("#moreBtn").addEventListener("click", openMore);
  $("#moreBackdrop").addEventListener("click", closeMore);
  $("#dupItem").addEventListener("click", function () {
    if (!current) return;
    var copy = JSON.parse(JSON.stringify(current));
    copy.id = uid(); copy.title = (current.title || "レシピ") + "（コピー）"; copy.updatedAt = Date.now();
    copy.ingredients.forEach(function (x) { x.id = uid(); });
    db.recipes.push(copy); save(); closeMore(); openRecipe(copy.id); toast("複製しました");
  });
  var delArmed = false;
  $("#delItem").addEventListener("click", function () {
    if (!current) return;
    if (!delArmed) { delArmed = true; this.textContent = "本当に削除する？"; return; }
    delArmed = false; this.textContent = "🗑 削除";
    db.recipes = db.recipes.filter(function (r) { return r.id !== current.id; });
    save(); closeMore(); showLibrary(); toast("削除しました");
  });
  $("#moreSheet").addEventListener("transitionend", function () {}); // no-op, keep delArmed reset simple
  function resetDelArm() { delArmed = false; $("#delItem").textContent = "🗑 削除"; }
  $("#backBtn").addEventListener("click", resetDelArm);

  /* ---------- canvas: vector strokes, Apple Pencil pressure ---------- */
  var canvas = $("#ink"), ctx = canvas.getContext("2d");
  var paperEl = $("#paper"), stageEl = $("#stage");
  var scale = 1, activeStroke = null, lastPt = null;

  function setupCanvas() {
    var h = current.paperH || PAPER_H0;
    paperEl.style.aspectRatio = PAPER_W + " / " + h;
    requestAnimationFrame(function () {
      var rect = paperEl.getBoundingClientRect();
      scale = rect.width / PAPER_W;
      var dpr = Math.min(window.devicePixelRatio || 1, 2.5);
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
      ctx.setTransform(dpr * scale, 0, 0, dpr * scale, 0, 0);
      redraw();
    });
  }
  window.addEventListener("resize", function () { if (current) setupCanvas(); });

  function toLocal(e) {
    var rect = canvas.getBoundingClientRect();
    return { x: (e.clientX - rect.left) / scale, y: (e.clientY - rect.top) / scale, p: e.pressure && e.pressure > 0 ? e.pressure : 0.5 };
  }

  function strokeWidth(kind, wide) {
    if (kind === "highlight") return wide ? 22 : 14;
    return wide ? 5.5 : 2.4;
  }

  function drawStroke(s) {
    if (s.pts.length < 1) return;
    ctx.save();
    ctx.lineJoin = "round"; ctx.lineCap = "round";
    ctx.strokeStyle = PEN_COLORS[s.pen] || "#2B2520";
    if (s.pen === "highlight") { ctx.globalAlpha = 0.38; ctx.globalCompositeOperation = "multiply"; }
    if (s.pts.length === 1) {
      var p0 = s.pts[0];
      ctx.beginPath(); ctx.fillStyle = ctx.strokeStyle;
      ctx.arc(p0[0], p0[1], (s.w * (0.5 + p0[2])) / 2, 0, 7); ctx.fill();
      ctx.restore(); return;
    }
    for (var i = 1; i < s.pts.length; i++) {
      var a = s.pts[i - 1], b = s.pts[i];
      ctx.beginPath();
      ctx.lineWidth = s.w * (0.5 + (a[2] + b[2]) / 2);
      ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
    }
    ctx.restore();
  }
  function redraw() {
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.restore();
    if (!current) return;
    current.strokes.forEach(drawStroke);
    if (activeStroke) drawStroke(activeStroke);
  }

  function hitStroke(s, x, y, r) {
    if (!s.pts.length) return false;
    for (var i = 0; i < s.pts.length; i++) { var p = s.pts[i]; if (Math.hypot(p[0] - x, p[1] - y) <= r) return true; }
    for (var i2 = 1; i2 < s.pts.length; i2++) {
      var a = s.pts[i2 - 1], b = s.pts[i2];
      var dx = b[0] - a[0], dy = b[1] - a[1], len2 = dx * dx + dy * dy;
      var t = len2 ? Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / len2)) : 0;
      var px = a[0] + dx * t, py = a[1] + dy * t;
      if (Math.hypot(px - x, py - y) <= r) return true;
    }
    return false;
  }
  function eraseAt(x, y) {
    if (!current) return false;
    var r = 16, before = current.strokes.length;
    current.strokes = current.strokes.filter(function (s) { return !hitStroke(s, x, y, r); });
    return current.strokes.length !== before;
  }

  var activePointerId = null;
  canvas.addEventListener("pointerdown", function (e) {
    if (mode !== "draw" || !current) return;
    var isPen = e.pointerType === "pen";
    if (!isPen && e.pointerType === "touch" && !fingerDraw) return; // let the browser scroll
    if (e.pointerType === "mouse" && e.buttons !== 1) return;
    e.preventDefault();
    activePointerId = e.pointerId;
    try { canvas.setPointerCapture(e.pointerId); } catch (err) {}
    var pt = toLocal(e);
    if (erasing) { eraseAt(pt.x, pt.y); redraw(); return; }
    activeStroke = { pen: pen, w: strokeWidth(pen, penWide), pts: [[pt.x, pt.y, pt.p]] };
    lastPt = pt;
  }, { passive: false });

  canvas.addEventListener("pointermove", function (e) {
    if (mode !== "draw" || e.pointerId !== activePointerId) return;
    e.preventDefault();
    var events = (e.getCoalescedEvents && e.getCoalescedEvents()) || [];
    if (!events.length) events = [e]; // empty array is truthy; guard against no-coalesced-sample cases
    if (erasing) {
      events.forEach(function (ev) { var pt = toLocal(ev); eraseAt(pt.x, pt.y); });
      redraw(); return;
    }
    if (!activeStroke) return;
    events.forEach(function (ev) {
      var pt = toLocal(ev);
      activeStroke.pts.push([pt.x, pt.y, pt.p]);
    });
    redraw();
  }, { passive: false });

  function endStroke(e) {
    if (e.pointerId !== activePointerId) return;
    activePointerId = null;
    try { canvas.releasePointerCapture(e.pointerId); } catch (err) {}
    if (erasing) { touch(); return; }
    if (activeStroke && activeStroke.pts.length) { current.strokes.push(activeStroke); touch(); }
    activeStroke = null; redraw();
  }
  canvas.addEventListener("pointerup", endStroke);
  canvas.addEventListener("pointercancel", endStroke);

  /* ---------- export / import ---------- */
  $("#exportBtn").addEventListener("click", function () {
    var data = JSON.stringify({ app: "recipebook", version: 1, exportedAt: nowISO(), recipes: db.recipes }, null, 2);
    var blob = new Blob([data], { type: "application/json" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = "recipe-book-" + new Date().toISOString().slice(0, 10) + ".json";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    toast("書き出しました");
  });
  $("#importBtn").addEventListener("click", function () { $("#importFile").click(); });
  $("#importFile").addEventListener("change", function (e) {
    var file = e.target.files[0]; if (!file) return;
    var reader = new FileReader();
    reader.onload = function () {
      try {
        var d = JSON.parse(reader.result);
        var incoming = Array.isArray(d) ? d : d.recipes;
        if (!Array.isArray(incoming)) throw new Error("形式エラー");
        var added = 0;
        incoming.forEach(function (r) {
          if (r && Array.isArray(r.ingredients) && CATS[r.category]) {
            r.id = uid(); r.updatedAt = r.updatedAt || Date.now();
            r.ingredients.forEach(function (x) { x.id = x.id || uid(); });
            r.strokes = Array.isArray(r.strokes) ? r.strokes : [];
            r.paperH = r.paperH || PAPER_H0;
            db.recipes.push(r); added++;
          }
        });
        save(); renderLibrary();
        toast(added + " 件を読み込みました");
      } catch (err) { toast("読み込めませんでした（JSON形式をご確認ください）"); }
      $("#importFile").value = "";
    };
    reader.readAsText(file);
  });

  /* ---------- toast / theme ---------- */
  var toastTimer;
  function toast(msg) {
    var t = $("#toast"); t.textContent = msg; t.classList.add("show");
    clearTimeout(toastTimer); toastTimer = setTimeout(function () { t.classList.remove("show"); }, 1900);
  }
  function currentDark() {
    var t = document.documentElement.getAttribute("data-theme");
    if (t) return t === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  function paintTheme() { $("#themeBtn").textContent = currentDark() ? "☾" : "☀"; }
  (function initTheme() {
    var saved = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch (e) {}
    if (saved === "dark" || saved === "light") document.documentElement.setAttribute("data-theme", saved);
    paintTheme();
  })();
  $("#themeBtn").addEventListener("click", function () {
    var next = currentDark() ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
    paintTheme();
    if (current) setupCanvas();
  });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () { paintTheme(); if (current) setupCanvas(); });

  /* ---------- init ---------- */
  showLibrary();
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () { navigator.serviceWorker.register("sw.js").catch(function () {}); });
  }

  window.__rb = { get db() { return db; }, get current() { return current; }, openRecipe: openRecipe, showLibrary: showLibrary };
})();
