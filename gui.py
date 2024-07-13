import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import json
import os
from PIL import Image, ImageTk
import scan
import render
import subprocess
import shutil

class BurstGod:
    def __init__(self, root):
        # Initialize global_settings and render_settings dictionaries
        self.global_settings = {}
        self.render_settings = {}
        self.root = root
        self.root.title("Burst God")

        # Configure column weights here
        for col in range(3):
            self.root.columnconfigure(col, weight=1)

        # Define a constant for padding
        self.padding =  5

        # Variables for GUI elements
        self.input_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.same_as_input_var = tk.BooleanVar(value=True)
        self.real_fps_var = tk.BooleanVar(value=False)
        #self.conform_rfps_var = tk.BooleanVar(value=False)
        self.output_type_var = tk.StringVar(value=".mov")
        self.image_sequence_type_var = tk.StringVar(value="Premiere")
        self.quality_var = tk.StringVar(value="high")
        self.frame_size_var = tk.StringVar(value="original")
        self.original_frame_size_var = tk.BooleanVar(value=True)
        self.frame_size_frame = tk.Frame(self.root)
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.crop_var = tk.BooleanVar(value=True)
        self.distort_var = tk.BooleanVar(value=False)
        self.crop_distort_var = tk.StringVar(value='Crop')
        self.min_frames_var = tk.IntVar(value=4)
        self.video_file_naming_vars = {}
        self.custom_text_var = tk.StringVar()
        self.custom_chk_var = tk.BooleanVar(value=False)
        self.framerate_var = tk.StringVar(value="24")
        self.additional_framerates_entries = []
        self.frame_length_var = tk.StringVar(value="1")
        self.additional_frame_lengths_entries = []
        self.pattern_mode_var = tk.BooleanVar(value=False)
        self.pattern_mode_entries = []

        #added variable for image sequence format
        self._image_sequence_format_frame = tk.Frame(self.root)

        self.image_sequence_format = tk.StringVar(value='jpeg')

        #self.export_both_var = tk.BooleanVar(value=False)
        self.export_original_rfps_var = tk.BooleanVar(value=False)
        self.checked_shots = []
        self.numbered_shot_list = []
        self.codec_options = self.get_ffmpeg_codecs()
        self.codec_var = tk.StringVar(value=self.codec_options[0] if self.codec_options else "")  # Default codec

        # Additional attribute for codec option
        self.codec_option_var = None
        self.codec_option_menu = None

        # Additional attribute for framerate_frame
        self.framerate_frame = tk.Frame(self.root)  # Initialize framerate_frame

        # Additional attribute for codec option
        self.codec_option_var = None
        self.codec_option_menu = None

        # Additional: a class variable for render type
        self.render_type_var = tk.StringVar()
        self.render_type_var.set("render_videos")  # Default to render_video also could be #make_sequences

        # Create GUI elements
        self.create_widgets()

        # Create blank table
        self.create_blank_table()

        # Load settings from file or set default values
        self.settings_file = "settings.json"
        #self.load_settings()

        # Load settings only when restoring previous shot lists
        self.load_settings(from_restore=True)

    def create_widgets(self):
        # Input Folder
        input_frame = tk.Frame(self.root)
        input_frame.pack(anchor='w', pady=(10, 0), padx=(0, self.padding))

        input_label = tk.Label(input_frame, text="Input Folder:", font=('Helvetica', 10))
        input_label.pack(side='left')

        input_entry = tk.Entry(input_frame, textvariable=self.input_folder_var, state="readonly", width=40)
        input_entry.pack(side='left', padx=(self.padding, 0))

        browse_button = tk.Button(input_frame, text="Browse", command=self.browse_input_folder)
        browse_button.pack(side='left', padx=(self.padding, 0))

        # Output Folder
        output_folder_frame = tk.Frame(self.root)
        output_folder_frame.pack(anchor='w', pady=5, padx=(0, self.padding))

        output_folder_label = tk.Label(output_folder_frame, text="Output Folder:", font=('Helvetica', 10))
        output_folder_label.pack(side='left')

        output_folder_entry = tk.Entry(output_folder_frame, textvariable=self.output_folder_var, state="readonly", width=40)
        output_folder_entry.pack(side='left', padx=(self.padding, 0))

        output_folder_browse_button = tk.Button(
            output_folder_frame, text="Browse", command=self.browse_output_folder, state=tk.NORMAL
        )
        output_folder_browse_button.pack(side='left', padx=(self.padding, 0))

        same_as_input_checkbox = tk.Checkbutton(
            output_folder_frame,
            text="Same as Input",
            variable=self.same_as_input_var,
            command=self.toggle_same_as_input,
        )
        same_as_input_checkbox.pack(side='left', padx=(self.padding, 0))

        output_folder_entry.configure(
            state="disabled" if self.same_as_input_var.get() else "readonly"
        )

        # Frame for the buttons
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(anchor='w', pady=10, padx=(self.padding, 0))

        # Place the reopen previous shotlist button
        reopen_shotlist_button = tk.Button(
            buttons_frame, text="Re-open Previous Shotlist", command=self.reopen_previous_shotlist
        )
        reopen_shotlist_button.pack(side='left', padx=(0, self.padding))

        # Create the button to clear settings
        clear_settings_button = tk.Button(
            buttons_frame, text="Clear Settings", command=self.clear_settings
        )
        clear_settings_button.pack(side='left', padx=(0, self.padding))

        # Create the button to clear output folder
        clear_output_folder_button = tk.Button(
            buttons_frame, text="Clear Output Folder", command=self.clear_output_folder
        )
        clear_output_folder_button.pack(side='left')


        # General Options for both image sequences and video export
        naming_section_label = tk.Label(
            self.root, text="Options for Image Sequence Export and Video Export", font=('Helvetica', 10, 'bold')
        )
        naming_section_label.pack(anchor='w', pady=(10, 0), padx=(0, self.padding))

        # Video File Naming Section
        naming_section_label = tk.Label(
            self.root, text="Clip and File Naming Options:", font=('Helvetica', 10)
        )
        naming_section_label.pack(anchor='w', pady=(10, 0), padx=(0, self.padding))

        # Frame for file naming options
        naming_frame = tk.Frame(self.root)
        naming_frame.pack(anchor='w', pady=(0, 10), padx=(0, self.padding))

        # Checkboxes for file naming options
        file_naming_options = [
            'Project Title',
            'Scene',
            'Shot',
            'Shot Description',
            'Take',
        ]
        for i, key in enumerate(file_naming_options):
            chk_var = tk.BooleanVar(value=True)  # Default on
            chk = tk.Checkbutton(naming_frame, text=key, variable=chk_var)
            chk.pack(side='left', padx=(0, self.padding))

            # Store the variables for later use
            self.video_file_naming_vars[key] = {'chk_var': chk_var}

        # Custom Text Checkbox
        custom_chk = tk.Checkbutton(
            naming_frame,
            text="(Custom)",
            variable=self.custom_chk_var,
            command=lambda: self.toggle_custom_text_entry(
                custom_text_entry, self.custom_chk_var
            ),
        )
        custom_chk.pack(side='left', padx=(self.padding, 0))

        # Custom Text Box
        custom_text_entry = tk.Entry(
            naming_frame, textvariable=self.custom_text_var, state="readonly", width=40
        )
        custom_text_entry.pack(side='left', padx=(self.padding, 0))        

        # Minimum Frames
        min_frames_frame = tk.Frame(self.root)
        min_frames_frame.pack(anchor='w', pady=5, padx=(0, self.padding))

        min_frames_label = tk.Label(min_frames_frame, text="Minimum Frames:", font=('Helvetica', 10))
        min_frames_label.pack(side='left')

        min_frames_entry = tk.Entry(
            min_frames_frame, textvariable=self.min_frames_var, width=5
        )
        min_frames_entry.pack(side='left', padx=(self.padding, 0))

        

        # Image sequence Only Options
        naming_section_label = tk.Label(
            self.root, text="Image Sequence Only Export Options", font=('Helvetica', 10, 'bold')
        )
        naming_section_label.pack(anchor='w', pady=(10, 0), padx=(0, self.padding))

        # Image sequence file format section
        self._image_sequence_format_frame.pack(anchor='w', pady=(10,0), padx=(0, self.padding))
        image_sequence_format_label = tk.Label(self._image_sequence_format_frame, text="Image Sequence Format:", font=('Helvetica', 10))
        image_sequence_format_label.grid(row=0, column=6, sticky='w', padx=(self.padding, 0))

        image_sequence_format_options = ['raw', 'dng', 'jpeg']
        image_sequence_format_var = tk.StringVar(value='jpeg') # Variable to hold the selected option
        image_sequence_format_menu = tk.OptionMenu(self._image_sequence_format_frame, self.image_sequence_format, *image_sequence_format_options)
        image_sequence_format_menu.grid(row=0, column=7, padx=(self.padding, 0))

        # Video Only Options
        naming_section_label = tk.Label(
            self.root, text="Video Only Export Options", font=('Helvetica', 10, 'bold')
        )
        naming_section_label.pack(anchor='w', pady=(10, 0), padx=(0, self.padding))

        # Image Size Label
        image_size_label = tk.Label(self.frame_size_frame, text="Image Size:", font=('Helvetica',   10))
        image_size_label.grid(row=0, column=0, sticky='w', padx=(0, self.padding))

        # Frame Size
        self.frame_size_frame.pack(anchor='w', pady=5, padx=(0, self.padding))

        # Label for Frame Size Options
        frame_size_options_label = tk.Label(
            self.frame_size_frame, text="Frame size options:", font=('Helvetica', 10)
        )
        frame_size_options_label.grid(row=0, column=0, sticky='w', padx=(0, self.padding))

        # Options for Frame Size Dropdown
        frame_size_options = ['Original', '3/4', '1/2', '1/4', '4K (3840x2160)', '1080p (1920x1080)', 'Custom']
        self.frame_size_var = tk.StringVar(value='Original') # Variable to hold the selected option

        frame_size_menu = tk.OptionMenu(self.frame_size_frame, self.frame_size_var, *frame_size_options)
        frame_size_menu.grid(row=0, column=1, padx=(self.padding, 0))

        # Function to handle dropdown selection
        def handle_frame_size_dropdown(*args):
            selected_option = self.frame_size_var.get()
            if selected_option == 'Custom':
                self.height_entry.config(state="normal")
                self.width_entry.config(state="normal")
            else:
                self.height_entry.delete(0, 'end')
                self.width_entry.delete(0, 'end')
                self.height_entry.config(state="disabled")
                self.width_entry.config(state="disabled")

        # Link the dropdown menu to the function
        self.frame_size_var.trace_add('write', handle_frame_size_dropdown)

        # Add labels "H:" and "W:" for the height and width boxes
        h_label = tk.Label(self.frame_size_frame, text="H:", font=('Helvetica', 10))
        h_label.grid(row=0, column=4, sticky='w', padx=(self.padding, 0))

        self.height_entry = tk.Entry(self.frame_size_frame, textvariable=self.height_var, state="disabled", width=5)
        self.height_entry.grid(row=0, column=5, padx=(self.padding, 0))

        w_label = tk.Label(self.frame_size_frame, text="W:", font=('Helvetica', 10))
        w_label.grid(row=0, column=2, sticky='w', padx=(self.padding, 0))

        self.width_entry = tk.Entry(self.frame_size_frame, textvariable=self.width_var, state="disabled", width=5)
        self.width_entry.grid(row=0, column=3, padx=(self.padding, 0))


        # Crop / Distort Selection
        crop_distort_label = tk.Label(self.frame_size_frame, text="Crop / Distort:", font=('Helvetica', 10))
        crop_distort_label.grid(row=0, column=6, sticky='w', padx=(self.padding, 0))

        crop_distort_options = ['Crop', 'Distort']
        crop_distort_var = tk.StringVar(value='Crop')  # Variable to hold the selected option
        crop_distort_menu = tk.OptionMenu(self.frame_size_frame, crop_distort_var, *crop_distort_options)
        crop_distort_menu.grid(row=0, column=7, padx=(self.padding, 0))

        # Framerate
        framerate_frame = tk.Frame(self.root)
        framerate_frame.pack(anchor='w', pady=5, padx=(0, self.padding))

        framerate_label_text = tk.Label(framerate_frame, text="Framerate:", font=('Helvetica', 10))
        framerate_label_text.pack(side='left')

        framerate_entry = tk.Entry(
            framerate_frame, textvariable=self.framerate_var, width=5
        )
        framerate_entry.pack(side='left', padx=(self.padding, 0))

        # New checkbox for exporting original RFPS
        self.export_original_rfps_var = tk.BooleanVar(value=False) # Default off
        export_original_rfps_checkbox = tk.Checkbutton(
            framerate_frame, text="Also Export Original RFPS? (will make 2 versions)", variable=self.export_original_rfps_var
        )
        export_original_rfps_checkbox.pack(side='left', padx=(self.padding, 0))

        # Additional Framerates Frame
        additional_framerates_frame = tk.Frame(self.root)
        additional_framerates_frame.pack(
            anchor='w', pady=5, padx=(0, self.padding)
        )

        # Additional framerates label and button
        additional_framerates_label = tk.Label(
            additional_framerates_frame,
            text="Additional Framerates:",
            font=('Helvetica', 10),
        )
        additional_framerates_label.grid(
            row=0, column=0, padx=(0, self.padding)
        )  # Adjusted indentation

        add_framerate_button = tk.Button(
            additional_framerates_frame, text="+", command=self.add_framerate_entry
        )
        add_framerate_button.grid(row=0, column=1, padx=(self.padding, 0))

        # Additional Framerates Entries
        self.additional_framerates_frame = tk.Frame(
            additional_framerates_frame
        )
        self.additional_framerates_frame.grid(row=0, column=2, padx=(self.padding, 0))

        # Additional attribute for framerate_frame
        self.framerate_frame = framerate_frame

        # Framelength
        frame_length_frame = tk.Frame(self.root)
        frame_length_frame.pack(anchor='w', pady=5, padx=(0, self.padding))

        frame_length_label_text = tk.Label(frame_length_frame, text="Frame Length:", font=('Helvetica', 10))
        frame_length_label_text.grid(row=0, column=0)

        frame_length_entry = tk.Entry(
            frame_length_frame, textvariable=self.frame_length_var, width=5
        )
        frame_length_entry.grid(row=0, column=1, padx=(self.padding, 0))

        # Additional Frame Lengths Label and Button
        additional_frame_lengths_label = tk.Label(
            frame_length_frame,
            text="Additional Frame Lengths:",
            font=('Helvetica', 10),
        )
        additional_frame_lengths_label.grid(row=0, column=2, padx=(self.padding, 0))

        add_frame_lengths_button = tk.Button(
            frame_length_frame, text="+", command=self.add_frame_length_entry
        )
        add_frame_lengths_button.grid(row=0, column=3, padx=(self.padding, 0))

        # Additional Frame Lengths Entries
        self.additional_frame_lengths_frame = tk.Frame(
            frame_length_frame
        )
        self.additional_frame_lengths_frame.grid(row=0, column=4, padx=(self.padding, 0))

        # Additional attribute for frame_length_frame
        self.frame_length_frame = frame_length_frame


        # pattern_mode Frame
        pattern_mode_frame = tk.Frame(self.root)
        pattern_mode_frame.pack(anchor='w', pady=5, padx=(0, self.padding))

        # Additional frame lengths label and button
        pattern_mode_label = tk.Label(
            pattern_mode_frame,
            text="Pattern Mode:",
            font=('Helvetica', 10),
        )

        # checkbox for pattern mode
        pattern_mode_var = tk.BooleanVar(value=False)  # Default off
        pattern_mode_checkbox = tk.Checkbutton(
            pattern_mode_frame, text="Enable Pattern Mode", variable=self.pattern_mode_var
        )
        pattern_mode_checkbox.grid(row=0, column=0, padx=(self.padding, 0))

        # pattern_mode label and button
        pattern_mode_label = tk.Label(
            pattern_mode_frame,
            text="Pattern:",
            font=('Helvetica', 10),
        )
        pattern_mode_label.grid(row=0, column=1, padx=(self.padding, 0))

        pattern_mode_button = tk.Button(
            pattern_mode_frame, text="+", command=self.add_pattern_mode_entry
        )
        pattern_mode_button.grid(row=0, column=2, padx=(self.padding, 0))

        # Additional pattern_mode Entries
        self.pattern_mode_frame = tk.Frame(
            pattern_mode_frame
        )
        self.pattern_mode_frame.grid(row=0, column=3, padx=(self.padding, 0))

        # Additional attribute for pattern_mode_frame
        self.frame_pattern_mode_frame = pattern_mode_frame

        # Create a single frame to contain Output Type, Quality, and Codec Option
        options_frame = tk.Frame(self.root)
        options_frame.pack(anchor='w', pady=5, padx=(0, self.padding))

        # Output Type
        output_type_label = tk.Label(options_frame, text="Output Type:", font=('Helvetica', 10))
        output_type_label.pack(side='left')

        output_type_options = [".mp4", ".mov"]
        output_type_menu = tk.OptionMenu(
            options_frame, self.output_type_var, *output_type_options
        )
        output_type_menu.pack(side='left', padx=(self.padding, 20))

        # Quality
        quality_label = tk.Label(options_frame, text="Quality:", font=('Helvetica', 10))
        quality_label.pack(side='left', padx=(self.padding, 20))

        quality_options = ["low", "acceptable", "high", "excessive", "lossless"]
        quality_menu = tk.OptionMenu(options_frame, self.quality_var, *quality_options)
        quality_menu.pack(side='left', padx=(self.padding, 20))

        # Codec Option
        codec_option_label = tk.Label(options_frame, text="Codec Option:", font=('Helvetica', 10))
        codec_option_label.pack(side='left', padx=(self.padding, 20))

        self.codec_option_var = tk.StringVar(value=self.codec_options[0] if self.codec_options else "")  # Default codec
        self.codec_option_menu = tk.OptionMenu(
            options_frame, self.codec_option_var, *self.codec_options
        )
        self.codec_option_menu.pack(side='left', padx=(self.padding, 0))


        # Scan / Render / Make Image Sequences
        naming_section_label = tk.Label(
            self.root, text="Scan / Render / Make Image Sequences", font=('Helvetica',  10, 'bold')
        )
        naming_section_label.pack(anchor='w', pady=(10,  0), padx=(0, self.padding))

        # Scan Only Button
        scan_only_button = tk.Button(
            self.root, text="Scan Only", command=self.scan_only
        )
        scan_only_button.pack(anchor='w', pady=10, padx=(self.padding,  0))

        # Frame for "Scan and Make Image Sequences" and "Make Sequences" buttons
        scan_make_sequences_frame = tk.Frame(self.root)
        scan_make_sequences_frame.pack(anchor='w', pady=10, padx=(self.padding,  0))

        # Scan and Make Image Sequences
        scan_and_make_sequences = tk.Button(
            scan_make_sequences_frame, text="Scan + Make Image Sequences", command=self.scan_and_make_sequences
        )
        scan_and_make_sequences.pack(side='left', padx=(0, self.padding))

        # Make Sequences Only Button
        self.make_sequences_button = tk.Button(
            scan_make_sequences_frame, text="Make Image Sequences Only", state=tk.DISABLED, command=self.make_sequences
        )
        self.make_sequences_button.pack(side='left')

        # Frame for "Scan and Render" and "Render" buttons
        scan_render_frame = tk.Frame(self.root)
        scan_render_frame.pack(anchor='w', pady=10, padx=(self.padding,  0))

        # Scan and Render Button
        scan_and_render_button = tk.Button(
            scan_render_frame, text="Scan and Render", command=self.scan_and_render
        )
        scan_and_render_button.pack(side='left', padx=(0, self.padding))

        # Render Only Button
        self.render_only_button = tk.Button(scan_render_frame, text="Render Only", command=self.render_only, state=tk.DISABLED)
        self.render_only_button.pack(side='left')

    def toggle_pattern_mode(self):
        # This function will be called whenever the checkbox is clicked
        # It prints the current state of the pattern_mode_var
        print("Pattern Mode is now:", self.pattern_mode_var.get())
        # Here you can add additional logic to update the pattern mode variable
        # For example, enabling or disabling certain features based on the checkbox state

    def browse_input_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.input_folder_var.set(folder_path)

            # Auto-populate output folder if "Same as Input" is checked
            if self.same_as_input_var.get():
                self.output_folder_var.set(folder_path)

    def browse_output_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_folder_var.set(folder_path)
            self.same_as_input_var.set(False)  # Uncheck the "Same as Input" checkbox

    def toggle_same_as_input(self):
        if self.same_as_input_var.get():
            # Disable output folder entry and set its value to the input folder
            self.output_folder_var.set(self.input_folder_var.get())
        else:
            # Enable output folder entry and clear its value
            self.output_folder_var.set("")

    def clear_settings(self):
        """
        Clears all settings and resets GUI to defaults.
        """
        # Get the path to the settings file in the output folder
        output_folder_path = self.output_folder_var.get()
        settings_file_path = os.path.join(output_folder_path, "settings.json")

        # Print the settings file path
        print("Deleting settings file:", settings_file_path)

        # Delete the settings file
        try:
            os.remove(settings_file_path)
            print("Settings cleared successfully.")
        except FileNotFoundError:
            print("No settings file found.")

        # Restart the GUI - you might need to implement this part

    def clear_output_folder(self):
        """
        Clears the 'output' subfolder of the provided output folder.
        """
        # Get the output folder path provided by the user
        output_folder_path = self.output_folder_var.get()

        # Construct the full path to the 'output' subfolder
        output_subfolder_path = os.path.join(output_folder_path, "output")

        # Print the folder that will be deleted
        print("Deleting folder:", output_subfolder_path)

        # Check if the 'output' subfolder exists
        if os.path.isdir(output_subfolder_path):
            # Delete the 'output' subfolder and all its contents
            shutil.rmtree(output_subfolder_path)
            print("Output folder cleared successfully.")
        else:
            print("The 'output' subfolder does not exist within the provided output folder.")

    def get_ffmpeg_codecs(self):
        try:
            # Run FFmpeg to get a list of available codecs
            result = subprocess.run(['ffmpeg', '-codecs'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stdout
            lines = output.split('\n')
            all_codecs = [line.split()[1] for line in lines if line.startswith(' D') or line.startswith('  E')]

            # Specify the desired professional video codecs
            professional_codecs = [
                'prores', 'h264', 'hevc', 'dnxhd', 'dvvideo',
                'mpeg2video', 'libaom-av1', 'libvpx-vp9', 'xdcam', 'apch'
            ]

            # Filter out the professional codecs that are installed
            available_codecs = [codec for codec in professional_codecs if codec in all_codecs]

            return available_codecs
        except Exception as e:
            print(f"Error getting FFmpeg codecs: {e}")
            return []

    def toggle_frame_size(self):
        if self.original_frame_size_var.get():
            self.height_entry.config(state="disabled")
            self.width_entry.config(state="disabled")
        else:
            self.height_entry.config(state="normal")
            self.width_entry.config(state="normal")

    def toggle_crop_distort(self, checkbox_name):
        # Determine which checkbox was clicked
        if checkbox_name == 'crop':
            # If crop is checked, uncheck it and check distort
            if self.crop_var.get():
                self.crop_var.set(False)
                self.distort_var.set(True)
            # If crop is unchecked, check it and uncheck distort
            else:
                self.crop_var.set(True)
                self.distort_var.set(False)
        elif checkbox_name == 'distort':
            # If distort is checked, uncheck it and check crop
            if self.distort_var.get():
                self.distort_var.set(False)
                self.crop_var.set(True)
            # If distort is unchecked, check it and uncheck crop
            else:
                self.distort_var.set(True)
                self.crop_var.set(False)

    def add_framerate_entry(self):
        additional_framerates_entry = tk.Entry(
            self.additional_framerates_frame, textvariable=tk.StringVar(value=""), width=5
        )
        additional_framerates_entry.pack(
            side='left', padx=(self.padding, 0)
        )
        self.additional_framerates_entries.append(additional_framerates_entry)
        # Refresh the layout of the framerate_frame to ensure proper placement
        self.framerate_frame.update_idletasks()

    def add_frame_length_entry(self):
        additional_frame_lengths_entry = tk.Entry(
            self.additional_frame_lengths_frame, textvariable=tk.StringVar(value=""), width=5
        )
        additional_frame_lengths_entry.pack(
            side='left', padx=(self.padding,  0)
        )
        self.additional_frame_lengths_entries.append(additional_frame_lengths_entry)
        # Refresh the layout of the frame_length_frame to ensure proper placement
        self.frame_length_frame.update_idletasks()
    
    def add_pattern_mode_entry(self):
        pattern_mode_entry = tk.Entry(
            self.pattern_mode_frame, textvariable=tk.StringVar(value=""), width=5
        )
        pattern_mode_entry.pack(
            side='left', padx=(self.padding,  0)
        )
        self.pattern_mode_entries.append(pattern_mode_entry)
        # Refresh the layout of the frame_length_frame to ensure proper placement
        self.pattern_mode_frame.update_idletasks()

    def populate_table(self, shot_list, check_shots=False):
        # Clear existing table rows
        for widget in self.table_frame_inner.winfo_children():
            widget.destroy()

        # Build the numbered shot list from the given shot_list
        self.numbered_shot_list = [{'number': index, **shot} for index, shot in enumerate(shot_list, start=1)]

        # Create table headers
        headers = ["Render", "Thumbnail", "Scene", "Shot", "Take", "Notes", "Number of Frames", "Real FPS", "Project Title"]
        for col, header in enumerate(headers):
            tk.Label(self.table_frame_inner, text=header, relief=tk.RIDGE, width=15).grid(
                row=0, column=col
            )

        # Create table rows for each shot
        for index, shot in enumerate(self.numbered_shot_list, start=1):
            # Create a BooleanVar for the render checkbox
            render_var = tk.BooleanVar(value=True)  # Set to True by default

            def update_render_var(idx, var):
                print(f"Updating render_var for shot {idx}: {var.get()}")  # Debugging statement
                if var.get():
                    if idx not in self.checked_shots:
                        self.checked_shots.append(idx)
                        print(f"Shot {idx} added to the list.")
                else:
                    if idx in self.checked_shots:
                        self.checked_shots.remove(idx)
                        print(f"Shot {idx} removed from the list.")

                # Sort the checked_shots list
                self.checked_shots.sort()

                # Print the updated list of shots
                print("Updated List of Shots:", self.checked_shots)

            render_check = tk.Checkbutton(
                self.table_frame_inner, variable=render_var,
                command=lambda idx=index, var=render_var: update_render_var(idx, var)
            )

            render_check.grid(row=index, column=0)

            # Store the render_var for later use
            shot['render_var'] = render_var

            # Thumbnail Image
            thumbnail_path = shot.get('thumbnail', '')
            thumbnail_image = self.load_thumbnail(thumbnail_path)
            thumbnail_label = tk.Label(self.table_frame_inner, image=thumbnail_image)
            thumbnail_label.image = thumbnail_image  # Keep a reference to the image
            thumbnail_label.grid(row=index, column=1)

            # Other columns remain unchanged
            scene_label = tk.Label(self.table_frame_inner, text=shot.get('scene', ''))
            scene_label.grid(row=index, column=2)

            shot_label = tk.Label(self.table_frame_inner, text=shot.get('shot', ''))
            shot_label.grid(row=index, column=3)

            take_label = tk.Label(
                self.table_frame_inner, text=str(shot.get('take', ''))
            )
            take_label.grid(row=index, column=4)

            notes_label = tk.Label(
                self.table_frame_inner, text=shot.get('description', '')
            )
            notes_label.grid(row=index, column=5)

            num_frames_label = tk.Label(
                self.table_frame_inner, text=str(shot.get('num_frames', ''))
            )
            num_frames_label.grid(row=index, column=6)

            real_fps_label = tk.Label(
                self.table_frame_inner, text=str(shot.get('real_fps', ''))
            )
            real_fps_label.grid(row=index, column=7)

            title_label = tk.Label(
                self.table_frame_inner, text=shot.get('title', '')
            )
            title_label.grid(row=index, column=8)

        # Update the scroll region of the canvas after populating the table
        self.update_canvas_scroll_region()

        # Enable Render Only button when there are items in the table
        # self.render_only_button['state'] = tk.NORMAL

        # Print the current list of shots
        print("Current List of Shots:", self.checked_shots)

    def update_canvas_scroll_region(self):
        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        # Calculate the required width based on the content
        required_width = self.table_frame_inner.winfo_reqwidth()
        # Update the width of the Canvas and table_frame_inner
        self.canvas.config(width=required_width)
        self.table_frame_inner.config(width=required_width)

    def update_checked_shots(self, idx, var):
        """Update the checked_shots list based on the state of the checkbox."""
        if var.get():
            if idx not in self.checked_shots:
                self.checked_shots.append(idx)
                print(f"Shot {idx} added to the list.")
        else:
            if idx in self.checked_shots:
                self.checked_shots.remove(idx)
                print(f"Shot {idx} removed from the list.")

        # Sort the checked_shots list
        self.checked_shots.sort()

        # Print the updated list of shots
        print("Updated List of Shots:", self.checked_shots)

    # Remove the update_render_var function as it's integrated into update_checked_shots

    def load_thumbnail(self, path):
        # Load and resize the thumbnail image
        print("Loading thumbnail...")
        if os.path.exists(path):
            print(f"Thumbnail path exists: {path}")
            image = Image.open(path)
            print("Thumbnail image opened successfully.")
            image.thumbnail((50, 50))  # Adjust the size as needed
            print("Thumbnail image resized.")
            return ImageTk.PhotoImage(image)
        else:
            print(f"Thumbnail path does not exist: {path}")
            return tk.PhotoImage()  # Return an empty PhotoImage if the path is invalid

    def reopen_previous_shotlist(self):
        output_folder = self.output_folder_var.get()
        if not output_folder:
            print("Please provide an output folder location.")
            return

        # Load the shot list from the JSON file generated by scan.py
        try:
            json_path = os.path.join(output_folder, 'shot_list.json')
            print(f"Attempting to load shot list from: {json_path}")
            with open(json_path, 'r') as f:
                shot_list = json.load(f)
            print("Shot list loaded successfully.")
        except FileNotFoundError:
            print("JSON file not found. Please check the output directory.")
            return
        except json.JSONDecodeError:
            print("Error decoding JSON file. Please check the contents of the JSON file.")
            return

        # Initialize the checked shots list with the indices of all shots
        self.checked_shots = list(range(1, len(shot_list) +  1))

        # Print the list of checked shots before populating the table
        print("List of Checked Shots Before Populating Table:", self.checked_shots)

        # Populate the table with the shot list and check all the checkboxes
        self.populate_table(shot_list, check_shots=True)

        # Enable Render Only button when there are items in the table
        self.render_only_button['state'] = tk.NORMAL

        # Make image sequences button when there are items in the table
        self.make_sequences_button['state'] = tk.NORMAL

        # Load the settings file
        settings_file_path = os.path.join(output_folder, 'settings.json')
        try:
            with open(settings_file_path, 'r') as f:
                settings = json.load(f)
            print("Settings loaded successfully.")

            # Apply the loaded settings to the GUI
            self.input_folder_var.set(settings['input_folder'])
            self.output_folder_var.set(settings['output_folder'])
            self.output_type_var.set(settings['output_type'])
            self.render_type_var.set(settings['render_type'])
            self.image_sequence_type_var.set(settings['image_sequence_type'])
            self.quality_var.set(settings['quality'])
            self.framerate_var.set(settings['framerate'])
            self.frame_length_var.set(settings['frame_length'])
            self.export_original_rfps_var.set(settings['export_original_rfps'])
            self.min_frames_var.set(settings['min_frames'])
            self.image_sequence_format.set(settings['image_sequence_format'])

            # Populate additional framerates
            for framerate in settings['additional_framerates']:
                additional_framerates_entry = tk.Entry(
                    self.additional_framerates_frame, textvariable=tk.StringVar(value=framerate), width=5
                )
                additional_framerates_entry.pack(side='left', padx=(self.padding, 0))
                self.additional_framerates_entries.append(additional_framerates_entry)

            # Populate additional frame lengths
            for frame_length in settings['additional_frame_lengths']:
                additional_frame_lengths_entry = tk.Entry(
                    self.additional_frame_lengths_frame, textvariable=tk.StringVar(value=frame_length), width=5
                )
                additional_frame_lengths_entry.pack(side='left', padx=(self.padding, 0))
                self.additional_frame_lengths_entries.append(additional_frame_lengths_entry)

            self.pattern_mode_var.set(settings['pattern_mode_var'])

            # Populate additional pattern modes
            for pattern in settings['pattern_mode_pattern']:
                pattern_mode_entry = tk.Entry(
                    self.pattern_mode_frame, textvariable=tk.StringVar(value=pattern), width=5
                )
                pattern_mode_entry.pack(side='left', padx=(self.padding, 0))
                self.pattern_mode_entries.append(pattern_mode_entry)

            # For file_naming_options, you need to iterate over the dictionary and set each checkbox
            for option, value in settings['file_naming_options'].items():
                if option in self.video_file_naming_vars:
                    self.video_file_naming_vars[option]['chk_var'].set(value)

            self.frame_size_var.set(settings['frame_size_option'])
            self.original_frame_size_var.set(settings['original_frame_size_option'])
            self.width_var.set(settings['width'])
            self.height_var.set(settings['height'])
            self.crop_distort_var.set(settings['crop_distort'])
            self.codec_option_var.set(settings['codec_option'])

        except FileNotFoundError:
            print("Settings file not found. Please check the output directory.")
            return
        except json.JSONDecodeError:
            print("Error decoding settings file. Please check the contents of the file.")
            return

    def save_settings(self, from_render_queue=False):
        # Get the 'output_folder' value from the GUI
        output_folder = self.output_folder_var.get()

        # Check if 'output_folder' is not empty
        if output_folder:
            # Gather all necessary information from the GUI
            settings_dict = {
                'input_folder': self.input_folder_var.get(),
                'output_folder': output_folder,
                'output_type': self.output_type_var.get(),
                'render_type': self.render_type_var.get(),
                'image_sequence_type': self.image_sequence_type_var.get(),
                'quality': self.quality_var.get(),
                'framerate': self.framerate_var.get(),
                'frame_length': self.frame_length_var.get(),
                'export_original_rfps': self.export_original_rfps_var.get(),
                'min_frames': self.min_frames_var.get(),
                'additional_framerates': [entry.get() for entry in self.additional_framerates_entries if entry.get()],
                'additional_frame_lengths': [entry.get() for entry in self.additional_frame_lengths_entries if entry.get()],
                'pattern_mode_var': self.pattern_mode_var.get(),
                'pattern_mode_pattern': [entry.get() for entry in self.pattern_mode_entries if entry.get()],
                'file_naming_options': {key: self.video_file_naming_vars[key]['chk_var'].get() for key in self.video_file_naming_vars},
                'frame_size_option': self.frame_size_var.get(),
                'original_frame_size_option': self.original_frame_size_var.get(),
                'width': self.width_var.get(),
                'height': self.height_var.get(),
                'crop_distort': self.crop_distort_var.get(),
                'codec_option': self.codec_option_var.get(),
                'image_sequence_format': self.image_sequence_format.get()
                # Add other GUI variables as needed
            }

            # Save the settings to a JSON file
            settings_file_path = os.path.join(output_folder, 'settings.json')
            with open(settings_file_path, 'w') as f:
                json.dump(settings_dict, f, indent=4)  # Indent with 4 spaces
            print(f"Settings saved to {settings_file_path}")
        else:
            print("Output folder is empty. Please provide one before exporting.")
            # Handle the error as needed, e.g., return or raise an exception

    def load_settings(self, from_restore=False):
        # Get the 'output_folder' value from the GUI
        output_folder = self.output_folder_var.get()

        print("Output folder value:", output_folder)  # Debugging print

        # Check if 'output_folder' is not empty
        if output_folder:
            # Load the settings file
            settings_file_path = os.path.join(output_folder, 'settings.json')
            try:
                with open(settings_file_path, 'r') as f:
                    settings_dict = json.load(f)
                print("Settings loaded successfully.")

                # Update all GUI variables with the loaded settings
                self.input_folder_var.set(settings_dict['input_folder'])
                print("Input folder set to:", settings_dict['input_folder'])
                self.output_type_var.set(settings_dict['output_type'])
                print("Output type set to:", settings_dict['output_type'])
                self.render_type_var.set(settings_dict['render_type'])
                print("Render type set to:", settings_dict['render_type'])
                self.image_sequence_type_var.set(settings_dict['image_sequence_type'])
                print("Image sequence type set to:", settings_dict['image_sequence_type'])
                self.quality_var.set(settings_dict['quality'])
                print("Quality set to:", settings_dict['quality'])
                self.framerate_var.set(settings_dict['framerate'])
                print("Framerate set to:", settings_dict['framerate'])
                self.frame_length_var.set(settings_dict['frame_length'])
                print("Frame length set to:", settings_dict['frame_length'])
                self.export_original_rfps_var.set(settings_dict['export_original_rfps'])
                print("Export original RFPS set to:", settings_dict['export_original_rfps'])
                self.min_frames_var.set(settings_dict['min_frames'])
                print("Min frames set to:", settings_dict['min_frames'])
                self.additional_framerates_entries = settings_dict['additional_framerates']
                self.additional_frame_lengths_entries = settings_dict['additional_frame_lengths']
                self.pattern_mode_var.set(settings_dict['pattern_mode_var'])
                print("Pattern mode set to:", settings_dict['pattern_mode_var'])
                self.pattern_mode_entries = settings_dict['pattern_mode_pattern']
                for key, value in settings_dict['file_naming_options'].items():
                    self.video_file_naming_vars[key]['chk_var'].set(value)
                    print(f"File naming option {key} set to:", value)
                self.frame_size_var.set(settings_dict['frame_size_option'])
                print("Frame size option set to:", settings_dict['frame_size_option'])
                self.original_frame_size_var.set(settings_dict['original_frame_size_option'])
                print("Original frame size option set to:", settings_dict['original_frame_size_option'])
                self.width_var.set(settings_dict['width'])
                print("Width set to:", settings_dict['width'])
                self.height_var.set(settings_dict['height'])
                print("Height set to:", settings_dict['height'])
                self.crop_distort_var.set(settings_dict['crop_distort'])
                print("Crop/distort set to:", settings_dict['crop_distort'])
                self.codec_option_var.set(settings_dict['codec_option'])
                self.image_sequence_format.set(settings_dict['image_sequence_format']) # Corrected key
                print("Image sequence format set to:", settings_dict['image_sequence_format']) # Corrected key
                # Add other GUI variables as needed

            except FileNotFoundError:
                print("Settings file not found. Please check the output directory.")
                return
            except json.JSONDecodeError:
                print("Error decoding settings file. Please check the contents of the file.")
                return
        else:
            print("Output folder is empty or loading settings is not required.")


    def make_sequences(self):
        # sets render type
        render_type = "render_image_sequences"
        self.render_type_var.set(render_type)  # Update the render type variable

        # Use self.numbered_shot_list instead of self.shot_list
        shots_to_render = []
        for index, shot in enumerate(self.numbered_shot_list, start=1):
            if shot['render_var'].get():
                shots_to_render.append(index)

        # Update self.checked_shots with the indices of the shots to render
        self.checked_shots = shots_to_render

        # Sort the checked_shots list
        self.checked_shots.sort()

        # Save settings before rendering
        self.save_settings()

        # Call the render method with only the selected shots
        self.render(shots_to_render=shots_to_render)

    def scan_and_make_sequences(self):
        # sets render type
        render_type = "render_image_sequences"
        self.render_type_var.set(render_type)  # Update the render type variable

        #Get the input and output folder paths
        input_folder = self.input_folder_var.get()
        output_folder = self.output_folder_var.get()
        if not input_folder or not output_folder:
            print("Please provide input and output folder locations.")
            return

        # Call the scan_images function from the scan module
        try:
            scan.scan_images(input_folder, output_folder)
        except Exception as e:
            print("Error occurred while scanning:", str(e))
            return

        # Load the shot list from the JSON file generated by scan.py
        try:
            with open(os.path.join(output_folder, 'shot_list.json'), 'r') as f:
                shot_list = json.load(f)
        except FileNotFoundError:
            print("JSON file not found. Please check the output directory.")
            return
        except json.JSONDecodeError:
            print("Error decoding JSON file. Please check the contents of the JSON file.")
            return

        # Populate the table with the shot list
        self.populate_table(shot_list)

        # Enable Render Only button when there are items in the table
        self.render_only_button['state'] = tk.NORMAL

        # Save settings before rendering
        self.save_settings()

        # Call the render method with scan_and_render=True
        self.render(scan_and_render=True)

    def render_only(self):
        # sets render type
        render_type = "render_videos"
        self.render_type_var.set(render_type)  # Update the render type variable

        # Use self.numbered_shot_list instead of self.shot_list
        shots_to_render = []
        for index, shot in enumerate(self.numbered_shot_list, start=1):
            if shot['render_var'].get():
                shots_to_render.append(index)

        # Update self.checked_shots with the indices of the shots to render
        self.checked_shots = shots_to_render

        # Sort the checked_shots list
        self.checked_shots.sort()

        # Save settings before rendering
        self.save_settings()

        # Call the render method with only the selected shots
        self.render(shots_to_render=shots_to_render)

    def scan_only(self):
        # Get the input and output folder paths
        print("scan only button pressed")
        input_folder = self.input_folder_var.get()
        output_folder = self.output_folder_var.get()
        if not input_folder or not output_folder:
            print("Please provide input and output folder locations.")
            return

        # Call the scan_images function from the scan module
        try:
            scan.scan_images(input_folder, output_folder)
        except Exception as e:
            print("Error occurred while scanning:", str(e))
            return

        # Load the shot list from the JSON file generated by scan.py
        try:
            with open(os.path.join(output_folder, 'shot_list.json'), 'r') as f:
                shot_list = json.load(f)
        except FileNotFoundError:
            print("JSON file not found. Please check the output directory.")
            return
        except json.JSONDecodeError:
            print("Error decoding JSON file. Please check the contents of the JSON file.")
            return

        # Populate the table with the shot list
        self.populate_table(shot_list)

        # Enable Make Sequences button when there are items in the table
        self.make_sequences_button['state'] = tk.NORMAL
        # Enable Render Only button when there are items in the table
        self.render_only_button['state'] = tk.NORMAL

    def scan_and_render(self):
        print("scan and render button pressed")
        # Get the input and output folder paths
        input_folder = self.input_folder_var.get()
        output_folder = self.output_folder_var.get()
        if not input_folder or not output_folder:
            print("Please provide input and output folder locations.")
            return

        # Add a variable for render_videos or make_sequences based on user selection
        render_type = "render_videos"
        self.render_type_var.set(render_type)  # Update the render type variable
        
        # Call the scan_images function from the scan module
        try:
            scan.scan_images(input_folder, output_folder)
        except Exception as e:
            print("Error occurred while scanning:", str(e))
            return

        # Load the shot list from the JSON file generated by scan.py
        try:
            with open(os.path.join(output_folder, 'shot_list.json'), 'r') as f:
                shot_list = json.load(f)
        except FileNotFoundError:
            print("JSON file not found. Please check the output directory.")
            return
        except json.JSONDecodeError:
            print("Error decoding JSON file. Please check the contents of the JSON file.")
            return

        # Populate the table with the shot list
        self.populate_table(shot_list)

        # Enable Render Only button when there are items in the table
        self.render_only_button['state'] = tk.NORMAL

        # Make image sequences button when there are items in the table
        self.make_sequences_button['state'] = tk.NORMAL

        # Save settings before rendering
        self.save_settings()

        # Call the render method with scan_and_render=True
        self.render(scan_and_render=True)

    def create_settings_file(self):
        if not os.path.exists(self.settings_file):
            self.save_settings()

    def render(self, scan_and_render=False, shots_to_render=None):
        print("collecting info from gui elements")
        # Collect data from GUI elements
        input_folder = self.input_folder_var.get()
        output_folder = self.output_folder_var.get()
        output_type = self.output_type_var.get()
        render_type = self.render_type_var.get()
        image_sequence_type = self.image_sequence_type_var.get()
        quality = self.quality_var.get()
        framerate = self.framerate_var.get()
        frame_length = self.frame_length_var.get()
        export_original_rfps = self.export_original_rfps_var.get()
        min_frames = self.min_frames_var.get()
        additional_framerates = [entry.get() for entry in self.additional_framerates_entries if entry.get()]
        additional_frame_lengths = [entry.get() for entry in self.additional_frame_lengths_entries if entry.get()]
        pattern_mode = self.pattern_mode_var.get()
        pattern_mode_pattern = [entry.get() for entry in self.pattern_mode_entries if entry.get()]
        file_naming_options = {key: self.video_file_naming_vars[key]['chk_var'].get() for key in self.video_file_naming_vars}
        frame_size = self.frame_size_var.get()
        original_frame_size = self.original_frame_size_var.get()
        width = self.width_var.get()
        height = self.height_var.get()
        crop_distort_selection = self.crop_distort_var.get()
        frame_size_option = self.frame_size_var.get()
        original_frame_size_option = self.original_frame_size_var.get()
        width = self.width_var.get()
        height = self.height_var.get()
        crop_distort_selection = self.crop_distort_var.get()
        codec_option = self.codec_option_var.get()
        # Retrieve the image_sequence_format from the GUI or settings
        image_sequence_format = self.image_sequence_format.get() # Assuming image_sequence_format is a StringVar

        # Capture the custom text box value
        custom_text = self.custom_text_var.get()

        # Include the custom text in the file naming options
        file_naming_options = {
            key: self.video_file_naming_vars[key]['chk_var'].get() for key in self.video_file_naming_vars
        }
        file_naming_options['custom_text'] = custom_text

        # Check if the output folder path is set and exists
        if not output_folder or not os.path.isdir(output_folder):
            print("Output folder is not set or does not exist.")
            return  # Exit the method early if the output folder is not valid

        # Load the shot list from the JSON file generated by scan.py
        print("loading shot_list.json")
        shot_list_path = os.path.join(output_folder, 'shot_list.json')
        try:
            with open(shot_list_path, 'r') as f:
                shot_list = json.load(f)
            print(f"Loaded shot list from {shot_list_path}")
        except FileNotFoundError:
            print(f"Error: shot_list.json not found at {shot_list_path}.")
            return
        except json.JSONDecodeError:
            print(f"Error: JSON decoding failed for shot_list.json at {shot_list_path}. Please check the contents of the file.")
            return

        # Update the checked_shots list based on the current state of the checkboxes
        for index, shot in enumerate(self.numbered_shot_list, start=1):
            self.update_checked_shots(index, shot['render_var'])

        global_settings = {
            "input_folder": input_folder,
            "output_folder": output_folder,
            "output_type": output_type,
            "render_type": render_type,
            "image_sequence_type": image_sequence_type,
            "quality": quality,
            "framerate": framerate,
            "export_original_rfps": export_original_rfps,
            "min_frames": min_frames,
            "additional_framerates": additional_framerates,
            "frame_length": frame_length,
            "additional_frame_lengths": additional_frame_lengths,
            "pattern_mode_var": pattern_mode,
            "pattern_mode_pattern": pattern_mode_pattern,
            "file_naming_options": file_naming_options,
            "frame_size_option": frame_size_option,
            "original_frame_size_option": original_frame_size_option,
            "width": width,
            "height": height,
            "crop_distort": crop_distort_selection,
            "codec_option": codec_option,
            "frame_size": frame_size,  # Add this line
            "original_frame_size": original_frame_size,  # Add this line
            'image_sequence_format': image_sequence_format,
        }

        # Create the render queue dictionary with the global settings and a list of shot numbers
        render_queue = {
            'global_settings': global_settings,
            'shots_to_render': self.checked_shots  # This is already a list of shot numbers
        }

        # Write the render_queue to a file with indentation
        render_queue_path = os.path.join(output_folder, 'render_queue.json')
        with open(render_queue_path, 'w') as f:
            json.dump(render_queue, f, indent=4)  # Indent with   4 spaces
        print(f"Render queue saved to {render_queue_path}")

        # Execute render.py with the output folder as an argument
        subprocess.run(['python', 'render.py', output_folder])
        print(f"Render script executed with output folder: {output_folder}")

        # Save settings after rendering
        self.save_settings(from_render_queue=True)

    def create_blank_table(self):
        # Create a frame to hold the table
        self.table_frame = tk.Frame(self.root)
        self.table_frame.pack(anchor='w', pady=(10, 0))

        # Create a canvas and a scrollbar
        self.canvas = tk.Canvas(self.table_frame)
        self.scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack the canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Create a frame inside the canvas to hold the table
        self.table_frame_inner = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.table_frame_inner, anchor="nw")

        # Bind the mousewheel to the canvas for scrolling
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

        # Call populate_table with an empty shot list to create the table headers
        self.populate_table([])

        # Update the scroll region after populating the table
        self.update_canvas_scroll_region()

    def _on_mousewheel(self, event):
        """Scroll the canvas with the mousewheel."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def toggle_custom_text_entry(self, entry, chk_var):
        if chk_var.get():
            entry.config(state="normal")  # Make the entry editable
        else:
            entry.config(state="readonly")  # Make the entry read-only

# Main entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = BurstGod(root)
    app.create_settings_file()
    root.mainloop()
