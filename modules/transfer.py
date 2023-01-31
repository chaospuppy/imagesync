import subprocess
import sys

from .utils.config import Config
from .utils.image import Image
from modules.utils import logger

log: logger = logger.setup(name="transfer")


class Transfer:
    def __init__(self, config: Config):
        self.registry: str = config.destination["registry"]
        self.secure: bool = config.destination["secure"]
        self.images: [Image] = config.images

    def execute(self):
        total_images = len(self.images)
        count = 0
        for source in self.images:
            count += 1
            destination = Image.new_registry(source, self.registry, self.secure)
            cmd = [
                "skopeo",
                "copy",
                f"docker://{source.name}",
                f"docker://{destination.name}",
            ]

            cmd += ["--dest-tls-verify=false"] if not self.secure else []

            log.info(f"[{count}/{total_images}] Copying {source} to {destination}")
            source_digest = source.digest()
            destination_digest = destination.digest()
            if not source_digest or not destination_digest or (source_digest != destination_digest):
                copy_result = subprocess.run(args=cmd, capture_output=True, check=True)
                log.info(copy_result.stdout.decode())
            else:
                log.info("Source and destination digests match, skipping sync for %s", source.name)

