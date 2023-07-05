import subprocess
import re
from pathlib import Path
from pipeline.utils.exceptions import GenericSubprocessError
from pipeline.container_tools.cosign import Cosign
from .utils.config import Config
from .utils.image import Image
from common.utils import logger

log: logger = logger.setup(name="transfer")


class Transfer:
    def __init__(self, config: Config):
        self.registry: str = config.destination["registry"]
        self.insecure: bool = config.source["insecure"]
        self.images: list[Image] = config.images
        self.cosign_verifiers = config.cosign_verifiers

    def _cosign_verify(self, image: Image, pubkey: Path):
        try:
            verify = Cosign.verify(image, pubkey, log_cmd=True)
        except GenericSubprocessError:
            verify = False
        return verify

    def execute(self):
        total_images = len(self.images)
        for count, source in enumerate(self.images):
            proceed = True
            for verifier in self.cosign_verifiers:
                if source.registry() == verifier.registry and re.match(
                    verifier.repo, source.repo()
                ):
                    proceed = self._cosign_verify(source, pubkey=verifier.key)

            if proceed:
                destination = Image.new_registry(source, self.registry)
                cmd = [
                    "crane",
                    "copy",
                    source.name,
                    destination.name,
                ]

                cmd += ["--insecure"] if self.insecure else []

                log.info(f"[{count}/{total_images}] Copying {source} to {destination}")
                copy_result = subprocess.run(args=cmd, capture_output=True, check=True)
                log.info(copy_result.stdout.decode())

            else:
                log.info(
                    "Image skipped due to failed cosign verification: %s", source.name
                )
