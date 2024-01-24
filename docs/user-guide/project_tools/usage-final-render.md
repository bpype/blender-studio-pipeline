# Final Render
Once the approved image sequences have been loaded into the main edit you are ready to create a final render of your film. 

1. Open your Edit .blend file
2. Render Video as PNG Sequence
	1. Under `Properties>Output` Set the output directory to `your_project_name/shared/editorial/deliver/frames/`
	2. Set the File Format to `PNG`
	3. Select `Render>Render Animation` 
3. Render Audio
	1. Select `Render>Render Audio`
	2. In the Side Panel select Container `.wav`
	3. Set the output directory to `your_project_name/shared/editorial/deliver/audio/`
4. Run Deliver script
	1. Copy the `delivery.py` from `your_project_name/blender-studio-pipeline/film-delivery/` to the directory `your_project_name/shared/editorial/deliver/`
	2. Enter delivery directory `cd /your_project_name/shared/editorial/deliver/ 
	3. Encode audio with `./deliver.py --encode_audio audio/{name_of_audio}.wav`
	4. Encode video with `.deliver.py --encode_video frames/`
	5. Finally `.delivery.py --mux`
5. Final Render will be found in the `mux` directory
