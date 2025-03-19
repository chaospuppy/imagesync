# Imagesync
The script in this directory, `imagesync.py` is used to both manage and transfer images from external registries (such as registry1, docker, quay, etc.)
to the registry specified in the `destination.registry` key of `images.yaml`.

There are two main functions this script provides:
- **tidy**: The `tidy` command will consume the `images.yaml` file specified with the `-f` flag and locate images that are either unused or missing from it.
- **sync**: The `sync` command syncs the images in the `images` key of `images.yaml` to the registry specified by `destination.registry` (or the `--registry` flag, if passed)

## Build
The Dockerfile in this directory will create an image that has imagesync.py and all its dependencies available.

To build the an image that is runnable on the architecture of your machine, execute the following command:
```bash
make build
```

To build the an image that is runnable on an ARM64 machine, execute the following command:

```bash
ARCH=arm64 make build
```

or for amd64

```bash
ARCH=amd64 make build
```

## Usage
The following sections describe how imagesync can be run using one of two methods:
- Using the image built by the `Build` section of this README
- Using the script directly

### WSL
If you are running WSL it is recommended that you download and setup[docker desktop wsl2 backend](https://docs.docker.com/desktop/windows/wsl/) and setup your folder structure on windows as:
```bash
C:\Users\{USER}\.docker
```
and on your WSL distro:
```bash
/home/{USER}/.docker
```

## Image
If you wish to use the image built by commands in the `Build` section of this README, you can run the following command:

```
docker run \
-v ${HOME}/.docker/:/home/python/.docker/ \
-v ${HOME}/.kube/config:/home/python/.kube/config \
-v ${PWD}/images.yaml:/app/images.yaml \
--rm imagesync:latest \
-f /app/images.yaml \
--help
```
