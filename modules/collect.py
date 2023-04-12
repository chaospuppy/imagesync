#!/usr/bin/env python

import sys
import subprocess
import json
import re
import requests

from dataclasses import dataclass
from .utils.image import Image
from modules.utils import logger

log: logger = logger.setup(name="collect")

BIGBANG_IMAGES_URL = (
    "https://umbrella-bigbang-releases.s3-us-gov-west-1.amazonaws.com/umbrella"
)


@dataclass(frozen=True, slots=True)
class Collector:
    image_name_annotation_key: str
    bigbang_version: str = ""

    def bigbang_images(self) -> list[str]:
        r = requests.get(f"{BIGBANG_IMAGES_URL}/{self.bigbang_version}/images.txt")
        r.raise_for_status()

        return [Image(image) for image in r.content.decode().splitlines()]

    def cluster_images(self) -> set[Image]:
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
                    resource_images = (
                        (
                            self._get_images_from_mutating_webhook_annotations(
                                item["metadata"]
                            )
                        )
                        if self.image_name_annotation_key
                        else []
                    )
                    if resource_images:
                        annotation = True
                    for image in resource_images:
                        images += [image] if image not in images else []
                    # If the original images we not added to the image list from annotations, retrieve images from the spec as usual
                    if not annotation:
                        resource_images = self._get_images_from_nested_spec(
                            item["spec"]
                        )
                        for image in resource_images:
                            images += [image] if image not in images else []
                elif resource == "jobs":
                    resource_images = self._get_images_from_nested_spec(
                        item["spec"]["template"]["spec"]
                    )
                    for image in resource_images:
                        images += [image] if image not in images else []
                elif resource == "cronjobs":
                    resource_images = self._get_images_from_nested_spec(
                        item["spec"]["jobTemplate"]["spec"]["template"]["spec"]
                    )
                    for image in resource_images:
                        images += [image] if image not in images else []
                else:
                    log.error("Unsupported resource. Cannot be parsed")
        return images

    # parse images out of item
    def _get_images_from_nested_spec(self, item_nested_spec) -> list[Image]:
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

    def _get_images_from_mutating_webhook_annotations(
        self, item_metadata
    ) -> list[Image]:
        """
        Call with:
        for item in resource_json['items']:
          if resource == 'pods':
            images += _get_images_from_mutating_webhook_annoations(item['metadata'])
        """
        log.debug("Finding images using annotation %s", self.image_name_annotation_key)
        mutating_webhook_re = re.compile(self.image_name_annotation_key)

        if "annotations" not in item_metadata:
            return []

        return [
            Image(v)
            for k, v in item_metadata["annotations"].items()
            if mutating_webhook_re.match(k)
        ]
