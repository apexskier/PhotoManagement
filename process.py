#!/usr/bin/python

import os, pprint, sys, time
from datetime import datetime
from PIL import Image
from PIL import ExifTags
import urllib2, json

import_folder = 'Import'
export_folder = 'Photos'
allowedExts = ['jpg', 'tiff', 'jpeg']

pp = pprint.PrettyPrinter(indent=4)
def get_exif_data(fname):
    # Get embedded EXIF data from image file.
    ret = {}
    try:
        img = Image.open(fname)
        if hasattr( img, '_getexif' ):
            exifinfo = img._getexif()
            if exifinfo != None:
                for tag, value in exifinfo.items():
                    decoded = ExifTags.TAGS.get(tag, tag)
                    ret[decoded] = value
    except IOError:
        print 'IOERROR ' + fname
    # make sure photo date exists, fall back to file creation date
    if 'DateTimeOriginal' in ret:
        ret['DateTimeOriginal'] = datetime.strptime(ret['DateTimeOriginal'], "%Y:%m:%d %H:%M:%S")
    else:
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(fname)
        ret['DateTimeOriginal'] = datetime.fromtimestamp(mtime)
    return ret

def loop_through_dir(folder, function):
    output = []
    for root, dirs, filenames in os.walk(folder):
        f_len = len(filenames) - 1
        for i, f in enumerate(filenames): # loop through files in import dir
            fileName, fileExt = os.path.splitext(f)
            if not f.startswith('.') and fileExt.lower()[1:] in allowedExts: # skip hidden files and only process allowed extensions
                f_full = os.path.join(root, f)
                exif = get_exif_data(f_full) # get exif data

            function(f, f_full, output, exif)

            if f_len > 0:
                sys.stdout.flush()
                percent_done = float(i) / f_len
                width = 40
                done = int(percent_done * width)
                sys.stdout.write("\r|{}>{}| {:.0f}%".format('-' * done, ' ' * (width - done - 1), percent_done * 100))

    return output

modified_folders = []

print "Sorting new photos."

# move files to month folders
def sort_import(f, f_full, cant_move, exif):
    year_dir = os.path.join(export_folder, str(exif['DateTimeOriginal'].year))
    month_dir = os.path.join(year_dir, str(exif['DateTimeOriginal'].month) + '-' + exif['DateTimeOriginal'].strftime('%B')) # months named like: 6-June

    # make sure folders that the photo's supposed to go in exist.
    if not os.path.exists(year_dir):
        os.makedirs(year_dir)
    if not os.path.exists(month_dir):
        os.makedirs(month_dir)

    try: # to move the photo into it's destination
        os.rename(f_full, os.path.join(month_dir, f))
        if month_dir not in modified_folders: # remember what folders have new stuff
            modified_folders.append(month_dir)
    except:
        cant_move.append(f_full)

cant_move = loop_through_dir(import_folder, sort_import)

print
if cant_move:
    print "Couldn't move the following files:"
    for p in cant_move:
        print p
    print
print "Moved photos into month folders."
print

# if testing or want to reevaluate all months, use the following instead of modified_folders
subdirs = [x[0] for x in os.walk(export_folder) if x[0].count('/') == 2]

def get_data(f, f_full, data, exif):
    gpsinfo = {}
    if 'GPSInfo' in exif:
        for key, val in exif['GPSInfo'].iteritems():
            decode = ExifTags.GPSTAGS.get(key, key)
            gpsinfo[decode] = val
    data.append({
        'path': f_full,
        'name': f,
        'date': exif['DateTimeOriginal'],
        'gps': gpsinfo
    })

modified_folders = subdirs

if modified_folders:
    print
    print "Organizing folders with new contents."
    print
# organize folders that have new contents
for folder in modified_folders:
    print folder
    # get data for each file
    data = loop_through_dir(folder, get_data)
    if len(data) > 1:
        print
    if data:
        # pp.pprint(data)
        groups = []
        last_dt = None
        dcount = 0
        start = 0

        # sort by date
        data = sorted(data, key=lambda k: k['date'])

        dates = list(set([v['date'].day for v in data if v['date']])) # generate list of unique days in the month
        def count_days(day): return (day, sum(v['date'].day == day for v in data), sum(v['date'].day < day for v in data))
        dates = sorted(map(count_days, dates), key=lambda k: k[0]) # get a list sorted by date of (day, count of days, starting index)
        print "Dates", dates


        # group data
        for i, p in enumerate(data):
            if last_dt: # group by consecutive dates
                if p['date'].day == last_dt.day or p['date'].day == last_dt.day + 1:
                    dcount += 1
                else:
                    if dcount > 5:
                        last_dt2 = None
                        days = []
                        count = 0
                        for j in range(start, start + dcount + 2):
                            if last_dt2:
                                if data[j]['date'].day == last_dt2.day:
                                    count += 1
                                else:
                                    if count and count < 3:
                                        days.append((j - count - 1, j - 1))
                                        count = 0
                            last_dt2 = data[j]['date']
                        if count and count < 3:
                            days.append((j - count - 1, j - 1))

                        print "days to eliminate:", days

                        groups.append((start, start + dcount + 1))

                    start = i
                    dcount = 0

            last_dt = p['date']
        # save groups with more than 5 photos
        if dcount > 5:
            groups.append((start, start + dcount))

        if groups:
            print groups

        # move photos into folders
        event_ct = 1
        event_names = []
        for pair in groups:
            event_name = str(data[pair[0]]['date'].day)
            if int(event_name) != data[pair[1]]['date'].day:
                event_name += '-' + str(data[pair[1]]['date'].day)
            avg = (pair[0] + pair[1]) / 2

            # create a name based on the place
            for i in range(pair[1] - pair[0] - 1):
                index = i / 2
                if i % 2 == 0:
                    index = -i / 2
                if data[avg + index]['gps'] and 'GPSLatitude' in data[avg + index]['gps']:
                    lat = data[avg + index]['gps']['GPSLatitude'][0][0] + \
                          data[avg + index]['gps']['GPSLatitude'][1][0] / 60.0 + \
                          data[avg + index]['gps']['GPSLatitude'][2][0] / 360000.0
                    lng = data[avg + index]['gps']['GPSLongitude'][0][0] + \
                          data[avg + index]['gps']['GPSLongitude'][1][0] / 60.0 + \
                          data[avg + index]['gps']['GPSLongitude'][2][0] / 360000.0
                    if str(data[avg + index]['gps']['GPSLatitudeRef']) == 'S':
                        lat = -lat
                    if str(data[avg + index]['gps']['GPSLongitudeRef']) == 'W':
                        lng = -lng

                    url = "http://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&sensor=false".format(lat=lat, lng=lng)
                    json_ = json.load(urllib2.urlopen(url))
                    address = ""
                    if json_['results']:
                        address = str(json_['results'][2]['formatted_address'])
                    else:
                        address = "Unknown Place"

                    if ', USA' in address:
                        address = address.replace(', USA', '')

                    event_name += '-' + address
                    if event_name in event_names:
                        event_name += ' ' + str(event_ct)
                    break

            # create folder
            event_dir = folder + '/' + event_name
            if not os.path.exists(event_dir):
                os.makedirs(event_dir)

            # make sure we don't have duplicate folders
            event_names.append(event_name)

            for i in range(pair[0], pair[1]):
                try:
                    pass
                    #os.rename(data[i]['path'], event_dir + '/' + data[i]['name'])
                except:
                    print "Can't move", data[i]['path']

            event_ct += 1

        import shutil
        # remove empty folders
        for root, dirs, filenames in os.walk(folder):
            for d in dirs:
                if os.listdir(os.path.join(root, d)) == ['.DS_Store']:
                    shutil.rmtree(os.path.join(root, d))
    else:
        print "No photos found in the folder."
        import shutil
        shutil.rmtree(folder)

    print
