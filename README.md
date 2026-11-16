# Docsify Server Docker

A pre-built, multi-arch Docker image that serves your Markdown docs with the official [`docsify-cli`](https://github.com/docsifyjs/docsify-cli). The workflow refreshes both `docsify-cli` and the Node LTS base image monthly, so you get an up-to-date server without installing anything locally.

Published to both registries:

- **GHCR** — `ghcr.io/rockbenben/docsify-server`
- **Docker Hub** — `rockben/docsify-server`

## Features

- 📝 **Effortless docs** — write Markdown, mount it, and Docsify serves it with style.
- 🐳 **Zero install** — just pull the image; no Node.js or npm on the host.
- 🏗️ **Multi-arch** — built for `linux/amd64` and `linux/arm64` (Apple Silicon, Raspberry Pi, etc.).
- 🔄 **Auto-update** — monthly rebuilds refresh both `docsify-cli` and the Node LTS base image.
- 🚀 **Zero-config first run** — new to Docsify? Mount an empty folder and the container scaffolds a ready-to-edit starter site for you (see below), so you never hit a cryptic "No docs found" crash.
- 📴 **Works offline** — the scaffolded site bundles its assets (search, TOC, image zoom, word count) inside the image; no CDN required.
- 🩺 **Health check** — the container reports healthy once the server responds on port `3000`.

## Image tags

| Tag | Meaning |
| --- | --- |
| `latest` | The newest tested build. |
| `5.0.1`, `v5.0.1` | Container release including the v5 port-binding fix. |
| `cli-<x.y.z>` | The latest build bundling that exact docsify-cli version. |

The current container release is **v5.0.1**, bundling **docsify-cli 5.0.0**. **Major and minor versions follow docsify-cli; repository fixes only advance the patch version** in [`VERSION`](VERSION). A newer CLI release provides the version baseline: CLI 5.1.0 leads to image v5.1.0, and a subsequent repository fix can release v5.1.1. Within the same major/minor line, the greater of the CLI patch and the repository patch is used. Monthly rebuilds with no version changes reuse the current tags. Older image tags mirrored the complete CLI version; this policy applies from v5.0.1 onward. See the [changelog](CHANGELOG.md).

> **All tags are rolling.** Rebuilds can refresh the same tags with new dependencies. Pin an image digest for a byte-for-byte reproducible deployment, e.g. `ghcr.io/rockbenben/docsify-server@sha256:…`. CI images record the exact CLI version in the label `io.github.rockbenben.docsify-cli.version`. Every image also records it in `/opt/docsify-server/DOCSIFY_CLI_VERSION`.

## Getting Started

### Prerequisites

Docker installed on your machine.

### Run with Docker Compose

Place your Markdown files in a local `./docs` directory, then create `docker-compose.yml`:

```yaml
services:
  docsify:
    container_name: docsify-server
    image: ghcr.io/rockbenben/docsify-server:latest
    volumes:
      - ./docs:/docs
    ports:
      - "8080:3000"
    restart: unless-stopped
```

Start it:

```sh
docker compose up -d
```

### Run with a single command

```sh
# GHCR
docker run -d -p 8080:3000 -v "$(pwd)/docs:/docs" --name docsify-server ghcr.io/rockbenben/docsify-server:latest

# Docker Hub
docker run -d -p 8080:3000 -v "$(pwd)/docs:/docs" --name docsify-server rockben/docsify-server:latest
```

Then open **http://localhost:8080**.

> The container serves whatever is mounted at `/docs` on `0.0.0.0:3000`; the examples map it to host port `8080`. The listen address is set explicitly so published ports remain reachable with docsify-cli v5, whose default is `localhost`.

## First run & the starter site

Docsify needs an `index.html` entry point. To keep first-time use painless, the container inspects `/docs` on startup:

| What you mount | What happens |
| --- | --- |
| **Empty folder** | A complete offline example site (`index.html` + bundled `assets/` + a bilingual `README.md`) is scaffolded so you have a working, editable example immediately. |
| **Markdown files, no `index.html`** | An `index.html` and missing starter assets are added, including inside an existing `assets/` directory; existing files are **never** overwritten. |
| **Your own `index.html`** | Left completely untouched — bring your own Docsify config and nothing is changed. |

The scaffolded files are just a starter example to get you going and show the format — edit or replace them freely. Once an `index.html` exists in `/docs`, the container never touches your folder again (upgrading the image won't overwrite anything). If you ever want to regenerate the example, delete `/docs/index.html` and restart.

### Turning it off

Set `DOCSIFY_AUTO_INIT=false` for strict behaviour — the container will not scaffold anything, and will exit with Docsify's usual message if no `index.html` is present:

```sh
docker run -d -p 8080:3000 -e DOCSIFY_AUTO_INIT=false -v "$(pwd)/docs:/docs" ghcr.io/rockbenben/docsify-server:latest
```

## How the auto-update works

The [`docker.yml`](.github/workflows/docker.yml) workflow runs monthly, when image inputs change on `main`, and on manual dispatch:

1. **check** resolves the latest stable CLI version from npm once. A newer CLI major/minor line becomes the image version baseline; within the same line, the greater of the CLI patch and `VERSION` patch is used. Older CLI major/minor lines are rejected to prevent accidental downgrades.
2. **build** installs that exact CLI version, tests container behavior and published-port access, then builds and publishes the multi-arch image to both registries as `latest`, `<version>`, `v<version>`, and `cli-<CLI version>`.

Every build pulls the current Node LTS base image. Pushes, manual runs, and monthly rebuilds run even when docsify-cli has no new release, so repository fixes and base-image security updates are included. Each CI run resolves the CLI version and the Node LTS multi-architecture digest once. The smoke test and both published architectures receive those same inputs. GitHub Actions dependencies are pinned to verified release commits and reviewed manually before releases. Scheduled checks depend on GitHub Actions scheduling and may be delayed.

To prepare a repository fix release, increment only the patch version in `VERSION` and update `CHANGELOG.md`. Base it on the current published version (for example, set `VERSION` to `5.1.1` after automatically following CLI 5.1.0). Upstream CLI upgrades are picked up by the next monthly build without a repository edit. To force a rebuild, use **Actions → Build and Push Docker Image → Run workflow**.

## Building locally

```sh
docker build --pull --no-cache -t docsify-server .
docker run -d -p 8080:3000 -v "$(pwd)/docs:/docs" docsify-server
```

The image is based on `node:lts-alpine`. Local builds default to `docsify-cli@latest`; use `--pull --no-cache` to refresh both the base image and the npm installation. CI resolves the latest CLI version once and passes that concrete version to all builds. To select a specific CLI version:

```sh
docker build --pull --build-arg DOCSIFY_CLI_VERSION=5.0.0 -t docsify-server .
```

Run the same container checks used before publishing (Python 3 and Docker required):

```sh
python3 tests/smoke.py docsify-server
```
