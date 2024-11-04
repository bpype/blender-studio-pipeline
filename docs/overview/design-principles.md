# Design Principles
Following Blender's mission, Blender Studio pursues creative content creation and knowledge sharing. For this reason, the entire production pipeline is built around free and open source software. When it comes to the final visual content (rendered frames), the only software used is Blender.

The pipeline and workflows are designed to facilitate a small production unit (10-20 people) so that artists can create and deliver content as quickly and seamlessly as possible.

## Editorial-centric workflow
We follow the principle that the editorial (and previz) process is the reference point during all stages of production. By continuosily referencing the edit of our production, we keep track of changes to the
assets and shots lists, and can effectively communicate task updates to artists working on the show.

## Blender-centric pipeline
Only use add-ons that are workflow/process specific and that won't be beneficial to a wide audience if included in Blender.
Any other feature required to deliver a production should be considered a development target, and designed, reviewed and planned as part of the blender.org public development activities.

## Review and Approve
Make use of a centralized review and approval platform, which enables tasks to be tracked. Provide access to the platform via the web, and within Blender as well.

## Version Control
Use a version control system (currently Subversion). Do not manually version working files. Incrementally version generated

## No Caching
When working on Blender-centric pipeline, we rely on Blender's linking system, limit the usage of caching as much as possible. While caches can provide performance and reliability improvements when working in complex scenarios, they also have downsides (storage, data sync, etc.). We consider the tradeoff not worth in our case.
