#!/usr/bin/env python3
"""Generate an AI-assisted code review for the current diff.

This script is designed to run inside a GitHub Actions workflow. It inspects the
current event payload to determine the base and head commits, extracts the diff,
and then asks an OpenAI chat model to provide a short review. The review is
written to STDOUT and, when available, appended to ``GITHUB_STEP_SUMMARY`` so it
appears in the workflow summary tab.
"""
from __future__ import annotations

import json
import os
import subprocess
import textwrap
from pathlib import Path

try:
    import openai  # type: ignore
except Exception as exc:  # pragma: no cover - defensive import guard
    raise SystemExit(f"Failed to import the OpenAI SDK: {exc}")


def _run_git_command(*args: str) -> str:
    """Run a git command and return its stdout."""
    result = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed with code {result.returncode}: {result.stderr.strip()}"
        )
    return result.stdout


def _load_event_payload() -> dict | None:
    """Load the GitHub event payload if it exists."""
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return None
    path = Path(event_path)
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError:
            return None


def _determine_base_and_head(payload: dict | None) -> tuple[str | None, str]:
    """Determine the base and head SHAs for the current run."""
    head = os.environ.get("GITHUB_SHA") or "HEAD"
    base = None
    event_name = os.environ.get("GITHUB_EVENT_NAME")

    if payload:
        if event_name == "pull_request":
            pull_request = payload.get("pull_request", {})
            base = pull_request.get("base", {}).get("sha")
            head = pull_request.get("head", {}).get("sha", head)
        elif event_name == "push":
            base = payload.get("before")
            head = payload.get("after", head)

    if not base:
        # Fall back to the previous commit if the base SHA is not available.
        try:
            base = _run_git_command("rev-parse", f"{head}^1").strip()
        except RuntimeError:
            base = None

    return base, head


def _collect_diff(base: str | None, head: str) -> str:
    """Collect the diff between ``base`` and ``head``.

    The diff is truncated to avoid exceeding token limits when passed to the
    language model.
    """
    diff_args = ["diff"]
    if base:
        diff_args.extend([base, head])
    else:
        empty_tree = _run_git_command("hash-object", "-t", "tree", "/dev/null").strip()
        diff_args.extend([empty_tree, head])
    diff = _run_git_command(*diff_args)
    diff = diff.strip()

    max_chars = int(os.environ.get("AI_REVIEW_MAX_DIFF_CHARS", "12000"))
    if len(diff) > max_chars:
        truncated_marker = textwrap.dedent(
            f"""
            Diff truncated to the first {max_chars} characters to keep the prompt a
            manageable size.
            """
        ).strip()
        diff = diff[:max_chars] + "\n" + truncated_marker

    return diff


def _build_prompt(diff: str) -> list[dict[str, str]]:
    """Construct the chat prompt for the OpenAI model."""
    repo = os.environ.get("GITHUB_REPOSITORY", "this repository")
    event_name = os.environ.get("GITHUB_EVENT_NAME", "workflow run")
    instructions = textwrap.dedent(
        f"""
        "You are reviewing a pull request for a Django project.\n\n"
    "Context:\n"
    "- PR Title: {{pr_title}}\n"
    "- PR Description: {{pr_description}}\n"
    "- CI Status: {{ci_status}}\n"
    "- Files Changed (paths only): {{files_changed}}\n"
    "- Commit Messages (newest first): {{commit_messages}}\n"
    "- Unified Diff (git diff with context):\n{{diff}}\n\n"
    "Task:\n"
    "Write an evidence-based review focused on what changed in this PR and why it matters. "
    "Your output must follow the exact format below. Do not use Markdown headers (#). "
    "Do not invent files, symbols, or line numbers that are not present in the diff. "
    "If information is missing, explicitly say \"Not shown in diff.\"\n\n"
    "Format:\n"
    "1) Start with a single paragraph beginning with: "
    "\"Based on the changes ... I’d give this code X out of 10\" "
    "where X is an integer 1–10. In the same paragraph, briefly justify the score and "
    "list the top 2–4 drivers (e.g., test coverage, correctness, complexity, security, performance, style).\n\n"
    "2) Summary Of Changes\n"
    "Write 3–6 concise bullet points that summarize WHAT changed at a high level "
    "(features removed/added, key refactors, migrations, settings changes) using the diff and commit messages.\n\n"
    "3) What Changed, File By File\n"
    "Provide one or more lines, each like this:\n"
    "- path/to/file.py:lineStart-lineEnd — brief description of the change and WHY it was made. "
    "Only include ranges visible in the diff. Group related hunks if useful.\n\n"
    "4) Strengths\n"
    "List 2–6 bullets highlighting the best parts of the PR with specific references where possible.\n\n"
    "5) Issues And How To Fix Them\n"
    "Write short sections using this exact 2-line format with a blank line between sections:\n"
    "Title Case Heading\n"
    "detail explaining the issue, cite file paths and line ranges, and give a concrete fix suggestion.\n\n"
    "6) Test Recommendations\n"
    "Suggest 2–6 realistic tests based on this PR. Use this format for each bullet:\n"
    "- test_name — target (path/module) — scenario and expected result.\n"
    "If no tests are missing, say: \"No additional tests recommended based on the diff.\"\n\n"
    "7) Risk And Impact\n"
    "In 2–4 bullets, summarize deploy risks including migrations, settings changes, or backward compatibility concerns.\n\n"
    "8) Why Points Were Deducted\n"
    "List 1–5 bullets that clearly explain the score, with evidence from specific files/lines.\n\n"
    "9) Changelog Snippet\n"
    "Provide 2–5 clean bullets suitable for a CHANGELOG.\n\n"
    "Guidelines:\n"
    "- Prioritize correctness, security, and data integrity over style.\n"
    "- Reference specific files and line ranges from the diff.\n"
    "- If CI failed, include brief failure context if it relates to these changes.\n"
    "- For database writes across multiple tables, suggest django.db.transaction.atomic if missing.\n"
    "- Identify possible N+1 Django ORM issues and suggest select_related/prefetch_related.\n"
    "- Review for unsafe DEBUG, SECRET_KEY, CORS, or ALLOWED_HOSTS usage.\n"
    "- Review DRF serializers, permissions, and validation.\n"
    "- For migrations, warn about destructive or risky schema changes.\n"
    "- Keep the tone helpful and specific. Avoid vague feedback.\n"
        """
    ).strip()

    user_content = f"Here is the diff to review:\n\n```diff\n{diff}\n```"
    return [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_content},
    ]


def _write_summary(review: str) -> None:
    """Append the review to the GitHub Actions step summary if possible."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return
    summary_path = Path(summary_file)
    with summary_path.open("a", encoding="utf-8") as handle:
        handle.write("## AI Review\n\n")
        handle.write(review)
        handle.write("\n")


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set; cannot run AI review.")

    model = os.environ.get("AI_REVIEW_MODEL", "gpt-4o-mini")

    payload = _load_event_payload()
    base, head = _determine_base_and_head(payload)
    diff = _collect_diff(base, head)
    if not diff:
        print("No changes detected in the diff. Skipping AI review.")
        return

    messages = _build_prompt(diff)

    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=800,
        )
    except Exception as exc:  # pragma: no cover - external API call
        raise SystemExit(f"Failed to generate AI review: {exc}")

    review_text = response["choices"][0]["message"]["content"].strip()

    print("AI Review Result:\n")
    print(review_text)
    _write_summary(review_text)


if __name__ == "__main__":
    main()
