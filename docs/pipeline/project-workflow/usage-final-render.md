# Final Render

Once the approved image sequences have been loaded into the main edit, you are ready to create a final render of your film.

1. Open your Edit .blend file.
2. Render video as a PNG sequence:
	1. Under `Properties > Output`, set the output directory to `your_project_name/shared/editorial/deliver/frames/`.
	2. Set the file format to `PNG`.
	3. Select `Render > Render Animation`.
3. Render audio:
	1. Select `Render > Render Audio`.
	2. In the side panel, select container `.wav`.
	3. Set the output directory to `your_project_name/shared/editorial/deliver/audio/`.
4. Run the deliver script:
	1. Copy `delivery.py` from `your_project_name/blender-studio-tools/film-delivery/` to the directory `your_project_name/shared/editorial/deliver/`.
	2. Enter the delivery directory: `cd your_project_name/shared/editorial/deliver/`
	3. Encode audio with `./delivery.py --encode_audio audio/{name_of_audio}.wav`
	4. Encode video with `./delivery.py --encode_video frames/`
	5. Finally, run `./delivery.py --mux`
5. The final render will be found in the `mux` directory.
