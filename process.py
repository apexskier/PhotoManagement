#!/usr/bin/python

import os, pprint
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
    return ret

modified_folders = []

print "Processing new files"

# move files to month folders
for root, dirs, filenames in os.walk(import_folder):
    for f in filenames:
        fileName, fileExt = os.path.splitext(f)
        if not f.startswith('.') and fileExt.lower()[1:] in allowedExts: # skip hidden files
            f_full = os.path.join(root, f)
            exif = get_exif_data(f_full)
            try:
                photo_date = datetime.strptime(exif['DateTimeOriginal'], "%Y:%m:%d %H:%M:%S")
                year_dir = os.path.join(export_folder, str(photo_date.year))
                month_dir = os.path.join(year_dir, str(photo_date.month) + '-' + photo_date.strftime('%B'))

                if not os.path.exists(year_dir):
                    os.makedirs(year_dir)
                if not os.path.exists(month_dir):
                    os.makedirs(month_dir)

                try:
                    os.rename(f_full, os.path.join(month_dir, f))

                    if month_dir not in modified_folders:
                        modified_folders.append(month_dir)
                except:
                    print "Can't move", f_full
            except KeyError:
                print "no original time for " + f_full
subdirs = [x[0] for x in os.walk(export_folder) if x[0].count('/') == 2]

# organize folders that have new stuff
for folder in modified_folders:
    data = []
    #print folder
    # get data for each file
    for root, dirs, filenames in os.walk(folder):
        for f in filenames:
            fileName, fileExt = os.path.splitext(f)
            if not f.startswith('.') and fileExt.lower()[1:] in allowedExts: # skip hidden files
                f_full = os.path.join(root, f)
                exif = get_exif_data(f_full)
                photo_date = datetime.strptime(exif['DateTimeOriginal'], "%Y:%m:%d %H:%M:%S")
                year_dir = str(photo_date.year)
                month_dir = year_dir + '/' + str(photo_date.month) + '-' + photo_date.strftime('%B')
                gpsinfo = {}
                if 'GPSInfo' in exif:
                    for key, val in exif['GPSInfo'].iteritems():
                        decode = ExifTags.GPSTAGS.get(key, key)
                        gpsinfo[decode] = val

                data.append({
                    'path': f_full,
                    'name': f,
                    'date': photo_date,
                    'gps': gpsinfo
                })

    groups = []
    last_dt = None
    dcount = 0
    start = 0
    i = 0

    # sort by date
    data = sorted(data, key=lambda k: k['date'])

    # group data
    for p in data:
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
        i += 1
    # save groups with more than 5 photos
    if dcount > 5:
        groups.append((start, start + dcount))

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
                os.rename(data[i]['path'], event_dir + '/' + data[i]['name'])
            except:
                print "Can't move", data[i]['path']

        event_ct += 1

    import shutil
    # remove empty folders
    for root, dirs, filenames in os.walk(folder):
        for d in dirs:
            if os.listdir(os.path.join(root, d)) == ['.DS_Store']:
                shutil.rmtree(os.path.join(root, d))

