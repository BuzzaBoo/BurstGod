import json
import os
import sys
import subprocess
import shutil
import rawpy
from PIL import Image
import numpy as np

debugging = True

def create_output_folder(base_folder):
    output_folder = os.path.join(base_folder, 'output')
    os.makedirs(output_folder, exist_ok=True)
    return output_folder

def create_folder_if_needed(folder_name, base_folder):
    folder_path = os.path.join(base_folder, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def execute_ffmpeg_command(command, filepath, debugging):
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if debugging:
            print(f"FFmpeg output:\n{result.stdout}\n{result.stderr}")
        print(f"Video saved at {filepath}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute FFmpeg command: {e}")
        print(f"FFmpeg error output:\n{e.stderr}")
        return False

def process_frame_size(frame_size_option, render_settings, crop_or_distort, original_dimensions):
    frame_size_option = frame_size_option.lower() # Convert to lowercase for consistency
    if frame_size_option == 'original':
        return original_dimensions
    elif frame_size_option == '3/4':
        return (original_dimensions[0] * 3 // 4, original_dimensions[1] * 3 // 4)
    elif frame_size_option == '1/2':
        return (original_dimensions[0] // 2, original_dimensions[1] // 2)
    elif frame_size_option == '1/4':
        return (original_dimensions[0] // 4, original_dimensions[1] // 4)
    elif frame_size_option == '4k (3840x2160)':
        return (3840, 2160)
    elif frame_size_option == '1080p (1920x1080)':
        return (1920, 1080)
    elif frame_size_option == 'custom':
        width = int(render_settings.get('width', original_dimensions[0]))
        height = int(render_settings.get('height', original_dimensions[1]))
        if crop_or_distort == 'Crop':
            return (width, height)
        elif crop_or_distort == 'Distort':
            return (width, height)
        else:
            raise ValueError(f"Invalid crop_or_distort option: {crop_or_distort}")
    else:
        raise ValueError(f"Invalid frame size option: {frame_size_option}")
    
def delete_existing_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Previous version found and deleted: {file_path}")

def create_video_from_images(shot, shot_list, render_settings, export_base_folder, framerate, frame_length, temp_images_folder, pattern_mode, pattern_mode_pattern, debugging=True):
    quality_level = render_settings['quality']

    print(f"temp images folder is {temp_images_folder}")

    # Use export_base_folder to construct the path for framerate_folder
    framerate_folder = create_folder_if_needed(f'{framerate}fps', export_base_folder)

    crf_value = '35' if quality_level == "low" else '23' if quality_level == 'acceptable' else '15' if quality_level == 'high' else '10' if quality_level == 'excessive' else '0' if quality_level == 'lossless' else '23'
    codec_option = render_settings['codec_option']

    first_image_path = os.path.join(temp_images_folder, f"{shot['shot_number']}_0001.jpeg")
    img = Image.open(first_image_path)
    original_dimensions = img.size
    desired_dimensions = process_frame_size(render_settings['frame_size_option'], render_settings, render_settings['crop_distort'], original_dimensions)

    codec_to_profile = {
        'prores': 'prores_422', # Corrected profile name
        'h264': 'high',
        'hevc': 'main10',
        'dnxhd': 'dnxhr_lb',
        'dvvideo': 'sd',
        'mpeg2video': 'mpeg2video',
        'libaom-av1': 'libaom-av1',
        'libvpx-vp9': 'libvpx-vp9',
        'xdcam': 'xdcam',
        'apch': 'apch',
    }

    profile = codec_to_profile.get(codec_option, 'hq')

    # Adjusted logic for file naming with pattern mode and custom text
    custom_text = render_settings['file_naming_options'].get('custom_text', '')
    filename_parts = []

    def get_shot_key(key):
        value = shot.get(key, '')
        if value is None:
            raise ValueError(f"Key '{key}' is not present in the shot dictionary.")
        return str(value)

    if render_settings['file_naming_options']['Project Title']:
        filename_parts.append(get_shot_key('title'))
    if render_settings['file_naming_options']['Scene']:
        filename_parts.append(get_shot_key('scene'))
    if render_settings['file_naming_options']['Shot']:
        filename_parts.append(get_shot_key('shot'))
    if render_settings['file_naming_options']['Shot Description']:
        filename_parts.append(get_shot_key('description'))
    if render_settings['file_naming_options']['Take']:
        filename_parts.append(get_shot_key('take'))

    if custom_text:
        filename_parts.append(custom_text)

    # Branching based on pattern mode
    print("starting branching based on pattern mode")
    if pattern_mode:
        pattern_string = '_'.join(map(str, pattern_mode_pattern))
        filename_parts.append(f"{framerate}fps_pattern_{pattern_string}")
    else:
        filename_parts.append(f"{framerate}fps_{frame_length}fl")

    filename = '_'.join(filename_parts) + f".{render_settings['output_type']}"

    # Corrected path construction to handle pattern mode and frame_length being None
    if pattern_mode:
        pattern_string = '_'.join(map(str, pattern_mode_pattern))
        frame_length_folder = create_folder_if_needed(f'pattern_{pattern_string}', framerate_folder)
    else:
        if frame_length is None:
            frame_length_folder = framerate_folder # Use framerate_folder directly if frame_length is None
        else:
            frame_length_folder = create_folder_if_needed(f'{frame_length}fl', framerate_folder)

    final_filepath = os.path.join(frame_length_folder, filename)

        # Check if the final file path already exists
    if os.path.exists(final_filepath):
        print(f"Video already exists at {final_filepath}. Skipping creation.")
        return # Skip the rest of the function

    images_pattern = os.path.join(temp_images_folder, f"{shot['shot_number']}_%04d.jpeg")

    command = [
        'ffmpeg',
        '-r', str(framerate),
        '-f', 'image2',
        '-i', images_pattern,
        '-s', f"{desired_dimensions[0]}x{desired_dimensions[1]}",
        '-c:v', codec_option,
        '-crf', crf_value,
        '-preset', 'veryfast',
        final_filepath
    ]

    print(f"FFmpeg command: {' '.join(command)}")
    result = execute_ffmpeg_command(command, final_filepath, debugging)

    if result:
        print(f"Video saved at {final_filepath}")
    else:
        print("FFmpeg command failed. Video not saved.")


def make_videos(shot, shot_list, render_settings, export_base_folder, temp_images_base_folder, global_settings, debugging=True):
    print("Starting make_videos for shot number:", shot['shot_number'])
    base_fps = round(float(render_settings['framerate']))
    real_fps = round(float(shot['real_fps']))
    frame_length = int(render_settings['frame_length'])  # Convert frame_length to integer
    additional_frame_lengths = [int(fl) for fl in render_settings['additional_frame_lengths']]  # Convert additional_frame_lengths to integers
    pattern_mode = render_settings['pattern_mode_var']
    pattern_mode_pattern = [int(val) for val in render_settings.get('pattern_mode_pattern', [])]

    print("Base FPS:", base_fps, "Real FPS:", real_fps, "Frame Length:", frame_length, "Pattern Mode:", pattern_mode,
          "pattern mode pattern:", pattern_mode_pattern)

    # Ensure frame_size_option is correctly set to a recognized value
    frame_size_option = render_settings['frame_size_option'].lower()

    # Ensure pattern_mode_pattern is always a list
    if isinstance(pattern_mode_pattern, int):
        pattern_mode_pattern = [pattern_mode_pattern]

    # First, create temporary images for all original frames (frame length 1)
    temp_images_folder_1fl = os.path.join(temp_images_base_folder, '1fl', str(shot['shot_number']))
    os.makedirs(temp_images_folder_1fl, exist_ok=True)
    original_frames = len(os.listdir(temp_images_folder_1fl))

    for frame_index, frame_path in enumerate(shot['frames'], start=1):
        if frame_path.lower().endswith(('.cr3', '.arw', '.arf', '.nef', '.raf', '.orf', '.raw')):
            with rawpy.imread(frame_path) as raw:
                rgb = raw.postprocess()
            img = Image.fromarray(np.uint8(rgb))
        elif frame_path.lower().endswith(('.jpeg', '.jpg')):
            img = Image.open(frame_path)
        else:
            print(f"Warning: Unsupported image format for frame {frame_index}")
            continue

        temp_jpeg_path = os.path.join(temp_images_folder_1fl, f'{shot["shot_number"]}_{frame_index:04d}.jpeg')
        img.save(temp_jpeg_path, 'JPEG', quality=100)
        print(f"Saved original frame {frame_index} to {temp_jpeg_path}")  # Debugging message


    # Process each frame length or pattern if pattern mode is enabled
    if pattern_mode and pattern_mode_pattern:
        # Join the pattern elements with underscores for the folder name
        pattern_folder_name = '_'.join(map(str, pattern_mode_pattern))
        temp_images_folder = os.path.join(temp_images_base_folder, f'pattern_mode_{pattern_folder_name}',str(shot['shot_number']))
        os.makedirs(temp_images_folder, exist_ok=True)
        print(f"Created folder for pattern mode {pattern_folder_name} at {temp_images_folder}")  # Debugging message

        # Initialize variables for pattern processing
        total_copied = 1
        pattern_index = 0

        # Iterate over the images
        for i, filename in enumerate(os.listdir(temp_images_folder_1fl), start=1):
            if filename.endswith('.jpeg'):
                # Determine the pattern value for the current image
                pattern_value = pattern_mode_pattern[pattern_index % len(pattern_mode_pattern)]

                # Calculate the new sequence number based on the total number of images copied so far
                new_sequence_number = total_copied

                # Construct the new filename
                new_filename = f'{shot["shot_number"]}_{new_sequence_number:04d}.jpeg'

                # Copy the image to the new location with the new filename
                output_file_path = os.path.join(temp_images_folder, new_filename)
                shutil.copy(os.path.join(temp_images_folder_1fl, filename), output_file_path)
                print(f"Copied {filename} to {output_file_path}")

                # Repeat the image according to the pattern value
                for _ in range(pattern_value - 1):
                    total_copied += 1
                    new_filename = f'{shot["shot_number"]}_{total_copied:04d}.jpeg'
                    output_file_path = os.path.join(temp_images_folder, new_filename)
                    shutil.copy(os.path.join(temp_images_folder_1fl, filename), output_file_path)
                    print(f"Repeated {filename} to {output_file_path}")

                # Move to the next pattern value
                pattern_index += 1
                total_copied += 1  # Increment total_copied after processing the current image

    else:
        # Existing logic for non-pattern mode
        for frame_length in [frame_length] + additional_frame_lengths:
            if frame_length > 1:
                # Initialize the duplicate_queue list for this frame_length
                duplicate_queue = []

                temp_images_folder = os.path.join(temp_images_base_folder, f'{frame_length}fl', str(shot['shot_number']))
                os.makedirs(temp_images_folder, exist_ok=True)
                print(f"Created folder for frame length {frame_length} at {temp_images_folder}")  # Debugging message

                # Add each image to the duplicate_queue with its original number and the current frame length
                for i, filename in enumerate(os.listdir(temp_images_folder_1fl), start=1):
                    if filename.endswith('.jpeg'):
                        for j in range(frame_length):
                            # Calculate the new sequence number based on the frame length
                            new_sequence_number = (i - 1) * frame_length + j + 1
                            # Construct the new filename
                            new_filename = f'{shot["shot_number"]}_{new_sequence_number:04d}.jpeg'
                            # Add the entry to the duplicate_queue
                            duplicate_queue.append(
                                (i, os.path.join(temp_images_folder_1fl, filename), new_filename))

                # Process the duplicate_queue to create the images
                for list_number, input_file_location, output_file_name in duplicate_queue:
                    # Copy the image to the new location with the new filename
                    output_file_path = os.path.join(temp_images_folder, output_file_name)
                    shutil.copy(input_file_location, output_file_path)
                    print(f"Copied {input_file_location} to {output_file_path}")  # Debugging message

    # Render videos for pattern mode if enabled
    if pattern_mode and pattern_mode_pattern:
        print("Starting render videos for pattern mode")
        pattern_folder_name = '_'.join(map(str, pattern_mode_pattern))
        temp_images_folder = os.path.join(temp_images_base_folder, f'pattern_mode_{pattern_folder_name}',str(shot['shot_number']))
        # Use the already constructed temp_images_folder for pattern mode
        print(f"Processing framerate {base_fps} and pattern mode {pattern_mode_pattern} with temp images folder: {temp_images_folder}")

        # Run the create_video_from_images command once with the correct parameters
        # For pattern mode, pass None for frame_length since it's not applicable
        create_video_from_images(shot, shot_list, render_settings, export_base_folder, base_fps, None, temp_images_folder, pattern_mode, pattern_mode_pattern, debugging=True)


        # Check if "export_original_rfps" is true in global_settings before rendering videos from temporary images for real_fps
        if global_settings.get("export_original_rfps", False):
            # Render videos from temporary images for real_fps in pattern mode
            print(f"Processing real_fps {real_fps} and pattern mode {pattern_mode_pattern} with temp images folder: {temp_images_folder}")
            create_video_from_images(shot, shot_list, render_settings, export_base_folder, real_fps, None, temp_images_folder, pattern_mode, pattern_mode_pattern, debugging=True)

        # Additional logic to handle additional framerates for pattern mode
        additional_framerates = [int(fl) for fl in render_settings.get('additional_framerates', [])]
        for additional_framerate in additional_framerates:
            print(f"Processing additional framerate {additional_framerate} and pattern mode {pattern_mode_pattern} with temp images folder: {temp_images_folder}")
            create_video_from_images(shot, shot_list, render_settings, export_base_folder, additional_framerate, None, temp_images_folder, pattern_mode, pattern_mode_pattern, debugging=True)

    # Render videos for temp images at base_fps and additional frame rates
    # Process the base frame length first
    else:
        # Now, set base_frame_length to the original frame length after processing varying frame lengths
        base_frame_length = int(render_settings['frame_length'])

        print("Starting render videos for framelengths and framerates")

        # Define all frame lengths to process, including the base frame length and additional frame lengths
        frame_lengths_to_process = [base_frame_length] + additional_frame_lengths

        # Print a message indicating the start of the rendering process
        print("Starting video rendering process...")

        # Iterate over all frame lengths
        for frame_length in frame_lengths_to_process:
            # Print a message indicating the current frame length being processed
            print(f"Processing frame length: {frame_length}...")
            
            # For each frame length, process it at each framerate
            for framerate in [base_fps] + [int(fr) for fr in render_settings['additional_framerates']]:
                # Construct the temp images folder path for the current frame length and framerate
                temp_images_folder = os.path.join(temp_images_base_folder, f'{frame_length}fl', str(shot['shot_number']))
                # Print a message indicating the current framerate being processed for the current frame length
                print(f" Processing framerate: {framerate} with temp images folder: {temp_images_folder}")
                
                # Call the function to create the video from images
                create_video_from_images(shot, shot_list, render_settings, export_base_folder, framerate, frame_length, temp_images_folder, pattern_mode, pattern_mode_pattern, debugging=True)

        # Print a message indicating the completion of the rendering process
        print("Video rendering process completed.")

        print("processing original_rfps if it exists")
        if global_settings.get("export_original_rfps", False):
            # Check if real_fps is greater than 1 before processing
            if real_fps > 1:
                # Render videos from temporary images for real_fps
                # Include the base frame length in the processing
                frame_lengths_to_process = [base_frame_length] + additional_frame_lengths
                for frame_length in frame_lengths_to_process:
                    # Only process real_fps for each frame length
                    temp_images_folder = os.path.join(temp_images_base_folder, f'{frame_length}fl', str(shot['shot_number']))
                    print(f"Processing real_fps {real_fps} and frame length {frame_length} with temp images folder: {temp_images_folder}")
                    # Ensure real_fps is correctly passed here
                    create_video_from_images(shot, shot_list, render_settings, export_base_folder, real_fps, frame_length, temp_images_folder, pattern_mode, pattern_mode_pattern, debugging=True)

        print(f"Render script executed with output folder: {export_base_folder}")

def determine_image_format(frames):
    for frame_path in frames:
        extension = os.path.splitext(frame_path)[1].lower()
        if extension == '.cr3':
            return 'cr3'
        elif extension == '.arw':
            return 'arw'
        elif extension == '.arf':
            return 'arf'
        elif extension == '.nef':
            return 'nef'
        elif extension == '.raf':
            return 'raf'
        elif extension == '.orf':
            return 'orf'
        elif extension == '.raw':
            return 'raw'
        elif extension in ['.jpeg', '.jpg']:
            return 'jpeg'
        elif extension == '.png':
            return 'png'
    # Default to 'cr3' if no recognizable format found
    return 'cr3'

def make_sequences(shot, shot_list, render_settings, export_base_folder, temp_images_base_folder, global_settings, debugging=True):
    print("Starting make_sequences for shot number:", shot['shot_number'])

    # Determine the image sequence input format
    image_sequence_input_format = determine_image_format(shot['frames'])
    print("Image sequence input format:", image_sequence_input_format)

    # Determine the image sequence output format
    image_sequence_format = render_settings.get('image_sequence_format', 'jpeg')  # Default to 'jpeg' if not specified

    # Function to create sequences based on the format
    def create_sequences(folder_path, file_extension):
        # Adjust the sequence folder path to include the image format
        sequence_folder = os.path.join(export_base_folder, image_sequence_format, f"{shot['shot_number']}")
        os.makedirs(sequence_folder, exist_ok=True)
        print(f"Creating {image_sequence_format} sequence for shot {shot['shot_number']} at {sequence_folder}")

        # Construct the filename using scene, shot, take, and description
        filename_base = f"{shot['title']}_{shot['scene']}_{shot['shot']}_{shot['take']}_{shot['description']}"

        # Initialize the sequence number for this shot
        sequence_number = 0

        # Strip the period from the file_extension if it exists
        if file_extension.startswith('.'):
            file_extension = file_extension[1:]

        for i, filename in enumerate(os.listdir(folder_path), start=1):
            if filename.endswith(file_extension):
                # Increment the sequence number for each frame
                formatted_sequence_number = f"C0000_{sequence_number:05d}"
                new_filename = f"{filename_base}_{formatted_sequence_number}.{file_extension}"
                output_file_path = os.path.join(sequence_folder, new_filename)
                shutil.copy(os.path.join(folder_path, filename), output_file_path)
                print(f"Copied {filename} to {output_file_path}")
                # Increment the sequence number for the next frame
                sequence_number += 1

    
    if image_sequence_input_format in ['raw', 'cr3', 'cr2', 'arw', 'arf', 'nef', 'raf', 'orf']:
        if image_sequence_format == 'raw':
            # Make sequences using the image_sequence_input_format type by copying and renaming 
            raw_folder = os.path.join(temp_images_base_folder, 'raw', str(shot['shot_number']))
            os.makedirs(raw_folder, exist_ok=True)
            for frame_index, frame_path in enumerate(shot['frames'], start=1):
                if frame_path.lower().endswith(('.cr3', '.cr2', '.raw', '.arw', '.arf', '.nef', '.raf', '.orf')):
                    raw_filename = f'{shot["shot_number"]}_{shot["take"]}_{frame_index:04d}{os.path.splitext(frame_path)[1]}'
                    raw_path = os.path.join(raw_folder, raw_filename)
                    shutil.copy(frame_path, raw_path)
                    print(f"Copied {frame_path} to {raw_path}")
            # Create RAW sequences
            create_sequences(raw_folder, os.path.splitext(frame_path)[1])
        elif image_sequence_format == 'dng':
            # Convert to DNG
            dng_folder = os.path.join(temp_images_base_folder, 'dng', str(shot['shot_number']))
            os.makedirs(dng_folder, exist_ok=True)
            for frame_index, frame_path in enumerate(shot['frames'], start=1):
                if frame_path.lower().endswith(('.cr3', '.raw', '.arw', '.arf', '.nef', '.raf', '.orf')):
                    dng_filename = f'{shot["shot_number"]}_{shot["take"]}_{frame_index:04d}.DNG'
                    dng_path = os.path.join(dng_folder, dng_filename)
                    command = ['dnglab', 'convert', frame_path, dng_path]
                    subprocess.run(command, check=True)
                    print(f"Converted {frame_path} to {dng_path}")
            # Create DNG sequences
            create_sequences(dng_folder, '.DNG')
        elif image_sequence_format == 'jpeg':
            # Convert to JPEG
            jpeg_folder = os.path.join(temp_images_base_folder, 'jpeg', str(shot['shot_number']))
            os.makedirs(jpeg_folder, exist_ok=True)
            for frame_index, frame_path in enumerate(shot['frames'], start=1):
                if frame_path.lower().endswith(('.cr3', '.raw', '.arw', '.arf', '.nef', '.raf', '.orf')):
                    with rawpy.imread(frame_path) as raw:
                        rgb = raw.postprocess()
                    img = Image.fromarray(np.uint8(rgb))
                    jpeg_filename = f'{shot["shot_number"]}_{shot["take"]}_{frame_index:04d}.jpeg'
                    jpeg_path = os.path.join(jpeg_folder, jpeg_filename)
                    img.save(jpeg_path, 'JPEG', quality=100)
                    print(f"Converted {frame_path} to {jpeg_path}")
            # Create JPEG sequences
            create_sequences(jpeg_folder, '.jpeg')
        else:
            print("Unsupported image sequence format")
            return

    elif image_sequence_input_format == 'jpeg':
        if image_sequence_format in ['raw', 'dng', 'jpeg']:
            # Determine the output folder based on the final output type
            output_folder = 'jpeg' if image_sequence_format == 'jpeg' else image_sequence_format

            # Create the output folder
            jpeg_folder = os.path.join(temp_images_base_folder, output_folder, str(shot['shot_number']))
            os.makedirs(jpeg_folder, exist_ok=True)

            # Iterate over frames and copy JPEG files directly without conversion
            for frame_index, frame_path in enumerate(shot['frames'], start=1):
                if frame_path.lower().endswith('.jpg') or frame_path.lower().endswith('.jpeg'):
                    jpeg_filename = f'{shot["shot_number"]}_{shot["take"]}_{frame_index:04d}.jpeg'
                    jpeg_path = os.path.join(jpeg_folder, jpeg_filename)
                    shutil.copy(frame_path, jpeg_path)
                    print(f"Copied {frame_path} to {jpeg_path}")

            # Create JPEG sequences
            create_sequences(jpeg_folder, '.jpeg')
        else:
            print("Unsupported image sequence format")
            return

    elif image_sequence_input_format == 'png':
        if image_sequence_format == 'png':
            # Create the output folder
            png_folder = os.path.join(temp_images_base_folder, 'png', str(shot['shot_number']))
            os.makedirs(png_folder, exist_ok=True)

            # Iterate over frames and copy PNG files directly without conversion
            for frame_index, frame_path in enumerate(shot['frames'], start=1):
                if frame_path.lower().endswith('.png'):
                    png_filename = f'{shot["shot_number"]}_{shot["take"]}_{frame_index:04d}.png'
                    png_path = os.path.join(png_folder, png_filename)
                    shutil.copy(frame_path, png_path)
                    print(f"Copied {frame_path} to {png_path}")

            # Create PNG sequences
            create_sequences(png_folder, '.png')
        else:
            print("Unsupported image sequence format")
            return
    else:
        print("Unknown input format")

def process_shot(shot, shot_list, render_settings, base_folder, output_folder, temp_images_base_folder, export_base_folder, global_settings, debugging=True):
    if debugging:
        print(f"Processing shot number {shot['shot_number']}")

    try:
        num_frames = int(shot['num_frames'])
    except ValueError:
        print(f"Warning: Shot number {shot['shot_number']} has an invalid number of frames.")
        return  # Skip to the next shot

    if debugging:
        print(f"Number of frames for shot {shot['shot_number']}:", num_frames)

    min_frames_required = render_settings['min_frames']
    if num_frames < min_frames_required:
        print(f"Warning: Shot number {shot['shot_number']} has fewer frames than the minimum required ({min_frames_required}). Skipping to the next shot.")
        return  # Skip to the next shot

    if debugging:
        print(f"Frames for shot {shot['shot_number']}:")
        for frame_index, frame_path in enumerate(shot['frames'], start=1):
            print(f"  Frame {frame_index}: {frame_path}")

    base_fps = round(float(render_settings['framerate']))
    # Check if 'real_fps' is not an empty string and not zero before rounding
    if shot['real_fps'] != '' and shot['real_fps'] != '0':
        real_fps = round(float(shot['real_fps']))
    else:
        # Handle the case where 'real_fps' is an empty string or zero
        # For example, set real_fps to a default value or handle it as needed
        real_fps = 0 # Default value, adjust as necessary


    render_type = render_settings['render_type']

    if render_type == 'render_videos':
        make_videos(shot, shot_list, render_settings, export_base_folder, temp_images_base_folder, global_settings, debugging)
    elif render_type == 'render_image_sequences':
        make_sequences(shot, shot_list, render_settings, export_base_folder, temp_images_base_folder, global_settings, debugging)

    if debugging:
        print(f"Base FPS: {base_fps}, Real FPS: {real_fps}")


def delete_temp_images_folder(temp_images_base_folder):
    if os.path.exists(temp_images_base_folder):
        print(f"Deleting temporary images folder: {temp_images_base_folder}")
        shutil.rmtree(temp_images_base_folder)
    else:
        print(f"Temporary images folder not found: {temp_images_base_folder}")

def main():
    if len(sys.argv) <   2:
        print("Usage: python render.py <output_folder>")
        sys.exit(1)
    
    base_folder = sys.argv[1]
    print(f"Base folder: {base_folder}")

    output_folder = create_output_folder(base_folder)
    if debugging:
        print(f"Output folder for all operations: {output_folder}")

    temp_images_base_folder = os.path.join(output_folder, "temp_images")
    os.makedirs(temp_images_base_folder, exist_ok=True)
    if debugging:
        print(f"temp images base folder: {temp_images_base_folder}")

    render_queue_path = os.path.join(base_folder, 'render_queue.json')
    try:
        with open(render_queue_path, 'r') as f:
            render_queue = json.load(f)
        print(f"Render queue loaded from {render_queue_path}")
    except FileNotFoundError:
        print(f"Error: render_queue.json not found at {render_queue_path}.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: JSON decoding failed for render_queue.json at {render_queue_path}. Please check the contents of the file.")
        sys.exit(1)

    global_settings = render_queue.get('global_settings', {})
    shots_to_render = render_queue.get('shots_to_render', [])

    if not isinstance(global_settings, dict):
        print("Error: 'global_settings' is not a dictionary.")
        sys.exit(1)

    # Add logic to handle duplicate additional framerates and frame lengths
    base_framerate = int(global_settings.get('framerate', 24))
    additional_framerates = set()
    for framerate in global_settings.get('additional_framerates', []):
        framerate = int(framerate)
        if framerate != base_framerate:
            additional_framerates.add(framerate)

    base_frame_length = int(global_settings.get('frame_length', 1))
    additional_frame_lengths = set()
    for frame_length in global_settings.get('additional_frame_lengths', []):
        frame_length = int(frame_length)
        if frame_length != base_frame_length:
            additional_frame_lengths.add(frame_length)

    global_settings['additional_framerates'] = list(additional_framerates)
    global_settings['additional_frame_lengths'] = list(additional_frame_lengths)

    # Print removed framerates and frame lengths and updated lists
    print("Removed additional framerates:", [framerate for framerate in global_settings.get('additional_framerates', []) if framerate == base_framerate])
    print("Updated additional framerates:", global_settings['additional_framerates'])
    print("Removed additional frame lengths:", [frame_length for frame_length in global_settings.get('additional_frame_lengths', []) if frame_length == base_frame_length])
    print("Updated additional frame lengths:", global_settings['additional_frame_lengths'])

    # Remove additional framerates and frame lengths if they are the same as the base ones
    if base_framerate in additional_framerates:
        additional_framerates.remove(base_framerate)
    if base_frame_length in additional_frame_lengths:
        additional_frame_lengths.remove(base_frame_length)

    render_type = global_settings.get('render_type')
    if render_type == 'render_videos':
        export_folder_type = 'rendered_videos'
    elif render_type == 'render_image_sequences':
        export_folder_type = 'image_sequences'
    else:
        raise ValueError(f"Invalid render type: {render_type}")

    export_base_folder = os.path.join(output_folder, export_folder_type)
    os.makedirs(export_base_folder, exist_ok=True)

    shot_list_path = os.path.join(base_folder, 'shot_list.json')
    print("checking for duplicate shots")
    try:
        with open(shot_list_path, 'r') as f:
            shot_list = json.load(f)
        print(f"Loaded shot list from {shot_list_path}")
    except FileNotFoundError:
        print(f"Error: shot_list.json not found at {shot_list_path}.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: JSON decoding failed for shot_list.json at {shot_list_path}. Please check the contents of the file.")
        sys.exit(1)

    # New code to handle duplicate shots
    shot_counts = {}
    for shot in shot_list:
        shot_id = (shot['scene'], shot['shot'], shot['take'])
        if shot_id in shot_counts:
            shot_counts[shot_id] += 1
            shot['take'] = f"{shot['take']}_{shot_counts[shot_id]}"
        else:
            shot_counts[shot_id] = 1

    # Save the updated shot list back to the file
    with open(shot_list_path, 'w') as f:
        json.dump(shot_list, f, indent=4)
    print(f"Updated shot list saved to {shot_list_path}")

    if isinstance(shots_to_render, list):
        for shot_number in shots_to_render:
            shot = next((s for s in shot_list if s['shot_number'] == shot_number), None)
            if shot:
                print(f"Processing shot number {shot_number} from shot_list.json")
                process_shot(shot, shot_list, global_settings, base_folder, output_folder, temp_images_base_folder, export_base_folder, global_settings, debugging=True)
            else:
                print(f"Warning: Shot number {shot_number} not found in shot list.")
    else:
        print("Error: 'shots_to_render' is not a list.")
        sys.exit(1)

    end_temp_delete = True
    if end_temp_delete == True:
        delete_temp_images_folder(temp_images_base_folder)

    else:
        print("Script finished")

if __name__ == "__main__":
    main()