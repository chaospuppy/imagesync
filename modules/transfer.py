import subprocess
import re
from pathlib import Path
from ironbank.pipeline.utils.exceptions import GenericSubprocessError
from ironbank.pipeline.container_tools.cosign import Cosign
from .utils.config import Config
from .utils.image import Image
from modules.utils import logger

log: logger = logger.setup(name="transfer")


class Transfer:
    def __init__(self, config: Config):
        self.registry: str = config.destination["registry"]
        self.secure: bool = config.destination["secure"]
        self.images: [Image] = config.images
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
            cosign_verifier = None
            for verifier in self.cosign_verifiers:
                if source.registry() == verifier["registry"] and re.match(verifier.repo, source.repo()):
                    proceed = self._cosign_verify(source, pubkey=cosign_verifier["key"])

            if proceed:
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
                if (
                    not source_digest
                    or not destination_digest
                    or (source_digest != destination_digest)
                ):
                    copy_result = subprocess.run(
                        args=cmd, capture_output=True, check=True
                    )
                    log.info(copy_result.stdout.decode())
                else:
                    log.info(
                        "Source and destination digests match, skipping sync for %s",
                        source.name,
                    )
            else:
                log.info(
                    "Image skipped due to failed cosign verification: %s", source.name
                )
