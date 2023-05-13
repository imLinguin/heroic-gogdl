# Handle old games downloading via V1 depot system
# V1 is there since GOG 1.0 days, it has no compression and relies on downloading chunks from big main.bin file
import os 
import logging
from gogdl import constants
from gogdl.dl import dl_utils
from gogdl.dl.objects import v1

manifests_dir = os.path.join(constants.CONFIG_DIR, "manifests")

class Manager:
    def __init__(self, generic_manager):
        self.game_id = generic_manager.game_id
        self.arguments = generic_manager.arguments
        self.unknown_arguments = generic_manager.unknown_arguments
        if "path" in self.arguments:
            self.path = self.arguments.path
        else:
            self.path = ""

        self.api_handler = generic_manager.api_handler
        self.should_append_folder_name = generic_manager.should_append_folder_name

        self.builds = generic_manager.builds
        self.build = generic_manager.target_build
        self.version_name = self.build["version_name"]

        self.lang = self.arguments.lang
        self.dlcs_should_be_downloaded = self.arguments.dlcs
        if self.arguments.dlcs_list:
            self.dlcs_list = self.arguments.dlcs_list.split(",")

        else:
            self.dlcs_list = list()
        
        self.dlc_only = self.arguments.dlc_only

        self.manifest = None
        self.meta = None

        self.logger = logging.getLogger("V1")
        self.logger.info("Initialized V1 Download Manager")

    # Get manifest of selected build
    def get_meta(self):
        meta_url = self.build["link"]
        self.meta, headers = dl_utils.get_zlib_encoded(self.api_handler,meta_url)
        self.version_etag = headers.get("Etag")

        # Append folder name when downloading
        if self.should_append_folder_name:
            self.path = os.path.join(self.path, self.meta["product"]["installDirectory"]) 

    def get_download_size(self):
        self.get_meta()
        dlcs = self.get_dlcs_user_owns(True)
        self.manifest = v1.Manifest(self.meta, self.lang, dlcs, self.api_handler, False)

        download_size, disk_size = self.manifest.calculate_download_size()
        available_branches = set([build["branch"]] for build in self.builds["items"])

        response = {
            "download_size": download_size,
            "disk_size": disk_size,
            "dlcs": dlcs,
            "buildId": self.build["legacy_build_id"],
            "languages": self.manifest.list_languages(),
            "folder_name": self.meta["product"]["installDirectory"],
            "dependencies": self.manifest.dependencies_ids,
            "versionEtag": self.version_etag,
            "versionName": self.version_name,
            "available_branches": list(available_branches)
        }
        return response

