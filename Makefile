OS ?= $(shell uname | awk '{print tolower($0)}')
ARCH ?= $(shell uname -m)
VERSION = $(shell cat VERSION)
IMAGE_REPO ?= localhost:5000
IMAGE_NAME ?= imagesync

build: VERSION
	docker build \
		--platform $(ARCH) \
		-t $(IMAGE_REPO)/imagesync:$(VERSION)-$(ARCH) \
		-t $(IMAGE_REPO)/imagesync:$(VERSION) \
		-f Dockerfile.$(ARCH) .

push-image: VERSION
	docker push $(IMAGE_REPO)/$(IMAGE_NAME):$(VERSION)-$(ARCH)
	docker push $(IMAGE_REPO)/$(IMAGE_NAME):$(VERSION)

push-latest-tag:
	docker tag $(IMAGE_REPO)/$(IMAGE_NAME):$(VERSION)-$(ARCH) $(IMAGE_REPO)/$(IMAGE_NAME):latest
	docker push $(IMAGE_REPO)/$(IMAGE_NAME):latest

artifact: build
	mkdir -p _build/
	docker save -o _build/imagesync.tar imagesync:latest

# .PHONY: build
# build-args:
# ifeq ($(OS), Darwin)
# ifeq ($(ARCH), arm64)
# 	ALT_ARCH="aarch64"
# else ifeq ($(OS), Linux)
# else ifeq ($(ARCH), amd64)
# 	ALT_ARCH="amd64"
# endif
# endif

