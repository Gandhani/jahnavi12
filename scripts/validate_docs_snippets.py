"""
Purpose: To ensure that no stray snippet opening/closing tags are present in our production docs

In short, this script creates a temporary Docusaurus build and utilizes grep to parse for stray tags.
"""

import shutil
import subprocess
import sys
import tempfile
from typing import List


def check_dependencies(*deps: str) -> None:
    for dep in deps:
        if not shutil.which(dep):
            raise Exception(f"Must have `{dep}` installed in PATH to run {__file__}")


def run_docusaurus_build(target_dir: str) -> None:
    # https://docusaurus.io/docs/cli#docusaurus-build-sitedir
    subprocess.call(
        [
            "yarn",
            "build",
            "--out-dir",
            target_dir,
            "--no-minify",  # Aids with debugging errors
        ],
    )


def run_grep(target_dir: str) -> List[str]:
    try:
        res = subprocess.run(
            [
                "grep",
                "-Er",  # Enable regex and directory search
                r"<\/?snippet",
                target_dir,
            ],
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Command {e.cmd} returned with error (code {e.returncode}): {e.output}"
        )
    return res.stdout.splitlines()


def parse_grep(lines: list[str]) -> list[str]:
    """Parse the grep output and exclude known issues.

    We are ok with some snippet tags in explanatory text on how to write snippets.

    E.g. the lines in docs/guides/miscellaneous/how_to_write_a_how_to_guide.md
    explaining how to use snippet tags.

    We need to parse the output rather than exclude from grep since we don't
    know the filename to exclude (since they are generated by yarn build).

    Args:
        lines: lines from the grep output

    Returns:
        lines to use in processing errors, excluding known issues

    """
    example_present = False
    only_one_closing_tag = False
    closing_tag_count = 0
    for line in lines:
        if (
            'name="tests/integration/docusaurus/template/script_example.py full"'
            in line
        ):
            example_present = True
        if "</snippet>" in line:
            closing_tag_count += 1

    if closing_tag_count == 1:
        only_one_closing_tag = True

    if len(lines) == 2 and example_present and only_one_closing_tag:
        return []
    else:
        return lines


def main() -> None:
    check_dependencies("yarn", "grep")
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_docusaurus_build(tmp_dir)
        grep_output = run_grep(tmp_dir)
        parsed_grep_output = parse_grep(grep_output)
        if parsed_grep_output:
            print("[ERROR] Found snippets in the docs build:")
            for line in parsed_grep_output:
                print(line)
            sys.exit(1)


if __name__ == "__main__":
    main()
