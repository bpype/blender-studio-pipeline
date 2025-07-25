# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import typing

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

APPROVED_COLOR = (0.24, 1, 0.139, 0.7)
PUSHED_TO_EDIT_COLOR = (0.8, .8, 0.1, 0.5)


Float2 = typing.Tuple[float, float]
Float3 = typing.Tuple[float, float, float]
Float4 = typing.Tuple[float, float, float, float]
LINE_WIDTH = 6


class LineDrawer:

    def draw(self, coords: typing.List[Float2], colors: typing.List[Float4]):
        line_shader = gpu.shader.from_builtin('FLAT_COLOR')
        global LINE_WIDTH

        if not coords:
            return
        gpu.state.blend_set("ALPHA")
        gpu.state.line_width_set(LINE_WIDTH)

        batch = batch_for_shader(
            line_shader, 'LINES',
            {"pos": coords, "color": colors}
        )
        batch.draw(line_shader)

def get_strip_rectf(strip) -> Float4:
    # Get x and y in terms of the grid's frames and channels.
    x1 = strip.frame_final_start
    x2 = strip.frame_final_end
    # Seems to be a 5 % offset from channel top start of strip.
    y1 = strip.channel + 0.05
    y2 = strip.channel - 0.05 + 1

    return x1, y1, x2, y2


def line_in_strip(
    strip_coords: Float4,
    pixel_size_x: float,
    color: Float4,
    line_height_factor: float,
    out_coords: typing.List[Float2],
    out_colors: typing.List[Float4],
):
    # Strip coords.
    s_x1, s_y1, s_x2, s_y2 = strip_coords

    # Calculate line height with factor.
    line_y = (1 - line_height_factor) * s_y1 + line_height_factor * s_y2

    # if strip is shorter than line_width use stips s_x2
    # line_x2 = s_x1 + line_width if (s_x2 - s_x1 > line_width) else s_x2
    line_x2 = s_x2

    # Be careful not to draw over the current frame line.
    cf_x = bpy.context.scene.frame_current_final

    # TODO(Sybren): figure out how to pass one colour per line,
    # instead of one colour per vertex.
    out_coords.append((s_x1, line_y))
    out_colors.append(color)

    if s_x1 < cf_x < line_x2:
        # Bad luck, the line passes our strip, so draw two lines.
        out_coords.append((cf_x - pixel_size_x, line_y))
        out_colors.append(color)

        out_coords.append((cf_x + pixel_size_x, line_y))
        out_colors.append(color)

    out_coords.append((line_x2, line_y))
    out_colors.append(color)


def draw_callback_px(line_drawer: LineDrawer):
    global LINE_WIDTH

    context = bpy.context

    if not context.scene.sequence_editor:
        return

    # From . import shown_strips.

    region = context.region
    xwin1, ywin1 = region.view2d.region_to_view(0, 0)
    xwin2, ywin2 = region.view2d.region_to_view(region.width, region.height)
    one_pixel_further_x, one_pixel_further_y = region.view2d.region_to_view(1, 1)
    pixel_size_x = one_pixel_further_x - xwin1

    # Strips = shown_strips(context).
    strips = context.scene.sequence_editor.sequences_all

    coords = []  # type: typing.List[Float2]
    colors = []  # type: typing.List[Float4]

    # Collect all the lines (vertex coords + vertex colours) to draw.
    for strip in strips:

        # Get corners (x1, y1), (x2, y2) of the strip rectangle in px region coords.
        strip_coords = get_strip_rectf(strip)

        # Check if any of the coordinates are out of bounds.
        if (
            strip_coords[0] > xwin2
            or strip_coords[2] < xwin1
            or strip_coords[1] > ywin2
            or strip_coords[3] < ywin1
        ):
            continue

        if strip.rr.is_approved:
            line_in_strip(
                strip_coords,
                pixel_size_x,
                APPROVED_COLOR,
                0.05,
                coords,
                colors,
            )
        elif strip.rr.is_pushed_to_edit:
            line_in_strip(
                strip_coords,
                pixel_size_x,
                PUSHED_TO_EDIT_COLOR,
                0.05,
                coords,
                colors,
            )

    line_drawer.draw(coords, colors)


def tag_redraw_all_sequencer_editors():
    context = bpy.context

    # Py cant access notifiers.
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "SEQUENCE_EDITOR":
                for region in area.regions:
                    if region.type == "WINDOW":
                        region.tag_redraw()


# This is a list so it can be changed instead of set
# if it is only changed, it does not have to be declared as a global everywhere
cb_handle = []


def callback_enable():
    global cb_handle

    if cb_handle:
        return

    # Doing GPU stuff in the background crashes Blender, so let's not.
    if bpy.app.background:
        return

    line_drawer = LineDrawer()
    cb_handle[:] = (
        bpy.types.SpaceSequenceEditor.draw_handler_add(
            draw_callback_px, (line_drawer,), "WINDOW", "POST_VIEW"
        ),
    )

    tag_redraw_all_sequencer_editors()


def callback_disable():
    global cb_handle

    if not cb_handle:
        return

    try:
        bpy.types.SpaceSequenceEditor.draw_handler_remove(cb_handle[0], "WINDOW")
    except ValueError:
        # Thrown when already removed.
        pass
    cb_handle.clear()

    tag_redraw_all_sequencer_editors()


# ---------REGISTER ----------.


def register():
    callback_enable()


def unregister():
    callback_disable()
