(() => {
  "use strict";
  const CATALOG = window.CATALOG || {};
  const SITE = window.SITE || {};
  const BASE = SITE.base || "";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = n => n.toLocaleString("uk-UA") + " грн";

  // ---------- Тост
  let toastTimer;
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg; t.classList.add("show");
    clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove("show"), 3000);
  }

  // ---------- Утримання фокуса в діалогах
  const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]):not([tabindex="-1"]), select, textarea, [tabindex]:not([tabindex="-1"])';
  function trapFocus(container, e) {
    if (e.key !== "Tab") return;
    const items = $$(FOCUSABLE, container).filter(el => el.offsetParent !== null);
    if (!items.length) return;
    const first = items[0], last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  // ---------- Надсилання форм (єдине місце підключення)
  // Щоб заявки почали надходити, вкажіть адресу обробника в data/site.json → formEndpoint
  // (наприклад, Formspree, власний сервер або вебхук CRM / Telegram-бота), потім запустіть build.py.
  async function send(type, payload) {
    if (!SITE.formEndpoint) return "not-configured";
    try {
      const r = await fetch(SITE.formEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ type, page: location.pathname, ...payload }),
      });
      return r.ok ? "ok" : "error";
    } catch { return "error"; }
  }

  function fallbackHtml(reason) {
    const ways = [];
    if (SITE.phone) ways.push(`зателефонуйте: <a href="${esc(SITE.phoneHref)}">${esc(SITE.phone)}</a>`);
    if (SITE.telegramUrl) ways.push(`напишіть у <a href="${esc(SITE.telegramUrl)}" target="_blank" rel="noopener">Telegram</a>`);
    if (SITE.email) ways.push(`напишіть на <a href="mailto:${esc(SITE.email)}">${esc(SITE.email)}</a>`);
    const head = reason === "not-configured"
      ? "Онлайн-заявки на сайті ще не підключено, тому ми її не отримали."
      : "Не вдалося надіслати заявку. Перевірте зʼєднання і спробуйте ще раз.";
    return `<p class="form__err">${head}${ways.length ? " Будь ласка, " + ways.join(" або ") + "." : ""}</p>`;
  }

  function validPhone(v) {
    const d = v.replace(/\D/g, "");
    return /^380\d{9}$/.test(d) || /^0\d{9}$/.test(d);
  }

  function validate(form) {
    let firstBad = null;
    const mark = (el, bad, msg) => {
      el.setAttribute("aria-invalid", bad ? "true" : "false");
      if (bad && !firstBad) firstBad = { el, msg };
    };
    $$("[required]", form).forEach(el => {
      if (el.type === "checkbox") mark(el, !el.checked, "Потрібна згода на обробку персональних даних");
      else if (el.type === "tel") mark(el, !validPhone(el.value), "Вкажіть телефон у форматі +380 XX XXX XX XX");
      else if (el.type === "email") mark(el, !/^\S+@\S+\.\S+$/.test(el.value.trim()), "Вкажіть коректний email");
      else mark(el, !el.value.trim(), "Заповніть обовʼязкові поля");
    });
    if (firstBad) { toast(firstBad.msg); firstBad.el.focus(); return false; }
    return true;
  }

  async function handleForm(form, type, extra, onOk) {
    if (!validate(form)) return;
    const data = Object.fromEntries(new FormData(form));
    if (data.website) return;                       // пастка для ботів
    delete data.website; delete data.consent;
    const btn = $("button[type=submit], button:not([type])", form);
    const result = $(".form__result", form) || form.appendChild(Object.assign(document.createElement("div"), { className: "form__result" }));
    result.setAttribute("role", "status");
    btn.disabled = true;
    const status = await send(type, { ...data, ...extra });
    btn.disabled = false;
    if (status === "ok") {
      result.innerHTML = '<p class="form__ok">Дякуємо! Заявку отримано, ми звʼяжемося з вами.</p>';
      form.reset();
      if (onOk) onOk();
    } else {
      result.innerHTML = fallbackHtml(status);
    }
  }

  $$("[data-form=lead]").forEach(f => f.addEventListener("submit", e => { e.preventDefault(); handleForm(f, "lead"); }));
  $$("[data-form=subscribe]").forEach(f => f.addEventListener("submit", e => { e.preventDefault(); handleForm(f, "subscribe"); }));

  // ---------- Кошик
  let cart = {};
  try { cart = JSON.parse(localStorage.getItem("cart") || "{}"); } catch { cart = {}; }
  Object.keys(cart).forEach(id => { if (!CATALOG[id]) delete cart[id]; });
  const save = () => { try { localStorage.setItem("cart", JSON.stringify(cart)); } catch {} };

  const drawer = $("#drawer");
  let lastFocus = null;

  function addToCart(id, qty) {
    const p = CATALOG[id]; if (!p) return;
    cart[id] = (cart[id] || 0) + qty; save(); renderCart();
    toast(`${p.b ? "Додано в кошик" : "Додано до запиту"}: ${p.n}`);
    const c = $("#cartCount"); c.classList.remove("bump"); void c.offsetWidth; c.classList.add("bump");
  }

  function renderCart() {
    const items = Object.entries(cart).map(([id, q]) => ({ id, p: CATALOG[id], q }));
    const total = items.reduce((s, i) => s + i.q, 0);
    $("#cartCount").textContent = total;
    $("#cartOpen").setAttribute("aria-label", `Відкрити кошик, позицій: ${total}`);
    if (!items.length) {
      $("#cartBody").innerHTML = '<p class="cart-empty">Кошик порожній.<br>Додайте товари з каталогу.</p>';
      $("#cartFoot").innerHTML = ""; return;
    }
    const buy = items.filter(i => i.p.b), ask = items.filter(i => !i.p.b);
    const row = ({ id, p, q }) => `
      <div class="ci">
        <a class="ci__name" href="${p.url}">${esc(p.n)}</a>
        <span class="ci__price">${p.b ? fmt(p.p * q) : "ціна в пропозиції"}</span>
        <div class="ci__row">
          <span class="qty"><button type="button" data-dq="${id}" data-d="-1" aria-label="Зменшити кількість">−</button><input value="${q}" readonly aria-label="Кількість"><button type="button" data-dq="${id}" data-d="1" aria-label="Збільшити кількість">+</button></span>
          <button type="button" class="ci__rm" data-rm="${id}">Видалити</button>
        </div>
      </div>`;
    $("#cartBody").innerHTML =
      (buy.length ? `<h3 class="cart-group">Замовлення</h3>${buy.map(row).join("")}` : "") +
      (ask.length ? `<h3 class="cart-group">Запит комерційної пропозиції</h3><p class="cart-note">Ціну на ці позиції розрахуємо окремо — вона не входить у суму нижче.</p>${ask.map(row).join("")}` : "");
    const sum = buy.reduce((s, i) => s + i.p.p * i.q, 0);
    $("#cartFoot").innerHTML = `
      ${buy.length ? `<div class="cart-total"><span>Сума замовлення</span><span>${fmt(sum)}</span></div><p class="cart-note">Без вартості доставки${ask.length ? " та позицій із запиту" : ""}.</p>` : ""}
      <form class="form" id="orderForm" novalidate>
        <input name="name" placeholder="Імʼя" aria-label="Імʼя" required autocomplete="name">
        <input name="phone" type="tel" placeholder="+380 XX XXX XX XX" aria-label="Телефон" required autocomplete="tel" inputmode="tel">
        <input name="city" placeholder="Місто доставки" aria-label="Місто доставки" autocomplete="address-level2">
        <label class="check"><input type="checkbox" name="consent" required> <span>Погоджуюся на обробку персональних даних відповідно до <a href="${BASE}/polityka-konfidentsiinosti/">політики конфіденційності</a></span></label>
        <div class="hp" aria-hidden="true"><input type="text" name="website" tabindex="-1" autocomplete="off"></div>
        <button class="btn btn--primary btn--block" type="submit">${buy.length ? "Оформити замовлення" : "Надіслати запит"}</button>
        <div class="form__result" role="status" aria-live="polite"></div>
      </form>`;
    $("#orderForm").addEventListener("submit", e => {
      e.preventDefault();
      const lines = items.map(i => ({ id: i.id, name: i.p.n, qty: i.q, price: i.p.b ? i.p.p : null }));
      handleForm(e.target, "order", { items: lines, total: sum }, () => {
        cart = {}; save();
        $("#cartBody").innerHTML = '<p class="cart-empty">Дякуємо! Замовлення отримано.</p>';
        $("#cartCount").textContent = "0";
      });
    });
  }

  $("#cartBody").addEventListener("click", e => {
    const d = e.target.closest("[data-dq]"), r = e.target.closest("[data-rm]");
    if (d) { const id = d.dataset.dq; cart[id] += +d.dataset.d; if (cart[id] < 1) delete cart[id]; }
    if (r) delete cart[r.dataset.rm];
    if (d || r) {
      save(); renderCart();
      const again = d && $(`[data-dq="${d.dataset.dq}"][data-d="${d.dataset.d}"]`);
      (again || $(".drawer__panel")).focus();
    }
  });

  function openCart() {
    lastFocus = document.activeElement;
    drawer.hidden = false; document.body.classList.add("no-scroll");
    $(".drawer__panel").focus();
  }
  function closeCart() {
    if (drawer.hidden) return;
    drawer.hidden = true; document.body.classList.remove("no-scroll");
    if (lastFocus) lastFocus.focus();
  }
  $("#cartOpen").addEventListener("click", openCart);
  drawer.addEventListener("click", e => { if (e.target.closest("[data-close-cart]")) closeCart(); });
  drawer.addEventListener("keydown", e => trapFocus($(".drawer__panel"), e));

  document.addEventListener("click", e => {
    const b = e.target.closest("[data-add]"); if (!b) return;
    const qtyInput = b.closest(".pd__actions") && $("#pdQty");
    addToCart(b.dataset.add, qtyInput ? Math.max(1, +qtyInput.value || 1) : 1);
  });

  // ---------- Сторінка товару: галерея і кількість
  $$(".pd__thumb").forEach(b => b.addEventListener("click", () => {
    const m = $("#pdMain"), base = `${BASE}/img/products/${b.dataset.img}`;
    m.srcset = `${base}-sm.webp 480w, ${base}.webp 1000w`; m.src = `${base}.webp`;
    $$(".pd__thumb").forEach(x => { const on = x === b; x.classList.toggle("is-active", on); x.setAttribute("aria-pressed", on); });
  }));
  $$(".pd__actions [data-q]").forEach(b => b.addEventListener("click", () => {
    const i = $("#pdQty"); i.value = Math.max(1, (+i.value || 1) + +b.dataset.q);
  }));

  // ---------- Каталог на головній: фільтр, пошук, сортування
  const grid = $("#grid");
  if (grid && $("#filters")) {
    const cards = $$(".card", grid);
    cards.forEach((c, i) => (c.dataset.i = i));
    const state = { cat: "all", q: "", sort: "default" };
    const apply = () => {
      let shown = 0;
      cards.forEach(c => {
        const ok = (state.cat === "all" || c.dataset.cat === state.cat) && (!state.q || c.dataset.name.includes(state.q));
        c.hidden = !ok; if (ok) shown++;
      });
      const key = state.sort === "default" ? (a, b) => a.dataset.i - b.dataset.i
        : state.sort === "price-asc" ? (a, b) => a.dataset.price - b.dataset.price
        : (a, b) => b.dataset.price - a.dataset.price;
      [...cards].sort(key).forEach(c => grid.appendChild(c));
      $("#empty").hidden = shown > 0;
    };
    $("#filters").addEventListener("click", e => {
      const b = e.target.closest("[data-filter]"); if (!b) return;
      state.cat = b.dataset.filter;
      $$("[data-filter]").forEach(x => { const on = x === b; x.classList.toggle("is-active", on); x.setAttribute("aria-pressed", on); });
      apply();
    });
    $("#search").addEventListener("input", e => { state.q = e.target.value.trim().toLowerCase(); apply(); });
    $("#sort").addEventListener("change", e => { state.sort = e.target.value; apply(); });
  }

  // ---------- Калькулятор пральні (спрощена оцінка)
  if ($("#calcResult")) {
    const calc = () => {
      const rooms = +$("#rooms").value, occ = +$("#occ").value;
      $("#roomsOut").textContent = rooms; $("#occOut").textContent = occ;
      const kgDay = Math.round(rooms * occ / 100 * 4.5);
      const perCycle = Math.ceil(kgDay / 4);
      const n = Math.max(kgDay > 60 ? 2 : 1, Math.ceil(perCycle / 45));
      const each = Math.min(45, Math.max(12, Math.ceil(perCycle / n)));
      $("#calcResult").innerHTML = `
        <h3>Орієнтовна потреба</h3>
        <p class="calc__big">${kgDay} кг на день</p>
        <ul class="calc__list">
          <li><span>Пральні машини</span><b>${n} × близько ${each} кг</b></li>
          <li><span>Сушильні машини</span><b>${n > 1 ? "двоярусні DD або " : ""}${n} × DS</b></li>
          <li><span>Завантаження за цикл</span><b>${perCycle} кг</b></li>
        </ul>
        <a href="#contacts" class="btn btn--primary btn--block">Отримати точний розрахунок</a>`;
    };
    ["rooms", "occ"].forEach(id => $("#" + id).addEventListener("input", calc));
    calc();
  }

  // ---------- Мобільне меню
  const nav = $("#nav"), burger = $("#burger"), backdrop = $("#navBackdrop");
  function setNav(open) {
    nav.classList.toggle("open", open);
    burger.setAttribute("aria-expanded", open);
    backdrop.hidden = !open;
    if (!open && document.activeElement && nav.contains(document.activeElement)) burger.focus();
  }
  burger.addEventListener("click", () => setNav(!nav.classList.contains("open")));
  backdrop.addEventListener("click", () => setNav(false));
  nav.addEventListener("click", e => { if (e.target.closest("a")) setNav(false); });

  // ---------- Кнопка звʼязку
  const chat = $("#chat"), chatBtn = $("#chatBtn");
  function setChat(open) { chat.classList.toggle("open", open); chatBtn.setAttribute("aria-expanded", open); }
  if (chatBtn) chatBtn.addEventListener("click", () => setChat(!chat.classList.contains("open")));

  document.addEventListener("keydown", e => {
    if (e.key !== "Escape") return;
    closeCart(); setNav(false); if (chat) setChat(false);
  });

  renderCart();
})();
