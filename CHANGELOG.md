# Changelog

## v5.0.1 - 2026-11-17

- Restore access through published Docker ports with docsify-cli v5 by explicitly binding to `0.0.0.0:3000`.
- Fill missing starter assets in existing directories without overwriting user files; copy the entry point last so interrupted initialization can be retried.
- Set the next container release to v5.0.1; refresh CLI monthly and follow its major/minor versions, with repository fixes advancing only the patch version. Use the same resolved CLI version for testing and publishing.
- Rebuild monthly to refresh both docsify-cli and the Node LTS base image, reusing existing version tags when versions are unchanged.
- Test published-port access, offline assets, existing user files, read-only mounts, and disabled initialization before publishing.
- Default local builds to the latest CLI, record the installed CLI version, and share one resolved Node LTS digest across CI test and release builds.
- Pin CI Actions to verified current release commits, with dependency updates reviewed manually before releases.
