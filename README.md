## Sorts my photos.

Run `run.sh` to sort any photos in a folder named Import a folder named Photos.
You can run `setup_directories.sh` to create the proper folders. Photos will be
sorted by month and year. The script will try to find groups in the folders
that get new images, and name them by their location and holiday.

Holidays are found using the `known_events.py` module. Supports holidays that
fall on specific days (e.g. 14th of February, or nth &lt;day&gt; of
&lt;month&gt; (e.g. 3rd Thursday of November). Also supports specified
birthdays, and Easter.

Will sort the following file extentions: .jpg, .jpeg, .tiff, .tif, .gif, .png.

Duplicate filenames will be skipped, and a notice will be printed.

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
