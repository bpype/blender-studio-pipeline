# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Dict, Tuple, Union, Any, Optional, Set
from pathlib import Path

import bpy
import gpu
import gpu_extras.presets
from mathutils import Matrix

from media_viewer import gpu_opsdata
from media_viewer import opsdata
from media_viewer.log import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)

GP_DRAWER = gpu_opsdata.GPDrawerCustomShader()


class MV_OT_render_review_img_editor(bpy.types.Operator):

    bl_idname = "media_viewer.render_review_img_editor"
    bl_label = "Render Image with Annotations"
    bl_description = (
        "Renders out active image in Image Editor with annotations on top. "
        "Uses custom openGL rendering pipeline. "
        "Saves image in review_output_path with timestamp. "
        "Can render out whole image sequence (in subfolder) or single image only"
    )
    render_sequence: bpy.props.BoolProperty(
        name="Render Sequence",
        description="Controls if entire image sequence should be rendered or only a single image",
        default=True,
    )

    sequence_file_type: bpy.props.EnumProperty(
        name="File Format",
        items=[("IMAGE", "IMAGE", ""), ("MOVIE", "MOVIE", "")],
        default="IMAGE",
        description="Only works when render_sequence is enabled. Controls if output should be a .mp4 or a jpg sequence",
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Check if image editor area available.
        area = opsdata.find_area(context, "IMAGE_EDITOR")
        if not area:
            logger.error("Failed to render image. No Image Editor area available.")
            return {"CANCELLED"}

        # Get active image that is loaded in the image editor.
        image: bpy.types.Image = area.spaces.active.image
        width = int(image.size[0])
        height = int(image.size[1])
        media_filepath = Path(bpy.path.abspath(image.filepath))
        review_output_dir = Path(context.window_manager.media_viewer.review_output_dir)

        # Reading image dimensions is not supported for multilayer EXRs
        # https://developer.blender.org/T53768
        # Workaround:
        # If exr image, and multilayer connect it to the viewer node
        # so we can read the size from bpy.data.images["Viewer Node"]
        # Edit: This workaround does not work because of:
        # https://developer.blender.org/T54314
        # The workaround of the workaround would be to write out the image and then
        # read the resolution of the jpg. This assumes each frame has same dimension.
        if (
            Path(image.filepath).suffix == ".exr"
        ):  # Could also be: image.file_format == "OPEN_EXR"
            if image.type == "MULTILAYER":  # Single layer is: IMAGE
                tmp_res_path: Path = review_output_dir.joinpath("check_resolution.jpg")
                image.save_render(tmp_res_path.as_posix())
                tmp_image = bpy.data.images.load(tmp_res_path.as_posix())

                # Read resolution from 'Viewer Node' image databablock.
                width = int(tmp_image.size[0])
                height = int(tmp_image.size[1])

                # Delete image again.
                bpy.data.images.remove(tmp_image)
                tmp_res_path.unlink(missing_ok=True)

        # Create new image datablack to save our newly composited image
        # (source image + annotation) to.
        new_image = bpy.data.images.new(
            f"{image.name}_annotated", width, height, float_buffer=True
        )
        print(f"Created image datablock: {new_image.name}({width}x{height})")

        file_list = opsdata.get_image_sequence(media_filepath)
        frames = range(context.scene.frame_start, context.scene.frame_end + 1)

        # Process sequence.
        if self.render_sequence:
            # Get an dir with timestamp inside out the review output dir.
            output_dir: Path = opsdata.get_review_output_path(
                review_output_dir, media_filepath, get_sequence_dir_only=True
            )

            # TODO: As soon as patch is submitted that adds these parameters
            # to image.save_render() to fix Could not acquire buffer from image.
            # layer_index = area.spaces.active.image_user.multilayer_layer
            # pass_index = area.spaces.active.image_user.multilayer_pass

            for idx, frame in enumerate(frames):

                # Calling this every frame to update UI results in same picture
                # for all frames?
                # bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)

                # Here we assume that the frame range is the same as in image.
                # This is insured by MV_OT_load_media_image, that makes sure of that.

                # That means we can use the current frame as it represents the
                # actual frame counter in the file.
                frame_counter = frame

                # If frame out of bound left take first frame.
                if frame < frames[0]:
                    frame_counter = frames[0]
                # If frame out of bound right take last frame.
                elif frame > frames[-1]:
                    frame_counter = frames[-1]

                output_path = output_dir.joinpath(f"{file_list[idx].stem}.jpg")
                # print("Loading frame counter: " + str(frame_counter))
                # print(f"{area.spaces.active.image_user.frame_duration}")
                render = self.render_image_editor_in_image_datablock(
                    area, new_image, frame_counter
                )

                # TODO: Error on multilayer exrs: Could not acquire buffer from image.
                render.save_render(output_path.as_posix())
                print(f"Saved image to {output_path.as_posix()}")

            if self.sequence_file_type == "MOVIE":
                # If sequence file type is set to movie execute this operator.
                # This will open a new Blender instance in the background and convert
                # the image sequence to a mp4.
                bpy.ops.media_viewer.convert_image_seq_to_movie(
                    filepath=output_dir.joinpath(f"{file_list[0].stem}.jpg").as_posix()
                )

        # Single image.
        else:
            frame = context.scene.frame_current
            frame_counter = frame
            # Means we have an image sequence loaded but want to render out current frame.
            if len(file_list) > 1:
                # If frame out of bound left take first frame.
                if frame < frames[0]:
                    frame_counter = frames[0]
                # If frame out of bound right take last frame.
                elif frame > frames[-1]:
                    frame_counter = frames[-1]
            # If not part of image sequence take frame 0
            else:
                frame_counter = frame

            # print("Loading frame counter: " + str(frame_counter))
            # print(f"{area.spaces.active.image_user.frame_duration}")
            output_path = opsdata.get_review_output_path(
                review_output_dir, media_filepath
            )
            output_path = output_path.parent.joinpath(f"{output_path.stem}.jpg")
            render = self.render_image_editor_in_image_datablock(
                area, new_image, frame_counter
            )
            render.save_render(output_path.as_posix())
            print(f"Saved image to {output_path.as_posix()}")

        # Free image and return.
        image.gl_free()
        return {"FINISHED"}

    def render_image_editor_in_image_datablock(
        self, area: bpy.types.Area, new_image: bpy.types.Image, frame: int
    ) -> bpy.types.Image:

        global GP_DRAWER

        # Get active image, layer and pass.
        image = area.spaces.active.image
        layer_idx = area.spaces.active.image_user.multilayer_layer
        pass_idx = area.spaces.active.image_user.multilayer_pass
        width = int(new_image.size[0])
        height = int(new_image.size[1])

        # Load image in to an OpenGL texture, will give us image.bindcode that we will later use
        # in gpu_extras.presets.draw_texture_2d()
        # Note: Colors read from the texture will be in scene linear color space
        # Here frame does not refer to timeline frame but to area.spaces.active.image_user.frame_current

        # Call gl.free() first otherwise first rendered out image will always
        # be current frame and not frame= argument.
        image.gl_free()
        image.gl_load(
            frame=frame,
            layer_index=layer_idx,
            pass_index=pass_idx,
        )
        image_gpu_tex = gpu.texture.from_image(image)

        # Create a Buffer on GPU that will be used to first render the image into,
        # then the annotation.

        # We can't user gpu.types.GPUOffscreen() here because the depth is not enough.
        # This leads to banding issues.
        # Instead we create a GPUFramebuffer(). Here we can use a GPUTexture with
        # the format="RGBA16F" which solves most of the banding.
        gpu_texture = gpu.types.GPUTexture((width, height), format="RGBA16F")
        frame_buffer = gpu.types.GPUFrameBuffer(color_slots={"texture": gpu_texture})

        with frame_buffer.bind():

            # Debugging: Flood image with color.
            #frame_buffer.clear(color=(0.0, 0.0, 0.0, 1.0), depth=1.0, stencil=0)

            with gpu.matrix.push_pop():
                # Our drawing is not in the right place, we need to use
                # a projection matrix to transform it.
                # This matrix scales it up twice and centers it (starts out in the top right
                # corner)
                mat = Matrix(
                    (
                        (2.0, 0.0, 0.0, -1.0),
                        (0.0, 2.0, 0.0, -1.0),
                        (0.0, 0.0, 1.0, 0.0),
                        (0.0, 0.0, 0.0, 1.0),
                    )
                )
                gpu.matrix.load_matrix(Matrix.Identity(4))
                gpu.matrix.load_projection_matrix(mat)

                # Draw the texture.
                gpu_extras.presets.draw_texture_2d(image_gpu_tex, (0, 0), 1, 1)

                # Draw grease pencil over it.
                gpu_opsdata.draw_callback(GP_DRAWER, frame=frame)

            buffer = gpu_texture.read()

            # new_image.scale(width, height) does not seem to do a difference?
            # Set new_image.pixels to the composited buffer.
            new_image.pixels = [f_val for row in buffer.to_list() for color in row for f_val in color]

        return new_image


# ---------REGISTER ----------.

classes = [MV_OT_render_review_img_editor]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


# OLDER APPROACHES FOR REFERENCE:
# We get an error from bgl.Buffer() that dimension must be between 1-255
# Question: Can this be solved without having to write out the image like this?
# if Path(image.filepath).suffix == ".exr":
#     old_image = image
#     filepath = "/tmp/convert.png"
#     # TODO: messes up topbar dropdown menu, maybe trigger redraw?
#     bpy.ops.image.save_as(
#         {"area": area}, filepath=filepath, save_as_render=False
#     )

#     print("Exported convert image")
#     image = bpy.data.images.load(filepath, check_existing=False)
#     area.spaces.active.image = old_image
#     area.tag_redraw()  # Does not solve mess up of topbar


# Also taking in to account: The image.gl_load() function
# Colors read from the texture will be in scene linear color space
# --> We need to convert them from lin to srgb
# print(list(buffer))


# # Startupblend contains image node connected to viewer node.
# image_node = context.scene.node_tree.nodes["Image"]
# viewer_node = context.scene.node_tree.nodes["Viewer"]

# # This might reset connection to viewer node.
# print(f"Assigning image({image}) to image node ({image_node})")
# image_node.image = image

# # Connect to image viewer to first output of image node.
# context.scene.node_tree.links.new(
#     viewer_node.inputs["Image"], image_node.outputs.values()[0]
# )
