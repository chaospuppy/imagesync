import yaml

from pathlib import Path
from dataclasses import dataclass
from .image import Image


class Config(yaml.YAMLObject):
    def __init__(self, images, include, exclude, cosign_verifiers, **kwargs):
        # Convert images in config to Image type
        self.images = [Image(image["name"]) for image in images]

        # Convert include in config to Image type
        self.include = [Image(image["name"]) for image in include]

        # Convert exclude in config to Image type
        self.exclude = [Image(image["name"]) for image in exclude]

        self.cosign_verifiers = [
            CosignVerifier(
                registry=verifier["registry"],
                repo=verifier["repo"],
                key=verifier["key"],
            )
            for verifier in cosign_verifiers
        ]

        for k, v in kwargs.items():
            setattr(self, k, v)

    def clean(self):
        self.images = sorted(
            list({Image(image.name) for image in self.images}), key=lambda x: x.name
        )

    def unused_images(self, used_images: list[Image]) -> list[Image]:
        return [image for image in self.images if image not in used_images]


@dataclass(frozen=True)
class CosignVerifier:
    registry: str
    repo: str
    key: str

    def __post_init__(self):
        object.__setattr__(self, "key", Path(self.key))

    def __getstate__(self):
        return dict(registry=self.registry, repo=self.repo, key=str(self.key))


# Override emitter to avoid outputting untrusted python object tags into generated yaml
yaml.emitter.Emitter.process_tag = lambda self, *args, **kwargs: None
