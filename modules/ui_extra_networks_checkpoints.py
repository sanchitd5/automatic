import html
import json
import os

from modules import shared, ui_extra_networks, sd_models


class ExtraNetworksPageCheckpoints(ui_extra_networks.ExtraNetworksPage):
    def __init__(self):
        super().__init__('Model')

    def refresh(self):
        shared.refresh_checkpoints()

    def list_items(self):
        checkpoint: sd_models.CheckpointInfo
        for name, checkpoint in sd_models.checkpoints_list.items():
            path, _ext = os.path.splitext(checkpoint.filename)
            yield {
                "name": checkpoint.name_for_extra,
                "title": checkpoint.title,
                "filename": path,
                "fullname": checkpoint.filename,
                "hash": checkpoint.shorthash,
                "preview": self.find_preview(path),
                "description": self.find_description(path),
                "info": self.find_info(path),
                "search_term": f'{self.search_terms_from_path(checkpoint.filename)} {(checkpoint.sha256 or "")} /{checkpoint.type}/',
                "onclick": '"' + html.escape(f"""return selectCheckpoint({json.dumps(name)})""") + '"',
                "local_preview": f"{path}.{shared.opts.samples_format}",
                "metadata": checkpoint.metadata,
            }

    def allowed_directories_for_previews(self):
        return [v for v in [shared.opts.ckpt_dir, shared.opts.diffusers_dir, sd_models.model_path] if v is not None]
