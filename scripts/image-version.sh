#!/bin/sh
# Shared by local Docker builds and CI: follow CLI major/minor; fixes advance the patch.
set -eu

release_version=$1
cli_version=$2
for version in "$release_version" "$cli_version"; do
  if ! printf '%s\n' "$version" | grep -Eq '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'; then
    echo "Invalid stable version: $version" >&2
    exit 1
  fi
done

cli_major=${cli_version%%.*}
release_major=${release_version%%.*}
cli_rest=${cli_version#*.}
release_rest=${release_version#*.}
cli_minor=${cli_rest%%.*}
release_minor=${release_rest%%.*}
cli_patch=${cli_version##*.}
release_patch=${release_version##*.}

if [ "$cli_major" -lt "$release_major" ] || {
  [ "$cli_major" -eq "$release_major" ] && [ "$cli_minor" -lt "$release_minor" ];
}; then
  echo "CLI version $cli_version is older than the image release line $release_version" >&2
  exit 1
elif [ "$cli_major" -gt "$release_major" ] || [ "$cli_minor" -gt "$release_minor" ] || [ "$cli_patch" -gt "$release_patch" ]; then
  printf '%s\n' "$cli_version"
else
  printf '%s\n' "$release_version"
fi
