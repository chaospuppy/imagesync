OS ?= $(shell uname -s | tr '[:upper:]' '[:lower:]')
ARCH ?= $(shell uname -m)
VERSION = $(shell cat VERSION)
IMAGE_REPO ?= localhost:5000
IMAGE_NAME ?= imagesync

build: VERSION
	docker build \
		--platform $(ARCH) \
		-t $(IMAGE_REPO)/imagesync:$(VERSION)-$(ARCH) \
		-f Dockerfile.$(ARCH) .

push-image: VERSION
	docker push $(IMAGE_REPO)/$(IMAGE_NAME):$(VERSION)-$(ARCH)

push-latest-tag-version: VERSION
	docker tag $(IMAGE_REPO)/$(IMAGE_NAME):$(VERSION)-$(ARCH) $(IMAGE_REPO)/$(IMAGE_NAME):latest
	docker tag $(IMAGE_REPO)/$(IMAGE_NAME):$(VERSION)-$(ARCH) $(IMAGE_REPO)/$(IMAGE_NAME):$(VERSION)
	docker push $(IMAGE_REPO)/$(IMAGE_NAME):$(VERSION)
	docker push $(IMAGE_REPO)/$(IMAGE_NAME):latest

artifact: build
	mkdir -p _build/
	docker save -o _build/imagesync.tar $(IMAGE_REPO)/$(IMAGE_NAME):$(VERSION)-$(ARCH)

.PHONY: build artifact push-image push-latest-tag-version
