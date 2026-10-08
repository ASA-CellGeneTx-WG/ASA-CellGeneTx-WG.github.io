#!/usr/bin/env python3
"""Turn an "Add a presentation" issue-form submission into a presentations.csv row.

The issue body arrives through the ISSUE_BODY environment variable rather than
being interpolated into the workflow's shell, so nothing in it is ever executed.
Submissions come from a public form, so every field is validated and screened
for spreadsheet formula injection before it reaches the file.
"""

import csv
import datetime
import os
import re
import sys

CSV_PATH = "data/presentations.csv"
COLUMNS = ["YEAR", "EVENT", "TYPE", "SPEAKER", "TITLE", "DATE", "LOCATION", "LINK"]

# form heading -> csv column
FIELDS = {
    "Year": "YEAR",
    "Event": "EVENT",
    "Type": "TYPE",
    "Speakers": "SPEAKER",
    "Title": "TITLE",
    "Date": "DATE",
    "Location": "LOCATION",
    "Link": "LINK",
}
OPTIONAL = {"LINK"}

ALLOWED_TYPES = {
    "Presentation", "Short course", "Round table", "Parallel session",
    "Contributed Panel Session", "Invited session", "Poster", "Other",
}

MAX_LEN = 300
# Leading these characters makes a cell executable in Excel / Sheets.
INJECTION_PREFIXES = ("=", "+", "@", "\t", "\r")


def fail(message):
    """Record a reviewer-facing reason and stop."""
    with open(os.environ.get("ERROR_FILE", "parse_error.md"), "w", encoding="utf-8") as fh:
        fh.write(message)
    print(f"::error::{message}")
    sys.exit(1)


def parse_body(body):
    """Pull `### Heading` / value pairs out of a rendered issue-form body."""
    values = {}
    # Split on headings, keeping the heading text.
    chunks = re.split(r"^###[ \t]*(.+?)[ \t]*$", body, flags=re.MULTILINE)
    # chunks[0] is any preamble; thereafter alternating heading, value.
    for i in range(1, len(chunks) - 1, 2):
        heading = chunks[i].strip()
        value = chunks[i + 1].strip()
        if value == "_No response_":
            value = ""
        values[heading] = value
    return values


def clean(column, value):
    value = " ".join(value.split())  # collapse all whitespace, including newlines

    if not value:
        if column in OPTIONAL:
            return ""
        fail(f"**{column}** is required but came through empty.")

    if len(value) > MAX_LEN:
        fail(f"**{column}** is {len(value)} characters; the limit is {MAX_LEN}.")

    if value.startswith(INJECTION_PREFIXES):
        fail(
            f"**{column}** starts with `{value[0]}`, which spreadsheet software "
            "would treat as a formula. Please remove the leading character and "
            "edit the issue."
        )

    if any(ord(c) < 32 for c in value):
        fail(f"**{column}** contains control characters.")

    return value


def read_body():
    """Prefer a file; the workflow writes the body there so that it is never
    interpolated into a shell command."""
    path = os.environ.get("ISSUE_BODY_FILE")
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    return os.environ.get("ISSUE_BODY", "")


def main():
    body = read_body()
    if not body.strip():
        fail("The issue body was empty, so there was nothing to parse.")

    found = parse_body(body)
    missing = [h for h in FIELDS if h not in found and FIELDS[h] not in OPTIONAL]
    if missing:
        fail(
            "Could not find these headings in the submission: "
            + ", ".join(f"**{m}**" for m in missing)
            + ". Was the issue created from the *Add a presentation* form?"
        )

    row = {col: clean(col, found.get(heading, "")) for heading, col in FIELDS.items()}

    if not re.fullmatch(r"(19|20|21)\d{2}", row["YEAR"]):
        fail(f"**YEAR** should be a four-digit year; got `{row['YEAR']}`.")

    try:
        parsed_date = datetime.date.fromisoformat(row["DATE"])
    except ValueError:
        fail(f"**DATE** should be in YYYY-MM-DD form; got `{row['DATE']}`.")

    if str(parsed_date.year) != row["YEAR"]:
        fail(
            f"**YEAR** is {row['YEAR']} but **DATE** is {row['DATE']}. "
            "Please make them agree."
        )

    if row["TYPE"] not in ALLOWED_TYPES:
        fail(f"**TYPE** `{row['TYPE']}` is not one of the options on the form.")

    if row["LINK"] and not re.match(r"https?://", row["LINK"]):
        fail("**Link** must start with `http://` or `https://`, or be left blank.")

    with open(CSV_PATH, newline="", encoding="utf-8") as fh:
        existing = list(csv.DictReader(fh))

    if any(
        r.get("TITLE", "").casefold() == row["TITLE"].casefold()
        and r.get("DATE", "") == row["DATE"]
        for r in existing
    ):
        fail(
            f"A presentation titled *{row['TITLE']}* on {row['DATE']} is already "
            "listed, so nothing was added."
        )

    existing.append(row)
    # Newest first, matching the order the page renders in, so the file reads
    # the same way as the site and a new entry lands at the top.
    existing.sort(key=lambda r: r.get("DATE", ""), reverse=True)

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({c: r.get(c, "") for c in COLUMNS} for r in existing)

    summary = "\n".join(f"| {c} | {row[c] or '—'} |" for c in COLUMNS)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"title={row['TITLE']}\n")
            fh.write("summary<<SUMMARY_EOF\n")
            fh.write("| Field | Value |\n|---|---|\n" + summary + "\n")
            fh.write("SUMMARY_EOF\n")

    print(f"Added: {row['TITLE']} ({row['DATE']})")


if __name__ == "__main__":
    main()
