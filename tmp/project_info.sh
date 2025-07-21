#!/bin/bash
set -euo pipefail

MODE="full"

for arg in "$@"; do
  case "$arg" in
    --core) MODE="core" ;;
    --quality) MODE="quality" ;;
    --devops) MODE="devops" ;;
    --full) MODE="full" ;;
  esac
done

safe_print() {
  key="$1"
  shift
  output=$(eval "$@" 2>/dev/null || echo "")
  echo "${key}=${output:-none}"
}

is_git_repo() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1
}

safe_git_dir() {
  git rev-parse --git-dir 2>/dev/null
}

if is_git_repo; then
  safe_print "current_branch" "git branch --show-current"
  safe_print "default_remote" "git remote get-url origin"

  if git rev-parse HEAD >/dev/null 2>&1; then
    safe_print "total_commits" "git rev-list --all --count"
    safe_print "total_authors" "git shortlog -sne | wc -l | tr -d ' '"
    safe_print "first_commit_date" "git log --reverse --date=short --pretty=format:'%ad' | head -1"
    safe_print "latest_commit_date" "git log -1 --date=short --pretty=format:'%ad'"

    top_authors_all=$(git shortlog -s -n | awk '{for (i=2; i<=NF; i++) printf $i " "; print ""}' | paste -s -d ',' -)
    echo "top_authors_all=${top_authors_all:-none}"

    safe_print "commits_last_7d" "git log --since='7 days ago' --oneline | wc -l | tr -d ' '"
    safe_print "authors_last_7d" "git log --since='7 days ago' --pretty=format:'%an' | sort -u | wc -l | tr -d ' '"

    top_authors_7d=$(git log --since='7 days ago' --pretty=format:'%an' | sort | uniq -c | sort -nr | awk '{for (i=2; i<=NF; i++) printf $i " "; print ""}' | paste -s -d ',' -)
    echo "top_authors_7d=${top_authors_7d:-none}"

    safe_print "files_changed_7d" "git log --since='7 days ago' --name-only --pretty=format: | grep -v '^$' | sort -u | wc -l | tr -d ' '"
    safe_print "lines_added_7d" "git log --since='7 days ago' --numstat | awk '{if (\$1 ~ /^[0-9]+$/) add+=\$1} END {print add+0}'"
    safe_print "lines_deleted_7d" "git log --since='7 days ago' --numstat | awk '{if (\$2 ~ /^[0-9]+$/) del+=\$2} END {print del+0}'"

    most_active_files_7d=$(git log --since='7 days ago' --name-only --pretty=format: | grep -v '^$' | sort | uniq -c | sort -nr | awk '{print $2}' | head -5 | paste -s -d ',' -)
    echo "most_active_files_7d=${most_active_files_7d:-none}"

    safe_print "total_tags" "git tag | wc -l | tr -d ' '"
    safe_print "last_tag" "git describe --tags --abbrev=0"
    safe_print "merge_count" "git log --merges --oneline | wc -l | tr -d ' '"

    first_commit_ts=$(git log --reverse --pretty=format:'%ct' | head -1)
    now_ts=$(date +%s)
    if [[ -n "$first_commit_ts" && "$first_commit_ts" =~ ^[0-9]+$ ]]; then
      total_commits=$(git rev-list --all --count)
      days=$(( (now_ts - first_commit_ts) / 86400 ))
      if (( days > 0 )); then
        avg=$(echo "scale=2; $total_commits / $days" | bc)
      else
        avg="$total_commits"
      fi
    else
      avg="0.00"
    fi
    echo "avg_commits_per_day=${avg}"
  fi

  safe_print "uncommitted_changes" "git status --porcelain | wc -l | tr -d ' '"
  safe_print "unstaged_files" "git diff --name-only | wc -l | tr -d ' '"
  safe_print "staged_files" "git diff --cached --name-only | wc -l | tr -d ' '"
  safe_print "untracked_files" "git ls-files --others --exclude-standard | wc -l | tr -d ' '"
  safe_print "local_branches" "git branch | wc -l | tr -d ' '"
  safe_print "remote_branches" "git branch -r | wc -l | tr -d ' '"
  safe_print "rebase_events" "grep rebase .git/logs/HEAD | wc -l | tr -d ' '"

  git_dir=$(safe_git_dir)
  safe_print "git_dir_size" "du -sh "$git_dir" | cut -f1"
  safe_print "git_object_count" "find "$git_dir/objects" -type f | wc -l | tr -d ' '"
  safe_print "custom_git_hooks" "find "$git_dir/hooks" -type f ! -name '*.sample' | wc -l | tr -d ' '"
fi
