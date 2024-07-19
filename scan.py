import os
import glob
import cv2
import json
import sys
import tempfile
from shutil import copyfile
from shutil import rmtree
from qreader import QReader
import rawpy

# Global variable to control whether to keep temporary files
KEEP_TEMP_FILES = False

def scan_images(input_folder, output_folder):
    if not os.path.isdir(input_folder):
        raise ValueError("Please provide a valid input folder location.")
    if not os.path.isdir(output_folder):
        raise ValueError("Please provide a valid output folder location.")

    json_file_path = os.path.join(output_folder, 'shot_list.json')

    # Clear the JSON file before starting the scan
    with open(json_file_path, 'w') as f:
        json.dump([], f, indent=4)
    print(f"JSON file '{json_file_path}' has been cleared.")

    shot_list = []
    current_shot = None
    shot_number = 1  # Initialize shot number

    # Generate a list of subfolders recursively
    subfolders = []
    for folder_path, _, _ in os.walk(input_folder):
        if not any(excluded_word in folder_path for excluded_word in ['temp', 'output', 'thumbnail']):
            subfolders.append(folder_path)

    # Check if the input folder is already in the list of subfolders
    if input_folder not in subfolders:
        subfolders.append(input_folder)

    # Loop through subfolders and scan images
    for subfolder in subfolders:
        print(f"Scanning images in folder: {subfolder}")

        # Initialize image_files list for each subfolder
        image_files = []

        # Calculate image files within the subfolder
        image_files.extend(sorted(glob.glob(os.path.join(subfolder, "*.cr3"))))
        image_files.extend(sorted(glob.glob(os.path.join(subfolder, "*.jpeg"))))
        image_files.extend(sorted(glob.glob(os.path.join(subfolder, "*.jpg"))))
        image_files.extend(sorted(glob.glob(os.path.join(subfolder, "*.png"))))
        image_files.extend(sorted(glob.glob(os.path.join(subfolder, "*.gif"))))
        image_files.extend(sorted(glob.glob(os.path.join(subfolder, "*.cr2"))))
        image_files.extend(sorted(glob.glob(os.path.join(subfolder, "*.nef"))))
        image_files.extend(sorted(glob.glob(os.path.join(subfolder, "*.arw"))))
        image_files.extend(sorted(glob.glob(os.path.join(subfolder, "*.raf"))))
        image_files.extend(sorted(glob.glob(os.path.join(subfolder, "*.orf"))))
        image_files.extend(sorted(glob.glob(os.path.join(subfolder, "*.raw"))))

        # Normalize all image file paths
        image_files = [os.path.normpath(file_path) for file_path in image_files]

        total_images = len(image_files)
        print(f"Starting scan of {total_images} images in folder: {subfolder}")

        # Skip processing if there are not enough frames
        if total_images < 1:
            print(f"Skipping folder {subfolder} as it contains no images.")
            continue
        elif total_images < 2:
            print(f"Skipping folder {subfolder} as it contains less than 2 images.")
            continue

        print(f"Starting scan of {total_images} images.")

        # Create a QReader instance
        qreader = QReader()

        # Create a temporary directory for processed images
        temp_folder = os.path.join(output_folder, 'temp_jpgs')
        os.makedirs(temp_folder, exist_ok=True)

        # Create a directory for thumbnails
        thumbnail_folder = os.path.join(output_folder, 'thumbnails')
        os.makedirs(thumbnail_folder, exist_ok=True)

        # Initialize no_qr_code_sequence as True before the loop starts
        no_qr_code_sequence = True

        for index, image_file in enumerate(image_files, start=1):
            print(f"\nProcessing image {index} out of {total_images}: {image_file}")

            try:
                # Convert raw images to JPEG and copy to temporary folder
                if image_file.lower().endswith(('.cr2', '.cr3', '.nef', '.arw', '.raf', '.orf', '.raw')):
                    temp_image_file = os.path.join(temp_folder, f"{index}.jpeg")
                    convert_raw_to_jpeg(image_file, temp_image_file)
                    print(f"Raw image converted to JPEG: {temp_image_file}")
                else:
                    temp_image_file = image_file

                # Read the image
                img = cv2.imread(temp_image_file, cv2.IMREAD_UNCHANGED)
                if img is None:
                    print(f"Error reading image {temp_image_file}. Skipping.")
                    continue

                # Resize image to 1% of its original size
                img = cv2.resize(img, (int(img.shape[1] * 0.1), int(img.shape[0] * 0.1)))
                print("Image resized.")

                # Convert the image to RGB color space
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                print("Image converted to RGB.")

                # Use the detect_and_decode function to get the decoded QR data
                decoded_text = qreader.detect_and_decode(image=img_rgb)

                # Process the decoded QR code
                if decoded_text:
                    for text in decoded_text:
                        if text is not None:
                            print(f"Decoded QR code data from {image_file}: {text}")
                            title, scene, shot, take, description = parse_qr_data(text)

                            # Start a new shot for each QR code
                            current_shot = {
                                'shot_number': shot_number,  # Assign shot number
                                'qr_start_marker': os.path.normpath(image_file),
                                'num_frames': 0,
                                'shot_start': '',
                                'shot_end': '',
                                'title': title,
                                'scene': scene,
                                'shot': shot,
                                'take': take,
                                'description': description,
                                'frames': [],
                                'start_frame': '',
                                'thumbnail': '',
                                'real_fps': '',  # Corrected key name
                            }

                            shot_number += 1

                            shot_list.append(current_shot)
                            print(f"Shot {shot_number} started.")

                            # Update no_qr_code_sequence to False since a QR code was found
                            no_qr_code_sequence = False
                else:
                    print(f"No QR codes found in {image_file}.")
                    if current_shot:
                        current_shot['frames'].append(image_file)
                        current_shot['num_frames'] += 1
                        print(f"Added frame to current shot: {image_file}")
                    else:
                        print(f"Warning: Image {index} does not contain a QR code and no current shot is active.")
            except Exception as e:
                print(f"Error processing image {index}: {str(e)}")

            percent_completed = (index / total_images) * 100
            print(f"Task progress: {percent_completed:.2f}%")

        if current_shot:
            current_shot['num_frames'] = len(current_shot['frames'])
            current_shot['shot_end'] = image_files[-1] if index == total_images else image_files[index - 1]

        # Create a shot from all photos in the folder if no QR code shots were found
        if no_qr_code_sequence:
            print("No QR code shots found. Creating a shot from all the photos in the folder.")
            new_shot = {
                'shot_number': shot_number,
                'qr_start_marker': image_files[0],
                'num_frames': total_images,
                'shot_start': image_files[0],
                'shot_end': image_files[-1],
                'title': 'No',
                'scene': 'QR',
                'shot': 'Codes',
                'take': 1,
                'description': 'Found',
                'frames': image_files,
                'start_frame': '',
                'thumbnail': '',
                'real_fps': 0,  # Set real_fps to 0 for no QR code sequence
            }

            shot_number += 1
            shot_list.append(new_shot)
            print("Shot created from all folder images.")
            print(f"{new_shot}")

        # Write the final shot list to the JSON file
        with open(json_file_path, 'w') as f:
            json.dump(shot_list, f, indent=4)
        print("Json shot list created successfully.")

        # Post-process the shot list to remove shots with zero frames
        print("removing shots with 0 frames")
        shot_list = [shot for shot in shot_list if shot['num_frames'] > 0]

        # Renumber shot numbers
        print("Renumbering shot list based on null shot deletion")
        for i, shot in enumerate(shot_list, start=1):
            shot['shot_number'] = i

        # Write the final shot list to the JSON file
        with open(json_file_path, 'w') as f:
            json.dump(shot_list, f, indent=4)
        print("Final JSON shot list created successfully.")

        # Calculate shot start and end for each shot
        print("calculating start and end")
        for i in range(len(shot_list)):
            print(f"\nProcessing shot {i + 1}")
            print(f"qr_start_marker: {shot_list[i]['qr_start_marker']}")

            # Normalize the qr_start_marker path for comparison
            print("normalizing the qr start marker path")
            normalized_qr_start_marker = os.path.normpath(shot_list[i]['qr_start_marker'])
            print(f" normalized qr start marker: {normalized_qr_start_marker}")
            print(f"image_files list: {image_files}")

            # Check if the normalized qr_start_marker is in the image_files list
            print("checking if normalized qr start marker is in the images_file list")
            if normalized_qr_start_marker not in image_files:
                print(f"Error: qr_start_marker '{normalized_qr_start_marker}' not found in image_files list.")
                continue  # Skip this shot if the qr_start_marker is not found

            # Find the index of the normalized path in the image_files list
            qr_start_index = image_files.index(normalized_qr_start_marker)

            # Skip calculation if qr_start_marker already matches shot_start
            if shot_list[i]['qr_start_marker'] == shot_list[i]['shot_start']:
                print("Skipping calculation as qr_start_marker already matches shot_start.")
                continue

            # Set shot_start to the next image in the folder after the QR code
            shot_list[i]['shot_start'] = image_files[min(qr_start_index + 1, len(image_files) - 1)]

            # Calculate shot_end based on shot_start and num_frames
            if shot_list[i]['num_frames'] > 0:
                start_frame_index = image_files.index(shot_list[i]['shot_start'])
                end_frame_index = start_frame_index + shot_list[i]['num_frames'] - 1
                shot_list[i]['shot_end'] = image_files[min(end_frame_index, len(image_files) - 1)]
                print(f"Shot end set to: {shot_list[i]['shot_end']}")

            print(f"num_frames: {shot_list[i]['num_frames']}")
            print(f"frames: {shot_list[i]['frames']}")

        # Delete the temporary folder if KEEP_TEMP_FILES is False
        if not KEEP_TEMP_FILES:
            rmtree(os.path.join(output_folder, 'temp_jpgs'))
            print(f"Temporary folder '{temp_folder}' has been deleted.")


    # Function to convert images to JPEG
    def convert_to_jpeg(source_file, destination_file):
        try:
            # Check if the source file is a RAW image
            if source_file.lower().endswith(('.cr2', '.cr3', '.nef', '.arw', '.raf', '.orf', '.raw')):
                # Convert RAW image to JPEG
                with rawpy.imread(source_file) as raw:
                    rgb = raw.postprocess()
                    cv2.imwrite(destination_file, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
            else:
                # Read the image
                img = cv2.imread(source_file, cv2.IMREAD_UNCHANGED)
                if img is None:
                    raise Exception("Error reading image.")
                # Write the image as JPEG
                cv2.imwrite(destination_file, img)
        except Exception as e:
            raise Exception(f"Error converting image to JPEG: {str(e)}")

    # Generate thumbnail for the first image of each shot (using shot start image)
    for shot in shot_list:
        if shot['frames']:
            original_filename = os.path.basename(shot['qr_start_marker'])
            thumbnail_filename = f"{original_filename}_thumbnail.jpg"
            thumbnail_path = os.path.join(thumbnail_folder, thumbnail_filename)

            try:
                # Check if the shot start image is already in a suitable format (JPEG or PNG)
                if any(shot['shot_start'].lower().endswith(fmt) for fmt in ['.jpeg', '.jpg', '.png']):
                    temp_shot_start = shot['shot_start']
                else:
                    # Convert shot start image (raw format) to JPEG
                    temp_shot_start = os.path.join(temp_folder, f"{original_filename}_shot_start.jpeg")
                    convert_raw_to_jpeg(shot['shot_start'], temp_shot_start)
                    print(f"Raw shot start image converted to JPEG for thumbnail: {temp_shot_start}")

                # Read the original shot start image for aspect ratio
                original_img = cv2.imread(temp_shot_start, cv2.IMREAD_UNCHANGED)
                original_height, original_width = original_img.shape[:2]

                # Resize the original shot start image for the thumbnail (maintaining aspect ratio)
                max_thumbnail_size = 100 # Adjust the maximum size as needed
                aspect_ratio = original_width / original_height
                if aspect_ratio > 1: # Landscape orientation
                    thumbnail_width = max_thumbnail_size
                    thumbnail_height = int(max_thumbnail_size / aspect_ratio)
                else: # Portrait or square orientation
                    thumbnail_width = int(max_thumbnail_size * aspect_ratio)
                    thumbnail_height = max_thumbnail_size

                thumbnail_img = cv2.resize(original_img, (thumbnail_width, thumbnail_height))

                # Save the thumbnail
                cv2.imwrite(thumbnail_path, thumbnail_img)
                shot['thumbnail'] = thumbnail_path
                print(f"Thumbnail generated for shot {shot['shot_number']}: {thumbnail_path}")

                # Calculate real FPS for each shot
                print("calculating real fps for each shot")
                if len(shot['frames']) >= 2 and (shot['real_fps']) != 0: # Exclude calculation for no QR code sequences
                    real_fps = calculate_real_fps(shot) # Capture the returned FPS
                    rounded_real_fps = round(real_fps, 2)
                    if real_fps is not None:
                        shot['real_fps'] = rounded_real_fps # Update the shot dictionary with the returned FPS
                        print(f"Real FPS for shot {shot['shot_number']} saved: {real_fps}")
                    else:
                        print("Real FPS calculation failed or returned None.")
                else:
                    print("The if statement failed due to insufficient frames or no QR code sequence.")

            except Exception as e:
                print(f"Error generating thumbnail for shot {shot['shot_number']}: {str(e)}")

    # Update the JSON file with thumbnail and real_fps information
    with open(json_file_path, 'w') as f:
        json.dump(shot_list, f, indent=4)
        print("JSON file updated with thumbnail and real_fps information.")



# Function to parse QR data
def parse_qr_data(qr_data):
    parts = qr_data.split('-')

    title = parts[0] if len(parts) >= 1 else None
    scene = parts[1] if len(parts) >= 2 else None
    shot = parts[2] if len(parts) >= 3 else None
    take = int(parts[3]) if len(parts) >= 4 else None
    description = '-'.join(parts[4:]) if len(parts) > 4 else None

    return title, scene, shot, take, description

# Function to convert raw images to JPEG
def convert_raw_to_jpeg(source_file, destination_file):
    # This function uses rawpy to convert raw images to JPEG
    # You may need to install rawpy if it's not already installed
    print(f"Source file: {source_file}")
    with rawpy.imread(source_file) as raw:
        rgb = raw.postprocess()
        cv2.imwrite(destination_file, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))

# Function to calculate real fps for a shot
def calculate_real_fps(shot):
    print("Starting real FPS calculation, examining data")
    if len(shot['frames']) < 2:
        print(f"Cannot calculate real FPS for shot {shot['shot_number']}: Insufficient frames.")
        return None

    first_frame_time = os.path.getctime(shot['frames'][0])
    last_frame_time = os.path.getctime(shot['frames'][-1])

    print("Calculating real FPS")
    time_difference = last_frame_time - first_frame_time
    num_frames = len(shot['frames'])

    if time_difference == 0:
        print(f"Error calculating real FPS for shot {shot['shot_number']}: Time difference is zero.")
        return None

    real_fps = num_frames / time_difference
    print(f"Real FPS for shot {shot['shot_number']}: {real_fps}")

    # Update the shot dictionary with real_fps
    shot['real_fps'] = real_fps

    return real_fps

if __name__ == "__main__":
    # Check if the correct number of command-line arguments is provided
    if len(sys.argv) != 3:
        print("Usage: python script.py input_folder output_folder")
        sys.exit(1)

    # Get input and output folder paths from command-line arguments
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]

    # Call the scan_images function with provided folder paths
    scan_images(input_folder, output_folder)
