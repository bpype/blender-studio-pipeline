from blender_kitsu.shot_builder.shot import Shot
from blender_kitsu.shot_builder.project import Production


class ProductionShot(Shot):
    def get_anim_file_path(self, production: Production, shot: Shot) -> str:
        """Get the animation file path for this given shot."""
        return self.file_path_format.format_map(
            {'production': production, 'shot': shot, 'task_type': "anim"}
        )

    def get_lighting_file_path(self, production: Production, shot: Shot) -> str:
        """Get the lighting file path for this given shot."""
        return self.file_path_format.format_map(
            {'production': production, 'shot': shot, 'task_type': "lighting"}
        )

    def get_output_collection_name(self, shot: Shot, task_type: str) -> str:
        """Get the collection name where the output is stored."""
        return f"{shot.name}.{task_type}.output"

    def is_valid(self) -> bool:
        """Check if this shot contains all data, so it could be selected
        for shot building.
        """
        if not super().is_valid():
            return False
        return True

    # Assuming path to file is in `project_name/svn/pro/shot/sequence_name/shot_name`
    # Render Ouput path should be `project_name/shared/shot_frames/sequence_name/shot_name/`

    def get_render_output_dir(self) -> str:
        return f"//../../../../../shared/shot_frames/{self.sequence_code}/{self.name}/{self.name}.lighting"

    def get_comp_output_dir(self) -> str:
        return f"//../../../../../shared/shot_frames/{self.sequence_code}/{self.name}/{self.name}.comp"


class GenericShot(ProductionShot):
    is_generic = True
