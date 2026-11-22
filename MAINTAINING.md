# Maintaining The Better Bite website

Em's recipe blog, live at **https://thebetterbitebyem.co.uk** and hosted free on GitHub Pages from this repository.

Instagram: [@thebetterbitebyem](https://www.instagram.com/thebetterbitebyem/)

## Adding a new recipe

Em sends the recipe (ingredients with amounts, steps, protein per serving, how many it makes) and a few photos to Claude, and Claude does the rest:

1. Add the photos to `photos/` as `<slug>-1.jpg`, `<slug>-2.jpg`… (about 1000px wide, JPEG quality around 82).
2. Add a 160×160 square copy of each to `photos/thumbs/` (same file name).
3. Add 1:1, 4:3 and 16:9 crops of the main photo to `photos/share/` as `<slug>-1x1.jpg`, `<slug>-4x3.jpg` and `<slug>-16x9.jpg`. Google uses these in search results.
4. Add an entry at the top of `recipes` in `src/recipes.json`. Copy an existing one and change every field. The first recipe in the list is the featured one on the home page.
5. Run `python3 src/build.py`, check the pages, then commit and push. The site updates within about 10 minutes.

### Recipe fields

| Field | What it's for |
| --- | --- |
| `slug` | The web address: `/recipes/<slug>/` |
| `title`, `seoTitle`, `description` | Name on the page, title Google shows, and the short summary Google shows (under 160 characters) |
| `cats` | Any of `breakfast`, `snacks`, `desserts`, `festive` (these drive the filter buttons) |
| `series`, `seriesOrder` | Optional: `Protein Snack Hack` or `Apple a Day` (no episode numbers on the site). `seriesOrder` only sets the order on the series page |
| `protein`, `kcal`, `per` | Per serving. Either can be `null`; the photo label shows protein when there is a figure, otherwise calories. Use only the figures on Em's recipe card |
| `carbs`, `fat`, `fibre`, `noteExtra` | Optional extra figures and a line for the small print (e.g. "Excludes the yogurt") |
| `kind` | Leave out for recipes. `"post"` is the taste-test layout (see the chocolate mousse entry) |
| `time`, `timeShort`, `prepMinutes`, `makes` | Shown on the page and given to Google |
| `tag` | The handwritten tag on the photo, e.g. `No bake` |
| `groups`, `method`, `tip` | Ingredients (optionally in named groups), steps and Em's tip |
| `photos`, `wide` | Photos with alt text and an optional `pos` crop focus; `wide` is a landscape photo for the home page feature |
| `tile`, `doodle` | Background colour and drawing, used only when a recipe has no photos |
| `draft` | `true` keeps a recipe off the live site |

Style notes: names and headings start with a capital letter; Em's recipes put protein first, and only show calories when she gives them.

## Files

- `index.html`, `recipes/*/index.html`, `sitemap.xml`, `robots.txt`, `404.html`, `CNAME`: made by `src/build.py`, so don't edit them by hand
- `assets/site.css`, `assets/site.js`: shared styles and the small scripts (filters, photo gallery, copy shopping list)
- `src/art.json`: the hand-drawn icons and placeholder drawings

## Contact and link-in-bio page

- Em's email is `site.email` in `src/recipes.json`; it appears in the Get in touch section, the footer and the links page.
- `links/index.html` (thebetterbitebyem.co.uk/links) is the page in Em's Instagram bio: a 3-column photo grid of every recipe in the same order as `src/recipes.json`. It's built automatically and marked noindex.

## Instagram reels

- `reel` on a recipe is its Instagram post link and shows a "Watch the reel" button. The taste-test post uses `reels` (one per episode, with a `base` that links each mousse recipe to its episode).
- `igOrder` is the position in Em's Instagram grid (0 = newest). The links page sorts by it; recipes without it go last. When adding a new recipe with a reel, give it `igOrder: 0` and add 1 to everyone else's.
