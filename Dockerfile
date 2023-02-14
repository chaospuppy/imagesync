FROM quay.io/skopeo/stable:latest

ARG KUBECTL_VERSION="v1.23.5"
ARG COSIGN_VERSION="1.13.1"

ARG ARCH="x86_64"
ARG ARCH_ALT="amd64"
ARG OS="linux"

RUN mkdir /app /root/.kube/ \
  && dnf install unzip -y \
  && rpm -ivh "https://github.com/sigstore/cosign/releases/download/v${COSIGN_VERSION}/cosign-${COSIGN_VERSION}.${ARCH}.rpm" \
  && curl "https://awscli.amazonaws.com/awscli-exe-linux-${ARCH}.zip" -o "awscliv2.zip" \
  && unzip awscliv2.zip \
  && ./aws/install

COPY . /app/
WORKDIR /app/

RUN curl -sSL https://install.python-poetry.org | python3 - \
  && /root/.local/bin/poetry install --only main \
  && curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/${OS}/${ARCH_ALT}/kubectl" \
  && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

RUN curl -LO https://amazon-ecr-credential-helper-releases.s3.us-east-2.amazonaws.com/0.6.0/linux-amd64/docker-credential-ecr-login \
  && chmod 755 docker-credential-ecr-login \
  && mv docker-credential-ecr-login /usr/local/bin/

ENTRYPOINT ["/root/.local/bin/poetry", "run", "/app/imagesync.py"]
