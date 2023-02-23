#!/usr/bin/env python

import inspect
import yaml
import os
import sys
import argparse
import pathlib
import copy


from subprocess import CalledProcessError
from requests.exceptions import HTTPError
from json import JSONDecodeError

from modules import collect, transfer
from modules.utils import logger
from modules.utils.config import Config
from modules.utils.image import Image

log: logger = logger.setup()


def main():
    parser = argparse.ArgumentParser(
        description="Tool to create, maintain, and transfer images listed in images.yaml from multiple source registries to a single destination registry"
    )
    parser.add_argument(
        "-f",
        "--images-file",
        help="Path to images.yaml",
        default=pathlib.Path(os.path.dirname(__file__)).joinpath("images.yaml"),
    )

    subparser = parser.add_subparsers(help="", dest="command")

    tidy_subparser = subparser.add_parser("tidy")
    tidy_subparser.add_argument(
        "version", help="version of BigBang to retrieve images for"
    )

    sync_subparser = subparser.add_parser("sync")
    sync_subparser.add_argument(
        "--registry", help="destination registry (overrides config setting)"
    )
    sync_subparser.add_argument(
        "--insecure",
        help="skip TLS verify for destination registry (overrides config setting)",
        action="store_true",
    )

    args = parser.parse_args()
    if not args.command:
        log.error(
            "Must specify one of 'tidy' or 'sync'.  See help output for more information"
        )
        sys.exit(1)

    log.info("Loading config...")
    with open(args.images_file) as f:
        config = Config(**yaml.safe_load(f))

    if args.command == "tidy":
        log.info("Collecting images from cluster...")
        used_images = []

        try:
            used_images.extend(collect.cluster_images())
        except HTTPError as e:
            log.error(f"Error retrieving images from cluster: {e.code} {e.reason}")
            sys.exit(1)
        except CalledProcessError as e:
            log.error(f"Error returned from query: {e.stderr}")
            sys.exit(1)
        except JSONDecodeError as e:
            log.error(f"Error decoding JSON returned from query: {e}")
            sys.exit(1)

        try:
            used_images.extend(collect.bigbang_images(args.version))
        except HTTPError as e:
            log.error(f"Error retreving images.txt from BigBang: {e.code} {e.reason}")
            sys.exit(1)

        # Remove images that are unconditionally excluded from image list
        for image in config.exclude:
            try:
                used_images.remove(image)
            except ValueError:
                pass

        # Add images that are unconditionally included in image list
        used_images.extend(config.include)
        used_images.sort(key=lambda x: x.name)

        log.info("Images to be removed from images.yaml:")
        for image in config.find_unused_images(used_images):
            log.info(image)
        log.info("Images to be added to images.yaml:")
        for image in used_images:
            if image not in config.images:
                log.info(image)

        # Set list of images in config equal to the list of used images to remove unused ones
        config.images = used_images
        # Remove duplicated images
        config.clean()

        filter_image_attr = lambda attr, image_list: [
            {attr: getattr(image, attr)} for image in image_list
        ]
        config_image_list_attributes = [
            name
            for name, value in inspect.getmembers(config)
            if isinstance(value, list) and value and isinstance(value[0], Image)
        ]
        with open(args.images_file, "w") as f:
            for attr in config_image_list_attributes:
                setattr(config, attr, filter_image_attr("name", getattr(config, attr)))
            yaml.dump(config, f)

    if args.command == "sync":
        if args.registry:
            config.destination["registry"] = args.registry
        if args.insecure:
            config.destination["secure"] = False
        # Instantiate Transfer
        transferer = transfer.Transfer(config)
        # Execute Transfer
        try:
            transferer.execute()
        except CalledProcessError as e:
            log.error(f"Error returned from transfer: {e.stderr}")
            sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
