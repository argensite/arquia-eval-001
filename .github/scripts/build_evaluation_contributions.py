"""Build the public list from labeled GitHub issues."""

import json
import os
from pathlib import Path
import string
from urllib.parse import urlencode
from urllib.request import Request, urlopen


CONTRIBUTION_LABEL = "open-evaluation"
REPRODUCED_LABEL = "evaluation-reproduced"
OUTPUT = Path(__file__).resolve().parents[2] / "evaluacion" / "APORTES.md"
MARKDOWN_ESCAPES = str.maketrans({char: f"\\{char}" for char in string.punctuation})


def list_contributions(repository, token):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "arquia-open-evaluation",
    }
    issues = []
    page = 1
    while True:
        query = urlencode({
            "state": "all",
            "labels": CONTRIBUTION_LABEL,
            "sort": "created",
            "direction": "asc",
            "per_page": 100,
            "page": page,
        })
        request = Request(f"https://api.github.com/repos/{repository}/issues?{query}", headers=headers)
        with urlopen(request, timeout=25) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError("GitHub returned an unexpected issue list")
        issues.extend(issue for issue in batch if "pull_request" not in issue)
        if len(batch) < 100:
            return issues
        page += 1


def render(issues, repository):
    lines = [
        "# Aportes de la comunidad · Community contributions",
        "",
        "Este listado se actualiza automáticamente. Abrí el hilo para leer el aporte y sus avances.",
        "This list updates automatically. Open a thread to read the contribution and its updates.",
        "",
        "[Cómo participar / How to take part](README.md) · [Evidencia y resultados / Evidence and results](RESULTADOS.md)",
        "",
    ]
    if not issues:
        lines.append("Todavía no hay aportes en el listado. / No contributions have been listed yet.")
        return "\n".join(lines) + "\n"

    lines.extend([
        "| Aporte / Contribution | Última actividad / Last activity (UTC) | Estado de evidencia / Evidence status |",
        "| --- | --- | --- |",
    ])
    for issue in sorted(issues, key=lambda item: (item["updated_at"], item["number"]), reverse=True):
        title = " ".join(issue["title"].split()).translate(MARKDOWN_ESCAPES)
        number = int(issue["number"])
        updated_at = issue["updated_at"].replace("T", " ").removesuffix("Z")
        labels = {label["name"] for label in issue["labels"]}
        status = "Reportado / Reported"
        if REPRODUCED_LABEL in labels:
            status = "Reproducción documentada / Reproduction documented"
        url = f"https://github.com/{repository}/issues/{number}"
        lines.append(f"| [#{number}]({url}) {title} | {updated_at} | {status} |")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    repository = os.environ["GITHUB_REPOSITORY"]
    issues = list_contributions(repository, os.environ["GH_TOKEN"])
    OUTPUT.write_text(render(issues, repository), encoding="utf-8")
