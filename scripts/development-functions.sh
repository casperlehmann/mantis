reset_cache() {
  poetry run python main.py reset
}

fetch_issues() {
  poetry run python main.py warmup-issues
}

inspect_issues() {
  poetry run python main.py inspect
}

jsonfmt() {
  find .jira_cache -type f -name '*.json' -exec sh -c 'jq . "$1" > "$1.tmp" && mv "$1.tmp" "$1"' _ {} \;
}

get_and_fmt() {
  reset_cache
  jsonfmt
}

get_and_fmt_with_issues_and_drafts() {
  reset_cache # Includes createmeta plugins
  fetch_issues # includes editmeta plugins and drafts (if not exists)
  jsonfmt
}

run_coverage() {
  poetry run pytest --cov
}

run_tests() {
  poetry run pytest -f -m "not slow"
}

run_mypy() {
  poetry run mypy --disallow-untyped-calls --disallow-untyped-defs --disallow-incomplete-defs mantis
}

run_flake8_sparse() {
  poetry run flake8 mantis --count --select=E9,F63,F7,F82 --show-source --statistics                 
}

run_flake8() {
  poetry run flake8 mantis --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
}

repo_health() {
    echo "\n# Running run_coverage"
    run_coverage
    echo "\n# Running run_mypy"
    run_mypy
    echo "\n# Running run_flake8_sparse"
    run_flake8_sparse
}

show_coverage() {
  poetry run pytest --cov-report html --cov
  open htmlcov/index.html
}

format_test_data() {
    find tests/data/jira_cache -type f -name '*.json' -exec sh -c 'jq . "$1" > "$1.tmp" && mv "$1.tmp" "$1"' _ {} \;
}

anonymize_test_data() {
    find tests/data/ -type f -name '*.json' -exec sh -c '
    for file do
        # Format JSON with jq, then replace emails
        tmp="${file}.tmp"
        if jq . "$file" > "$tmp"; then
        # Replace emails with dummy value (e.g., dummy@example.com)
        sed -E -i.bak "s/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/dummy@example.com/g" "$tmp"
        mv "$tmp" "$file"
        rm "$tmp.bak"
        else
        echo "Invalid JSON: $file"
        rm -f "$tmp"
        fi
    done
    ' sh {} +
}

update_test_data() {
    cp -rf drafts/ tests/data/drafts
    cp -rf .jira_cache/* tests/data/jira_cache/
    cp -rf plugins/ tests/data/plugins
    format_test_data
    anonymize_test_data
}
