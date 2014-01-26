#!/usr/bin/python3

import os, sys, time, shutil
from datetime import datetime
from PIL import Image, ExifTags
import urllib3, json
import known_events

import_folder = '../Import'
export_folder = '../Photos'
imgExts = ['jpg', 'jpeg', 'tiff', 'tif', 'gif', 'png']
vidExts = ['mov', 'm4v', '3gp']
allowedExts = imgExts + vidExts

def get_exif_data(fname, fileExt):
    ret = {}
    if fileExt in imgExts:
        # Get embedded EXIF data from image file.
        try:
            img = Image.open(fname)
            if hasattr( img, '_getexif' ):
                exifinfo = img._getexif()
                if exifinfo != None:
                    for tag, value in exifinfo.items():
                        decoded = ExifTags.TAGS.get(tag, tag)
                        ret[decoded] = value
        except IOError:
            print("[Error] Couldn't open image: " + fname)

    # Make sure photo date exists, fall back to file creation date.
    if 'DateTimeOriginal' in ret:
        ret['DateTimeOriginal'] = datetime.strptime(ret['DateTimeOriginal'], "%Y:%m:%d %H:%M:%S")
    else:
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(fname)
        ret['DateTimeOriginal'] = datetime.fromtimestamp(mtime)
    return ret

def loop_through_dir(folder, function, bar=False):
    output = []
    for root, dirs, filenames in os.walk(folder):
        f_len = len(filenames) - 1
        errs = []
        for i, f in enumerate(filenames): # Loop through files in directory.
            fileName, fileExt = os.path.splitext(f)
            fileExt = fileExt.lower()[1:]
            f_full = os.path.join(root, f)
            exif = None
            # Skip hidden files and only process allowed extensions.
            if not f.startswith('.') and fileExt in allowedExts:
                exif = get_exif_data(f_full, fileExt) # get exif data

                # Do something with files.
                function(f, f_full, output, exif)

                if f_len > 0 and bar:
                    percent_done = float(i) / f_len
                    width = 40
                    done = int(percent_done * width)
                    sys.stdout.write("\r|{}>{}| {:.0f}%".format('-' * done, ' ' * (width - done - 1), percent_done * 100))
            elif not f.startswith('.'):
                errs.append("Found a random file {:s}".format(f_full))
        if errs: print(*errs, sep='\n')

    return output

modified_folders = []

print("Moving photos into years/months.")

# move files to month folders
def sort_import(f, f_full, cant_move, exif):
    year_dir = os.path.join(export_folder, str(exif['DateTimeOriginal'].year))
    month_dir = os.path.join(year_dir, str(exif['DateTimeOriginal'].month) + '-' + exif['DateTimeOriginal'].strftime('%B')) # months named like: 6-June

    if os.path.exists(os.path.join(month_dir, f)):
        cant_move.append("Duplicate name for " + f_full + " (moving to " + month_dir + ").")
    else:
        try: # to move the photo into it's destination
            if f_full != os.path.join(month_dir, f):
                os.renames(f_full, os.path.join(month_dir, f))
                if month_dir not in modified_folders: # remember what folders have new stuff
                    modified_folders.append(month_dir)
        except:
            cant_move.append(f_full)

cant_move = loop_through_dir(import_folder, sort_import, True)

if cant_move:
    print("Couldn't move the following files:")
    print(*cant_move, sep='\n')
    print

# Remove empty folders
for root, dirs, filenames in os.walk(import_folder):
    for d in dirs:
        dirlist = os.listdir(os.path.join(root, d))
        if not dirlist or dirlist == ['.DS_Store']:
            shutil.rmtree(os.path.join(root, d))

# If testing or resortting everything, use the following line.
modified_folders = [x[0] for x in os.walk(export_folder) if x[0].count('/') == 3]

if modified_folders:
    print("Organizing folders with new contents.")

    http = urllib3.PoolManager()

    def get_data(f, f_full, data, exif):
        gpsinfo = {}
        if 'GPSInfo' in exif:
            for key, val in exif['GPSInfo'].items():
                decode = ExifTags.GPSTAGS.get(key, key)
                gpsinfo[decode] = val

        data.append({
            'path': f_full,
            'name': f,
            'date': exif['DateTimeOriginal'],
            'gps': gpsinfo
        })

    for folder in modified_folders:
        # get data for each file
        data = loop_through_dir(folder, get_data)
        if data:
            # sort by date
            data = sorted(data, key=lambda k: k['date'])

            # find groups
            groups = list(set([v['date'].day for v in data if v['date']])) # generate list of unique days in the month
            def count_days(day): return (day, sum(v['date'].day == day for v in data), sum(v['date'].day < day for v in data))
            groups = sorted(map(count_days, groups), key=lambda k: k[0]) # get a list sorted by date of (day, count of days, starting index)
            groups = [date for date in groups if date[1] > 4]

            # combine groups
            temp_groups = []
            len_groups = len(groups)
            i = 0
            while i < len_groups:
                group = groups[i]
                count = group[1]
                while i < len_groups - 1 and groups[i][0] == groups[i + 1][0] - 1:
                    count += groups[i + 1][1]
                    i += 1
                temp_groups.append((group[0], count, group[2], groups[i][0]))
                i += 1
            groups = temp_groups

            for group in groups:
                event_name = str(group[0])
                if group[0] != group[3]:
                    event_name += '-' + str(group[3])

                holiday = None
                date = data[group[2]]['date']
                day = group[3]
                while not holiday and day >= group[0]:
                    try: holiday = known_events.getHoliday(datetime(date.year, date.month, day))
                    except ValueError: break
                    day -= 1

                if type(holiday) == tuple:
                    event_name += '--'
                    if type(holiday[1]) == int:
                        age = data[group[2]]['date'].year - holiday[1]
                        if age == 0:
                            event_name += holiday[0] + "'s Birthday"
                        else:
                            if 4 <= age <= 20 or 24 <= day <= 30:
                                suffix = "th"
                            else:
                                suffix = ["st", "nd", "rd"][age % 10 - 1]
                            event_name += holiday[0] + "'s " + str(age) + suffix + " Birthday"
                    elif type(holiday[1]) == str:
                        if group[0] == group[1]:
                            event_name = holiday[0]
                        else:
                            event_name += holiday[0] + " " + holiday[1]
                elif holiday:
                    event_name += '--'
                    if group[0] == group[1]:
                        event_name = holiday
                    else:
                        event_name += holiday

                # create a name based on the place
                for i in range(group[2], group[2] + group[1]):
                    if data[i]['gps'] and 'GPSLatitude' in data[i]['gps']:
                        # location data is stored like:
                        # ...
                        # 'GPSLatitude': (
                        #         ({deg}, {multiplier}),
                        #         ({min}, {mulitplier}),
                        #         ({sec}, {mulitplier})
                        #     ),
                        # ...
                        try:
                            lat = data[i]['gps']['GPSLatitude'][0][0] / data[i]['gps']['GPSLatitude'][0][1] + \
                                  data[i]['gps']['GPSLatitude'][1][0] / (60.0 * data[i]['gps']['GPSLatitude'][1][1]) + \
                                  data[i]['gps']['GPSLatitude'][2][0] / (3600.0 * data[i]['gps']['GPSLatitude'][2][1])
                            lng = data[i]['gps']['GPSLongitude'][0][0] / data[i]['gps']['GPSLongitude'][0][1] + \
                                  data[i]['gps']['GPSLongitude'][1][0] / (60.0 * data[i]['gps']['GPSLongitude'][1][1]) + \
                                  data[i]['gps']['GPSLongitude'][2][0] / (3600.0 * data[i]['gps']['GPSLongitude'][2][1])
                            if str(data[i]['gps']['GPSLatitudeRef']) == 'S':
                                lat = -lat
                            if str(data[i]['gps']['GPSLongitudeRef']) == 'W':
                                lng = -lng

                            url = "http://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&sensor=false".format(lat=lat, lng=lng)
                            try:
                                json_ = json.loads(http.request('GET', url).data.decode('utf-8'))
                            except urllib3.exceptions.HTTPError as e:
                                print("[Error] urllib3 error for {:s}".format(url), e)
                                json_ = {}

                            if json_['results']:
                                address = json_['results'][1]['formatted_address']
                                address = address.replace(', USA', '')
                                address = address.split(',')[0]
                                event_name += '--' + address
                                if address != "Unknown Place":
                                    break # Found a name
                        except ZeroDivisionError: pass

                # create folder
                event_dir = folder + '/' + event_name

                print("Creating new event '{:s}' at {:s} ({}).".format(event_name, event_dir, data[group[2]]['date']))

                for i in range(group[2], group[2] + group[1]):
                    try:
                        if data[i]['path'] != os.path.join(event_dir, data[i]['name']):
                            os.renames(data[i]['path'], os.path.join(event_dir, data[i]['name']))
                    except:
                        print("Can't move", data[i]['path'], "to", event_dir + '/' + data[i]['name'])

            # remove empty folders
            for root, dirs, filenames in os.walk(folder):
                for d in dirs:
                    dirlist = os.listdir(os.path.join(root, d))
                    if not dirlist or dirlist == ['.DS_Store']:
                        shutil.rmtree(os.path.join(root, d))
        else:
            print("No photos found in the folder.")
            shutil.rmtree(folder)
