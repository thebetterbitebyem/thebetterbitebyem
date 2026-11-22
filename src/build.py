#!/usr/bin/env python3
"""Builds The Better Bite website (thebetterbitebyem.co.uk) from src/recipes.json.

Run from anywhere:  python3 src/build.py

It writes index.html, a page per recipe or post at recipes/<slug>/index.html,
a page per series at series/<slug>/index.html, sitemap.xml, robots.txt, 404.html
and CNAME. Entries with "draft": true are skipped. See README.md for how to add a recipe.
"""
import datetime
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "src", "recipes.json"), encoding="utf-8"))
ART = json.load(open(os.path.join(ROOT, "src", "art.json"), encoding="utf-8"))
SITE = DATA["site"]
SERIES = DATA.get("series", {})
URL = SITE["url"].rstrip("/")
DOMAIN = URL.split("://", 1)[1]
ENTRIES = [r for r in DATA["recipes"] if not r.get("draft")]
RECIPES = [r for r in ENTRIES if r.get("kind", "recipe") == "recipe"]
TODAY = datetime.date.today().isoformat()

CATS = {"breakfast": "Breakfast", "snacks": "Snacks", "desserts": "Desserts", "drinks": "Drinks", "festive": "Festive"}
CAT_ICONS = {"all": "sparkle", "breakfast": "bowl", "snacks": "cookie", "desserts": "cupcake", "drinks": "cup", "festive": "snow"}

try:
    from PIL import Image
except ImportError:  # sizes are optional
    Image = None


def esc(s):
    return html.escape(str(s), quote=True)


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def series_slug(name):
    for k, v in SERIES.items():
        if v["name"] == name:
            return k
    return None


def size_attrs(path):
    """width/height attributes for an image, when Pillow is available."""
    if not Image:
        return ""
    try:
        w, h = Image.open(os.path.join(ROOT, path)).size
        return f' width="{w}" height="{h}"'
    except OSError:
        return ""


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, indent=1).replace("</", "<\\/") + "</script>"


# ---------- Small drawings ----------

ART["icons"].setdefault("play", '<circle class="il f-orange" cx="12" cy="12" r="9.5"/><path class="f-white il thin" d="M10 8.2l6 3.8-6 3.8z"/>')
ART["icons"].setdefault("mail", '<rect class="il f-white" x="2.5" y="5" width="19" height="14" rx="2.5"/><path class="il o" d="M3.5 6.5l8.5 6.5 8.5-6.5"/>')
ART["icons"].setdefault("chat", '<path class="il f-peach" d="M4 5h16a1.5 1.5 0 0 1 1.5 1.5v9A1.5 1.5 0 0 1 20 17h-9l-4.5 3.5V17H4a1.5 1.5 0 0 1-1.5-1.5v-9A1.5 1.5 0 0 1 4 5z"/><circle class="f-ink" cx="8" cy="11" r="1.1"/><circle class="f-ink" cx="12" cy="11" r="1.1"/><circle class="f-ink" cx="16" cy="11" r="1.1"/>')


def icon(name):
    return f'<svg class="ic" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><g filter="url(#wobble-s)">{ART["icons"][name]}</g></svg>'


def doodle(name):
    bursts = "".join(
        f'<g transform="translate({x} {y}) rotate({r})"><path class="dash" d="M-10 -2L-16 -12M0 -5V-18M10 -2L16 -12"/></g>'
        for x, y, r in ART["bursts"][name])
    return f'<svg viewBox="0 0 200 200" aria-hidden="true" focusable="false"><g filter="url(#wobble)">{ART["doodles"][name]}{bursts}</g></svg>'


FILTERS = """<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">
  <defs>
    <filter id="wobble" x="-5%" y="-5%" width="110%" height="110%">
      <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="7"/>
      <feDisplacementMap in="SourceGraphic" scale="3.5" xChannelSelector="R" yChannelSelector="G"/>
    </filter>
    <filter id="wobble-s" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.18" numOctaves="2" seed="3"/>
      <feDisplacementMap in="SourceGraphic" scale="0.9" xChannelSelector="R" yChannelSelector="G"/>
    </filter>
  </defs>
</svg>"""


# ---------- Recipe helpers ----------

def page_url(r):
    return f"{URL}/recipes/{r['slug']}/"


def portions(r):
    digits = "".join(c for c in r["makes"] if c.isdigit())
    n = int(digits) if digits else 1
    return f"{n} {r['per']}{'s' if n > 1 else ''}"


def share_images(r):
    imgs = [f"photos/share/{r['slug']}-{k}.jpg" for k in ("1x1", "4x3", "16x9")]
    imgs = [p for p in imgs if os.path.exists(os.path.join(ROOT, p))]
    if not imgs and r.get("photos"):
        imgs = [r["photos"][0]["src"]]
    return [f"{URL}/{p}" for p in imgs]


def photo(p, prefix, id_=None, eager=False):
    pos = p.get("pos", "50% 50%")
    load = ' fetchpriority="high"' if eager else ' loading="lazy"'
    idattr = f' id="{id_}"' if id_ else ""
    return (f'<img class="photo"{idattr} src="{prefix}{esc(p["src"])}" alt="{esc(p["alt"])}"'
            f'{size_attrs(p["src"])} style="object-position:{pos}" decoding="async"{load}>')


def art_for(r, prefix):
    return photo(r["photos"][0], prefix) if r.get("photos") else doodle(r["doodle"])


def pill_text(r):
    if r.get("pill"):
        return r["pill"]
    if r.get("protein"):
        return f"{r['protein']}g protein"
    return f"~{r['kcal']} kcal"


def search_text(r):
    parts = [r["title"], r["intro"], r.get("tag", ""), r.get("series", "")] + r["cats"]
    parts += [i for g in r.get("groups", []) for i in g["items"]]
    parts += [m["name"] + " " + " ".join(m["items"]) for m in r.get("mousses", [])]
    return esc(" ".join(parts).lower())


def card(r, prefix):
    return f"""<a class="card" href="{prefix}recipes/{r['slug']}/" data-cats="{' '.join(r['cats'])}" data-search="{search_text(r)}">
        <div class="tile t-{r['tile']}">{art_for(r, prefix)}<span class="pill">{esc(pill_text(r))}</span><span class="note-tag">{esc(r['tag'])}</span></div>
        <h3>{esc(r['title'])}</h3>
        <p class="meta">{esc(r['timeShort'])} · {esc(r['makes'])}</p>
      </a>"""


def cats_line(r, prefix):
    parts = [esc(CATS[c]) for c in r["cats"]]
    if r.get("series"):
        s = series_slug(r["series"])
        parts.append(f'<a href="{prefix}series/{s}/">{esc(r["series"])}</a>' if s else esc(r["series"]))
    return " · ".join(parts)


def gallery(r, prefix):
    if not r.get("photos"):
        return doodle(r["doodle"]), ""
    main = photo(r["photos"][0], prefix, id_="main-photo", eager=True)
    thumbs = ""
    if len(r["photos"]) > 1:
        thumbs = '<div class="thumbs" role="group" aria-label="More photos">' + "".join(
            f'<button type="button" class="thumb" data-src="{prefix}{esc(p["src"])}" data-alt="{esc(p["alt"])}" '
            f'data-pos="{p.get("pos", "50% 50%")}" aria-pressed="{str(i == 0).lower()}" aria-label="Show photo {i + 1} of {len(r["photos"])}">'
            f'<img src="{prefix}{esc(p["src"].replace("photos/", "photos/thumbs/"))}" alt="" width="160" height="160" loading="lazy"></button>'
            for i, p in enumerate(r["photos"])) + "</div>"
    return main, thumbs


def more_section(r, prefix):
    others = [x for x in ENTRIES if x["slug"] != r["slug"]]
    others.sort(key=lambda x: (-(bool(r.get("series")) and x.get("series") == r.get("series")),
                               -len(set(x["cats"]) & set(r["cats"]))))
    if not others:
        return ""
    return f"""
      <section class="more" aria-labelledby="more-title">
        <h2 id="more-title">More to make</h2>
        <div class="grid">{''.join(card(x, prefix) for x in others[:4])}</div>
      </section>"""


# ---------- Page shell ----------

def verify_tag(canonical):
    """Google Search Console ownership tag, on the home page only."""
    code = SITE.get("googleVerification")
    if code and canonical == URL + "/":
        return f'<meta name="google-site-verification" content="{esc(code)}">\n'
    return ""


def head(title, desc, canonical, prefix, image, structured, og_type="website", nav=True):
    return f"""<!DOCTYPE html>
<html lang="en-GB" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
{verify_tag(canonical)}<meta property="og:site_name" content="{esc(SITE['name'])}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{image}">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#F7F2EA">
<link rel="icon" type="image/png" sizes="32x32" href="{prefix}favicon-32.png">
<link rel="apple-touch-icon" href="{prefix}apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&family=Gloock&family=Gochi+Hand&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}assets/site.css">
{structured}
<script src="{prefix}assets/site.js" defer></script>
</head>
<body>
{FILTERS}
{nav_html(prefix) if nav else ""}"""


def nav_html(prefix):
    return f"""<header class="nav">
  <div class="wrap">
    <a class="brand" href="{prefix or './'}"><img src="{prefix}logo.png" alt="" width="40" height="40"><span>The Better Bite <em class="by">by Em</em></span></a>
    <nav class="nav-links" aria-label="Main">
      <a class="nav-recipes" href="{prefix}#recipes">Recipes</a>
      <a class="nav-about" href="{prefix}#about">About</a>
      <a href="{SITE['instagram']}" target="_blank" rel="noopener">Instagram ↗</a>
    </nav>
  </div>
</header>"""


def foot(prefix):
    return f"""
<footer>
  <div class="wrap">
    <a class="brand" href="{prefix or './'}"><img src="{prefix}logo.png" alt="" width="32" height="32"><span>The Better Bite <em class="by">by Em</em></span></a>
    <span class="foot-links"><a href="mailto:{SITE['email']}">{SITE['email']}</a> · <a href="{SITE['instagram']}" target="_blank" rel="noopener">@thebetterbitebyem</a></span>
    <span>© {datetime.date.today().year} The Better Bite by Em. Protein and calories are estimates and vary by brand.</span>
  </div>
</footer>
</body>
</html>
"""


def chips_html(entries):
    used = [c for c in CATS if any(c in r["cats"] for r in entries)]
    return "".join(
        f'<button type="button" class="chip" data-cat="{k}" aria-pressed="{str(k == "all").lower()}">{icon(CAT_ICONS[k])}{label}</button>'
        for k, label in [("all", "All")] + [(c, CATS[c]) for c in used])


# ---------- Home page ----------

def build_home():
    f = ENTRIES[0]
    wide = f.get("wide") or (f["photos"][0] if f.get("photos") else None)
    f_art = photo(wide, "", eager=True) if wide else doodle(f["doodle"])
    f_label = "Festive pick!" if "festive" in f["cats"] else "New recipe!"
    desc = ("Better-for-you, high-protein recipes by Em from @thebetterbitebyem: no-bake desserts, "
            "snack hacks and treats, with protein on every recipe.")
    structured = ld([
        {"@context": "https://schema.org", "@type": "WebSite", "name": SITE["name"], "url": URL + "/"},
        {"@context": "https://schema.org", "@type": "Person", "name": SITE["author"], "url": URL + "/",
         "sameAs": [SITE["instagram"]]},
        {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": page_url(r)} for i, r in enumerate(RECIPES)]},
    ])
    image = (share_images(f) or [URL + "/logo.png"])[-1]

    def series_item(slug, ic, name, sub):
        inner = f'<span class="ico">{icon(ic)}</span><span>{name}<small>{sub}</small></span>'
        if slug in SERIES:
            return f'<li><a class="series-link" href="series/{slug}/">{inner}</a></li>'
        return f"<li>{inner}</li>"

    out = head("The Better Bite by Em | High-Protein Recipes That Taste Like a Treat", desc, URL + "/", "", image, structured)
    out += f"""
<main id="top">
  <div class="wrap">
    <section class="hero">
      <div>
        <img class="hero-logo" src="logo.png" alt="The Better Bite logo" width="96" height="96">
        <p class="welcome">Welcome to The Better Bite</p>
        <h1>Hi, I'm <span class="hl">Em!<svg class="swoosh" viewBox="0 0 120 16" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path vector-effect="non-scaling-stroke" d="M3 12C30 5 66 3 117 7"/></svg></span></h1>
        <p class="lede"><strong>Healthy eating, decoded.</strong> Better-for-you, high-protein recipes that still taste like the treat you were craving, with protein listed on every recipe.</p>
        <div class="actions">
          <a class="btn btn-primary" href="#recipes">Browse recipes</a>
          <a class="btn" href="{SITE['instagram']}" target="_blank" rel="noopener">@thebetterbitebyem</a>
        </div>
      </div>
      <a class="featured" href="recipes/{f['slug']}/">
        <div class="tile t-{f['tile']}">{f_art}<span class="pill">{esc(pill_text(f))}</span><span class="note-tag top">{f_label}</span><span class="note-tag">{esc(f['tag'])}</span></div>
        <div class="featured-cap"><h2>{esc(f['title'])}</h2><p class="meta">{esc(f['timeShort'])} · {esc(f['makes'])}</p></div>
      </a>
    </section>

    <section id="recipes" class="section" aria-labelledby="recipes-title">
      <div class="sec-head">
        <h2 id="recipes-title">Recipes</h2>
        <p class="side-note">Pick a craving!<svg viewBox="0 0 34 26" aria-hidden="true" focusable="false"><path d="M4 4c12-2 22 4 24 16M22 15l6 6 4-7"/></svg></p>
      </div>
      <div class="toolbar">
        <div class="chips" role="group" aria-label="Filter recipes">{chips_html(ENTRIES)}</div>
        <div class="search">
          <label class="sr-only" for="search">Search recipes or ingredients</label>
          <input id="search" type="search" placeholder="Search, e.g. apple" autocomplete="off">
        </div>
      </div>
      <div class="grid" id="grid" aria-live="polite">
      {''.join(card(r, '') for r in ENTRIES)}
        <p class="empty" id="empty" hidden>No recipes match “<span></span>” yet. Try another ingredient.</p>
      </div>
    </section>

    <section id="about" class="section" aria-labelledby="about-title">
      <div class="about">
        <div>
          <p class="welcome">Nice to meet you!</p>
          <h2 id="about-title">About The Better Bite <em class="by">by Em</em></h2>
          <p>I'm Em, and I make high-protein versions of the snacks and sweet things I actually want to eat. Everything here uses ingredients from a normal supermarket shop, and every recipe lists the protein or calories per serving so it's easy to fit into your day.</p>
          <ul class="pillars" aria-label="What The Better Bite covers">
            <li>{icon('bar')}Protein finds</li>
            <li>{icon('basket')}Smarter swaps</li>
            <li>{icon('pan')}Easy recipes</li>
            <li>{icon('bulb')}Tips + explainers</li>
            <li>{icon('list')}Honest rankings</li>
          </ul>
          <a class="btn btn-primary" href="{SITE['instagram']}" target="_blank" rel="noopener">Follow on Instagram</a>
        </div>
        <ul class="series" aria-label="Series on Instagram and TikTok">
          {series_item('protein-snack-hack', 'cookie', 'Protein Snack Hack', 'Classic snacks, made higher protein')}
          {series_item('apple-a-day', 'apple', 'Apple a Day Series', 'Five apple recipes for apple season')}
          {series_item('food-myths', 'myth', 'Food Myths: True or False?', 'Swipe to test yourself')}
          {series_item('snack-reviews', 'star', 'Snack Reviews', 'Honest ratings, scored out of 10')}
        </ul>
      </div>
    </section>

    <section id="contact" class="section" aria-labelledby="contact-title">
      <div class="contact">
        <div>
          <p class="welcome">Say hi!</p>
          <h2 id="contact-title">Get in touch</h2>
          <p>For collabs and brand work, questions about a recipe, or just to tell me you made something, drop me an email or send me a DM on Instagram.</p>
        </div>
        <div class="contact-actions">
          <a class="contact-card" href="mailto:{SITE['email']}">{icon('mail')}<span><b>Email</b>{SITE['email'].replace('@', '@<wbr>')}</span></a>
          <a class="contact-card" href="{SITE['instagram']}" target="_blank" rel="noopener">{icon('chat')}<span><b>Instagram DMs</b>@thebetterbitebyem</span></a>
        </div>
      </div>
    </section>
  </div>
</main>
"""
    out += foot("")
    write("index.html", out)


# ---------- Recipe pages ----------

def nutrition_figures(r):
    figs = []
    if r.get("protein"):
        figs.append(f"{r['protein']}g protein")
    for key, label in (("carbs", "carbs"), ("fat", "fat"), ("fibre", "fibre")):
        if r.get(key):
            figs.append(f"{r[key]}g {label}")
    if r.get("kcal"):
        figs.append(f"about {r['kcal']} kcal")
    return figs[0] if len(figs) == 1 else ", ".join(figs[:-1]) + " and " + figs[-1]


def recipe_ld(r):
    nutrition = {"@type": "NutritionInformation", "servingSize": f"1 {r['per']}"}
    if r.get("kcal"):
        nutrition["calories"] = f"{r['kcal']} calories"
    for key, prop in (("protein", "proteinContent"), ("carbs", "carbohydrateContent"),
                      ("fat", "fatContent"), ("fibre", "fiberContent")):
        if r.get(key):
            nutrition[prop] = f"{r[key]} g"
    obj = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": r["title"],
        "image": share_images(r),
        "author": {"@type": "Person", "name": SITE["author"], "url": URL + "/"},
        "datePublished": r.get("datePublished", TODAY),
        "description": r.get("description", r["intro"]),
        "recipeCategory": r.get("category", "Dessert"),
        "recipeYield": portions(r),
        "keywords": ", ".join(r.get("keywords", [])),
        "nutrition": nutrition,
        "recipeIngredient": [i for g in r["groups"] for i in g["items"]],
        "recipeInstructions": [
            {"@type": "HowToStep", "position": n + 1, "text": s, "url": f"{page_url(r)}#step-{n + 1}"}
            for n, s in enumerate(r["method"])],
        "url": page_url(r),
    }
    if r.get("prepMinutes"):
        obj["prepTime"] = f"PT{r['prepMinutes']}M"
    if r.get("cookMinutes"):
        obj["cookTime"] = f"PT{r['cookMinutes']}M"
        if r.get("prepMinutes"):
            obj["totalTime"] = f"PT{r['prepMinutes'] + r['cookMinutes']}M"
    if r.get("series"):
        obj["isPartOf"] = {"@type": "CreativeWorkSeries", "name": r["series"]}
    return obj


def reel_button(url, label="Watch the reel"):
    return (f'<a class="btn btn-reel" href="{esc(url)}" target="_blank" rel="noopener">'
            f'{icon("play")}{esc(label)}<span class="sr-only"> on Instagram (opens in a new tab)</span></a>')


def build_recipe(r):
    prefix = "../../"
    main, thumbs = gallery(r, prefix)

    n = 0
    groups = ""
    for g in r["groups"]:
        if g.get("name"):
            groups += f"<h3>{esc(g['name'])}</h3>"
        items = ""
        for item in g["items"]:
            items += f'<li><label for="ing-{n}"><input type="checkbox" id="ing-{n}"><span>{esc(item)}</span></label></li>'
            n += 1
        groups += f"<ul>{items}</ul>"

    stats = []
    if r.get("protein"):
        stats.append(f'<div class="protein"><dt>{icon("bolt")}Protein</dt><dd>{r["protein"]}g</dd></div>')
    if r.get("kcal"):
        stats.append(f'<div><dt>{icon("flame")}Calories</dt><dd>{r["kcal"]} kcal</dd></div>')
    stats.append(f'<div><dt>{icon("clock")}Time</dt><dd>{esc(r["time"])}</dd></div>')
    stats.append(f'<div><dt>{icon("cutlery")}Makes</dt><dd>{esc(portions(r))}</dd></div>')
    stat_class = {2: " two", 3: " three", 4: ""}[len(stats)]
    note = f"Per {esc(r['per'])}: {nutrition_figures(r)}. " + (esc(r["noteExtra"]) + " " if r.get("noteExtra") else "") + \
           "These are estimates and vary with the brands you use."

    images = share_images(r)
    title = f"{r.get('seoTitle', r['title'])} | The Better Bite"
    out = head(title, r.get("description", r["intro"]), page_url(r), prefix, images[-1] if images else URL + "/logo.png",
               ld(recipe_ld(r)), og_type="article")
    out += f"""
<main>
  <div class="wrap">
    <a class="back" href="{prefix}#recipes">← All recipes</a>
    <article>
      <div class="recipe-head">
        <div class="recipe-media">
          <div class="tile big t-{r['tile']}">
            <img class="badge" src="{prefix}logo.png" alt="" width="72" height="72">
            {main}<span class="note-tag">{esc(r['tag'])}</span>
          </div>
          {thumbs}
        </div>
        <div>
          <p class="cats">{cats_line(r, prefix)}</p>
          <h1>{esc(r['title'])}</h1>
          <p class="lede">{esc(r['intro'])}</p>
          <dl class="stats{stat_class}">
            {''.join(stats)}
          </dl>
          <p class="note">{note}</p>
          {f'<div class="reel-row">{reel_button(r["reel"])}</div>' if r.get("reel") else ""}
        </div>
      </div>
      <div class="recipe-body">
        <section class="ingredients" aria-labelledby="ing-title">
          <div class="ing-head">
            <h2 id="ing-title">Ingredients</h2>
            <button type="button" class="btn btn-sm" id="copy-list">Copy shopping list</button>
          </div>
          {groups}
          <p class="status" id="copy-status" aria-live="polite"></p>
        </section>
        <section class="method" aria-labelledby="method-title">
          <h2 id="method-title">Method</h2>
          <ol>{''.join(f'<li id="step-{i + 1}"><p>{esc(s)}</p></li>' for i, s in enumerate(r['method']))}</ol>
          <aside class="tip"><strong>{icon('bulb')}Em's tip</strong><p>{esc(r['tip'])}</p></aside>
        </section>
      </div>{more_section(r, prefix)}
    </article>
  </div>
</main>
"""
    out += foot(prefix)
    write(f"recipes/{r['slug']}/index.html", out)


# ---------- Taste-test posts ----------

def build_post(r):
    prefix = "../../"
    main, thumbs = gallery(r, prefix)
    ms = r["mousses"]
    winner = min(ms, key=lambda m: m["rank"])
    best_macro = max(ms, key=lambda m: m["per100"])

    rows = "".join(
        f'<tr class="{"win" if m is winner else ""}"><td class="rank"><span>{m["rank"]}</span></td>'
        f'<td class="name"><a href="#{m["id"]}">{esc(m["name"])}</a><small>{m["kcal"]} kcal · {m["protein"]}g protein</small></td>'
        f'<td class="kcal-col">{m["kcal"]}</td><td>{m["per100"]}g</td><td class="taste">{m["taste"]}</td></tr>'
        for m in sorted(ms, key=lambda m: m["rank"]))
    summary = "".join(f'<div><strong>{esc(a)}</strong><span>{esc(b)}</span></div>' for a, b in r["summary"])
    awards = "".join(f'<li>{icon("medal")}<span><b>{esc(a)}</b><strong>{esc(b)}</strong><small>{esc(c)}</small></span></li>'
                     for a, b, c in r["awards"])
    recipes = "".join(
        f'<article class="mousse{" win" if m is winner else ""}" id="{m["id"]}">'
        f'<span class="place">#{m["rank"]} · {m["taste"]}/10</span>'
        f'<h3>{esc(m["name"])}</h3><p class="mmeta"><b>{m["protein"]}g protein</b> · about {m["kcal"]} kcal per bowl</p>'
        f'<ul>{"".join(f"<li>{esc(i)}</li>" for i in m["items"])}</ul>'
        + "".join(f'<a class="mreel" href="{esc(x["url"])}" target="_blank" rel="noopener">{icon("play")}Watch {esc(x["label"].split(":")[0].lower())} on Instagram</a>'
                  for x in r.get("reels", []) if m["id"].startswith(x["base"]))
        + '</article>'
        for m in sorted(ms, key=lambda m: m["rank"]))

    reels = r.get("reels", [])
    reels_row = ""
    if reels:
        reels_row = ('<p class="reel-title">Watch the taste test</p><div class="reel-row">'
                     + "".join(reel_button(x["url"], x["label"]) for x in reels) + "</div>")
    images = share_images(r)
    structured = ld({
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": r["title"], "description": r["description"], "image": images,
        "author": {"@type": "Person", "name": SITE["author"], "url": URL + "/"},
        "datePublished": r.get("datePublished", TODAY), "mainEntityOfPage": page_url(r),
        "keywords": "healthy chocolate mousse, high protein chocolate mousse, silken tofu chocolate mousse, greek yogurt chocolate mousse, cottage cheese chocolate mousse",
    })
    out = head(f"{r['seoTitle']} | The Better Bite", r["description"], page_url(r), prefix,
               images[-1] if images else URL + "/logo.png", structured, og_type="article")
    out += f"""
<main>
  <div class="wrap">
    <a class="back" href="{prefix}#recipes">← All recipes</a>
    <article>
      <div class="recipe-head">
        <div class="recipe-media">
          <div class="tile big t-{r['tile']}">
            <img class="badge" src="{prefix}logo.png" alt="" width="72" height="72">
            {main}<span class="note-tag">{esc(r['tag'])}</span>
          </div>
          {thumbs}
        </div>
        <div>
          <p class="cats">{cats_line(r, prefix)}</p>
          <h1>{esc(r['title'])}</h1>
          <p class="lede">{esc(r['intro'])}</p>
          <dl class="stats three">
            <div><dt>{icon('cupcake')}Recipes</dt><dd>{len(ms)}</dd></div>
            <div><dt>{icon('bowl')}Bases</dt><dd>3</dd></div>
            <div class="protein"><dt>{icon('medal')}Winner</dt><dd>{winner['taste']}/10</dd></div>
          </dl>
          <p class="note">The winner: <a href="#{winner['id']}">{esc(winner['name'].lower())}</a>. Macros are approximate per bowl and vary by brand.</p>
          {reels_row}
        </div>
      </div>

      <section class="post-section" aria-labelledby="how-title">
        <h2 id="how-title">How I tested them</h2>
        <p class="sub">Same cocoa, same maple, same night in the fridge. The only things that changed were the base and the sweetener.</p>
        <ol class="tested">{''.join(f'<li>{esc(s)}</li>' for s in r['tested'])}</ol>
      </section>

      <section class="post-section" aria-labelledby="rank-title">
        <h2 id="rank-title">The final ranking</h2>
        <p class="sub">Ranked on taste. Protein is shown per 100 kcal, so you can compare them fairly.</p>
        <div class="board-wrap">
          <table class="board">
            <thead><tr><th>#</th><th>Mousse</th><th class="kcal-col">kcal</th><th>Protein /100 kcal</th><th>Taste</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        <div class="summary">{summary}</div>
      </section>

      <section class="post-section" aria-labelledby="awards-title">
        <h2 id="awards-title">The awards</h2>
        <p class="sub">Silken tofu wins on taste. The best macros go to {esc(best_macro['name'].lower())}, with {best_macro['per100']}g protein per 100 kcal.</p>
        <ul class="awards">{awards}</ul>
      </section>

      <section class="post-section" aria-labelledby="recipes-title">
        <h2 id="recipes-title">All 6 recipes</h2>
        <p class="sub">Each one makes one bowl.</p>
        <div class="mousse-recipes">{recipes}</div>
        <p class="method-note">Method for all of them: {esc(r['method'])}</p>
        <aside class="tip"><strong>{icon('bulb')}Em's tip</strong><p>{esc(r['tip'])}</p></aside>
      </section>{more_section(r, prefix)}
    </article>
  </div>
</main>
"""
    out += foot(prefix)
    write(f"recipes/{r['slug']}/index.html", out)


# ---------- Series pages ----------

def build_series(slug, s):
    prefix = "../../"
    items = sorted([r for r in ENTRIES if r.get("series") == s["name"]], key=lambda r: r.get("seriesOrder", 99))
    if not items:
        return False
    canonical = f"{URL}/series/{slug}/"
    structured = ld({"@context": "https://schema.org", "@type": "ItemList", "name": s["name"], "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "url": page_url(r)} for i, r in enumerate(items)]})
    image = (share_images(items[0]) or [URL + "/logo.png"])[-1]
    out = head(f"{s['name']} Recipes | The Better Bite", s["intro"], canonical, prefix, image, structured)
    out += f"""
<main>
  <div class="wrap">
    <a class="back" href="{prefix}#recipes">← All recipes</a>
    <header class="series-head">
      <p class="welcome">The series</p>
      <h1>{esc(s['name'])}</h1>
      <p>{esc(s['intro'])}</p>
    </header>
    <section class="section">
      <div class="grid">{''.join(card(r, prefix) for r in items)}</div>
    </section>
  </div>
</main>
"""
    out += foot(prefix)
    write(f"series/{slug}/index.html", out)
    return True


# ---------- Link-in-bio page ----------

def build_links():
    prefix = "../"
    tiles = "".join(
        f'<a class="ltile" href="{prefix}recipes/{r["slug"]}/">'
        f'<span class="limg">{photo(r["photos"][0], prefix) if r.get("photos") else doodle(r["doodle"])}</span>'
        f'<span class="lname">{esc(r["title"])}</span></a>'
        for r in sorted(ENTRIES, key=lambda r: r.get("igOrder", 999)))
    out = head("The Better Bite by Em | Recipes from Instagram",
               "Tap a photo to get the recipe. High-protein recipes by Em from @thebetterbitebyem.",
               URL + "/links/", prefix, URL + "/logo.png", '<meta name="robots" content="noindex">', nav=False)
    out += f"""
<main class="links-page">
  <div class="wrap">
    <header class="links-head">
      <img src="{prefix}logo.png" alt="The Better Bite logo" width="92" height="92">
      <h1>The Better Bite <em class="by">by Em</em></h1>
      <p>High-protein recipes that still taste like a treat.</p>
      <p class="side-note">Tap a photo for the recipe!</p>
      <div class="links-actions">
        <a class="btn btn-primary" href="{prefix}#recipes">All recipes</a>
        <a class="btn" href="mailto:{SITE['email']}">Email me</a>
      </div>
    </header>
    <div class="ltiles">{tiles}</div>
    <p class="links-foot"><a href="{prefix}">thebetterbitebyem.co.uk</a></p>
  </div>
</main>
</body>
</html>
"""
    write("links/index.html", out)


# ---------- Extras ----------

def build_extras(series_built):
    urls = [(URL + "/", TODAY)]
    urls += [(page_url(r), r.get("updated", r.get("datePublished", TODAY))) for r in ENTRIES]
    urls += [(f"{URL}/series/{s}/", TODAY) for s in series_built]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {URL}/sitemap.xml\n")
    write("CNAME", DOMAIN + "\n")
    write(".nojekyll", "")
    out = head("Page not found | The Better Bite", "This page doesn't exist. Find all of Em's recipes on The Better Bite.",
               URL + "/404.html", "/", URL + "/logo.png", '<meta name="robots" content="noindex">')
    out += """
<main>
  <div class="wrap section">
    <p class="welcome">Oops!</p>
    <h1 style="font-family:var(--font-display);font-weight:400;font-size:clamp(2.2rem,6vw,3.4rem);margin:0 0 12px">That page isn't on the menu</h1>
    <p>The link may be old, or the recipe may have moved.</p>
    <a class="btn btn-primary" href="/#recipes">See all recipes</a>
  </div>
</main>
"""
    out += foot("/")
    write("404.html", out)


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


if __name__ == "__main__":
    build_home()
    for entry in ENTRIES:
        (build_post if entry.get("kind") == "post" else build_recipe)(entry)
    built = [slug for slug, s in SERIES.items() if build_series(slug, s)]
    build_links()
    build_extras(built)
    print(f"Built {len(RECIPES)} recipes, {len(ENTRIES) - len(RECIPES)} post(s) and {len(built)} series pages "
          f"(skipped {len(DATA['recipes']) - len(ENTRIES)} drafts) for {URL}")
