Burst God
See examples: https://www.burstgod.com

Burst God uses QR codes as a film slate for burst photography to facilitate the creation of video clips from burst photography sequences. If you've ever filmed using burst photography and edited footage from a large folder of images, you know the pain. Burst God will do all the hard work for you; it's like having an assistant editor. Simply capture a shot of a QR code between each shot in your burst photography sequence. While this process can be a bit tedious, it will save you a tremendous amount of time during editing. If you haven't tried filming with burst photography, Burst God is an excellent way to start. Under the right circumstances, the footage can look stunning and achieve extremely high definition.

To use this software as intended, you must use the Burst God QR code generating film slate. Take a photo of the generated QR code before your first shot and between each subsequent shot. The app functions as a film slate, storing data such as scene, shot, take, and description. Don't worry if you accidentally photograph the QR code multiple times or forget to update your QR code; the software can handle these situations. It can also batch process multiple camera card folders—just place all the cards into the input folder. Burst God takes care of the chore of sorting and editing large, unedited sequences of images. It can create both image sequences and videos. 

Let's delve into the basics of the software.

Installation
As long as you have Python installed on your computer, the program should run smoothly, including downloading dependencies. Ensure that gui.py, scan.py, and render.py are all in the same folder. Run gui.py to launch the program. If you encounter any issues, refer to the requirements.txt file for a list of dependencies. The QR Slate is a simple HTML file—just open it, and it should function properly.

Here is an overview of the software functions and capabilities:

Input Folder
Choose the input folder containing your files or image folders.

Output Folder
Select the folder where you want your image sequences, videos, and JSON files to be saved. By default, the output folder is the same as the input folder. Videos will be organized into folders based on their frame rates.

Re-Open Previous Shotlist
If you have previously scanned a folder, the shot list will be saved as shot_list.json. You can reopen previously scanned folders, and the shots will automatically populate. This also restores previous settings.

Naming Options
These options allow you to specify how your exported files are named.

Minimum Frames
This sets the minimum number of frames required for a shot to be processed, which is useful for filtering out very short clips.

Image Sequence Only Options
Image Sequence Format
Note that image sequences retain the full frame size of your original files. Other options such as frame length and patterns do not apply to this mode. While Burst God is primarily designed for creating videos, image sequences can also be exported. The following section provides information specific to image sequence settings.

RAW
The RAW option simply separates your input images into folders and renames them for batch importing. These images may not work with most video editing software, but you may have reasons to preserve the original RAW format. 

When creating image sequences, you can specify the file type to be created:
DNG (Windows Only)
This option converts RAW images into DNG files and renames them. Pro tip: In After Effects, open the import window and search your image_sequences output folder for 00000 to import the first frame of all your shots. After searching for 00000, select all images and click the "multiple sequences" option in the After Effects import window. DNG mode requires downloading dnglab.exe. DNG Lab is available on GitHub at: https://github.com/dnglab/dnglab/releases/tag/v0.6.2. Download the Windows version, unzip the folder, and drag the dnglab.exe file into your main Burst God software folder (the same folder as gui.py).

JPEG
This option creates full-size JPEG image sequences from your images, organized into different shots.

Video Only Export Options

Frame Size Options
Choose your final frame size. You can crop to standard sizes like 4k or 1920x1080. Note that exporting original frame sizes can create very large video files, requiring ample hard drive space.

Frame Rate Options
Base Frame Rate: This is the primary frame rate for rendering videos. For optimal results, use the maximum FPS your camera shoots bursts at; many cameras shoot bursts around 20 FPS. If your burst is shot at 20 FPS but exported at 24 FPS, your footage will play faster. Exporting at 15 FPS will slow your footage and may cause stuttering, which can be used for special effects.

Also Export Original RFPS: This option additionally renders each shot at its estimated original frames per second, determined by comparing the start time of the first and last image. This estimation isn't exact; factors like the QR code picture or missing QR code picture can affect it. Each shot's original frame rate, in addition to the base frame rate, will be rendered, creating several additional frame rate folders. Issues exporting can arise from an impossible real FPS frame rate. Unchecking this button should resolve the issue. If not, restart the program and re-enter your settings.

Additional Frame Rates: Clicking the "+" button adds extra frame rates to the render queue. This is useful for testing how videos look at various frame rates, such as 24, 30, and 35, in a single export. Use caution when processing many shots; extra frame rates can consume hard drive space.

Frame Length
Frame length determines how many times each image appears consecutively in the sequence. At a frame rate of 1, images ABCD would result in frames ABCD. Setting a frame length of 2 would output AABBCCDD, effectively stretching the footage. For example, 12 frames at 24 FPS would yield a half-second clip, whereas 12 frames at a frame length of 2 and 24 FPS would yield a full-second clip.

Additional Frame Lengths
Similar to frame rates, additional frame lengths can be added for multiple lengths in a single render. This is useful for testing how footage looks at various lengths. Note that each frame length is rendered for each frame rate, potentially creating numerous variations.

Enable Pattern Mode / Pattern Mode
Pattern mode is unique, allowing multiple frame lengths to function as a pattern. Enabling pattern mode ignores regular frame lengths, producing only pattern videos. This feature is exclusive to video export. Here's an example of pattern mode:

Pattern mode must be enabled to function; click the "+" button to add a box for each desired frame length in the pattern. For instance, a [3][2][1] pattern (the brackets represent text boxes) would use the first image three times, the second image twice, and the third image once. Input ABCD with a pattern of 3, 2, 1 would output AAABBCDDD. Input ABCDE with a pattern of 1, 2, 1 would output ABBCDEE, ideal for generating stuttering video effects, especially suited for music videos or experimental projects.

Output Type
Choose between MOV or MP4 formats. Errors or failures to render videos may stem from settings mismatches. ProRes must be MOV, and H.264 must be MP4. Codec options depend on a pre-determined list cross-checked with your installed codecs.

Quality
Higher quality video settings generate large files. Processing extensive footage at high quality, full size, and multiple frame rates/lengths can quickly consume disk space, leading to out-of-space errors.

Scan Only
This scans through your selected input folder, creating temporary JPEG files and scanning for QR codes to segment images between them into shots. Note that shot lists include a "Shot Number" for tracking shots; it does not affect the "shot" value from your QR code.

After a successful scan, all shots should appear in a table at the bottom of the GUI. The "Make Image Sequences Only" and "Render Only" buttons become available after scanning or reopening a previous shot list. The scan function automatically searches 3-4 subfolders deep for images. If no QR codes are found, all images in the folder become a shot.

Scan + Make Image Sequences
This option runs a scan and creates image sequences for all detected shots. Refer below for details on image sequence creation. The program may appear to freeze during processing; processing time varies.

Make Image Sequences Only
This button is available post-scan or upon reopening a previous shot list. Creating image sequences generates a folder for each shot containing the selected image sequence format. Images are renamed in a format friendly to After Effects. Each processed shot resides in a distinct folder labeled sequentially (e.g., 1, 2, 3), corresponding to the shooting order. File names retain selected QR code data. Pro tip: for DNG or JPEG sequence import into After Effects, open the import window, locate your image_sequences folder, and search for 00000. After searching, select all images (the first image of your shots), and choose "multiple sequences" to import all shots into After Effects, pre-named and segmented into image sequences.

Scan + Render
This choice scans and renders identified shots. Expect apparent program freeze during processing; scanning and rendering take time.

Render Only
Available post-scan or upon reopening a prior shot list. Rendering videos uses multiple settings. For each shot, render at various frame rates and lengths can fill drive space. Test a small batch initially for best results; consider a single/few frame rates/lengths for focused rendering.

A few additional notes:

To remove unwanted text boxes for frame rates, patterns, or lengths, delete the content and leave blank.

To resolve settings recurrence upon reopening prior shot lists, delete settings.json in the output folder, and restart.

For issues with rendering a second time, copy your output folder to another folder, delete the output folder and restart the software. 

Burst God Best Practices:
Before the Shoot
1. Get the software running and scan/render the test photos to ensure everything is working.
2. Do tests with your shooting camera before any shoot to ensure your camera settings are correct and that your photos are compatible with Burst God, but most camera photo types will work. 

Camera Settings
1. Make sure to read up on mechanical vs electronic shutter: https://www.canon-europe.com/pro/infobank/electronic-vs-mechanical-shutter/
Try doing some tests to see if your footage is having issues with rolling shutter. 
2. Always use manual focus. Autofocus can cause issues because the autofocus can slow down your max fps burst shooting speed.
3. Keep your shutter speed fast enough. A high shutter speed will make your images clear and hyper-realistic. On the other hand, you can achieve different effects by using a lower shutter speed but it may lower your fps. 
4. Decide whether you need RAW or can live with JPEG. If you use JPEG instead of raw, it can produce faster max burst speed on some cameras. 

Lighting
You need a ton of light. Shooting outside during the day is great. I haven’t tested this out using photography strobe lights. I have only used my full light kit, which is only enough for a medium shot. Shooting indoors on a professional set with lots of lights would yield amazing results. Also make sure that lights won’t cause a similar issue to a rolling stutter. This occurs when some lights have a refresh rate that is out of sync with the shutter speed. 

Shooting
1. Use a tripod. Unless you’re going for an artistic effect, you’re probably better off using a tripod unless you want the footage to be nauseating. Camera shake is especially pronounced with burst photography.
2. Use a remote shoot application. For example, use the Canon camera connect app to remotely shoot your QR Code pictures and burst shots. This way you don’t have to worry about shaking the camera when you press the shoot button. 

On Set
1. You need an assistant on set to operate the QR code slate. They can use the html file in the main Burst God Folder. Or they can use the QR Code Generator. Doing this solo can be challenging because you’ll need to be switching back and forth between your remote shooting app and the QR slate webpage. 
2. Do a quick test on set to make sure your settings are correct. I’d suggest shooting at least two shots and make sure you’re not having rolling shutter problems before proceeding with the real shoot. 
3. Be careful about overdoing it with your camera. Doing a large number of burst photos will put some wear on your camera. Be especially mindful of taking breaks if the camera feels too hot. 

Post Shoot
1. Make sure you have a ton of harddrive space. If you’re working with full size videos based on the size of the original images, the video files will be huge. 
2. Backup your photos before processing them. 
3. Try testing out a few clips with various settings before processing all of your photos unless you already have a desired framerate. Unfortunately, if you only want to process a few clips, you should manually create a new folder and drag those few sections inside. 
4. There is a special way of importing image sequences described in the readme document. 
5. If you’re having issues scanning or rendering, you may need to install some dependencies. 
6. When in doubt, if you are having problems, restart the program and delete the json files to clear your settings and start from scratch. These will be generated in the same folder as your input folder. 
