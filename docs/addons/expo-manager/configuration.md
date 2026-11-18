# Project Configuration

Expo Manager reads project settings from `{project_root}/.blender_project/expo_config.toml`. These settings define how your project interprets Kitsu data, where files are stored, and which optional project behaviors are enabled. All paths are relative to the project's root.

:::warning
Project administrators should maintain this file: invalid settings can prevent the project session from starting or cause operations to fail.
:::

## Sample Files
**Sample Configuration Files for [film](https://projects.blender.org/studio/expo-manager/src/branch/main/tests/test_configs/expo_config.toml) and [TV](https://projects.blender.org/studio/expo-manager/src/branch/main/tests/test_configs/expo_config_tv.toml) projects are provided.**

## Configuration Values

These values belong at the top level of the TOML file, before any section headings.

| Value | Purpose |
| --- | --- |
| `kitsu_server` | URL of the Kitsu server, required to [start a project session](introduction.md#setting-add-on-preferences). |
| `kitsu_project_id` | ID of the production on Kitsu, required to [start a project session](introduction.md#setting-add-on-preferences). Find it in the production's URL after `/productions/`. |
| `3d_start` | Default start frame for shot files. Each Shot's start frame is tracked on the Kitsu server; update it with [Push Frame Range](shot.md#frame-range). |
| `version_backups` | Enables disk [backups](backups.md) when publishing and exposes the manual backup panel. |
| `convention_required` | Require all [convention checks](conventions.md) to pass before publishing. |
| `farm_job_type` | Flamenco job type used when [submitting a farm job](shot.md#submit-farm-job). Set this to a job type available on your Flamenco server. |

## Naming

The `[naming]` section controls how entity names are used in generated paths and some Blender data names.

| Value | Purpose |
| --- | --- |
| `delimiter` | Value substituted for the `{delimiter}` token in patterns used by the [File Builder](file_builder.md). Defaults to `-`. |
| `space_replacer` | Replaces spaces in entity names used by the [File Builder](file_builder.md); also supplies the `{space}` token. Defaults to `_`. |
| `lowercase_entities` | Converts entity names to lowercase when generating paths and supported data names; see [Context](context.md). Defaults to `false`. |

## File Patterns

The `[patterns.Shot]`, `[patterns.Sequence]`, `[patterns.Asset]`, and `[patterns.Edit]` sections define work-file and publish locations for each entity type. Expo also uses work-file patterns to [detect the file's context](context.md). Define the sections needed by your production; each defined section requires `dir`, `file`, `publish_dir`, and `publish_file`. Shot rendering also needs `publish_frames`.

| Value | Purpose |
| --- | --- |
| `dir` | Directory containing the entity's working `.blend` file, used by the [File Builder](file_builder.md). |
| `file` | Filename of the working `.blend` file, used by the [File Builder](file_builder.md). |
| `publish_dir` | Directory for [published Shot previews](shot.md#publishing) or [Edit exports](edit.md#export-publish). |
| `publish_file` | Filename for a [published Shot preview](shot.md#publishing) or [Edit export](edit.md#export-publish). |
| `publish_frames` | Directory for a Shot Task's [rendered image sequence](shot.md#publish-preview-publish-render), used by [Render Review](render-review.md). |

### Pattern Tokens

Use the tokens available for each entity in its patterns. Shot and Sequence work files are Task-specific; Asset and Edit work files are not. Publish patterns can additionally use `{task_type}` and `{version}`.

| Section | Entity tokens |
| --- | --- |
| `patterns.Shot` | [Shot](shot.md) patterns can use `{sequence}`, `{shot}`, `{task_type}`, and `{episode}`. |
| `patterns.Sequence` | [Sequence](file_builder.md#sequence-building) patterns can use `{sequence}`, `{task_type}`, and `{episode}`. |
| `patterns.Asset` | [Asset](asset.md) patterns can use `{asset}` and `{asset_type}`. |
| `patterns.Edit` | [Edit](edit.md) patterns can use `{edit}` and `{episode}`. |

`{episode}` is intended for TV projects. The `{delimiter}` and `{space}` tokens use the values from `[naming]`. Context detection needs the work-file path to identify its entity: include the relevant entity tokens, including `{edit}` for Edit files and `{task_type}` for Task-specific files. Tokens must be available to the entity and operation that resolves the pattern.

## Shared Paths

The `[paths]` section defines locations used by individual features, relative to the project root.

| Value | Purpose |
| --- | --- |
| `farm_output` | Root directory for [Submit Farm Job](shot.md#submit-farm-job) output; [Render Review](render-review.md) will search this output to find jobs to approve. |
| `hooks_file` | Python file containing production-specific [shot-building hooks](file_builder.md#shot-building). |
| `conventions_file` | Python file containing the project's [convention checks](conventions.md) and optional fixes. |
| `templates_dir` | Directory containing custom templates for [new files](file_builder.md) and the optional [Render Review template](render-review.md#new-render-review-session). |

## Shot Builder

The `[shot_builder]` section and its subsections control shot assembly. For Task-specific settings, use the Task Type short names configured on Kitsu, or the full name when a short name is not set. Match the names' capitalization.

| Value | Purpose |
| --- | --- |
| `frame_range_sync` | Enables the [Frame Range panel](shot.md#frame-range) and checks Shot timing when files are opened. Defaults to `true`. |
| `link_camera_rig_task_types` | List of Shot Task Types for which the [builder](file_builder.md#shot-building) looks for a camera and creates one if needed. |
| `camera_name` | Name of the camera the [builder](file_builder.md#shot-building) looks for in the Shot's output collection when camera setup is enabled. |
| `action_name` | Naming pattern for actions created on armatures in overridden assets during [shot building](file_builder.md#shot-building). Supports `{shot}`, `{asset}`, `{delimiter}`, and `{space}`. |
| `output_col_create` | Maps Task Types to booleans indicating whether the builder creates an [output collection](shot.md#output-collection). |
| `output_col_link_mapping` | Maps each Task Type to a list of upstream Task Type short names whose [output collections](shot.md#output-collection) should be linked into its Shot file. |
| `load_editorial_ref` | Maps Task Types to booleans indicating whether the builder loads the latest [editorial reference](shot.md#editorial-reference). |
| `asset_type_to_override` | Maps Asset Type names to booleans indicating whether [shot building](file_builder.md#shot-building) should link cast Assets with library overrides. The builder looks up the part of the [registered collection name](asset.md#set-asset-collection) before its first hyphen; the configuration keys are also validated against Kitsu Asset Types. |

For details on which settings can be left empty and how that affects assembly, see [Shot Building](file_builder.md#shot-building).
