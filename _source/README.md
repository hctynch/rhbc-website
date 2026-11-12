# Website Source (for editing the site)

This folder holds the files used to build the website. Visitors never need it, and nothing on the site links to it.

| File | What it is |
| --- | --- |
| `rhbc/src2.html` | The master source for the whole site: pages, design and code. Edit this, never `index.html` directly. |
| `build_gh.py` | Turns `rhbc/src2.html` into the published `index.html` for GitHub Pages. |
| `logo/`, `logo3/`, `artifact-files/` | Images the build copies in. |
| `tests/` | Browser tests (Playwright). `tsplit.py` fakes GitHub so staff saving can be tested safely; `tabc.py` tests schedule editing; `tdoc.py` tests bulletins and newsletters. |

## Build and publish

```bash
cd _source
python3 build_gh.py hctynch rhbc-website out ../data/site.json --noindex
cp out/index.html ../index.html      # only index.html; never copy out/data
cd .. && git add index.html _source && git commit -m "…" && git push
```

- Copy **only** `out/index.html`. The live calendar, bulletins and other content live in `data/site.json`, which staff update with **Save Changes** — never overwrite it from `out/`.
- If you add a new pop-up dialog (`overlay16`, `overlay17`…), add its id to the overlay lists in `build_gh.py` too.
- In the page script, use `var` (not `let`/`const`) for anything `renderAll` touches early, to avoid start-up errors. Also define it near the top of the script (next to `ORD`): a `var` defined further down is still empty when the page first draws. If start-up code fails, the page silently falls back to the built-in sample content (old events), so run `tests/tcalview.py` after any change; it checks both Calendar views (Full Calendar and Agenda).
- After pushing, GitHub Pages takes 1–10 minutes. If the "pages build and deployment" run fails with a timeout on GitHub's side, re-run it.

## Testing before publishing

```bash
cd _source/tests
python3 tabc.py      # builds must be in ../out first
```

Test pages for Sam to review are published as an unlinked file (for example `print-test.html` with a gold "TEST SITE" bar), then removed when approved.

## Security

Never put a staff sign-in key, the Vimeo token or any other key in these files. Keys live only in each person's browser or in the repository's GitHub **Secrets**.

## When something breaks (self-correcting start-up and the Website Check)

- Each section of the page loads on its own through `safe()` in `src2.html`. Wrap any new render call in `safe("Section Name",renderX,"containerId")`.
- If a section fails, the page clears the visitor's remembered choices (Calendar view) and tries again. If it still fails, only that section shows "This section couldn't load right now", and signed-in staff see a **Staff Only: Website Error** bar on every page naming the page, plus a red note on the section.
- If start-up itself fails, the page reloads once with remembered choices cleared, then shows a red "Part of this page couldn't load" bar. If the data can't download after two tries, a red "We couldn't load the latest church information" bar shows. The built-in sample content is never shown.
- `.github/workflows/website-check.yml` runs `tests/site_check.py` after every change to `index.html` or `data/site.json`, every 6 hours, and by hand. If a page has an error (or an error that fixed itself), it opens a GitHub issue labeled `website-error` that @mentions the site administrator (`ADMIN` in the workflow), so GitHub emails them. It closes the issue when the check passes.
- Tests: `tests/tstartup.py` (demos; needs a test page made by `tests/make_startup_test.py out/index.html out/startup-test.html`) and `tests/tstartup.py --net` (reload safety net).

