/* ===== ストックボード ===== */
(function () {
  "use strict";
  var $ = function (s) { return document.querySelector(s); };

  /* ---------- seed (initial count) ---------- */
  var SEED_LOCS = [
    { id: "fz_low", name: "下の冷凍ストッカー" }, { id: "fr_low", name: "下冷蔵庫" },
    { id: "pantry", name: "常温倉庫" }, { id: "fz_up", name: "上と冷凍庫" }
  ];
  var SEED_ITEMS = (function () {
    var L = [
      ["fz_low","サーモン",9],["fz_low","豆グラタン",1],["fz_low","ポキイトシチュー",8],
      ["fr_low","粉チーズ",3],["fr_low","ミックスチーズ",2],["fr_low","レクレ",10],["fr_low","バゲット",9],
      ["fr_low","パスタ",8],["fr_low","バター",14],["fr_low","ニンニク",5],["fr_low","ヨーグルト",2],["fr_low","バケット",48],
      ["pantry","PBスープ",2,"㌜"],["pantry","フライドオニオン",2],["pantry","フライドガーリック",2],["pantry","ベーコンチップ",1],
      ["pantry","MIXハーブ",2],["pantry","マヨネーズ",4],["pantry","ケチャップ",3],["pantry","韓国のり",4],
      ["pantry","薄力粉",1],["pantry","片栗粉",1],["pantry","トマトパウチ",1,"㌜","＋1P"],["pantry","トマト缶",4,"㌜","＋3缶"],
      ["pantry","ブレンドOIL",4],["pantry","サラダ油",1],["pantry","卵",1,"㌜","＋1シート"],["pantry","じゃがいも",0.5,"㌜"],
      ["pantry","クッキングシート",1],["pantry","アルミホイル",3],["pantry","ラップ",1],["pantry","ペーパータオル",9],["pantry","リードペーパー",2],
      ["fz_up","ベリー",1],["fz_up","ムール",1],["fz_up","イカ",1],["fz_up","ポテト",3.5],["fz_up","エビフリット",0.5],
      ["fz_up","チキンリンクス",2],["fz_up","ボロネーゼ",2],["fz_up","豆グラ",1],["fz_up","シラス",0.2],["fz_up","焼き鯖",1],
      ["fz_up","ポテトスライス",0],["fz_up","オニオンソテー",1],["fz_up","イカスミ",10],["fz_up","明太",3],["fz_up","たん",0],
      ["fz_up","ハラミ",0],["fz_up","豚バラ1.5mm",1],["fz_up","豚バラ1.4センチ",0],["fz_up","ハツ",1],["fz_up","鶏もも",0],
      ["fz_up","バナメイ",2],["fz_up","チョリソー",4],["fz_up","モンゴウイカ",0.8]
    ];
    var out = {};
    L.forEach(function (r, i) {
      out["s" + String(i).padStart(2, "0")] = { loc: r[0], name: r[1], qty: r[2], unit: r[3] || "", memo: r[4] || "", min: 1, order: i, updatedAt: "" };
    });
    return out;
  })();

  /* ---------- helpers ---------- */
  function uid() { return "i" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }
  function nowISO() { return new Date().toISOString(); }
  function fmtQ(n) { n = Number(n) || 0; return (Math.round(n * 100) / 100).toString(); }
  function fmtT(iso) { if (!iso) return ""; var d = new Date(iso); if (isNaN(d)) return ""; return (d.getMonth() + 1) + "/" + d.getDate() + " " + String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0"); }
  function status(it) { var q = Number(it.qty) || 0, m = Number(it.min); if (isNaN(m)) m = 1; if (q <= 0) return "out"; if (q <= m) return "low"; return "ok"; }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  /* ---------- storage (this device) ---------- */
  var KEY = "stockboard.v1";
  var state = { locations: SEED_LOCS.slice(), items: JSON.parse(JSON.stringify(SEED_ITEMS)), filter: "all", q: "", collapsed: {}, savedAt: "" };
  (function load() {
    try {
      var r = localStorage.getItem(KEY);
      if (r) { var d = JSON.parse(r); if (d && d.items && Array.isArray(d.locations)) { state.locations = d.locations; state.items = d.items; state.savedAt = d.savedAt || ""; } }
    } catch (e) {}
  })();
  var storageOK = true;
  function save() {
    state.savedAt = nowISO();
    try { localStorage.setItem(KEY, JSON.stringify({ locations: state.locations, items: state.items, savedAt: state.savedAt })); storageOK = true; }
    catch (e) { storageOK = false; toast("保存できませんでした（端末の空き容量やブラウザ設定をご確認ください）"); }
    paintMode();
  }
  function paintMode() { $("#modeTxt").textContent = storageOK ? ("この端末に保存" + (state.savedAt ? "　" + fmtT(state.savedAt) : "")) : "保存できません"; $("#mode").className = "mode " + (storageOK ? "local" : "err"); }

  function writeItem(id, data) { state.items[id] = data; save(); render(); }
  function patchItem(id, patch) { if (!state.items[id]) return; Object.assign(state.items[id], patch); save(); render(); }
  function removeItem(id) { delete state.items[id]; save(); render(); }
  function writeLocs(locs) { state.locations = locs; save(); render(); }

  /* ---------- render ---------- */
  var listEl = $("#list");
  function counts() { var o = 0, l = 0, a = 0; Object.keys(state.items).forEach(function (id) { a++; var s = status(state.items[id]); if (s === "out") o++; else if (s === "low") l++; }); return { out: o, low: l, all: a }; }
  function sortedIds(locId) { return Object.keys(state.items).filter(function (id) { return state.items[id].loc === locId; }).sort(function (a, b) { return (state.items[a].order || 0) - (state.items[b].order || 0) || String(state.items[a].name).localeCompare(String(state.items[b].name), "ja"); }); }
  function render() {
    var c = counts();
    $("#nOut").textContent = c.out; $("#nLow").textContent = c.low; $("#nAll").textContent = c.all;
    ["out", "low", "all"].forEach(function (f) { document.querySelector('[data-filter="' + f + '"]').classList.toggle("on", state.filter === f); });
    var q = state.q.trim().toLowerCase();
    listEl.innerHTML = ""; var any = false;
    state.locations.forEach(function (loc) {
      var ids = sortedIds(loc.id), lo = 0, lw = 0;
      ids.forEach(function (id) { var s = status(state.items[id]); if (s === "out") lo++; else if (s === "low") lw++; });
      var shown = ids.filter(function (id) {
        var it = state.items[id], s = status(it);
        if (state.filter === "out" && s !== "out") return false;
        if (state.filter === "low" && s === "ok") return false;
        if (q && String(it.name).toLowerCase().indexOf(q) < 0 && String(it.memo || "").toLowerCase().indexOf(q) < 0) return false;
        return true;
      });
      if ((state.filter !== "all" || q) && shown.length === 0) return;
      any = true;
      var closed = state.collapsed[loc.id] && !q && state.filter === "all";
      var sec = document.createElement("section"); sec.className = "sec" + (closed ? " closed" : "");
      sec.innerHTML = '<div class="sec-h"><button class="toggle" data-loc="' + esc(loc.id) + '" aria-expanded="' + (closed ? "false" : "true") + '">' +
        '<span class="chev">▼</span><h2>' + esc(loc.name) + '</h2><span class="cnt">' + ids.length + '品目</span>' +
        (lo ? '<span class="badge crit">切れ ' + lo + '</span>' : '') + (lw ? '<span class="badge warn">要発注 ' + lw + '</span>' : '') + '</button>' +
        '<button class="add" data-addto="' + esc(loc.id) + '" aria-label="この場所に品目を追加">＋</button></div><div class="rows"></div>';
      var rows = sec.querySelector(".rows");
      if (!shown.length) rows.innerHTML = '<div class="empty">品目がありません</div>';
      shown.forEach(function (id) {
        var it = state.items[id], s = status(it);
        var r = document.createElement("div"); r.className = "row st-" + s;
        var stTxt = s === "out" ? "在庫切れ" : s === "low" ? "要発注（発注点 " + fmtQ(it.min == null ? 1 : it.min) + "）" : "";
        r.innerHTML = '<div class="stripe"></div>' +
          '<button class="name" data-edit="' + id + '"><span class="nm">' + esc(it.name) + '</span><span class="sub">' +
          (stTxt ? '<span class="st">' + esc(stTxt) + '</span>' : '') + (it.memo ? '<span>' + esc(it.memo) + '</span>' : '') +
          (it.updatedAt ? '<span>更新 ' + esc(fmtT(it.updatedAt)) + '</span>' : '') + '</span></button>' +
          '<div class="stepper"><button class="dec" data-dec="' + id + '" aria-label="1減らす">−</button>' +
          '<button class="qty" data-edit="' + id + '" aria-label="数量を編集"><b>' + fmtQ(it.qty) + '</b>' + (it.unit ? '<small>' + esc(it.unit) + '</small>' : '') + '</button>' +
          '<button class="inc" data-inc="' + id + '" aria-label="1増やす">＋</button></div>';
        rows.appendChild(r);
      });
      listEl.appendChild(sec);
    });
    if (!any) { var e = document.createElement("div"); e.className = "empty"; e.textContent = q ? "「" + state.q + "」に一致する品目はありません" : state.filter === "out" ? "在庫切れの品目はありません 🎉" : "要発注の品目はありません 🎉"; listEl.appendChild(e); }
    if (state.filter === "all" && !q) { var b = document.createElement("button"); b.className = "add-loc"; b.id = "addLoc"; b.textContent = "＋ 場所を追加"; listEl.appendChild(b); }
  }

  /* ---------- interactions ---------- */
  listEl.addEventListener("click", function (e) {
    var t = e.target.closest("button"); if (!t) return;
    if (t.dataset.loc) { state.collapsed[t.dataset.loc] = !state.collapsed[t.dataset.loc]; render(); return; }
    if (t.dataset.addto) { openEdit(null, t.dataset.addto); return; }
    if (t.dataset.edit) { openEdit(t.dataset.edit); return; }
    if (t.id === "addLoc") { openLoc(); return; }
    var id = t.dataset.dec || t.dataset.inc; if (!id) return;
    var it = state.items[id]; if (!it) return;
    var q = Number(it.qty) || 0; q = t.dataset.dec ? Math.max(0, q - 1) : q + 1; q = Math.round(q * 100) / 100;
    patchItem(id, { qty: q, updatedAt: nowISO() });
  });
  document.querySelector(".stats").addEventListener("click", function (e) { var b = e.target.closest("[data-filter]"); if (!b) return; state.filter = b.dataset.filter; render(); });
  $("#q").addEventListener("input", function () { state.q = this.value; render(); });

  /* edit sheet */
  var editId = null, delArmed = false;
  function fillLocs(sel, val) { sel.innerHTML = ""; state.locations.forEach(function (l) { var o = document.createElement("option"); o.value = l.id; o.textContent = l.name; sel.appendChild(o); }); sel.value = val || (state.locations[0] && state.locations[0].id) || ""; }
  function openSheet(id) { $("#backdrop").hidden = false; $(id).hidden = false; }
  function closeSheets() { $("#backdrop").hidden = true; ["#sheet", "#locSheet", "#pasteSheet", "#importSheet"].forEach(function (s) { $(s).hidden = true; }); editId = null; }
  $("#backdrop").addEventListener("click", closeSheets);
  function openEdit(id, locId) {
    editId = id; delArmed = false;
    var it = id ? state.items[id] : { name: "", qty: 0, unit: "", loc: locId, min: 1, memo: "" };
    $("#sheetTitle").textContent = id ? "品目を編集" : "品目を追加";
    $("#eName").value = it.name || ""; $("#eQty").value = fmtQ(it.qty); $("#eMin").value = fmtQ(it.min == null ? 1 : it.min); $("#eMemo").value = it.memo || "";
    var u = $("#eUnit"); u.value = it.unit || ""; if (u.value !== (it.unit || "")) { var o = document.createElement("option"); o.textContent = it.unit; u.appendChild(o); u.value = it.unit; }
    fillLocs($("#eLoc"), it.loc);
    $("#eDel").hidden = !id; $("#eDel").textContent = "削除";
    $("#eMeta").textContent = id && it.updatedAt ? "最終更新 " + fmtT(it.updatedAt) : "";
    openSheet("#sheet"); setTimeout(function () { $("#eName").focus(); }, 50);
  }
  $("#eSave").addEventListener("click", function () {
    var name = $("#eName").value.trim(); if (!name) { toast("品名を入力してください"); $("#eName").focus(); return; }
    var qty = Math.max(0, parseFloat($("#eQty").value) || 0), min = Math.max(0, parseFloat($("#eMin").value) || 0);
    var data = { name: name, qty: Math.round(qty * 100) / 100, unit: $("#eUnit").value, loc: $("#eLoc").value, min: min, memo: $("#eMemo").value.trim(), updatedAt: nowISO() };
    var id = editId, base = id ? (state.items[id] || {}) : {};
    data.order = base.order == null ? Object.keys(state.items).length : base.order;
    var isNew = !id; if (!id) id = uid();
    closeSheets(); writeItem(id, Object.assign({}, base, data)); toast(isNew ? "追加しました" : "保存しました");
  });
  $("#eDel").addEventListener("click", function () {
    if (!editId) return;
    if (!delArmed) { delArmed = true; this.textContent = "本当に削除する？"; return; }
    var id = editId, nm = state.items[id] && state.items[id].name; closeSheets(); removeItem(id); toast("「" + nm + "」を削除しました");
  });
  function openLoc() { $("#lName").value = ""; openSheet("#locSheet"); setTimeout(function () { $("#lName").focus(); }, 50); }
  $("#lSave").addEventListener("click", function () {
    var n = $("#lName").value.trim(); if (!n) { toast("場所の名前を入力してください"); return; }
    closeSheets(); writeLocs(state.locations.concat([{ id: "l" + Date.now().toString(36), name: n }])); toast("「" + n + "」を追加しました");
  });
  $("#addBtn").addEventListener("click", function () { openEdit(null, state.locations[0] && state.locations[0].id); });

  /* ---------- paste (bulk add / update) ----------
     Quantity = the LAST number on the line preceded by a space/colon, so names
     with digits ("豚バラ1.5mm 1") still parse. Units are an explicit list. */
  var UNIT = "(?:ケース|シート|パック|kg|㌜|本|個|缶|袋|枚|箱|束|玉|g|P|p)";
  var LINE_STRICT = new RegExp("^(.*\\S)[\\s:：]+([0-9]+(?:\\.[0-9]+)?)\\s*(" + UNIT + ")?\\s*(.*)$");
  var LINE_LOOSE = new RegExp("^(.*?)\\s*([0-9]+(?:\\.[0-9]+)?)\\s*(" + UNIT + ")?\\s*(.*)$");
  function parseLines(text) {
    var out = [];
    String(text || "").split(/\r?\n/).forEach(function (raw) {
      var line = raw.replace(/^[・\-\*•]\s*/, "").trim(); if (!line) return;
      var m = LINE_STRICT.exec(line) || LINE_LOOSE.exec(line);
      if (!m || !m[1].trim()) { out.push({ name: line, qty: 0, unit: "", memo: "", nonum: true }); return; }
      var unit = m[3] || "", memo = (m[4] || "").trim();
      if (memo) memo = "＋" + memo.replace(/^[と＋+、,]\s*/, "");
      out.push({ name: m[1].trim(), qty: parseFloat(m[2]), unit: unit, memo: memo });
    });
    return out;
  }
  function planPaste() {
    var locId = $("#pLoc").value, rows = parseLines($("#pText").value), add = 0, upd = 0, nonum = 0;
    var byName = {}; sortedIds(locId).forEach(function (id) { byName[String(state.items[id].name).trim()] = id; });
    rows.forEach(function (r) { if (r.nonum) nonum++; if (byName[r.name]) upd++; else add++; });
    return { rows: rows, byName: byName, add: add, upd: upd, nonum: nonum, locId: locId };
  }
  function previewPaste() {
    var p = planPaste(), el = $("#pPreview");
    if (!p.rows.length) { el.textContent = "貼り付けると、追加・更新の件数がここに出ます"; return; }
    el.innerHTML = "<b>" + p.add + "</b> 件を新規追加、<b>" + p.upd + "</b> 件の数量を更新" + (p.nonum ? "（数量が読めない行 " + p.nonum + " 件は 0 で追加）" : "");
  }
  $("#pasteBtn").addEventListener("click", function () { fillLocs($("#pLoc"), state.locations[0] && state.locations[0].id); $("#pText").value = ""; previewPaste(); openSheet("#pasteSheet"); setTimeout(function () { $("#pText").focus(); }, 50); });
  $("#pText").addEventListener("input", previewPaste); $("#pLoc").addEventListener("change", previewPaste);
  $("#pApply").addEventListener("click", function () {
    var p = planPaste(); if (!p.rows.length) { toast("貼り付ける内容がありません"); return; }
    var order = Object.keys(state.items).length, ts = nowISO();
    p.rows.forEach(function (r) {
      var id = p.byName[r.name];
      if (id) { var patch = { qty: r.qty, updatedAt: ts }; if (r.unit) patch.unit = r.unit; if (r.memo) patch.memo = r.memo; Object.assign(state.items[id], patch); }
      else { state.items[uid()] = { name: r.name, qty: r.qty, unit: r.unit, memo: r.memo, loc: p.locId, min: 1, order: order++, updatedAt: ts }; }
    });
    save(); render(); closeSheets(); toast("追加 " + p.add + " 件・更新 " + p.upd + " 件を反映しました");
  });

  /* ---------- copy ---------- */
  function listText(onlyNeeded) {
    var lines = [(onlyNeeded ? "📋 発注リスト " : "📦 在庫一覧 ") + fmtT(nowISO())], n = 0;
    state.locations.forEach(function (loc) {
      var ids = sortedIds(loc.id).filter(function (id) { return onlyNeeded ? status(state.items[id]) !== "ok" : true; });
      if (!ids.length) return; lines.push("", "【" + loc.name + "】");
      ids.forEach(function (id) { var it = state.items[id], s = status(it); n++; lines.push("・" + it.name + "　" + fmtQ(it.qty) + (it.unit || "") + (it.memo ? "（" + it.memo + "）" : "") + (s === "out" ? "　★切れ" : s === "low" ? "　▲要発注" : "")); });
    });
    return { text: lines.join("\n"), n: n };
  }
  $("#copyBtn").addEventListener("click", function () { var r = listText(true); if (!r.n) { toast("発注が必要な品目はありません"); return; } copyText(r.text, "発注リスト " + r.n + " 品目をコピーしました"); });
  $("#copyAllBtn").addEventListener("click", function () { var r = listText(false); if (!r.n) { toast("品目がありません"); return; } copyText(r.text, "全在庫 " + r.n + " 品目をコピーしました"); });
  function copyText(t, msg) {
    var done = function () { toast(msg); }, fail = function () { var ta = document.createElement("textarea"); ta.value = t; ta.style.position = "fixed"; ta.style.opacity = "0"; document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); done(); } catch (e) { toast("コピーできませんでした"); } ta.remove(); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, fail); else fail();
  }

  /* ---------- backup: export / import ---------- */
  $("#exportBtn").addEventListener("click", function () {
    var data = JSON.stringify({ app: "stockboard", version: 1, exportedAt: nowISO(), locations: state.locations, items: state.items }, null, 2);
    var blob = new Blob([data], { type: "application/json" }), url = URL.createObjectURL(blob);
    var a = document.createElement("a"); a.href = url; a.download = "stock-board-" + nowISO().slice(0, 10) + ".json";
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    toast("バックアップを書き出しました");
  });
  var importData = null;
  $("#importBtn").addEventListener("click", function () { $("#importFile").click(); });
  $("#importFile").addEventListener("change", function (e) {
    var f = e.target.files[0]; if (!f) return;
    var rd = new FileReader();
    rd.onload = function () {
      try {
        var d = JSON.parse(rd.result);
        if (!d || !d.items || !Array.isArray(d.locations)) throw new Error("bad");
        importData = { locations: d.locations, items: d.items };
        $("#iPreview").innerHTML = "<b>" + Object.keys(d.items).length + "</b> 品目・<b>" + d.locations.length + "</b> か所（" + (d.exportedAt ? fmtT(d.exportedAt) + " 書き出し" : "日時不明") + "）";
        openSheet("#importSheet");
      } catch (err) { toast("読み込めませんでした（このアプリの書き出しファイルを選んでください）"); }
      $("#importFile").value = "";
    };
    rd.readAsText(f);
  });
  $("#iApply").addEventListener("click", function () {
    if (!importData) return;
    state.locations = importData.locations; state.items = importData.items; importData = null;
    save(); render(); closeSheets(); toast("バックアップを読み込みました");
  });

  /* ---------- toast / theme ---------- */
  var tt; function toast(m) { var t = $("#toast"); t.textContent = m; t.classList.add("show"); clearTimeout(tt); tt = setTimeout(function () { t.classList.remove("show"); }, 2000); }
  function isDark() { var t = document.documentElement.getAttribute("data-theme"); if (t) return t === "dark"; return window.matchMedia("(prefers-color-scheme: dark)").matches; }
  function paintTheme() { $("#themeBtn").textContent = isDark() ? "☾" : "☀"; }
  (function () { var s = null; try { s = localStorage.getItem("stockboard.theme"); } catch (e) {} if (s === "dark" || s === "light") document.documentElement.setAttribute("data-theme", s); paintTheme(); })();
  $("#themeBtn").addEventListener("click", function () { var n = isDark() ? "light" : "dark"; document.documentElement.setAttribute("data-theme", n); try { localStorage.setItem("stockboard.theme", n); } catch (e) {} paintTheme(); });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", paintTheme);

  /* ---------- boot ---------- */
  if (!state.savedAt) save(); else paintMode();
  render();

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () { navigator.serviceWorker.register("sw.js").catch(function () {}); });
  }
})();
