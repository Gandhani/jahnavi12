import subprocess
from collections import defaultdict
from typing import Dict, List, Optional

TYPE_HINT_ERROR_THRESHOLD: int = (
    2534  # This number is to be reduced as we annotate more functions!
)


def get_changed_files(branch: str) -> List[str]:
    """Perform a `git diff` against a given branch.

    Args:
        branch (str): The branch to diff against (generally `origin/develop`)

    Returns:
        A list of changed files.
    """
    git_diff: subprocess.CompletedProcess = subprocess.run(
        ["git", "diff", branch, "--name-only"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return [f for f in git_diff.stdout.split()]


def run_mypy(directory: str) -> List[str]:
    """Run mypy to identify functions with type hint violations.

    Flags:
        --ignore-missing-imports: Omitting for simplicity's sake (https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports)
        --disallow-untyped-defs:  What is responsible for highlighting function signature errors
        --show-error-codes:       Allows us to label each error with its code, enabling filtering
        --install-types:          We need common type hints from typeshed to get a more thorough analysis
        --non-interactive:        Automatically say yes to '--install-types' prompt

    Args:
        directory (str): The target directory to run mypy against

    Returns:
        A list containing filtered mypy output relevant to function signatures
    """
    raw_results: subprocess.CompletedProcess = subprocess.run(
        [
            "mypy",
            "--ignore-missing-imports",
            "--disallow-untyped-defs",
            "--show-error-codes",
            "--install-types",
            "--non-interactive",
            directory,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    # Check to make sure `mypy` actually ran
    err: str = raw_results.stderr
    if "command not found" in err:
        raise ValueError(err)

    filtered_results: List[str] = _filter_mypy_results(raw_results)
    return filtered_results


def _filter_mypy_results(raw_results: subprocess.CompletedProcess) -> List[str]:
    def _filter(line: str) -> bool:
        return "error:" in line and "untyped-def" in line

    return list(filter(lambda line: _filter(line), raw_results.stderr.split("\n")))


def render_deviations(changed_files: List[str], deviations: List[str]) -> None:
    """Iterates through changed files in order to provide the user with useful feedback around mypy type hint violations

    Args:
        changed_files (List[str]): The files relevant to the given commit/PR
        deviations (List[str]): mypy deviations as generated by `run_mypy`

    Raises:
        AssertionError if number of style guide violations is higher than threshold
    """
    deviations_dict: Dict[str, List[str]] = _build_deviations_dict(deviations)

    error_count: int = len(deviations)
    print(f"[SUMMARY] {error_count} functions have untyped-def violations!")

    threshold_is_surpassed: bool = error_count > TYPE_HINT_ERROR_THRESHOLD

    if threshold_is_surpassed:
        print(
            "\nHere are violations of the style guide that are relevant to the files changed in your PR:"
        )
        for file in changed_files:
            errors: Optional[List[str]] = deviations_dict.get(file)
            if errors:
                print(f"\n  {file}:")
                for error in errors:
                    print(f"    {error}")

    # Chetan - 20220417 - While this number should be 0, getting the number of style guide violations down takes time
    # and effort. In the meanwhile, we want to set an upper bound on errors to ensure we're not introducing
    # further regressions. As functions are annotated in adherence with style guide standards, developers should update this number.
    assert (
        threshold_is_surpassed is False
    ), f"""A function without proper type annotations was introduced; please resolve the matter before merging.
                We expect there to be {TYPE_HINT_ERROR_THRESHOLD} or fewer violations of the style guide (actual: {error_count})"""


def _build_deviations_dict(mypy_results: List[str]) -> Dict[str, List[str]]:
    deviations_dict: Dict[str, List[str]] = defaultdict(list)
    for row in mypy_results:
        file: str = row.split(":")[0]
        deviations_dict[file].append(row)

    return deviations_dict


if __name__ == "__main__":
    changed_files: List[str] = get_changed_files("origin/develop")
    untyped_def_deviations: List[str] = run_mypy("great_expectations")
    render_deviations(changed_files, untyped_def_deviations)
