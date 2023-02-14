# Imagesync
The script in this directory, `imagesync.py` is used to both manage and transfer images from external registries (such as registry1, docker, quay, etc.)
to the registry specified in the `destination.registry` key of `ecr.yaml`.

There are two main functions this script provides:
- **tidy**: The `tidy` command will consume the `ecr.yaml` file specified with the `-f` flag and locate images that are either unused or missing from it.
- **sync**: The `sync` command syncs the images in the `images` key of `ecr.yaml` to the registry specified by `destination.registry` (or the `--registry` flag, if passed)

## Build
The Dockerfile in this directory will create an image that has imagesync.py and all its dependencies available.

To build the an image that is runnable on an AMD64 machine, execute the following command:
```bash
docker build \
-t imagesync:latest \
.
```

To build the an image that is runnable on an ARM64 machine, execute the following command:

```bash
docker build \
-t imagesync:$(cat VERSION)-arm64 \
--build-arg ARCH=aarch64 \
--build-arg ALT_ARCH=arm64 \
.
```

## Usage
The following sections describe how imagesync can be run using one of two methods:
- Using the image built by the `Build` section of this README
- Using the script directly

## Image
If you wish to use the image built by commands in the `Build` section of this README, you can run the following command:

```
docker run \
-v ${HOME}/.docker/:/root/.docker/ \
-v ${HOME}/.aws/:/root/.aws/ \
-v ${HOME}/.kube/config:/root/.kube/config \
-v ${PWD}/images.yaml:/app/images.yaml \
--rm imagesync:latest \
-f /app/images.yaml \
--help
```
