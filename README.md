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

Photos will be sorted by month and year. The script will try to find groups in
the folders that get new images, and name them by their location and holiday.

- Holidays are found using `holiday.go`.
- Locations are found using gps exif data and google's location api.
- Duplicates will be copied with a `-D`, where D is the number found appended to
  the filename.

### Using

`go get github.com/apexskier/PhotoManagement`
`cd $GOPATH/src/github.com/apexskier/PhotoManagement`
`make`

This will get the project, build an executable, and copy and load a launchd
plist file onto your machine. OS X will keep the program running for you
through launchd. It will also check for a configuration file and make a
default one if not found. See `~/.gophotoconfig`.

### Example

Example directory structure...

<pre>
└── Photo Library
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
