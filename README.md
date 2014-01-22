## Sorts my photos.

Run `run.sh` to sort any photos in a folder named Import in the same folder as
the script.  You can run `setup_directories.sh` to create the Import folder.
Photos will be moved into the Photos folder and sorted by month and year. The
script will try to find groups in the folders that get new images, and name
them by their location and holiday.

Holidays are found using the `known_events.py` module. Supports holidays that
fall on specific days (e.g. 14th of February, or nth &lt;day&gt; of
&lt;month&gt; (e.g. 3rd Thursday of November). Also supports specified
birthdays, and Easter.

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
        │   └── img2.jpg
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
