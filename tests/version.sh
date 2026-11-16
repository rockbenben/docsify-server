#!/bin/sh
set -eu
script="$(dirname "$0")/../scripts/image-version.sh"

check_version() {
  actual=$(sh "$script" "$1" "$2")
  if [ "$actual" != "$3" ]; then
    echo "Expected $3, got $actual (project $1, CLI $2)" >&2
    exit 1
  fi
}

check_version 5.0.1 5.0.0 5.0.1
check_version 5.0.1 5.0.2 5.0.2
check_version 5.0.1 5.1.0 5.1.0
check_version 5.2.3 5.9.0 5.9.0
check_version 5.0.1 6.0.0 6.0.0
check_version 5.0.1 6.2.4 6.2.4
check_version 6.0.1 6.2.4 6.2.4
check_version 9.2.3 10.1.0 10.1.0
check_version 5.0.2 5.0.0 5.0.2
check_version 5.1.3 5.1.2 5.1.3
check_version 5.1.3 5.1.3 5.1.3
check_version 5.9.9 5.10.0 5.10.0

for invalid in 5.0.0-rc.1 5.0 05.0.0 bad; do
  if sh "$script" 5.0.1 "$invalid" >/dev/null 2>&1; then
    echo "Accepted invalid CLI version: $invalid" >&2
    exit 1
  fi
done
if sh "$script" 6.0.1 5.9.0 >/dev/null 2>&1; then
  echo "Accepted a CLI major downgrade" >&2
  exit 1
fi
if sh "$script" 5.2.1 5.1.9 >/dev/null 2>&1; then
  echo "Accepted a CLI minor downgrade" >&2
  exit 1
fi
echo "PASS: CLI major/minor tracking, repository patch releases, and invalid versions"
