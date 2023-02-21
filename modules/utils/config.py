import yaml

from dataclasses import dataclass, field
from .image import Image


class Config(yaml.YAMLObject):
    def __init__(self, images, include, exclude, **kwargs):

        # Convert images in config to Image type
        self.images = [Image(image["name"]) for image in images]

        # Convert include in config to Image type
        self.include = [Image(image["name"]) for image in include]

        # Convert exclude in config to Image type
        self.exclude = [Image(image["name"]) for image in exclude]

        for k, v in kwargs.items():
            setattr(self, k, v)

    def clean(self):
        self.images = sorted(
            list({Image(image.name) for image in self.images}), key=lambda x: x.name
        )

    def find_unused_images(self, used_images: [Image]) -> [Image]:
        return [image for image in self.images if image not in used_images]


# Override emitter to avoid outputting untrusted python object tags into generated yaml
yaml.emitter.Emitter.process_tag = lambda self, *args, **kwargs: None
