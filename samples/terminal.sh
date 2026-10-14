#!/usr/bin/env bash
# Deepwick standard terminal screenshot content.
set -euo pipefail

names=(black red green yellow blue magenta cyan white)

printf '\n  ANSI 16\n\n'
for base in 30 90; do
  printf '  '
  for i in "${!names[@]}"; do
    printf '\e[%dm%-9s\e[0m' $((base + i)) "${names[$i]}"
  done
  printf '\n'
done
for base in 40 100; do
  printf '  '
  for i in "${!names[@]}"; do
    printf '\e[%dm%-9s\e[0m' $((base + i)) ' '
  done
  printf '\n'
done
printf '\n  \e[1mbold\e[0m  \e[3mitalic\e[0m  \e[4munderline\e[0m  \e[7mreverse\e[0m\n'

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cd "$work"

export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
g() { git -c color.ui=always -c core.pager=cat "$@"; }

g init -q -b main
g config user.name "Deepwick"
g config user.email "deepwick@example.invalid"
mkdir -p src docs
printf 'def greet(name):\n    return "Hello, " + name\n' > src/app.py
printf '# Notes\n' > docs/README.md
printf '#!/bin/sh\necho run\n' > run.sh
chmod +x run.sh
ln -s src/app.py app-link.py
g add -A
g commit -qm "Initial commit"
g checkout -qb feature
printf 'def wave(name):\n    return "Bye, " + name\n' >> src/app.py
g commit -qam "Add wave"
g checkout -q main
printf 'Deepwick sample repository.\n' >> docs/README.md
g commit -qam "Update notes"
g merge -q --no-ff feature -m "Merge branch feature"
sed -i 's/Hello/Hi/' src/app.py
printf 'scratch\n' > untracked.txt

printf '\n  $ ls -lgoA --color=always\n'
ls -lgoA --color=always
printf '\n  $ git diff\n'
g diff
printf '\n  $ git log --graph --oneline --decorate --all\n'
g log --graph --oneline --decorate --all
