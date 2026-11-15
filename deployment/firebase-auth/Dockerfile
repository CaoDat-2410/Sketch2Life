FROM node:22-bookworm-slim

ARG FIREBASE_TOOLS_VERSION=14.22.0
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --global "firebase-tools@${FIREBASE_TOOLS_VERSION}"

WORKDIR /workspace
COPY deployment/firebase-auth/firebase.json ./firebase.json
COPY deployment/firebase-auth/entrypoint.sh /usr/local/bin/firebase-auth-entrypoint
RUN chmod 0755 /usr/local/bin/firebase-auth-entrypoint

EXPOSE 9099
ENTRYPOINT ["/usr/local/bin/firebase-auth-entrypoint"]
