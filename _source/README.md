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
