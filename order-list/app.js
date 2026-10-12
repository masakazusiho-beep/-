/* ===== 発注チェック ===== */
(function () {
  "use strict";
  var $ = function (s) { return document.querySelector(s); };

  /* ---------- seed (仕入先別商品一覧より) ---------- */
  var SEED_SUPS = [
    { id: "s01", name: "西原商会（食材・調味料）" },
    { id: "s02", name: "西原商会（消耗品）" },
    { id: "s03", name: "岩田産業" },
    { id: "s04", name: "トーホー" },
    { id: "s05", name: "日本産業" },
    { id: "s06", name: "山方屋" },
    { id: "s07", name: "高瀬物産（消耗品）" },
    { id: "s08", name: "タカナシ乳業" },
    { id: "s09", name: "めいらく" },
    { id: "s10", name: "尾家産業" },
    { id: "s11", name: "ユーロトレーディング" },
    { id: "s12", name: "フレッシュ青果" }
  ];
  var SEED_ITEMS = (function () {
    var L = [
      ["s01","oneケチャップ"],["s01","フライドオニオン"],["s01","キユーピーマヨネーズ"],["s01","米酢"],
      ["s01","のり佃煮"],["s01","ミックスベリー"],["s01","麺つゆ"],["s01","サラダ油"],["s01","ポン酢"],
      ["s01","柚子胡椒"],["s01","ハチミツ"],["s01","昆布茶"],["s01","オニオンソテー"],
      ["s01","トルティーヤ",1],["s01","あおさのり",1],["s01","天日塩"],["s01","醤油"],["s01","ハリッサ"],
      ["s01","酒"],["s01","金山寺味噌"],["s01","コラビータEXオイル"],["s01","アサリ",1],["s01","ミックスハーブ"],
      ["s02","液体ハイター"],["s02","アルコール"],["s02","パワーストリームコンク"],["s02","アクシャルニュースター"],
      ["s02","ハンドペーパー"],["s02","リードペーパー"],["s02","ラップ"],["s02","アルミホイル"],["s02","クッキングシート"],
      ["s03","粉唐辛子"],["s03","バルサミコ"],["s03","グラニュー糖"],["s03","バター",1],["s03","韓国のり",1],
      ["s03","ムール貝",1],["s03","片栗粉"],["s03","薄力粉"],["s03","スライスポテト"],["s03","コクの力",1],
      ["s03","フライエシャ（赤ネギ）"],["s03","明太子",1],
      ["s04","トマトパウチ（レヴィーナ）",1],["s04","伯方の塩"],["s04","食べるラー油"],
      ["s05","しらす",1],["s05","ムキエビ",1],["s05","トビイカリング",1],
      ["s06","タン"],["s06","ハラミ"],["s06","豚バラスライス1.5mm"],["s06","豚バラブロック1.4cm"],
      ["s06","ミンチ類"],["s06","ベーコン"],["s06","レバー"],["s06","鶏モモ"],["s06","ヤゲン軟骨"],
      ["s07","70Lゴミ袋"],["s07","No.18ポリ袋"],
      ["s08","リコッタ"],["s08","レクレ",1],["s08","パルメザンパウダー",1],
      ["s09","MIXチーズ",1],
      ["s10","鮭"],["s10","バケット",1],["s10","ブラックペッパー"],["s10","フライドポテト"],["s10","鷹の爪"],["s10","フルードセル"],
      ["s11","ドンナローザ（トマト缶）",1],["s11","パルミジャーノブロック"],["s11","ゴルゴンゾーラ"],["s11","イカスミ",1],
      ["s11","サラミ"],["s11","スペック"],["s11","パプリカパウダー ピカンテ"],["s11","パプリカパウダー ドゥルセ"],
      ["s12","卵",1],["s12","ジャガイモ"],["s12","紫キャベツ"],["s12","にんにく"],["s12","キノコ（しめじ・舞茸・エリンギ）",1],
      ["s12","ムキ玉葱"],["s12","パプリカ"],["s12","紅志大根"],["s12","パセリ"],["s12","ディル"]
    ];
    var out = {};
    L.forEach(function (r, i) {
      out["i" + String(i).padStart(2, "0")] = { sup: r[0], name: r[1], freq: !!r[2], checked: false, note: "", order: i, updatedAt: "" };
    });
    return out;
  })();

  /* ---------- helpers ---------- */
  function uid() { return "i" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }
  function nowISO() { return new Date().toISOString(); }
  function fmtT(iso) { if (!iso) return ""; var d = new Date(iso); if (isNaN(d)) return ""; return (d.getMonth() + 1) + "/" + d.getDate() + " " + String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0"); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  /* ---------- storage (this device) ---------- */
  var KEY = "orderlist.v1";
  var state = { suppliers: SEED_SUPS.slice(), items: JSON.parse(JSON.stringify(SEED_ITEMS)), filter: "all", q: "", collapsed: {}, savedAt: "" };
  (function load() {
    try {
      var r = localStorage.getItem(KEY);
      if (r) { var d = JSON.parse(r); if (d && d.items && Array.isArray(d.suppliers)) { state.suppliers = d.suppliers; state.items = d.items; state.savedAt = d.savedAt || ""; } }
    } catch (e) {}
  })();
  var storageOK = true;
  function save() {
    state.savedAt = nowISO();
    try { localStorage.setItem(KEY, JSON.stringify({ suppliers: state.suppliers, items: state.items, savedAt: state.savedAt })); storageOK = true; }
    catch (e) { storageOK = false; toast("保存できませんでした（端末の空き容量やブラウザ設定をご確認ください）"); }
    paintMode();
  }
  function paintMode() { $("#modeTxt").textContent = storageOK ? ("この端末に保存" + (state.savedAt ? "　" + fmtT(state.savedAt) : "")) : "保存できません"; $("#mode").className = "mode " + (storageOK ? "local" : "err"); }

  function writeItem(id, data) { state.items[id] = data; save(); render(); }
  function patchItem(id, patch) { if (!state.items[id]) return; Object.assign(state.items[id], patch); save(); render(); }
  function removeItem(id) { delete state.items[id]; save(); render(); }
  function writeSups(sups) { state.suppliers = sups; save(); render(); }

  /* ---------- render ---------- */
  var listEl = $("#list");
  function counts() { var c = 0, f = 0, a = 0; Object.keys(state.items).forEach(function (id) { a++; var it = state.items[id]; if (it.checked) c++; if (it.freq) f++; }); return { checked: c, freq: f, all: a }; }
  function sortedIds(supId) { return Object.keys(state.items).filter(function (id) { return state.items[id].sup === supId; }).sort(function (a, b) { return (state.items[a].order || 0) - (state.items[b].order || 0) || String(state.items[a].name).localeCompare(String(state.items[b].name), "ja"); }); }
  function render() {
    var c = counts();
    $("#nChecked").textContent = c.checked; $("#nFreq").textContent = c.freq; $("#nAll").textContent = c.all;
    ["checked", "freq", "all"].forEach(function (f) { document.querySelector('[data-filter="' + f + '"]').classList.toggle("on", state.filter === f); });
    var q = state.q.trim().toLowerCase();
    listEl.innerHTML = ""; var any = false;
    state.suppliers.forEach(function (sup) {
      var ids = sortedIds(sup.id), ck = 0;
      ids.forEach(function (id) { if (state.items[id].checked) ck++; });
      var shown = ids.filter(function (id) {
        var it = state.items[id];
        if (state.filter === "checked" && !it.checked) return false;
        if (state.filter === "freq" && !it.freq) return false;
        if (q && String(it.name).toLowerCase().indexOf(q) < 0 && String(it.note || "").toLowerCase().indexOf(q) < 0) return false;
        return true;
      });
      if ((state.filter !== "all" || q) && shown.length === 0) return;
      any = true;
      var closed = state.collapsed[sup.id] && !q && state.filter === "all";
      var sec = document.createElement("section"); sec.className = "sec" + (closed ? " closed" : "");
      sec.innerHTML = '<div class="sec-h"><button class="toggle" data-sup="' + esc(sup.id) + '" aria-expanded="' + (closed ? "false" : "true") + '">' +
        '<span class="chev">▼</span><h2>' + esc(sup.name) + '</h2><span class="cnt">' + ids.length + '品目</span>' +
        (ck ? '<span class="badge on">✓ ' + ck + '</span>' : '') + '</button>' +
        '<button class="add" data-addto="' + esc(sup.id) + '" aria-label="この仕入先に品目を追加">＋</button></div><div class="rows"></div>';
      var rows = sec.querySelector(".rows");
      if (!shown.length) rows.innerHTML = '<div class="empty">品目がありません</div>';
      shown.forEach(function (id) {
        var it = state.items[id];
        var r = document.createElement("div"); r.className = "row" + (it.freq ? " freq" : "") + (it.checked ? " checked" : "");
        r.innerHTML = '<button class="chk" data-chk="' + id + '" aria-label="発注チェック" aria-pressed="' + (it.checked ? "true" : "false") + '"><span class="box"></span></button>' +
          '<button class="name" data-edit="' + id + '"><span class="nm">' + esc(it.name) + (it.freq ? '<span class="star">★頻度多め</span>' : '') + '</span>' +
          (it.note ? '<span class="sub">' + esc(it.note) + '</span>' : '') + '</button>';
        rows.appendChild(r);
      });
      listEl.appendChild(sec);
    });
    if (!any) { var e = document.createElement("div"); e.className = "empty"; e.textContent = q ? "「" + state.q + "」に一致する品目はありません" : state.filter === "checked" ? "チェック中の品目はありません" : "頻度多めの品目はありません"; listEl.appendChild(e); }
    if (state.filter === "all" && !q) { var b = document.createElement("button"); b.className = "add-loc"; b.id = "addSup"; b.textContent = "＋ 仕入先を追加"; listEl.appendChild(b); }
  }

  /* ---------- interactions ---------- */
  listEl.addEventListener("click", function (e) {
    var t = e.target.closest("button"); if (!t) return;
    if (t.dataset.sup) { state.collapsed[t.dataset.sup] = !state.collapsed[t.dataset.sup]; render(); return; }
    if (t.dataset.addto) { openEdit(null, t.dataset.addto); return; }
    if (t.dataset.edit) { openEdit(t.dataset.edit); return; }
    if (t.id === "addSup") { openSup(); return; }
    if (t.dataset.chk) { var it = state.items[t.dataset.chk]; if (!it) return; patchItem(t.dataset.chk, { checked: !it.checked, updatedAt: nowISO() }); return; }
  });
  document.querySelector(".stats").addEventListener("click", function (e) { var b = e.target.closest("[data-filter]"); if (!b) return; state.filter = b.dataset.filter; render(); });
  $("#q").addEventListener("input", function () { state.q = this.value; render(); });

  /* edit sheet */
  var editId = null, delArmed = false;
  function fillSups(sel, val) { sel.innerHTML = ""; state.suppliers.forEach(function (s) { var o = document.createElement("option"); o.value = s.id; o.textContent = s.name; sel.appendChild(o); }); sel.value = val || (state.suppliers[0] && state.suppliers[0].id) || ""; }
  function openSheet(id) { $("#backdrop").hidden = false; $(id).hidden = false; }
  function closeSheets() { $("#backdrop").hidden = true; ["#sheet", "#supSheet"].forEach(function (s) { $(s).hidden = true; }); editId = null; }
  $("#backdrop").addEventListener("click", closeSheets);
  function openEdit(id, supId) {
    editId = id; delArmed = false;
    var it = id ? state.items[id] : { name: "", sup: supId, freq: false, checked: false, note: "" };
    $("#sheetTitle").textContent = id ? "品目を編集" : "品目を追加";
    $("#eName").value = it.name || ""; $("#eFreq").checked = !!it.freq; $("#eNote").value = it.note || "";
    fillSups($("#eSup"), it.sup);
    $("#eDel").hidden = !id; $("#eDel").textContent = "削除";
    $("#eMeta").textContent = id && it.updatedAt ? "最終更新 " + fmtT(it.updatedAt) : "";
    openSheet("#sheet"); setTimeout(function () { $("#eName").focus(); }, 50);
  }
  $("#eSave").addEventListener("click", function () {
    var name = $("#eName").value.trim(); if (!name) { toast("品名を入力してください"); $("#eName").focus(); return; }
    var data = { name: name, sup: $("#eSup").value, freq: $("#eFreq").checked, note: $("#eNote").value.trim(), updatedAt: nowISO() };
    var id = editId, base = id ? (state.items[id] || {}) : {};
    data.checked = base.checked || false;
    data.order = base.order == null ? Object.keys(state.items).length : base.order;
    var isNew = !id; if (!id) id = uid();
    closeSheets(); writeItem(id, Object.assign({}, base, data)); toast(isNew ? "追加しました" : "保存しました");
  });
  $("#eDel").addEventListener("click", function () {
    if (!editId) return;
    if (!delArmed) { delArmed = true; this.textContent = "本当に削除する？"; return; }
    var id = editId, nm = state.items[id] && state.items[id].name; closeSheets(); removeItem(id); toast("「" + nm + "」を削除しました");
  });
  function openSup() { $("#supName").value = ""; openSheet("#supSheet"); setTimeout(function () { $("#supName").focus(); }, 50); }
  $("#supSave").addEventListener("click", function () {
    var n = $("#supName").value.trim(); if (!n) { toast("仕入先の名前を入力してください"); return; }
    closeSheets(); writeSups(state.suppliers.concat([{ id: "u" + Date.now().toString(36), name: n }])); toast("「" + n + "」を追加しました");
  });
  $("#addBtn").addEventListener("click", function () { openEdit(null, state.suppliers[0] && state.suppliers[0].id); });

  /* ---------- 全解除 ---------- */
  $("#resetBtn").addEventListener("click", function () {
    var c = counts(); if (!c.checked) { toast("チェック中の品目はありません"); return; }
    if (!confirm("チェック中の " + c.checked + " 品目を全部解除する？（発注し終わったときに）")) return;
    Object.keys(state.items).forEach(function (id) { state.items[id].checked = false; });
    save(); render(); toast("チェックを全解除しました");
  });

  /* ---------- copy ---------- */
  function listText() {
    var lines = ["📋 発注リスト " + fmtT(nowISO())], n = 0;
    state.suppliers.forEach(function (sup) {
      var ids = sortedIds(sup.id).filter(function (id) { return state.items[id].checked; });
      if (!ids.length) return; lines.push("", "【" + sup.name + "】");
      ids.forEach(function (id) { var it = state.items[id]; n++; lines.push("・" + it.name + (it.freq ? "　★頻度多め" : "") + (it.note ? "（" + it.note + "）" : "")); });
    });
    return { text: lines.join("\n"), n: n };
  }
  $("#copyBtn").addEventListener("click", function () { var r = listText(); if (!r.n) { toast("チェック中の品目がありません"); return; } copyText(r.text, "発注リスト " + r.n + " 品目をコピーしました"); });
  function copyText(t, msg) {
    var done = function () { toast(msg); }, fail = function () { var ta = document.createElement("textarea"); ta.value = t; ta.style.position = "fixed"; ta.style.opacity = "0"; document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); done(); } catch (e) { toast("コピーできませんでした"); } ta.remove(); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, fail); else fail();
  }

  /* ---------- backup: export / import ---------- */
  $("#exportBtn").addEventListener("click", function () {
    var data = JSON.stringify({ app: "orderlist", version: 1, exportedAt: nowISO(), suppliers: state.suppliers, items: state.items }, null, 2);
    var blob = new Blob([data], { type: "application/json" }), url = URL.createObjectURL(blob);
    var a = document.createElement("a"); a.href = url; a.download = "order-list-" + nowISO().slice(0, 10) + ".json";
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
        if (!d || !d.items || !Array.isArray(d.suppliers)) throw new Error("bad");
        importData = { suppliers: d.suppliers, items: d.items };
        $("#iPreview").innerHTML = "<b>" + Object.keys(d.items).length + "</b> 品目・<b>" + d.suppliers.length + "</b> 仕入先（" + (d.exportedAt ? fmtT(d.exportedAt) + " 書き出し" : "日時不明") + "）";
        openSheet("#importSheet");
      } catch (err) { toast("読み込めませんでした（このアプリの書き出しファイルを選んでください）"); }
      $("#importFile").value = "";
    };
    rd.readAsText(f);
  });
  $("#iApply").addEventListener("click", function () {
    if (!importData) return;
    state.suppliers = importData.suppliers; state.items = importData.items; importData = null;
    save(); render(); closeSheets(); toast("バックアップを読み込みました");
  });

  /* ---------- toast / theme ---------- */
  var tt; function toast(m) { var t = $("#toast"); t.textContent = m; t.classList.add("show"); clearTimeout(tt); tt = setTimeout(function () { t.classList.remove("show"); }, 2000); }
  function isDark() { var t = document.documentElement.getAttribute("data-theme"); if (t) return t === "dark"; return window.matchMedia("(prefers-color-scheme: dark)").matches; }
  function paintTheme() { $("#themeBtn").textContent = isDark() ? "☾" : "☀"; }
  (function () { var s = null; try { s = localStorage.getItem("orderlist.theme"); } catch (e) {} if (s === "dark" || s === "light") document.documentElement.setAttribute("data-theme", s); paintTheme(); })();
  $("#themeBtn").addEventListener("click", function () { var n = isDark() ? "light" : "dark"; document.documentElement.setAttribute("data-theme", n); try { localStorage.setItem("orderlist.theme", n); } catch (e) {} paintTheme(); });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", paintTheme);

  /* ---------- boot ---------- */
  if (!state.savedAt) save(); else paintMode();
  render();

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () { navigator.serviceWorker.register("sw.js").catch(function () {}); });
  }
})();
