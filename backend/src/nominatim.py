import logging
import docker
import os

import requests

from src.util.functions import get_region_url


class NominatimManager:
    """
    Manages Nominatim Docker containers for different regions.
    Uses Docker SDK to start, stop, and check the status of Nominatim containers.
    Is a singleton class, accessed via the NominatimManager.get_instance() method.
    """

    _instance = None

    def __init__(self):
        self.client = docker.from_env()

        self.running_container = None

        self.volume_data = os.getenv("NOMINATIM_DATA_VOLUME", "nominatim-data")
        self.volume_settings = os.getenv("NOMINATIM_SETTINGS_VOLUME", "nominatim-settings")
        self.volume_flatnode = os.getenv("NOMINATIM_FLATNODE_VOLUME", "nominatim-flatnode")
        self.volumes = [
            self.volume_data,
            self.volume_settings,
            self.volume_flatnode,
        ]
        self.image_name = os.getenv("NOMINATIM_IMAGE_NAME", "mediagis/nominatim:4.1.0")
        self.base_container_name = os.getenv("NOMINATIM_BASE_CONTAINER_NAME", "nominatim")
        self.host_port = int(os.getenv("NOMINATIM_HOST_PORT", "8080"))
        self.container_port = int(os.getenv("NOMINATIM_CONTAINER_PORT", "8080"))
        self.nominatim_password = os.getenv("NOMINATIM_PASSWORD", "nominatimpassword")

        self.logger = logging.getLogger(self.__class__.__name__)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def stop_running(self):
        if self.running_container is not None:
            self.stop_container(self.running_container)
            self.running_container = None

    def _init_volumes(self):
        """
        Initialize Docker volumes for Nominatim if they do not exist.
        """

        self.logger.info("Initializing Nominatim volumes...")

        for vol in self.volumes:
            if vol not in [v.name for v in self.client.volumes.list()]:
                self.client.volumes.create(name=vol)

    async def _init_container(self, region: str):
        """
        Initialize and run a Nominatim Docker container for the specified region.
        Args:
            region (str): The region to initialize the Nominatim container for. (geofabrik style, e.g. "europe/germany/brandenburg")
        """

        self._init_volumes()

        self.logger.info("Starting Nominatim container...")

        self.client.containers.run(
            self.image_name,
            name=self._get_region_container_name(region),
            detach=True,
            ports={f"{self.container_port}/tcp": self.host_port},
            volumes={
                self.volume_data: {"bind": "/var/lib/postgresql/12/main", "mode": "rw"},
                self.volume_settings: {"bind": "/var/www/html/build", "mode": "rw"},
                self.volume_flatnode: {"bind": "/data", "mode": "rw"},
            },
            environment={
                "NOMINATIM_PASSWORD": self.nominatim_password,
                "IMPORT_STYLE": "full",
                "PBF_URL": await get_region_url(region),
            },
        )

    def _get_region_container_name(self, region: str) -> str:
        """
        Get the name of the Nominatim container for the specified region.
        Args:
            region (str): The region to get the container name for.
        Returns:
            str: The name of the Nominatim container for the specified region.
        """
        return f"{self.base_container_name}-{region.replace('/', '-')}"

    async def start_container(self, region: str) -> str:
        """
        Start the Nominatim container for the specified region.

        Args:
            region (str): The region to start Nominatim for.
        Returns:
            str: "new" if a new container was created, "existing" if an existing container was started.
        """

        if self.running_container is not None and self.running_container != region:
            self.stop_container(self.running_container)

        self.logger.info("Starting Nominatim container...")
        existing = True
        try:
            container = self.client.containers.get(self._get_region_container_name(region))
            self.logger.info(f"Nominatim container found: {container.id}")
            if container.status != "running":
                container.start()
        except docker.errors.NotFound:
            existing = False
            await self._init_container(region)
        if self.is_running(region):
            self.running_container = region
            self.logger.info(
                f"Nominatim container for region '{self.running_container}' is running."
            )
        return "existing" if existing else "new"

    def stop_container(self, region: str):
        """
        Stop the Nominatim container for the specified region.
        Args:
            region (str): The region to stop Nominatim for.
        """
        self.logger.info("Stopping Nominatim container...")
        try:
            container = self.client.containers.get(self._get_region_container_name(region))
            if container.status == "running":
                container.stop()
                self.running_container = None
        except docker.errors.NotFound:
            pass

    def is_running(self, region: str) -> bool:
        """
        Check if the Nominatim container for the specified region is running.
        Args:
            region (str): The region to check Nominatim for.
        Returns:
            bool: True if the Nominatim container is running, False otherwise.
        """
        try:
            container = self.client.containers.get(self._get_region_container_name(region))
            return container.status == "running"
        except docker.errors.NotFound:
            return False

    def status(self, region: str = None) -> dict:
        """
        Get the status of the Nominatim container for the specified region.
        Args:
            region (str): The region to get the status for.
        Returns:
            dict: The status of the Nominatim container for the specified region.
            Keys:
                - container_status: The status of the Docker container (e.g. "running", "exited").
                - nominatim_status: The status of the Nominatim service (e.g. initialization progress).
                - nominatim_log_tail: The last 10 lines of the Nominatim container log.
        """
        try:
            container_status = (
                self.client.containers.get(self._get_region_container_name(region)).status
                if region
                else "unknown"
            )
            container_logs = (
                self.client.containers.get(self._get_region_container_name(region))
                .logs(tail=10)
                .decode("utf-8")
                .splitlines()
                if region
                else []
            )
            status = {"container_status": container_status, "nominatim_log_tail": container_logs}

            if self.running_container == region or region is None:
                try:
                    print(
                        f"Checking Nominatim status at http://localhost:{self.host_port}/status.php"
                    )
                    response = requests.get(
                        f"http://localhost:{self.host_port}/status.php", timeout=5
                    )
                    if response.status_code == 200:
                        status["nominatim_status"] = "running"
                    else:
                        status["nominatim_status"] = "loading"
                except requests.exceptions.RequestException as e:
                    status["nominatim_status"] = "loading"
            else:
                status["nominatim_status"] = "offline"
        except docker.errors.NotFound:
            return {
                "container_status": "unknown",
                "nominatim_status": "unknown",
                "nominatim_log_tail": [],
            }
        return status
