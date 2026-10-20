# Quantum Trajectories and Open Many-Body Dynamics

A self-contained Quarto book for advanced undergraduates and beginning graduate students, using Andrew J. Daley's [2014 review](https://doi.org/10.1080/00018732.2014.933502) as its scientific backbone.

**Read online:** <https://xing-phys.github.io/quantum-trajectories-book/>

**PDF:** <https://xing-phys.github.io/quantum-trajectories-book/quantum-trajectories-book.pdf>

The book covers every scientific subsection of the review, with a section-by-section map in `review-map.qmd`. It adds prerequisite material, explicit derivations, worked examples, exercises and guidance, original figures, and reproducible Julia numerical examples. This is an independently authored companion. AI assistance was used in preparing the initial edition.

## Build locally

Install [Quarto](https://quarto.org/) (tested with 1.10.18) and a LuaLaTeX-capable TeX distribution (or run `quarto install tinytex`). Then:

```sh
quarto render
python3 scripts/check_book.py
quarto preview --no-browser
```

The HTML book and combined PDF are written to `_site/`. Render all formats for publication: rendering only HTML cleans the previous combined PDF from the output directory. Quarto prints the preview URL. The sources do not execute numerical calculations while rendering: verified figure assets are committed, so readers can build without Julia or Python plotting packages.

## Reproduce the physics

The computational laboratory documents all parameters and commands. Dynamics use Julia standard libraries. Plotting uses NumPy and Matplotlib:

```sh
julia --project=. test/runtests.jl
julia --project=. scripts/trajectories.jl
python3 -m venv .venv
.venv/bin/pip install -r requirements-figures.txt
.venv/bin/python scripts/make_figures.py
.venv/bin/python scripts/make_schematics.py
```

Generated numerical data and the figure generator are kept with the sources. See the laboratory for the statistical and integration accuracy of the examples.

## Organization

- Root `.qmd` files: chapters, notation, references, and review coverage map.
- `_quarto.yml`: shared HTML/PDF settings, chapter order, and publishing metadata.
- `assets/`: verified central bibliography, APS citation style, synchronized LaTeX/MathJax physics macros, and light/dark styling.
- `applications.bib`, `numerics.bib`: supporting primary literature.
- `figs/`: original PNG/PDF figures; `scripts/`: reproductions and output checks.
- `.github/workflows/publish.yml`: validates and builds both formats, then deploys GitHub Pages on pushes to `main`. Pull requests build and check without deploying.
- `.research/`: ignored local reading copies; the review PDF is not redistributed.

Optional browser checks (using a fresh headless Chrome profile, with Chrome installed):

```sh
.venv/bin/pip install -r requirements-browser.txt
python3 -m http.server 4207 --directory _site
# In another terminal:
.venv/bin/python scripts/check_browser.py
```

These check representative MathJax equations, light/dark figure display, JavaScript errors, and mobile width. QA screenshots stay in ignored `.research/`.

## Editing and publication

Edit Markdown and LaTeX in the chapter sources. Use native Quarto equation/figure/section labels and citations. Maintain equivalent macro definitions in `assets/macros.sty` and `assets/mathjax-config.html`. Run the numerical checks after changing the simulator, and render/check the book after changing its text or assets.

Push changes to `main` to trigger publication. GitHub Pages is configured to use GitHub Actions. The workflow uploads `_site/` as a Pages artifact and deploys it. Use `gh run list` and `gh run view --log-failed` to diagnose a failed build.

When contributing physics corrections, identify the equation or section, state the assumption at issue, and provide a primary reference or a reproducible counterexample where possible. New material should distinguish established identities, approximations, numerical observations, and proposals.

## License

Original prose and figures: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Code: MIT. See `LICENSE`. Cited publications retain their own rights; third-party figures are not included.
