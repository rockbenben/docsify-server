# 跟随 Node LTS，长期自动获得安全更新，无需手动升主版本号
ARG NODE_IMAGE=node:lts-alpine
FROM ${NODE_IMAGE}

LABEL org.opencontainers.image.title="docsify-server" \
      org.opencontainers.image.description="A Dockerized docsify-cli server for serving Markdown docs." \
      org.opencontainers.image.source="https://github.com/rockbenben/docsify-server" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /docs

# CI 显式传入解析后的版本，保证测试和多架构发布安装同一个 CLI。
ARG DOCSIFY_CLI_VERSION=latest
RUN npm install -g "docsify-cli@${DOCSIFY_CLI_VERSION}" --no-fund --no-audit \
    && mkdir -p /opt/docsify-server \
    && node -p "require('/usr/local/lib/node_modules/docsify-cli/package.json').version" > /opt/docsify-server/DOCSIFY_CLI_VERSION \
    && npm cache clean --force

# 内置离线起始模板（含 vendored 资产），供 entrypoint 在空目录时自举
COPY template/ /opt/docsify-template/
COPY VERSION /opt/docsify-server/VERSION
COPY scripts/image-version.sh /opt/docsify-server/image-version.sh
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN IMAGE_VERSION=$(sh /opt/docsify-server/image-version.sh "$(cat /opt/docsify-server/VERSION)" "$(cat /opt/docsify-server/DOCSIFY_CLI_VERSION)") \
    && printf '%s\n' "$IMAGE_VERSION" > /opt/docsify-server/VERSION \
    && chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 3000/tcp

# 简单健康检查：确认 serve 端口在响应
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://127.0.0.1:3000 || exit 1

# entrypoint 内部用 exec 交棒给 docsify，使其成为 PID 1 优雅停止
ENTRYPOINT ["docker-entrypoint.sh"]
