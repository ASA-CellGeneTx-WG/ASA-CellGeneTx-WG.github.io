# Cell and Gene Therapy working group

Website of the ASA Cell and Gene Therapy Scientific Working Group:
<https://asa-cellgenetx-wg.github.io/>

## How publishing works

The site is a [Quarto](https://quarto.org) website. `.github/workflows/publish.yml`
renders it and deploys it to GitHub Pages:

```
data/*.xlsx  ──►  quarto render  ──►  _site/  ──►  GitHub Pages
  (+ *.qmd)        (GitHub Actions)
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

| Page | Edit |
|------|------|
| Sub-teams | `data/members.xlsx`, `data/objectives.xlsx` |
| Presentations | `data/presentations.xlsx` |
| Publications | `publications.qmd` |
| Resources | `resources.qmd` |
| Home | `index.qmd` |

`data/members.xlsx` column notes: the first sheet in workbook order is the one
that is read. A task force appears on the site only if its name is listed in the
`taskforces` vector in `subteams.qmd` **and** its row in `objectives.xlsx` has
`active = 2`. `Lead_TF` names the task force a person leads; `Firstname`,
`Lastname` and `Institution` are the only columns rendered.

## Syncing the spreadsheets from Teams

The working group maintains the workbooks in a Teams channel. A Teams channel's
files live in a SharePoint document library, so a scheduled Power Automate flow
copies them into `data/` here, and the resulting commit triggers the workflow
above.

The flow compares content before writing, so an unchanged workbook produces no
commit and no rebuild.

### One-time setup

**1. Create a GitHub token.** Settings → Developer settings → Personal access
tokens → Fine-grained tokens. Scope it to this repository only, and grant
*Repository permissions → Contents: Read and write*. Note the expiry date and set
a calendar reminder — the flow fails silently-ish when the token lapses. A GitHub
App installation token avoids expiry if you would rather not rotate.

**2. Build the flow.** In Power Automate, create a **scheduled cloud flow**
(hourly is plenty). For each workbook:

| Step | Action | Notes |
|------|--------|-------|
| 1 | SharePoint → *Get file content using path* | Path of the workbook in the channel's library |
| 2 | HTTP → `GET https://api.github.com/repos/ASA-CellGeneTx-WG/ASA-CellGeneTx-WG.github.io/contents/data/<name>.xlsx` | Returns the current `sha` and base64 `content` |
| 3 | Condition | Compare step 2's `content` with `base64(body('Get_file_content'))`, after stripping whitespace from both — GitHub wraps its base64 in newlines |
| 4 | HTTP → `PUT .../contents/data/<name>.xlsx` | Only on the "different" branch |

Headers for the HTTP actions:

```
Authorization: Bearer <token>
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

Body for step 4:

```json
{
  "message": "Update <name>.xlsx from Teams",
  "content": "<base64 of the SharePoint file>",
  "sha": "<sha from step 2>",
  "branch": "main"
}
```

The `sha` is required — it is how GitHub detects a conflicting concurrent edit.

### Things worth knowing

- **The HTTP action is a premium Power Automate connector.** If the licence is
  not available, the alternative is to invert the direction: have the workflow
  pull the files from SharePoint via Microsoft Graph on a schedule, which needs
  an Entra app registration with `Sites.Selected` plus a client secret stored as
  a GitHub Actions secret.
- **Prefer a schedule over an on-modified trigger.** Excel autosaves, so a
  "when a file is modified" trigger fires repeatedly during a single editing
  session and produces a burst of commits.
- **This repository is public.** Anything pushed into `data/` is world-readable
  and stays in the git history. `members.xlsx` carries member email addresses in
  its `email`/`email2` columns; the site never renders them, so removing those
  columns from the workbook that gets synced costs nothing and keeps them out of
  a public repository.
