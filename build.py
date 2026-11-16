#!/usr/bin/env python3
"""Збирання сайту: data/*.json + css/js/img/fonts  ->  dist/ (готові HTML-сторінки).

Запуск:   python3 build.py
          python3 build.py --real --out dist-real   (як виглядатиме сайт БЕЗ демо-даних)
          python3 build.py --out docs --base /laundry-site   (версія для GitHub Pages)
Перегляд: python3 -m http.server 8080 --directory dist
Нічого встановлювати не потрібно — лише стандартний Python 3.
"""
import json, re, shutil, sys
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"

site_raw = json.loads((ROOT / "data/site.json").read_text(encoding="utf-8"))
cat_raw = json.loads((ROOT / "data/products.json").read_text(encoding="utf-8"))

DEMO = bool(site_raw.get("demoMode")) and "--real" not in sys.argv
if "--out" in sys.argv:
    DIST = ROOT / sys.argv[sys.argv.index("--out") + 1]
# --base /назва-репозиторію : сайт лежить у підпапці (GitHub Pages без власного домену)
BASE = sys.argv[sys.argv.index("--base") + 1].rstrip("/") if "--base" in sys.argv else ""


def _filled(v):
    if isinstance(v, list):
        return any(_filled(x) for x in v)
    return bool(v)


# Чинні налаштування: справжні значення; у демо-режимі порожні місця заповнюються демо-даними.
S = {}
for key in set(site_raw["real"]) | set(site_raw["demo"]):
    real = site_raw["real"].get(key)
    S[key] = real if _filled(real) else (site_raw["demo"].get(key) if DEMO else real)
    if not _filled(S[key]):
        S[key] = [] if isinstance(site_raw["demo"].get(key), list) else ""

BRAND = S["brandName"] or "Пральне обладнання"
SITE_URL = S["siteUrl"].rstrip("/")
CATS = cat_raw["categories"]
CAT = {c["id"]: c for c in CATS}

PRODUCTS = []
for p in cat_raw["products"]:
    if p.get("demo") and not DEMO:
        continue
    p = dict(p)
    p["specsAll"] = {**p.get("specs", {}), **(p.get("demoSpecs", {}) if DEMO else {})}
    p["priceShown"] = p.get("price") if p.get("price") else (p.get("demoPrice") if DEMO else None)
    p["priceConfirmed"] = bool(p.get("price"))
    p["type"] = CAT[p["cat"]]["type"]
    p["buyable"] = p["type"] == "consumable" and p["priceShown"] is not None
    p["url"] = f"/{CAT[p['cat']]['slug']}/{p['slug']}/"
    PRODUCTS.append(p)

VISIBLE_CATS = [c for c in CATS if any(p["cat"] == c["id"] for p in PRODUCTS)]
for c in VISIBLE_CATS:
    c["url"] = f"/{c['slug']}/"

ICONS = {
    "washer": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><rect x="8" y="5" width="32" height="38" rx="5"/><line x1="8" y1="14" x2="40" y2="14"/><circle cx="14" cy="9.5" r="1.3" fill="currentColor"/><circle cx="24" cy="28" r="9"/><path d="M18 29c2-2 4 2 6 0s4-1 6 0"/></svg>',
    "dryer": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><rect x="8" y="5" width="32" height="38" rx="5"/><line x1="8" y1="14" x2="40" y2="14"/><circle cx="24" cy="28" r="9"/><path d="M20 24c2 2-2 4 0 6M24 24c2 2-2 4 0 6M28 24c2 2-2 4 0 6"/></svg>',
    "stack": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><rect x="12" y="3" width="24" height="42" rx="4"/><line x1="12" y1="24" x2="36" y2="24"/><circle cx="24" cy="14" r="6"/><circle cx="24" cy="35" r="6"/></svg>',
    "iron": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><rect x="5" y="14" width="38" height="16" rx="8"/><circle cx="13" cy="22" r="4"/><line x1="10" y1="30" x2="8" y2="42"/><line x1="38" y1="30" x2="40" y2="42"/><path d="M18 8c0-2 2-2 2-4M24 8c0-2 2-2 2-4M30 8c0-2 2-2 2-4"/></svg>',
    "dryclean": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round" aria-hidden="true"><path d="M17 7 7 12l3 8 4-2v22h20V18l4 2 3-8-10-5c-1 3-4 4-7 4s-6-1-7-4Z"/><path d="M24 22v8M20 26h8" stroke-linecap="round"/></svg>',
    "chem": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M18 5h12M20 5v10l-9 19a5 5 0 0 0 4.5 7h17a5 5 0 0 0 4.5-7l-9-19V5"/><path d="M14 30h20"/><circle cx="21" cy="35" r="1.5" fill="currentColor"/><circle cx="27" cy="34" r="1" fill="currentColor"/></svg>',
    "box": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M6 15 24 6l18 9v18l-18 9-18-9V15Z"/><path d="m6 15 18 9 18-9M24 24v18"/></svg>',
}
LOGO_SVG = '<svg viewBox="0 0 32 32" width="32" height="32" aria-hidden="true"><rect x="3" y="3" width="26" height="26" rx="7" fill="currentColor"/><circle cx="16" cy="17" r="7" fill="none" stroke="#fff" stroke-width="2.5"/><circle cx="9" cy="8.5" r="1.5" fill="#fff"/><path d="M11 18c2-2 4 2 6 0s3-1 4 0" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>'


# ---------- дрібні помічники
def money(n):
    return f"{n:,}".replace(",", " ") + " грн"


def tel_href(phone):
    return "tel:+" + re.sub(r"\D", "", phone)


def absu(path):
    return (SITE_URL or BASE) + path


def with_base(html):
    """Додає префікс підпапки до всіх внутрішніх адрес у готовій сторінці."""
    if not BASE:
        return html
    html = re.sub(r'(href|src|srcset)="/(?!/)', rf'\1="{BASE}/', html)
    return html.replace(", /img/", f", {BASE}/img/")


def img(name, alt, sizes, cls="", eager=False):
    extra = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} src="/img/products/{name}-sm.webp" '
            f'srcset="/img/products/{name}-sm.webp 480w, /img/products/{name}.webp 1000w" '
            f'sizes="{sizes}" width="480" height="480" alt="{e(alt)}" {extra}>')


def price_html(p):
    if p["priceShown"] is None:
        return '<span class="price price--ask">Ціна за запитом</span>'
    if p["type"] == "equipment":
        return f'<span class="price"><small>орієнтовно від</small>{money(p["priceShown"])}</span>'
    return f'<span class="price"><small>за {e(p.get("unit", "шт."))}</small>{money(p["priceShown"])}</span>'


def add_btn(p, big=False):
    label = "У кошик" if p["buyable"] else "Запит ціни"
    if big:
        label = "Додати в кошик" if p["buyable"] else "Додати до запиту"
    cls = "btn--primary" if (p["buyable"] or big) else "btn--outline"
    size = "" if big else " btn--sm"
    return f'<button type="button" class="btn {cls}{size}" data-add="{p["id"]}">{label}</button>'


def specs_html(p, limit=99):
    rows = "".join(f"<li><span>{e(k)}</span><b>{e(v)}</b></li>" for k, v in list(p["specsAll"].items())[:limit])
    return f'<ul class="card__specs">{rows}</ul>' if rows else ""


def card(p, h="h3"):
    cat = CAT[p["cat"]]
    if p.get("img"):
        visual = img(p["img"][0], p["name"], "(max-width: 560px) 90vw, 280px")
        photo = " card__img--photo"
    else:
        visual, photo = ICONS[cat["icon"]], ""
    badge = f'<span class="badge">{e(p["badge"])}</span>' if p.get("badge") else ""
    tag = "В наявності" if p["buyable"] else "Під замовлення"
    return f'''<article class="card" data-cat="{p["cat"]}" data-price="{p["priceShown"] or 0}" data-name="{e((p["name"] + " " + p["desc"]).lower())}">
  <a class="card__img{photo}" href="{p["url"]}" tabindex="-1" aria-hidden="true">{visual}{badge}<span class="card__tag">{tag}</span></a>
  <div class="card__body">
    <span class="card__cat">{e(cat["name"])}</span>
    <{h} class="card__title"><a href="{p["url"]}">{e(p["name"])}</a></{h}>
    {specs_html(p, 3)}
    <div class="card__foot">{price_html(p)}{add_btn(p)}</div>
  </div>
</article>'''


def crumbs(items):
    """items: [(name, url|None)]"""
    lis = "".join(
        f'<li><a href="{u}">{e(n)}</a></li>' if u else f'<li aria-current="page">{e(n)}</li>' for n, u in items)
    return f'<nav class="crumbs" aria-label="Навігаційний ланцюжок"><ol>{lis}</ol></nav>'


def crumbs_schema(items, path):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": absu(u or path)} for i, (n, u) in enumerate(items)]}


def consent_field(idp):
    return (f'<label class="check"><input type="checkbox" name="consent" required id="{idp}Consent"> '
            f'<span>Погоджуюся на обробку персональних даних відповідно до '
            f'<a href="/polityka-konfidentsiinosti/">політики конфіденційності</a></span></label>')


HP = '<div class="hp" aria-hidden="true"><label>Не заповнюйте це поле<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>'


# ---------- каркас сторінки
def layout(title, desc, path, body, schemas=(), og_img=None, preload=None):
    logo_a, logo_b = (S["logoParts"] + ["", ""])[:2] if S["logoParts"] else ("", "")
    logo_text = f"{e(logo_a)}<b>{e(logo_b)}</b>" if (logo_a or logo_b) else e(BRAND)
    nav = [("Каталог", "/#catalog"), ("Рішення", "/#solutions")]
    if S["steps"] or S["features"]:
        nav.append(("Послуги", "/#services"))
    if S["aboutText"]:
        nav.append(("Про нас", "/#about"))
    nav.append(("Контакти", "/#contacts"))
    nav_html = "".join(f'<a href="{u}">{n}</a>' for n, u in nav)

    contacts_nav = ""
    if S["phone"]:
        contacts_nav += f'<a href="{tel_href(S["phone"])}">{e(S["phone"])}</a>'
    if S["telegramUrl"]:
        contacts_nav += f'<a href="{e(S["telegramUrl"])}" target="_blank" rel="noopener">Telegram</a>'
    if S["viberNumber"]:
        contacts_nav += f'<a href="viber://chat?number=%2B{re.sub(chr(92) + "D", "", S["viberNumber"])}">Viber</a>'
    if contacts_nav:
        nav_html += f'<div class="nav__contacts">{contacts_nav}</div>'

    top_left = e(S["delivery"])
    top_right = ""
    if S["phone"]:
        top_right += f'<a href="{tel_href(S["phone"])}">{e(S["phone"])}</a>'
    if S["hours"]:
        top_right += ('<span class="sep">·</span>' if top_right else "") + f"<span>{e(S['hours'])}</span>"
    topbar = (f'<div class="topbar"><div class="container topbar__inner"><span>{top_left}</span>'
              f'<span class="topbar__right">{top_right}</span></div></div>') if (top_left or top_right) else ""

    strip_items = ""
    if S["phone"]:
        strip_items += f'<a href="{tel_href(S["phone"])}" class="contact-strip__item"><span class="contact-strip__ico" aria-hidden="true">☎</span>{e(S["phone"])}</a>'
    if S["email"]:
        strip_items += f'<a href="mailto:{e(S["email"])}" class="contact-strip__item"><span class="contact-strip__ico" aria-hidden="true">✉</span>{e(S["email"])}</a>'
    strip = f'''<div class="contact-strip"><div class="container contact-strip__inner">{strip_items}
    <form class="subscribe" data-form="subscribe" novalidate>
      <label for="subEmail">Новини та акції на витратні матеріали</label>
      <div class="subscribe__row"><input id="subEmail" name="email" type="email" placeholder="Ваш email" required autocomplete="email"><button class="btn btn--primary btn--sm">Підписатися</button></div>
      {HP}
    </form></div></div>'''

    chat_links = ""
    if S["telegramUrl"]:
        chat_links += f'<a href="{e(S["telegramUrl"])}" target="_blank" rel="noopener" class="chat__link chat__link--tg">Telegram</a>'
    if S["viberNumber"]:
        chat_links += f'<a href="viber://chat?number=%2B{re.sub(chr(92) + "D", "", S["viberNumber"])}" class="chat__link chat__link--vb">Viber</a>'
    if S["phone"]:
        chat_links += f'<a href="{tel_href(S["phone"])}" class="chat__link chat__link--ph">Подзвонити</a>'
    chat = f'''<div class="chat" id="chat"><div class="chat__menu" id="chatMenu">{chat_links}</div>
  <button class="chat__btn" id="chatBtn" aria-label="Звʼязатися з нами" aria-expanded="false" aria-controls="chatMenu">
    <svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true"><path d="M4 5h16v11H8l-4 4V5Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><circle cx="9" cy="10.5" r="1.2" fill="currentColor"/><circle cx="12" cy="10.5" r="1.2" fill="currentColor"/><circle cx="15" cy="10.5" r="1.2" fill="currentColor"/></svg>
  </button></div>''' if chat_links else ""

    ribbon = '<div class="demo-ribbon" role="note">Демо-версія: назва, контакти, ціни, частина товарів і цифри — умовні</div>' if DEMO else ""
    canonical = f'<link rel="canonical" href="{SITE_URL}{path}">' if SITE_URL else ""
    robots = '<meta name="robots" content="noindex, nofollow">' if DEMO else ""
    og = og_img or "/img/products/fw-1.webp"
    ld = "".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in schemas)
    pre = f'<link rel="preload" as="image" href="{preload}" fetchpriority="high">' if preload else ""
    year = "2026"

    return f'''<!doctype html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{robots}{canonical}
<meta property="og:type" content="website">
<meta property="og:locale" content="uk_UA">
<meta property="og:site_name" content="{e(BRAND)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{absu(og)}">
<meta name="theme-color" content="#0b2239">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/fonts/manrope-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
{pre}
<link rel="stylesheet" href="/css/styles.css">
{ld}
</head>
<body>
<a class="skip" href="#main">Перейти до змісту</a>
{ribbon}
{topbar}
<header class="header">
  <div class="container header__inner">
    <a href="/" class="logo" aria-label="{e(BRAND)} — на головну">{LOGO_SVG}<span>{logo_text}</span></a>
    <nav class="nav" id="nav" aria-label="Головне меню">{nav_html}</nav>
    <div class="header__actions">
      <button class="cart-btn" id="cartOpen" aria-label="Відкрити кошик" aria-haspopup="dialog">
        <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M3 4h2l2.4 11.2a2 2 0 0 0 2 1.6h7.7a2 2 0 0 0 2-1.5L21 8H6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="10" cy="20" r="1.4" fill="currentColor"/><circle cx="17" cy="20" r="1.4" fill="currentColor"/></svg>
        <span class="cart-count" id="cartCount">0</span>
      </button>
      <a href="/#contacts" class="btn btn--primary btn--sm hide-mobile">Консультація</a>
      <button class="burger" id="burger" aria-label="Меню" aria-expanded="false" aria-controls="nav"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>
<div class="nav-backdrop" id="navBackdrop" hidden></div>
<main id="main">
{body}
</main>
{strip}
<footer class="footer">
  <div class="container footer__inner">
    <div><a href="/" class="logo logo--light"><span>{logo_text}</span></a>
      <p>© {year} {e(BRAND)}. Професійне пральне обладнання та витратні матеріали.</p></div>
    <nav class="footer__nav" aria-label="Меню у підвалі">{"".join(f'<a href="{c["url"]}">{e(c["name"])}</a>' for c in VISIBLE_CATS)}<a href="/polityka-konfidentsiinosti/">Політика конфіденційності</a></nav>
  </div>
</footer>
<aside class="drawer" id="drawer" hidden>
  <div class="drawer__backdrop" data-close-cart></div>
  <div class="drawer__panel" role="dialog" aria-modal="true" aria-labelledby="cartTitle" tabindex="-1">
    <div class="drawer__head"><h2 id="cartTitle">Кошик</h2><button class="modal__close" data-close-cart aria-label="Закрити кошик">×</button></div>
    <div class="drawer__body" id="cartBody"></div>
    <div class="drawer__foot" id="cartFoot"></div>
  </div>
</aside>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
{chat}
<script src="/js/data.js"></script>
<script src="/js/app.js" defer></script>
</body>
</html>
'''


def write(path, html):
    out = DIST / path.strip("/") / "index.html" if not path.endswith((".txt", ".xml", ".js", ".svg")) else DIST / path.strip("/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(with_base(html) if out.suffix == ".html" else html, encoding="utf-8")


# ---------- головна
def home():
    spot = next((p for p in PRODUCTS if p["id"] == "combo"), None)
    eyebrow = f"Офіційний дилер {S['manufacturerBrand']}" if S["manufacturerBrand"] else "Обладнання та витратні матеріали"

    facts = "".join(f"<li><b>{e(f['value'])}</b><span>{e(f['label'])}</span></li>" for f in S["heroFacts"])
    facts = f'<ul class="hero__facts">{facts}</ul>' if facts else ""
    hcards = "".join(f'<div class="hero__card hero__card--{i + 1}">{e(t)}</div>' for i, t in enumerate(S["heroCards"][:2]))

    hero = f'''<section class="hero"><div class="container hero__inner">
  <div class="hero__text">
    <p class="eyebrow">{e(eyebrow)}</p>
    <h1>Професійне пральне обладнання <span class="accent">для вашого бізнесу</span></h1>
    <p class="lead">Пральні й сушильні машини, пральні колони та машини Combo для пралень самообслуговування, готелів і закладів. А також хімія, аксесуари й витратні матеріали для пралень і хімчисток.</p>
    <div class="hero__cta"><a href="#catalog" class="btn btn--primary">Перейти до каталогу</a><a href="#calc" class="btn btn--ghost">Розрахувати пральню</a></div>
    {facts}
  </div>
  <div class="hero__visual"><div class="lineup">
    {img("fwdd-1", "Пральна колона FWDD", "(max-width: 860px) 45vw, 270px", "lineup__side lineup__side--l")}
    {img("fw-1", "Пральна машина серії FW", "(max-width: 860px) 60vw, 330px", "lineup__main", eager=True)}
    {img("dd-1", "Двоярусна сушильна машина DD", "(max-width: 860px) 45vw, 270px", "lineup__side lineup__side--r")}
  </div>{hcards}</div>
</div></section>'''

    spotlight = ""
    if spot:
        ticks = "".join(f"<li>{e(k)}: {e(v)}</li>" for k, v in list(spot["specsAll"].items())[:3])
        spotlight = f'''<section class="section section--tight"><div class="container"><div class="spotlight">
  <div class="spotlight__img">{img(spot["img"][0], spot["name"], "(max-width: 860px) 80vw, 380px")}</div>
  <div class="spotlight__text">
    <p class="eyebrow">Новинка</p>
    <h2>{e(spot["name"])}</h2>
    <p class="muted">{e(spot["desc"])}</p>
    <ul class="ticks">{ticks}</ul>
    <div class="hero__cta hero__cta--tight"><a class="btn btn--primary" href="{spot["url"]}">Детальніше</a><a class="btn btn--outline" href="#contacts">Запитати ціну</a></div>
  </div></div></div></section>'''

    sectors = [
        ("Пральні самообслуговування", "Пральні й сушильні машини, колони та Combo з оплатою за цикл."),
        ("Готелі та хостели", "Власна пральня для постільної білизни й рушників."),
        ("Заклади харчування", "Прання скатертин, серветок і уніформи персоналу."),
        ("Гуртожитки та житлові комплекси", "Компактні пральні колони для спільних пральних кімнат."),
        ("Медичні та соціальні заклади", "Обладнання для щоденного прання білизни й одягу."),
        ("Хімчистки та пральні", "Хімія, аксесуари й витратні матеріали для щоденної роботи."),
    ]
    sect = "".join(f'<article class="solution"><span class="solution__num">{i + 1:02d}</span><h3>{e(t)}</h3><p>{e(d)}</p></article>'
                   for i, (t, d) in enumerate(sectors))
    solutions = f'''<section class="section" id="solutions"><div class="container">
  <div class="section__head"><p class="eyebrow">Галузі</p><h2>Рішення для кожного бізнесу</h2></div>
  <div class="solutions">{sect}</div></div></section>'''

    cats = ""
    for c in VISIBLE_CATS:
        items = [p for p in PRODUCTS if p["cat"] == c["id"]]
        w = next((p for p in items if p.get("img")), None)
        vis = (f'<span class="cat__photo">{img(w["img"][0], "", "120px")}</span>' if w
               else f'<span class="cat__ico">{ICONS[c["icon"]]}</span>')
        n = len(items)
        word = "позиція" if n % 10 == 1 and n % 100 != 11 else ("позиції" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else "позицій")
        cats += f'<a class="cat" href="{c["url"]}">{vis}<span class="cat__name">{e(c["name"])}</span><span class="cat__count">{n} {word}</span></a>'
    categories = f'''<section class="section section--alt" id="categories"><div class="container">
  <div class="section__head"><h2>Категорії</h2><p>Обладнання й усе необхідне для щоденної роботи пральні та хімчистки.</p></div>
  <div class="cats">{cats}</div></div></section>'''

    chips = '<button type="button" class="chip is-active" data-filter="all" aria-pressed="true">Усі</button>' + "".join(
        f'<button type="button" class="chip" data-filter="{c["id"]}" aria-pressed="false">{e(c["name"])}</button>' for c in VISIBLE_CATS)
    has_buyable = any(p["buyable"] for p in PRODUCTS)
    cat_note = ("Обладнання продаємо за комерційною пропозицією. Хімію та аксесуари можна замовити одразу."
                if has_buyable else "Обладнання продаємо за комерційною пропозицією — додайте позиції до запиту, і ми надішлемо ціни.")
    catalog = f'''<section class="section" id="catalog"><div class="container">
  <div class="section__head section__head--row">
    <div><h2>Каталог</h2><p>{cat_note}</p></div>
    <div class="catalog__tools">
      <input type="search" id="search" placeholder="Пошук за назвою…" aria-label="Пошук товарів">
      <select id="sort" aria-label="Сортування"><option value="default">За замовчуванням</option><option value="price-asc">Ціна: за зростанням</option><option value="price-desc">Ціна: за спаданням</option></select>
    </div>
  </div>
  <div class="filters" id="filters" role="group" aria-label="Фільтр за категорією">{chips}</div>
  <div class="grid" id="grid">{"".join(card(p) for p in PRODUCTS)}</div>
  <p class="empty" id="empty" hidden>Нічого не знайдено. Спробуйте інший запит.</p>
</div></section>'''

    services = ""
    if S["steps"] or S["features"]:
        steps = "".join(f'<li><span>{i + 1:02d}</span><h3>{e(s["title"])}</h3><p>{e(s["text"])}</p></li>' for i, s in enumerate(S["steps"]))
        feats = "".join(f'<div class="feature"><div class="feature__ico" aria-hidden="true">{e(f["icon"])}</div><h3>{e(f["title"])}</h3><p>{e(f["text"])}</p></div>' for f in S["features"])
        services = f'''<section class="section section--alt" id="services"><div class="container">
  <div class="section__head"><p class="eyebrow">Послуги</p><h2>Не лише продаємо — запускаємо</h2></div>
  {f'<ol class="steps">{steps}</ol>' if steps else ""}{f'<div class="features">{feats}</div>' if feats else ""}
</div></section>'''

    calc = '''<section class="section" id="calc"><div class="container calc">
  <div class="calc__text">
    <h2>Скільки обладнання потрібно?</h2>
    <p class="muted">Попередня оцінка для готелю. Розрахунок спрощений: близько 4,5 кг білизни на зайнятий номер і чотири цикли прання за зміну. Точний підбір зробимо під ваш обʼєкт.</p>
    <label for="rooms">Кількість номерів</label>
    <div class="range"><input type="range" id="rooms" min="10" max="300" step="5" value="60"><output id="roomsOut" for="rooms">60</output></div>
    <label for="occ">Середня завантаженість, %</label>
    <div class="range"><input type="range" id="occ" min="30" max="100" step="5" value="70"><output id="occOut" for="occ">70</output></div>
  </div>
  <div class="calc__result" id="calcResult" aria-live="polite"></div>
</div></section>'''

    reviews = ""
    if S["reviews"]:
        rv = "".join(f'<figure class="review"><blockquote>«{e(r["text"])}»</blockquote><figcaption><b>{e(r["name"])}</b>{e(r["role"])}</figcaption></figure>' for r in S["reviews"])
        reviews = f'''<section class="section section--alt" id="reviews"><div class="container">
  <div class="section__head"><p class="eyebrow">Відгуки</p><h2>Що кажуть клієнти</h2></div><div class="reviews">{rv}</div></div></section>'''

    faq = ""
    if S["faq"]:
        qa = "".join(f'<details><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>' for f in S["faq"])
        faq = f'''<section class="section" id="faq"><div class="container faq">
  <div class="section__head"><p class="eyebrow">Запитання</p><h2>Часті запитання</h2></div><div class="faq__list">{qa}</div></div></section>'''

    about = ""
    if S["aboutText"]:
        st = "".join(f"<li><b>{e(a['value'])}</b><span>{e(a['label'])}</span></li>" for a in S["aboutStats"])
        about = f'''<section class="section section--dark" id="about"><div class="container about">
  <div><h2>Про компанію</h2><p>{e(S["aboutText"])}</p></div>{f'<ul class="about__stats">{st}</ul>' if st else ""}</div></section>'''

    clist = ""
    if S["phone"]:
        clist += f'<li><b>Телефон:</b> <a href="{tel_href(S["phone"])}">{e(S["phone"])}</a></li>'
    if S["email"]:
        clist += f'<li><b>Email:</b> <a href="mailto:{e(S["email"])}">{e(S["email"])}</a></li>'
    if S["address"]:
        clist += f'<li><b>Адреса:</b> {e(S["address"])}</li>'
    contacts = f'''<section class="section" id="contacts"><div class="container contacts">
  <div><h2>Отримайте консультацію</h2>
    <p class="muted">Розкажіть про свій обʼєкт — підберемо обладнання й підготуємо комерційну пропозицію.</p>
    {f'<ul class="contacts__list">{clist}</ul>' if clist else ""}</div>
  <form class="form" data-form="lead" novalidate>
    <label>Імʼя<input name="name" required autocomplete="name"></label>
    <label>Телефон<input name="phone" type="tel" required autocomplete="tel" placeholder="+380 __ ___ __ __" inputmode="tel"><small class="hint">Формат: +380 XX XXX XX XX</small></label>
    <label>Тип бізнесу<select name="business"><option>Пральня самообслуговування</option><option>Готель або хостел</option><option>Заклад харчування</option><option>Хімчистка</option><option>Медичний заклад</option><option>Інше</option></select></label>
    <label>Коментар<textarea name="message" rows="3" placeholder="Що плануєте відкрити або замінити?"></textarea></label>
    {consent_field("lead")}{HP}
    <button class="btn btn--primary btn--block" type="submit">Надіслати заявку</button>
    <div class="form__result" role="status" aria-live="polite"></div>
  </form>
</div></section>'''

    schemas = []
    org = {"@context": "https://schema.org", "@type": "Organization", "name": BRAND}
    if SITE_URL:
        org["url"] = SITE_URL + "/"
    if S["phone"]:
        org["telephone"] = "+" + re.sub(r"\D", "", S["phone"])
    if S["email"]:
        org["email"] = S["email"]
    if S["address"]:
        org["address"] = S["address"]
    if S["foundedYear"]:
        org["foundingDate"] = str(S["foundedYear"])
    schemas.append(org)
    if S["faq"]:
        schemas.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in S["faq"]]})

    body = hero + spotlight + solutions + categories + catalog + services + calc + reviews + faq + about + contacts
    title = f"{BRAND} — професійне пральне обладнання та витратні матеріали"
    desc = "Пральні й сушильні машини, пральні колони та машини Combo для пралень самообслуговування, готелів і закладів. Хімія, аксесуари й витратні матеріали для пралень і хімчисток."
    write("/", layout(title, desc, "/", body, schemas, preload="/img/products/fw-1-sm.webp"))


# ---------- сторінка категорії
def category_page(c):
    items = [p for p in PRODUCTS if p["cat"] == c["id"]]
    cr = [("Головна", "/"), (c["name"], None)]
    body = f'''<section class="section section--page"><div class="container">
  {crumbs(cr)}
  <div class="section__head"><h1 class="h-page">{e(c["name"])}</h1><p>{e(c["intro"])}</p></div>
  <div class="grid">{"".join(card(p, "h2") for p in items)}</div>
  <div class="page-cta"><p>Не знаєте, що обрати? Розкажіть про свій обʼєкт — допоможемо з підбором.</p><a class="btn btn--primary" href="/#contacts">Отримати консультацію</a></div>
</div></section>'''
    schemas = [crumbs_schema(cr, c["url"]),
               {"@context": "https://schema.org", "@type": "ItemList", "name": c["name"], "itemListElement": [
                   {"@type": "ListItem", "position": i + 1, "name": p["name"], "url": absu(p["url"])} for i, p in enumerate(items)]}]
    first = next((p for p in items if p.get("img")), None)
    write(c["url"], layout(f"{c['name']} — {BRAND}", c["intro"], c["url"], body, schemas,
                           og_img=f"/img/products/{first['img'][0]}.webp" if first else None))


# ---------- сторінка товару
def product_page(p):
    c = CAT[p["cat"]]
    cr = [("Головна", "/"), (c["name"], c["url"]), (p["name"], None)]
    if p.get("img"):
        thumbs = ""
        if len(p["img"]) > 1:
            thumbs = '<div class="pd__thumbs">' + "".join(
                f'<button type="button" class="pd__thumb{"" if i else " is-active"}" data-img="{n}" aria-label="Показати фото {i + 1}" aria-pressed="{"false" if i else "true"}">'
                f'<img src="/img/products/{n}-sm.webp" width="64" height="64" alt="" loading="lazy"></button>' for i, n in enumerate(p["img"])) + "</div>"
        m0 = p["img"][0]
        main = (f'<img id="pdMain" src="/img/products/{m0}.webp" srcset="/img/products/{m0}-sm.webp 480w, /img/products/{m0}.webp 1000w" '
                f'sizes="(max-width: 860px) 90vw, 380px" width="1000" height="1000" alt="{e(p["name"])}" fetchpriority="high">')
        gallery = f'<div class="pd__img pd__img--photo">{main}{thumbs}</div>'
    else:
        gallery = f'<div class="pd__img">{ICONS[c["icon"]]}</div>'

    note = ('<p class="muted small">Остаточна ціна залежить від моделі, комплектації та умов монтажу. Додайте позицію до запиту — надішлемо комерційну пропозицію.</p>'
            if not p["buyable"] else "")
    demo_note = '<p class="demo-note">Демо-позиція: товар і ціна вигадані для макета.</p>' if p.get("demo") else ""
    related = [x for x in PRODUCTS if x["cat"] == p["cat"] and x["id"] != p["id"]][:4]
    rel = (f'<div class="related"><h2>Інші товари категорії</h2><div class="grid">{"".join(card(x) for x in related)}</div></div>'
           if related else "")
    body = f'''<section class="section section--page"><div class="container">
  {crumbs(cr)}
  <div class="pd">
    {gallery}
    <div class="pd__body">
      <a class="card__cat" href="{c["url"]}">{e(c["name"])}</a>
      <h1 class="h-page">{e(p["name"])}</h1>
      {demo_note}
      <p>{e(p["desc"])}</p>
      {specs_html(p)}
      <p class="pd__price">{price_html(p)}</p>
      {note}
      <div class="pd__actions">
        <span class="qty"><button type="button" data-q="-1" aria-label="Зменшити кількість">−</button><input id="pdQty" type="number" min="1" value="1" aria-label="Кількість"><button type="button" data-q="1" aria-label="Збільшити кількість">+</button></span>
        {add_btn(p, big=True)}
      </div>
    </div>
  </div>
  {rel}
</div></section>'''
    prod = {"@context": "https://schema.org", "@type": "Product", "name": p["name"], "description": p["desc"], "category": c["name"]}
    if p.get("img"):
        prod["image"] = [absu(f"/img/products/{n}.webp") for n in p["img"]]
    if S["manufacturerBrand"] and not p.get("demo"):
        prod["brand"] = {"@type": "Brand", "name": S["manufacturerBrand"]}
    if p["priceConfirmed"]:
        prod["offers"] = {"@type": "Offer", "price": p["price"], "priceCurrency": "UAH", "url": absu(p["url"]),
                          "availability": "https://schema.org/InStock" if p["buyable"] else "https://schema.org/PreOrder"}
    write(p["url"], layout(f"{p['name']} — {BRAND}", p["desc"][:155], p["url"], body, [crumbs_schema(cr, p["url"]), prod],
                           og_img=f"/img/products/{p['img'][0]}.webp" if p.get("img") else None,
                           preload=None))


# ---------- політика конфіденційності
def privacy_page():
    contact = S["email"] or S["phone"] or "контактами, вказаними на сайті"
    body = f'''<section class="section section--page"><div class="container prose">
  {crumbs([("Головна", "/"), ("Політика конфіденційності", None)])}
  <h1 class="h-page">Політика конфіденційності</h1>
  <p class="demo-note">Шаблон. Перед публікацією текст має перевірити юрист і доповнити реквізитами компанії.</p>
  <h2>Які дані ми збираємо</h2>
  <p>Коли ви залишаєте заявку, оформлюєте замовлення або підписуєтеся на розсилку, ми отримуємо дані, які ви самі вказали у формі: імʼя, номер телефону, адресу електронної пошти, місто доставки та текст повідомлення.</p>
  <h2>Навіщо ми їх використовуємо</h2>
  <p>Щоб звʼязатися з вами, підготувати комерційну пропозицію, виконати замовлення й доставку, а за вашою згодою — надсилати новини та пропозиції.</p>
  <h2>Кому ми їх передаємо</h2>
  <p>Службам доставки та платіжним сервісам — лише в обсязі, потрібному для виконання замовлення. Ми не продаємо персональні дані третім особам.</p>
  <h2>Ваші права</h2>
  <p>Відповідно до Закону України «Про захист персональних даних» ви можете дізнатися, які ваші дані ми зберігаємо, вимагати їх виправити або видалити та відкликати згоду на обробку. Для цього звʼяжіться з нами: {e(contact)}.</p>
  <h2>Кошик і локальне сховище</h2>
  <p>Вміст кошика зберігається лише у вашому браузері й не передається нам, доки ви не надішлете замовлення.</p>
</div></section>'''
    write("/polityka-konfidentsiinosti/", layout(f"Політика конфіденційності — {BRAND}", "Як ми обробляємо персональні дані відвідувачів сайту.",
                                                   "/polityka-konfidentsiinosti/", body))


# ---------- службові файли
def service_files():
    data = {p["id"]: {"n": p["name"], "p": p["priceShown"], "b": p["buyable"], "u": p.get("unit", "шт."), "url": BASE + p["url"]} for p in PRODUCTS}
    cfg = {"phone": S["phone"], "phoneHref": tel_href(S["phone"]) if S["phone"] else "", "email": S["email"],
           "telegramUrl": S["telegramUrl"], "formEndpoint": S["formEndpoint"], "base": BASE}
    write("/js/data.js", "window.CATALOG=" + json.dumps(data, ensure_ascii=False) + ";\nwindow.SITE=" + json.dumps(cfg, ensure_ascii=False) + ";\n")

    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "Google-Extended", "PerplexityBot", "ClaudeBot", "Claude-SearchBot"]
    robots = "User-agent: *\nAllow: /\n\n" + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots)
    pages = ["/"] + [c["url"] for c in VISIBLE_CATS] + [p["url"] for p in PRODUCTS] + ["/polityka-konfidentsiinosti/"]
    if SITE_URL:
        robots += f"Sitemap: {SITE_URL}/sitemap.xml\n"
        sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
            f"  <url><loc>{SITE_URL}{u}</loc></url>\n" for u in pages) + "</urlset>\n"
        write("/sitemap.xml", sm)
    write("/robots.txt", robots)

    lines = [f"# {BRAND}", "",
             "> Постачальник професійного прального обладнання в Україні: пральні й сушильні машини, пральні колони, машини Combo, "
             "а також хімія, аксесуари й витратні матеріали для пралень і хімчисток. Обладнання продається за комерційною пропозицією.", ""]
    if S["manufacturerBrand"]:
        lines += [f"Офіційний дилер бренду {S['manufacturerBrand']}.", ""]
    lines.append("## Каталог")
    for c in VISIBLE_CATS:
        lines.append(f"\n### [{c['name']}]({absu(c['url'])})\n{c['intro']}")
        for p in PRODUCTS:
            if p["cat"] == c["id"] and not p.get("demo"):
                spec = "; ".join(f"{k}: {v}" for k, v in p.get("specs", {}).items())
                lines.append(f"- [{p['name']}]({absu(p['url'])}): {p['desc']}" + (f" ({spec})" if spec else ""))
    contact = [x for x in (S["phone"], S["email"], S["address"]) if x]
    if contact and not DEMO:
        lines += ["", "## Контакти", *[f"- {x}" for x in contact]]
    write("/llms.txt", "\n".join(lines) + "\n")

    fav = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect x="3" y="3" width="26" height="26" rx="7" fill="#0a6f7a"/><circle cx="16" cy="17" r="7" fill="none" stroke="#fff" stroke-width="2.5"/><circle cx="9" cy="8.5" r="1.5" fill="#fff"/></svg>'
    write("/favicon.svg", fav)
    (DIST / ".nojekyll").write_text("")


def main():
    # Очищаємо вміст dist/, але саму папку не видаляємо — щоб запущений сервер перегляду не «загубив» її.
    DIST.mkdir(exist_ok=True)
    for item in DIST.iterdir():
        shutil.rmtree(item) if item.is_dir() else item.unlink()
    for d in ("css", "js", "img", "fonts"):
        shutil.copytree(ROOT / d, DIST / d)
    home()
    for c in VISIBLE_CATS:
        category_page(c)
    for p in PRODUCTS:
        product_page(p)
    privacy_page()
    service_files()

    n_pages = 2 + len(VISIBLE_CATS) + len(PRODUCTS)
    print(f"Готово: {n_pages} сторінок у папці {DIST.name}/ ({len(PRODUCTS)} товарів, {len(VISIBLE_CATS)} категорій).")
    if DEMO:
        print("УВАГА: увімкнено демо-режим (demoMode: true). Сайт позначено як демо й закрито від індексації.")
    missing = [k for k, v in site_raw["real"].items() if not _filled(v)]
    if missing:
        print("Не заповнено справжні дані (data/site.json → real): " + ", ".join(sorted(missing)))
    no_price = [p["id"] for p in PRODUCTS if not p.get("demo") and not p.get("price")]
    if no_price:
        print("Товари без підтвердженої ціни: " + ", ".join(no_price))


if __name__ == "__main__":
    sys.exit(main())
