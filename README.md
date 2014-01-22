## Sorts my photos.

### Why

I wanted a way to keep my and my family's photos organized. I've got a lot of
them.

I've used iPhoto, but have had issues with performance with a large library,
and I don't like how Photo Stream organizes my photos when they're
automatically added. I've also had a couple major iPhoto corruptions, which are
soul sucking when you've spent hours perfecting your events and tagging all
your photos.

I've also used Picasa, but its interface is pretty bad and Google's definitely
pushing towards Google+ photos and away from Picasa. I don't really want all my
photos online with a loss in metadata or resolution.

I like how iOS's new Photos app organizes my photos automatically by date and
location.

### What I want it to do

- Save all my photos in their original sizes
- Organize my photos for easy browsing
- Give me clues as to what's in an event
- Be quick while browsing
- Automatically find important events

### What it does

Run `run.sh` to sort any photos in a folder named Import a folder named Photos.
You can run `setup_directories.sh` to create the proper folders. Photos will be
sorted by month and year. The script will try to find groups in the folders
that get new images, and name them by their location and holiday.

### How it does it

Holidays are found using the `known_events.py` module. Supports holidays that
fall on specific days (e.g. 14th of February, or nth &lt;day&gt; of
&lt;month&gt; (e.g. 3rd Thursday of November). Also supports specified
birthdays, and Easter.

Locations are found using gps exif data and google's location api. To disable this functionality
remove lines 180 to 216 of App/process.py.

Will sort the following file extentions: .jpg, .jpeg, .tiff, .tif, .gif, .png.

Duplicate filenames will be skipped, and a notice will be printed.

### Example

Example directory structure after running...

<pre>
├── setup_directories.sh
├── run.sh
├── App
│   └── ...
├── Import
│   └── anything left over (movies, duplicates)
└── Photos
    └── 2013
        ├── 1-January
        │   ├── img1.jpg
        │   ├── img2.jpg
        │   └── 1-New Year's
        │       ├── img25.jpg
        │       ├── img26.jpg
        │       ├── img27.jpg
        │       └── img28.jpg
        ├── 2-February
        │   ├── img3.jpg
        │   ├── img4.jpg
        │   └── 13--Bellingham, WA
        │       ├── img5.jpg
        │       ├── img6.jpg
        │       ├── img7.jpg
        │       ├── img8.jpg
        │       └── img9.jpg
        └── 4-April
            └── img10.jpg
</pre>
