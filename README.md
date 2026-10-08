# Cell and Gene Therapy working group

Website of the ASA Cell and Gene Therapy Scientific Working Group:
<https://asa-cellgenetx-wg.github.io/>

## How publishing works

The site is a [Quarto](https://quarto.org) website. `.github/workflows/publish.yml`
renders it and deploys it to GitHub Pages:

```
data/  ──►  quarto render  ──►  _site/  ──►  GitHub Pages
 (+ *.qmd)   (GitHub Actions)
```

The rendered output is **not** committed. `_site/` is git-ignored and exists only
inside the workflow run, so the published site cannot drift from the sources.

The workflow runs when:

- anything under `data/`, `tools/`, a `.qmd`, `_quarto.yml`, `styles.css` or a
  `theme-*.scss` changes on `main`;
- you press **Run workflow** on the Actions tab (republish with no content change);
- something sends a `data-updated` repository dispatch event.

### Building locally

```sh
quarto render    # writes _site/
quarto preview   # live reload while editing
```

The sub-teams and presentations pages execute R, so a local render needs R plus
`knitr`, `rmarkdown`, `dplyr`, `readxl`, `glue`, `pander` and `reporttools`. The
other pages need no R.

## Updating content

This repository is the source of truth. Edit the files here and the site
republishes on merge to `main`.

| Page | Source | How to edit |
|------|--------|-------------|
| Presentations | `data/presentations.csv` | Open an [Add a presentation](../../issues/new?template=add-presentation.yml) issue, or edit the CSV directly |
| Sub-teams | `data/members.csv`, `data/objectives.xlsx` | Edit the CSV in the browser; download/upload the workbook |
| Publications | `publications.qmd` | Edit in the browser |
| Resources | `resources.qmd` | Edit in the browser |
| Home | `index.qmd` | Edit in the browser |

The two member-facing files are CSV so that GitHub renders them as tables, shows
line-level diffs, allows in-browser editing and can merge concurrent edits —
none of which works with `.xlsx`.

### Adding a presentation

A member fills in the issue form; `.github/workflows/presentation-submission.yml`
parses it, appends a row to `data/presentations.csv` and opens a pull request.
Merging it republishes the site. Submitters never touch a data file, and nothing
goes live without review.

The form requires a GitHub account. If a member does not have one, send the
details to a maintainer, who can add the row by editing the CSV in the browser.

Editing the issue re-runs the parse and updates the same pull request. If a
submission is rejected — bad date, duplicate entry, a field that would behave as
a spreadsheet formula — the workflow comments on the issue explaining why.

### Notes on the data files

`data/members.csv` — one row per person. `Lead_TF` names the task force a person
leads. The task-force columns (`RWE` … `DSAI`) mark membership with a `1`; blank
means not a member. Only `Firstname`, `Lastname` and `Institution` are rendered.

`data/objectives.xlsx` — still a workbook because the objectives are
multi-paragraph text with bullet structure, which survives editing better in
Excel than in CSV. `read_excel` is called without a `sheet=` argument, so only
the first sheet in workbook order is read.

A task force appears on the site only if its name is listed in the `taskforces`
vector in `subteams.qmd` **and** its row in `objectives.xlsx` has `active = 2`.

### A note for maintainers

This repository is public, so anything committed under `data/` is world-readable
and stays in the git history. Member email addresses were removed from the member
list in October 2026 for this reason; the site never rendered them. Please keep
contact details out of this repository.

An earlier plan synced the workbooks from the group's Teams channel via Power
Automate. That was dropped in favour of editing here directly: it needed a
premium connector licence, and having two copies of the data meant one of them
was always the stale one. The write-up is in the git history if it is ever needed.
