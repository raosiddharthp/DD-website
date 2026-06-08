#!/usr/bin/env python3
"""
DataDomine — Article Date Updater
===================================
Updates the meta date in each restyled article.
Run from the DD-website root (same place as restyle_articles.py).

Usage:
    python3 update_dates.py
"""

import re
from pathlib import Path

BLOG_DIR = Path(__file__).parent / "Website" / "Blog"

DATES = {
    "article-model-last.html":                                    "September 2025",
    "article-question-problem.html":                              "September 2025",
    "article-why-technical-training-fails-before-it-starts.html": "October 2025",
    "article-what-happens-in-the-brain.html":                     "October 2025",
    "article-rag-constraint-decision.html":                       "November 2025",
    "article-finetuning-not-retrieval-fix.html":                  "November 2025",
    "article-the-problem-with-learning-objectives.html":          "December 2025",
    "article-real-use-cases-are-the-point.html":                  "December 2025",
    "article-03-multi-agent-design.html":                         "January 2026",
    "article-05-memory-architecture-bottleneck.html":             "January 2026",
    "article-blooms-taxonomy-production-checklist.html":          "February 2026",
    "article-motivation-not-your-job.html":                       "February 2026",
    "article-02-hitl-write-path-lock.html":                       "March 2026",
    "article-06-zero-trust-architecture.html":                    "March 2026",
    "article-04-adr-design-artefact.html":                        "April 2026",
    "article-merge-vs-finetune.html":                             "April 2026",
    "article-onprem-sovereignty.html":                            "May 2026",
    "article-07-40m-problem.html":                                "May 2026",
    "article-how-to-measure-training.html":                       "June 2026",
    "article-forgetting-curve-not-your-enemy.html":               "June 2026",
}

# Matches: <span class="article-hero__date">May 2026</span>
DATE_PATTERN = re.compile(
    r'(<span class="article-hero__date">)([^<]+)(</span>)'
)

def update_file(path: Path, new_date: str) -> bool:
    html = path.read_text(encoding="utf-8")
    new_html, count = DATE_PATTERN.subn(
        lambda m: m.group(1) + new_date + m.group(3),
        html
    )
    if count == 0:
        return False
    path.write_text(new_html, encoding="utf-8")
    return True


def main():
    print("\nDataDomine — Article Date Updater")
    print(f"Blog folder: {BLOG_DIR}\n")

    if not BLOG_DIR.exists():
        print(f"❌  Blog folder not found: {BLOG_DIR}")
        print("    Run from the DD-website root.\n")
        return

    ok, skipped = 0, 0
    for filename, date in DATES.items():
        path = BLOG_DIR / filename
        if not path.exists():
            print(f"  ⚠️  Not found — {filename}")
            skipped += 1
            continue
        if update_file(path, date):
            print(f"  ✓  {date:<18}  {filename}")
            ok += 1
        else:
            print(f"  ✗  No date span found — {filename}")
            skipped += 1

    print(f"\nDone. {ok} updated, {skipped} skipped.\n")


if __name__ == "__main__":
    main()
