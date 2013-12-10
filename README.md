## Sorts my photos.

Run the python script (or run.sh) to sort any photos in a folder named Import in the same folder as the script.
You can run setup.sh to create the Import folder. Photos will be moved into the Photos folder in folders named
by month and folders named by year. The script will try to find groups in the folders that get new images,
and name them by their location.

Example dir structure after running...

<pre>
├── process.py
├── run.sh
├── Import
│   └── anything left over
└── Photos
    └── 2013
        ├── 1-January
        │   ├── img1.jpg
        │   └── img2.jpg
        ├── 2-February
        │   ├── img3.jpg
        │   ├── img4.jpg
        │   └── 13-14-Bellingham, WA
        │       ├── img5.jpg
        │       ├── img6.jpg
        │       ├── img7.jpg
        │       ├── img8.jpg
        │       └── img9.jpg
        └── 4-April
            └── img10.jpg
</pre>
