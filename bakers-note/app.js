/* ===== ベーカーズ％ノート ===== */
(function () {
  "use strict";

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var STORE_KEY = "bakersnote.v1";
  var THEME_KEY = "bakersnote.theme";

  /* ---------- data ---------- */
  function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }

  function seedRecipes() {
    return [
      { id: uid(), name: "フィナンシェ", note: "焦がしバターで。170℃前後で焼成。", updatedAt: Date.now(),
        ingredients: [
          ig("卵白", 65), ig("無塩バター（焦がし）", 68),
          ig("薄力粉", 20, true), ig("アーモンドパウダー", 35, true),
          ig("きび砂糖", 30), ig("ハチミツ", 20), ig("ベーキングパウダー", 2)
        ] },
      { id: uid(), name: "タルト生地（パート・シュクレ）", note: "", updatedAt: Date.now() - 1,
        ingredients: [
          ig("薄力粉", 200, true), ig("無塩バター", 100), ig("粉糖", 80),
          ig("全卵", 40), ig("アーモンドパウダー", 25), ig("塩", 1)
        ] },
      { id: uid(), name: "パウンドケーキ", note: "", updatedAt: Date.now() - 2,
        ingredients: [
          ig("薄力粉", 100, true), ig("無塩バター", 100), ig("グラニュー糖", 100),
          ig("全卵", 100), ig("ベーキングパウダー", 3)
        ] }
    ];
  }
  function ig(name, g, base) { return { id: uid(), name: name, g: g, base: !!base }; }

  function load() {
    try {
      var raw = localStorage.getItem(STORE_KEY);
      if (raw) {
        var d = JSON.parse(raw);
        if (d && Array.isArray(d.recipes)) return d;
      }
    } catch (e) {}
    return { recipes: seedRecipes() };
  }

  var storageOK = true;
  function save() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(db)); }
    catch (e) { storageOK = false; $("#storeState").textContent = "（保存に失敗：ブラウザの容量設定をご確認ください）"; }
  }

  var db = load();

  /* ---------- editor session state ---------- */
  var current = null;   // recipe object being edited
  var mult = 1;

  function baseTotal(r) { return r.ingredients.reduce(function (s, x) { return s + (x.base ? num(x.g) : 0); }, 0); }
  function grandTotal(r) { return r.ingredients.reduce(function (s, x) { return s + num(x.g); }, 0); }
  function num(v) { var n = parseFloat(v); return isFinite(n) && n > 0 ? n : (n === 0 ? 0 : 0); }

  function fmt(n, dp) {
    if (!isFinite(n)) return "—";
    var f = Number(n.toFixed(dp === undefined ? 1 : dp));
    return f.toLocaleString("ja-JP");
  }
  function round(n, dp) { var p = Math.pow(10, dp); return Math.round(n * p) / p; }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  /* ---------- views ---------- */
  var libView = $("#libView"), edView = $("#edView");

  function showLibrary() {
    current = null;
    edView.hidden = true; libView.hidden = false;
    renderLibrary();
    window.scrollTo(0, 0);
  }

  function renderLibrary() {
    var grid = $("#recipeGrid");
    var list = db.recipes.slice().sort(function (a, b) { return b.updatedAt - a.updatedAt; });
    $("#libCount").textContent = list.length + " 件";
    grid.innerHTML = "";

    list.forEach(function (r) {
      var bt = baseTotal(r), gt = grandTotal(r);
      var card = document.createElement("button");
      card.className = "recipe-card";
      card.type = "button";
      card.innerHTML =
        '<div class="rc-name">' + esc(r.name || "（名称未設定）") + '</div>' +
        '<div class="rc-meta">' +
          '<span>材料 <span class="b">' + r.ingredients.length + '</span></span>' +
          '<span>粉基準 <span class="b">' + (bt > 0 ? fmt(bt) + "g" : "—") + '</span></span>' +
          '<span>全体 <span class="b">' + (gt > 0 ? fmt(gt) + "g" : "—") + '</span></span>' +
        '</div>';
      card.addEventListener("click", function () { openRecipe(r.id); });
      grid.appendChild(card);
    });

    var add = document.createElement("button");
    add.className = "add-card"; add.type = "button";
    add.innerHTML = "＋ 新しいレシピ";
    add.addEventListener("click", newRecipe);
    grid.appendChild(add);

    if (list.length === 0) {
      var e = document.createElement("p");
      e.className = "empty";
      e.textContent = "レシピがありません。「新しいレシピ」から始めましょう。";
      grid.appendChild(e);
    }
  }

  function newRecipe() {
    var r = { id: uid(), name: "", note: "", updatedAt: Date.now(),
      ingredients: [ ig("薄力粉", 100, true), ig("", 0) ] };
    db.recipes.push(r); save();
    openRecipe(r.id);
    $("#titleIn").focus();
  }

  function openRecipe(id) {
    current = db.recipes.filter(function (r) { return r.id === id; })[0];
    if (!current) { showLibrary(); return; }
    mult = 1;
    libView.hidden = true; edView.hidden = false;
    $("#titleIn").value = current.name;
    $("#noteIn").value = current.note || "";
    renderEditor();
    window.scrollTo(0, 0);
  }

  function touch() { if (current) { current.updatedAt = Date.now(); save(); flagSaved(); } }

  var savedTimer;
  function flagSaved() {
    var f = $("#savedFlag");
    f.classList.add("show");
    clearTimeout(savedTimer);
    savedTimer = setTimeout(function () { f.classList.remove("show"); }, 1400);
  }

  function renderEditor() {
    var r = current; if (!r) return;
    var bt = baseTotal(r), gt = grandTotal(r), m = mult;

    $("#warn").hidden = bt > 0;

    $("#tBase").innerHTML        = bt > 0 ? fmt(bt) + '<small>g</small>' : "—";
    $("#tTotal").innerHTML       = gt > 0 ? fmt(gt) + '<small>g</small>' : "—";
    $("#tBaseScaled").innerHTML  = bt > 0 ? fmt(bt * m) + '<small>g</small>' : "—";
    $("#tTotalScaled").innerHTML = gt > 0 ? fmt(gt * m) + '<small>g</small>' : "—";

    var tb = $("#rows"); tb.innerHTML = "";
    r.ingredients.forEach(function (x, i) {
      var pct = bt > 0 ? (num(x.g) / bt * 100) : NaN;
      var tr = document.createElement("tr");
      if (x.base) tr.className = "base";
      tr.innerHTML =
        '<td><input class="name-in" type="text" value="' + esc(x.name) + '" placeholder="材料名" data-i="' + i + '" data-f="name"></td>' +
        '<td class="num"><input class="g-in" type="number" step="0.1" min="0" inputmode="decimal" value="' + (x.g || 0) + '" data-i="' + i + '" data-f="g"> <span class="scaled u">g</span></td>' +
        '<td class="mid"><label class="base-toggle"><input type="checkbox" ' + (x.base ? "checked" : "") + ' data-i="' + i + '" data-f="base" aria-label="基準（粉）に含める"><span class="dot">✓</span></label></td>' +
        '<td class="num"><span class="pct ' + (x.base ? "base-pct" : "") + '">' + (isFinite(pct) ? fmt(pct) + '<span class="u">%</span>' : "—") + '</span></td>' +
        '<td class="num"><span class="scaled">' + fmt(num(x.g) * m) + '<span class="u">g</span></span></td>' +
        '<td class="mid"><button class="del" data-i="' + i + '" aria-label="この材料を削除">×</button></td>';
      tb.appendChild(tr);
    });

    $("#footG").innerHTML      = gt > 0 ? fmt(gt) + '<span class="u" style="color:var(--muted);font-weight:400">g</span>' : "—";
    $("#footPct").innerHTML    = bt > 0 ? fmt(gt / bt * 100) + '<span class="u" style="color:var(--muted);font-weight:400">%</span>' : "—";
    $("#footScaled").innerHTML = gt > 0 ? fmt(gt * m) + '<span class="u" style="color:var(--muted);font-weight:400">g</span>' : "—";

    var mi = $("#mult"), ti = $("#targetBase");
    if (document.activeElement !== mi) mi.value = round(m, 3);
    if (document.activeElement !== ti) ti.value = bt > 0 ? round(bt * m, 1) : "";
  }

  /* ---------- editor events ---------- */
  $("#rows").addEventListener("input", function (e) {
    var el = e.target, i = el.dataset.i, f = el.dataset.f;
    if (i === undefined || !current) return;
    var x = current.ingredients[+i];
    if (f === "name") { x.name = el.value; touch(); return; }        // no re-render → caret stays
    if (f === "g") { x.g = Math.max(0, parseFloat(el.value) || 0); touch(); renderEditor(); }
  });
  $("#rows").addEventListener("change", function (e) {
    var el = e.target;
    if (el.dataset.f === "base" && current) {
      current.ingredients[+el.dataset.i].base = el.checked; touch(); renderEditor();
    }
  });
  $("#rows").addEventListener("click", function (e) {
    var b = e.target.closest(".del");
    if (!b || !current) return;
    current.ingredients.splice(+b.dataset.i, 1); touch(); renderEditor();
  });

  $("#addBtn").addEventListener("click", function () {
    if (!current) return;
    current.ingredients.push(ig("", 0)); touch(); renderEditor();
    var names = document.querySelectorAll(".name-in");
    if (names.length) names[names.length - 1].focus();
  });

  $("#titleIn").addEventListener("input", function () {
    if (current) { current.name = this.value; touch(); }
  });
  $("#noteIn").addEventListener("input", function () {
    if (current) { current.note = this.value; touch(); }
  });

  $("#mult").addEventListener("input", function () {
    var v = parseFloat(this.value);
    if (isFinite(v) && v >= 0) { mult = v; renderEditor(); }
  });
  $("#targetBase").addEventListener("input", function () {
    if (!current) return;
    var bt = baseTotal(current), v = parseFloat(this.value);
    if (bt > 0 && isFinite(v) && v >= 0) { mult = v / bt; renderEditor(); }
  });
  Array.prototype.forEach.call(document.querySelectorAll(".quick button"), function (b) {
    b.addEventListener("click", function () { mult = parseFloat(b.dataset.m); renderEditor(); });
  });

  $("#backBtn").addEventListener("click", showLibrary);

  $("#dupBtn").addEventListener("click", function () {
    if (!current) return;
    var copy = JSON.parse(JSON.stringify(current));
    copy.id = uid();
    copy.name = (current.name || "レシピ") + "（コピー）";
    copy.updatedAt = Date.now();
    copy.ingredients.forEach(function (x) { x.id = uid(); });
    db.recipes.push(copy); save();
    openRecipe(copy.id);
    toast("複製しました");
  });

  $("#delBtn").addEventListener("click", function () {
    if (!current) return;
    if (!confirm("「" + (current.name || "このレシピ") + "」を削除しますか？")) return;
    db.recipes = db.recipes.filter(function (r) { return r.id !== current.id; });
    save(); showLibrary(); toast("削除しました");
  });

  $("#copyBtn").addEventListener("click", function () {
    if (!current) return;
    var r = current, bt = baseTotal(r), m = mult;
    var lines = [];
    lines.push("【" + (r.name || "レシピ") + "】" + (m !== 1 ? "  ×" + round(m, 3) : ""));
    r.ingredients.forEach(function (x) {
      if (!x.name && !x.g) return;
      lines.push("・" + (x.name || "材料") + "  " + fmt(num(x.g) * m) + "g" +
        (bt > 0 ? "  (" + fmt(num(x.g) / bt * 100) + "%)" : ""));
    });
    lines.push("― 合計 " + fmt(grandTotal(r) * m) + "g");
    var text = lines.join("\n");
    copyText(text);
  });

  /* ---------- export / import ---------- */
  $("#exportBtn").addEventListener("click", function () {
    var data = JSON.stringify({ app: "bakersnote", version: 1, exportedAt: new Date().toISOString(), recipes: db.recipes }, null, 2);
    var blob = new Blob([data], { type: "application/json" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "bakers-note-" + new Date().toISOString().slice(0, 10) + ".json";
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
          if (r && Array.isArray(r.ingredients)) {
            r.id = uid(); r.updatedAt = r.updatedAt || Date.now();
            r.ingredients.forEach(function (x) { x.id = x.id || uid(); x.base = !!x.base; });
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

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { toast("コピーしました"); },
        function () { fallbackCopy(text); });
    } else { fallbackCopy(text); }
  }
  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); toast("コピーしました"); }
    catch (e) { toast("コピーできませんでした"); }
    ta.remove();
  }

  /* ---------- toast ---------- */
  var toastTimer;
  function toast(msg) {
    var t = $("#toast");
    t.textContent = msg; t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove("show"); }, 1900);
  }

  /* ---------- theme ---------- */
  function currentDark() {
    var t = document.documentElement.getAttribute("data-theme");
    if (t) return t === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  function paintTheme() { $("#themeIcon").textContent = currentDark() ? "☾" : "☀"; }
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
  });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", paintTheme);

  /* ---------- init ---------- */
  showLibrary();

  /* ---------- service worker (offline / installable) ---------- */
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("sw.js").catch(function () {});
    });
  }
})();
