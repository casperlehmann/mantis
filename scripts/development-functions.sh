reset_cache() {
  python main.py --action reset
}

jsonfmt() {
  find .jira_cache -type f -name '*.json' -exec sh -c 'jq . "$1" > "$1.tmp" && mv "$1.tmp" "$1"' _ {} \;
}

get_and_fmt() {
  reset_cache
  jsonfmt
}

run_coverage() {
  pytest --cov
}

run_mypy() {
  mypy --disallow-untyped-calls --disallow-untyped-defs --disallow-incomplete-defs mantis
}

run_flake8_sparse() {
  flake8 mantis --count --select=E9,F63,F7,F82 --show-source --statistics                 
}

run_flake8() {
  flake8 mantis --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
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
  pytest --cov-report html --cov
  open htmlcov/index.html
}
