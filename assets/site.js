/* The Better Bite: small extras. Every page still works without this file. */
(function () {
  document.documentElement.classList.remove("no-js");

  // Home page: category chips and search
  var grid = document.getElementById("grid");
  if (grid) {
    var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));
    var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
    var search = document.getElementById("search");
    var empty = document.getElementById("empty");
    var cat = "all";
    var apply = function () {
      var q = search ? search.value.trim().toLowerCase() : "";
      var shown = 0;
      cards.forEach(function (c) {
        var ok = (cat === "all" || c.dataset.cats.split(" ").indexOf(cat) > -1) && (!q || c.dataset.search.indexOf(q) > -1);
        c.hidden = !ok;
        if (ok) shown++;
      });
      if (empty) {
        empty.hidden = shown > 0;
        empty.querySelector("span").textContent = q;
      }
    };
    chips.forEach(function (ch) {
      ch.addEventListener("click", function () {
        cat = ch.dataset.cat;
        chips.forEach(function (x) { x.setAttribute("aria-pressed", String(x === ch)); });
        apply();
      });
    });
    if (search) search.addEventListener("input", apply);
  }

  // Recipe page: tap a small photo to show it big
  var main = document.getElementById("main-photo");
  var thumbs = document.querySelector(".thumbs");
  if (main && thumbs) {
    thumbs.addEventListener("click", function (e) {
      var b = e.target.closest(".thumb");
      if (!b) return;
      main.src = b.dataset.src;
      main.alt = b.dataset.alt;
      main.style.objectPosition = b.dataset.pos;
      thumbs.querySelectorAll(".thumb").forEach(function (t) { t.setAttribute("aria-pressed", String(t === b)); });
    });
  }

  // Recipe page: copy the ingredients as a shopping list
  var copy = document.getElementById("copy-list");
  if (copy) {
    copy.addEventListener("click", function () {
      var status = document.getElementById("copy-status");
      var lines = [document.querySelector("h1").textContent.trim()];
      document.querySelectorAll(".ingredients h3, .ingredients li").forEach(function (el) {
        lines.push(el.tagName === "H3" ? "\n" + el.textContent.trim() : "- " + el.textContent.trim());
      });
      var fail = function () { status.textContent = "Couldn't copy here. Press and hold the list to select and copy it instead."; };
      try {
        navigator.clipboard.writeText(lines.join("\n")).then(function () { status.textContent = "Shopping list copied."; }, fail);
      } catch (e) { fail(); }
    });
  }
})();
