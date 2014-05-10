package main

import (
    "bytes"
    "os"
    "fmt"
    "time"
    "errors"
    "path/filepath"
    "io/ioutil"
    "sort"
    "encoding/json"
    "flag"

    "github.com/rwcarlsen/goexif/exif"
    "code.google.com/p/go.exp/fsnotify"
)

var (
    imgExts []string
    vidExts []string
    allExts []string
    data dataType
    baseTime time.Time = time.Now()
    maxK = 8
    ConfigPath string
    Config *ConfigType
)

type ConfigType struct {
    Import []string
    Export string
}

type dataType struct {
    Photos Photos
    Times map[int]map[time.Month]map[int]int
}

type Photo struct {
    Path string
    Date time.Time
    Groupl int
    Holiday string
    Gps gpsType
    // contrast
    // color
}

type gpsType struct {
    Lat, Lng float64
}

type Photos []Photo
func (slice Photos) Len() int {
    return len(slice)
}
func (slice Photos) Less(i, j int) bool {
    return slice[i].Date.Before(slice[j].Date)
}
func (slice Photos) Swap(i, j int) {
    slice[i], slice[j] = slice[j], slice[i]
}
func (slice Photos) Search(p Photo) int {
    return sort.Search(slice.Len(), func(i int) bool {
        return !slice[i].Date.Before(p.Date)
    })
}

func InsertPhoto(p Photo) int {
    i := data.Photos.Search(p)
    if (i < data.Photos.Len() && i >= 0) && data.Photos[i].Path == p.Path {
        panic(fmt.Sprintf("inserting duplicate: \n    %v\n    %v", p.Path, data.Photos[i].Path))
    }
    data.Photos = append(data.Photos, p) // increase capacity by one
    copy(data.Photos[i+1:], data.Photos[i:]) // shift latter part of array over
    data.Photos[i] = p // insert new value
    return i
}

func init() {
    flag.StringVar(&ConfigPath, "config", os.Getenv("HOME") + "/.gophotoconfig", "Optional path to Config file.")
}

func main() {
    flag.Parse()
    ConfigFile, err := os.Open(ConfigPath)
    defer ConfigFile.Close()
    if err != nil {
        fmt.Println("Couldn't open Config file:", err)
        os.Exit(1)
    }
    decoder := json.NewDecoder(ConfigFile)
    Config = &ConfigType{}
    err = decoder.Decode(&Config)
    if err != nil {
        fmt.Println("Error parsing Config file:", err)
        os.Exit(1)
    }

    imgExts = []string{".jpg", ".jpeg", ".tiff", ".tif", ".gif", ".png", ".JPG"}
    vidExts = []string{".mov", ".m4v", ".3gp"}
    allExts = append(imgExts, vidExts...)

    data.Times = make(map[int]map[time.Month]map[int]int)

    err = os.MkdirAll(Config.Export, 0744)
    if err != nil {
        fmt.Println(err)
        panic(err)
    }
    err = filepath.Walk(Config.Export, gatherInfo)
    if err != nil {
        fmt.Println("[Error]", err)
        os.Exit(1)
    }

    watcher, err := fsnotify.NewWatcher()
    if err != nil {
        fmt.Println(err)
        return
    }

    wait, _ := time.ParseDuration("0.5s")
    done := make(chan bool)
    go func() {
        for {
            select {
                case ev := <-watcher.Event:
                    //fmt.Println(ev)
                    if ev.IsCreate() || ev.IsModify() {
                        var f os.FileInfo
                        f, err = os.Stat(ev.Name)
                        if err == nil {
                            for {
                                f, err = os.Stat(ev.Name)
                                if err != nil {
                                    fmt.Println(err)
                                    break
                                }
                                if f.Size() != 0 {
                                    break
                                }
                            }
                            time.Sleep(wait)

                            if f.IsDir() {
                                fmt.Println("Directories not supported.")
                                err = filepath.Walk(ev.Name, gatherInfo)
                                if err != nil {
                                    fmt.Println("[Error]", err)
                                    os.Exit(1)
                                }
                            } else {
                                ProcessFile(ev.Name, f)
                            }
                        } else if !os.IsNotExist(err) {
                            fmt.Println(err)
                        }
                    }
                case err := <-watcher.Error:
                    fmt.Println("error:", err)
                    return
            }
        }
    }()

    for _, importFolder := range Config.Import {
        if _, err := os.Stat(importFolder); os.IsNotExist(err) {
            fmt.Println("import folder doesn't exist:", importFolder)
        } else if err == nil {
            err = filepath.Walk(importFolder, gatherInfo)
            if err != nil {
                fmt.Println("[Error]", err)
                os.Exit(1)
            }

            err = watcher.Watch(importFolder)
            if err != nil {
                fmt.Println("error:", err)
                return
            }
        } else {
            fmt.Println("error:", err)
        }
    }
    <-done

    watcher.Close()
}

func gatherInfo(path string, f os.FileInfo, err error) (e error) {
    e = ProcessFile(path, f)
    return
}

func ProcessFile(path string, f os.FileInfo) (e error) {
    if f.Mode().IsRegular(); strIn(filepath.Ext(path), allExts) {
        var (
            date time.Time
            gps bool = false
            lat, lng float64 = 0, 0
        )
        defer func() {
            if r := recover(); r != nil {
                fmt.Printf("recovered from panic: %v, at: %v", r, path)
            } else if e == nil {
                pa, err := filepath.Abs(path)
                if err == nil {
                    err = AddPhoto(date, pa, gps, lat, lng)
                    if err != nil {
                        fmt.Println(err)
                    }
                } else {
                    fmt.Println(err)
                }
            }
        }()

        f, err := os.Open(path)
        defer f.Close()
        if err != nil {
            return fmt.Errorf("opening %v: %v", path, err)
        }

        // TODO: check if ext is vid
        if x, err := exif.Decode(f); err == nil {
            if gpsv, err := x.Get(exif.GPSVersionID); err == nil && bytes.Equal(gpsv.Val, []byte{2, 2, 0}) {
                latr, _ := x.Get(exif.GPSLatitudeRef)
                latd, _ := x.Get(exif.GPSLatitude)
                lngr, _ := x.Get(exif.GPSLongitudeRef)
                lngd, _ := x.Get(exif.GPSLongitude)

                lat = gpsUtilVal(latd.Val[0:8]) + gpsUtilVal(latd.Val[8:16])/60 + gpsUtilVal(latd.Val[16:24])/3600
                lng = gpsUtilVal(lngd.Val[0:8]) + gpsUtilVal(lngd.Val[8:16])/60 + gpsUtilVal(lngd.Val[16:24])/3600

                if fmt.Sprint(latr.Val) == "S" {
                    lat = -lat
                }
                if fmt.Sprint(lngr.Val) == "W" {
                    lng = -lng
                }
            }
            if d, err := x.Get(exif.DateTimeOriginal); err == nil {
                if date, err = time.Parse("2006:01:02 15:04:05", d.StringVal()); err == nil {
                    return nil
                }
            }
        }

        s, err := f.Stat()
        if err != nil {
            return fmt.Errorf("couldn't get date for %v: %v", path, err)
        }
        date = s.ModTime()
    }
    return nil
}
func gpsUtilVal(in []byte) float64 {
    n := int(in[3]) + int(in[2])*256 // may need to add more stuff here
    d := int(in[7]) + int(in[6])*256

    return float64(n) / float64(d)
}

func AddPhoto(date time.Time, path string, gps bool, lat, lng float64) error {
    h, err := GetHoliday(date)
    if err != nil {
        return err
    }

    var g gpsType;
    if gps {
        g.Lat = lat
        g.Lng = lng
    }
    photo := Photo{
        Date:date,
        Path:path,
        Holiday:h,
        Gps:g,
    }

    y := date.Year()
    m := date.Month()
    d := date.Day()
    if _, ok := data.Times[y]; !ok {
        data.Times[y] = make(map[time.Month]map[int]int)
    }
    if _, ok := data.Times[y][m]; !ok {
        data.Times[y][m] = make(map[int]int)
    }
    if _, ok := data.Times[y][m][d]; !ok {
        data.Times[y][m][d] = 0
    }
    data.Times[y][m][d]++

    loc := InsertPhoto(photo)
    if loc < 0 {
        return errors.New("invalid insert")
    }

    if err := GroupPhoto(loc); err != nil {
        return errors.New("addphoto: " + err.Error())
    }
    return nil
}

func GroupPhoto(loc int) error {
    var p, n int
    date := data.Photos[loc].Date
    y := date.Year()
    m := date.Month()
    d := date.Day()
    if v, ok := data.Times[y][m][d]; ok {
        if v > 3 {
            days := make(map[int]bool)
            days[d] = true
            for i := d - 1; i > 0; i-- {
                if v2, ok := data.Times[y][m][i]; !ok || v2 < 4 {
                    break
                }
                days[i] = true
            }
            for i := d + 1; i <= 31; i++ {
                if v2, ok := data.Times[y][m][i]; !ok || v2 < 4 {
                    break
                }
                days[i] = true
            }

            for p = loc - 1; p > 0; p-- {
                if v, ok := days[data.Photos[p].Date.Day()]; !ok || !v {
                    p++
                    break
                }
            }
            if p == -1 { p++ }
            l := len(data.Photos)
            for n = loc + 1; n < l; n++ {
                if v, ok := days[data.Photos[n].Date.Day()]; !ok || !v {
                    n--
                    break
                }
            }
            if n == l { n-- }

            if err := MovePhotos(loc, p, n); err != nil {
                return errors.New("groupphoto: " + err.Error())
            }
        } else {
            return MovePhotos(loc, loc, loc)
        }
    } else {
        return fmt.Errorf("no day found: %v", date)
    }
    return nil
}

func MovePhotos(l, p, n int) error {
    if l > n || l < p {
        return errors.New("l not in p to n")
    }
    d := data.Photos[l].Date
    dir, err := filepath.Abs(filepath.Join(Config.Export, fmt.Sprintf("%d", d.Year()), fmt.Sprintf("%d-%s", d.Month(), d.Month().String())))
    if err != nil {
        return errors.New("movephotos: " + err.Error())
    }
    if n - p >= 3 {
        var event string
        fDay := data.Photos[p].Date.Day()
        lDay := data.Photos[n].Date.Day()
        if lDay == fDay {
            event = fmt.Sprintf("%d", lDay)
        } else {
            event = fmt.Sprintf("%d-%d", fDay, lDay)
        }
        for i := p; i <= n; i++ {
            if data.Photos[i].Holiday != "" {
                event = event + "--" + data.Photos[i].Holiday
                break
            }
        }
        dir = filepath.Join(dir, event)
    }
    for i := p; i <= n; i++ {
        path := data.Photos[i].Path
        tmpDir := filepath.Join(dir, filepath.Base(path))
        if tmpDir != path {
            err = os.MkdirAll(filepath.Dir(tmpDir), 0744)
            if err != nil {
                return errors.New("movephotos: mkdir: " + err.Error())
            }
            if _, err := os.Stat(path); err == nil {
                count := 1
                loop:
                if _, err := os.Stat(tmpDir); os.IsNotExist(err) {
                    err = os.Rename(path, tmpDir)
                    if err != nil {
                        panic(err)
                    }
                    data.Photos[i].Path = tmpDir
                } else {
                    ext := filepath.Ext(tmpDir)
                    tmpDir = fmt.Sprintf("%v-%d%v", tmpDir[:len(tmpDir) - len(ext)], count, ext)
                    count++
                    goto loop
                }
            }

            var rmDir = filepath.Dir(path)
            fs, err := ioutil.ReadDir(rmDir)
            if err == nil {
                for len(fs) == 0 {
                    os.Remove(rmDir)
                    rmDir = filepath.Dir(rmDir)
                    fs, err = ioutil.ReadDir(rmDir)
                    if err != nil {
                        break
                    }
                }
            }
        }
    }
    return nil
}

func strIn(a string, list []string) bool {
    for _, b := range list {
        if b == a {
            return true
        }
    }
    return false
}
