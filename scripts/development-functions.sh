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

