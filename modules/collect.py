#!/usr/bin/env python

import sys
import subprocess
import json
import re
import requests

from .utils.image import Image
from modules.utils import logger

log: logger = logger.setup(name="collect")

BIGBANG_IMAGES_URL = (
    "https://umbrella-bigbang-releases.s3-us-gov-west-1.amazonaws.com/umbrella"
)


def bigbang_images(version) -> list[str]:
    r = requests.get(f"{BIGBANG_IMAGES_URL}/{version}/images.txt")
    r.raise_for_status()

    return [Image(image) for image in r.content.decode().splitlines()]


def cluster_images() -> set[Image]:
    resources = ["pods", "jobs", "cronjobs"]
    images = []
    for resource in resources:
        cmd = [
            "kubectl",
            "get",
            f"{resource}",
            "-A",
            "-o",
            "json",
        ]

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        resource_json = json.loads(result.stdout)

        for item in resource_json["items"]:
            annotation = False
            if resource == "pods":
                resource_images = _get_images_from_imageswap_annotations(
                    item["metadata"]
                )
                if resource_images:
                    annotation = True
                for image in resource_images:
                    images += [image] if image not in images else []
                # If the original images we not added to the image list from annotations, retrieve images from the spec as usual
                if not annotation:
                    resource_images = _get_images_from_nested_spec(item["spec"])
                    for image in resource_images:
                        images += [image] if image not in images else []
            elif resource == "jobs":
                resource_images = _get_images_from_nested_spec(
                    item["spec"]["template"]["spec"]
                )
                for image in resource_images:
                    images += [image] if image not in images else []
            elif resource == "cronjobs":
                resource_images = _get_images_from_nested_spec(
                    item["spec"]["jobTemplate"]["spec"]["template"]["spec"]
                )
                for image in resource_images:
                    images += [image] if image not in images else []
            else:
                log.error("Unsupported resource. Cannot be parsed")
    return images


# parse images out of item
def _get_images_from_nested_spec(item_nested_spec) -> list[Image]:
    """
    Call with:
    for item in resource['items']:
        image_set = _get_images_from_nested(item['spec']['blah'])
    """
    images = []
    for container in item_nested_spec["containers"]:
        images.append(Image(container["image"]))
    for container in item_nested_spec.get("initContainers", []):
        images.append(Image(container["image"]))
    return images


def _get_images_from_imageswap_annotations(item_metadata) -> list[Image]:
    """
    Call with:
    for item in resource_json['items']:
      if resource == 'pods':
        images += _get_images_from_imageswap_annoations(item['metadata'])
    """
    # TODO: Update this annotation once imageswap is updated to allow for arbitrary annotation key
    imageswap_re = re.compile(r"imageswap.ironbank.dso.mil/[0-9]+")

    if "annotations" not in item_metadata:
        return []

    return [
        Image(v)
        for k, v in item_metadata["annotations"].items()
        if imageswap_re.match(k)
    ]
