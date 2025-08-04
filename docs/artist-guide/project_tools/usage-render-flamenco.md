# Render Shot with Flamenco
<!--- TODO improve description --->
Once your shots are all ready to go, you can now render a final EXR from each of your shot files.

1. Open your shot `.blend` file by navigating to `Project > Open Shot`.
2. In the properties panel, navigate to Output and set your file format to OpenEXR with Previews enabled.
3. In the properties panel, navigate to Flamenco:
	1. Select `Fetch Job Types`.
	2. From the dropdown, select `Simple Blender Render`.
	3. Set Render Output Directory to `your_project_name/render/`.
	4. Set Add Path Components to `3`.
	5. Finally, select `Submit to Flamenco`.