import subprocess
import re

from pathlib import Path
from pipeline.utils.exceptions import GenericSubprocessError
from pipeline.container_tools.cosign import Cosign
from .utils.image import Image
from common.utils import logger

log = logger.setup(name="transfer")


class Transfer:
    def __init__(self, config):
        self.registry = config.destination["registry"]
        self.insecure = config.source["insecure"]
        self.images = config.images
        self.cosign_verifiers = config.cosign_verifiers

    def _select_verifier(self, source):
        for verifier in self.cosign_verifiers:
            if source.registry() == verifier.registry and re.match(
                verifier.repo, source.repo()
            ):
                return verifier
        return

    def execute(self):
        total_images = len(self.images)
        for count, source in enumerate(self.images):
            verifier = self._select_verifier(source)
            if verifier:
                try:
                    Cosign.verify(
                        image=source,
                        docker_config_dir=Path(f"{Path.home().as_posix()}/.docker/"),
                        use_key=True,
                        pubkey=verifier.key,
                        log_cmd=True,
                    )
                except GenericSubprocessError:
                    log.warning(
                        "Image skipped due to failed cosign verification: %s",
                        source.name,
                    )
                    continue
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
