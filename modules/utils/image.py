import re
import subprocess
import json
from dataclasses import dataclass, field
from modules.utils import logger

log: logger = logger.setup(name="Image")


@dataclass(frozen=True)
class Image:
    name: str
    secure: bool = True

    def __post_init__(self):
        """
        In the event that an image is specified in-cluster without a FQDN prefix, assume that this image is coming from docker.io
        """
        if len(self.name.split("/")) > 1:
            registry = self.name.split("/")[0]
            if not (
                re.search("\.", registry) or re.search("localhost:[0-9]+", registry)
            ):
                object.__setattr__(self, "name", f"docker.io/{self.name}")
        else:
            object.__setattr__(self, "name", f"docker.io/library/{self.name}")

    def __repr__(self):
        return self.name

    def digest(self, cache=False):
        log.info("Getting for digest for %s", self.name)
        cmd = ["skopeo", "inspect", "--raw", f"docker://{self.name}"]

        if not self.secure:
            cmd += ["--tls-verify=false"]

        try:
            manifest = subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            log.info("Error while getting digest for %s", self.name)
            return None

        manifest_json = json.loads(manifest.stdout)
        # TODO: The manifests format returned from the inspect command is inconsistent, so we should build more flexiblity into this
        try:
            return manifest_json["config"]["digest"]
        except KeyError:
            log.info("Error parsing digest for %s", self.name)
            return None

    def registry(self):
        return self.name.split("/")[0]

    def repo(self):
        return "/".join(self.name.split("/")[1:]).split(":")[0]

    @classmethod
    def new_registry(cls, image, registry, secure):
        name = image.name.split("/")
        name[0] = registry
        return cls("/".join(name), secure)
