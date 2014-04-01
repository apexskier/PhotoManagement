package main

import (
    "os"
    "fmt"
    "time"
    "errors"
    "path/filepath"
    "io/ioutil"

    "github.com/rwcarlsen/goexif/exif"
    "code.google.com/p/go.exp/fsnotify"
)

var (
    imgExts []string
    data dataType
    baseTime time.Time = time.Now()
    importFolder string
    exportFolder string
    maxK = 8
)

type dataType struct {
    Photos Photos
    Groups Nodes
    MinGroups Nodes
}

type Node struct {
    First int
    Last int
    Groups Nodes
    Granularity time.Duration
    Parent *Node
}

type Nodes []*Node

type Photo struct {
    Path string
    Date time.Time
    Groupl int
    // contrast
    // color
}

type Photos []Photo

func main() {
    importFolder = "Import"
    exportFolder = "Photos"
    err := os.MkdirAll(exportFolder, 0744)
    if err != nil {
        fmt.Println(err)
        panic(err)
    }

    imgExts = []string{".jpg", ".jpeg", ".tiff", ".tif", ".gif", ".png"}
    //vidExts := []string{".mov", ".m4v", ".3gp"}
    //allExts := append(imgExts, vidExts...)

    cwd, _ := os.Getwd()
    fmt.Println(cwd)

    err = filepath.Walk(exportFolder, gatherInfo)
    if err != nil {
        fmt.Println("[Error]", err)
        os.Exit(1)
    }
    err = filepath.Walk(importFolder, gatherInfo)
    if err != nil {
        fmt.Println("[Error]", err)
        os.Exit(1)
    }

    watcher, err := fsnotify.NewWatcher()
    if err != nil {
        fmt.Println(err)
        return
    }

    done := make(chan bool)
    go func() {
        for {
            select {
                case ev := <-watcher.Event:
                    if ev.IsCreate() {
                        fmt.Println("event:", ev)
                        f, err := os.Stat(ev.Name)
                        if err != nil {
                            fmt.Println(err)
                            break
                        }
                        if f.IsDir() {
                            err = filepath.Walk(ev.Name, gatherInfo)
                            if err != nil {
                                fmt.Println("[Error]", err)
                                os.Exit(1)
                            }
                        } else {
                            ProcessFile(ev.Name, f)
                        }
                    }
                case err := <- watcher.Error:
                    fmt.Println("error:", err)
                    return
            }
        }
    }()

    err = watcher.Watch(importFolder)
    if err != nil {
        fmt.Println("error:", err)
        return
    }
    <-done

    watcher.Close()
}

func gatherInfo(path string, f os.FileInfo, err error) (e error) {
    e = ProcessFile(path, f)
    return
}

func ProcessFile(path string, f os.FileInfo) (e error) {
    if f.Mode().IsRegular(); strIn(filepath.Ext(path), imgExts) {
        var date time.Time
        defer func() {
            if e == nil {
                pa, err := filepath.Abs(path)
                if err == nil {
                    err = AddPhoto(date, pa)
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

        if x, err := exif.Decode(f); err == nil {
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

func AddPhoto(date time.Time, path string) error {
    photo := Photo{
        Date:date,
        Path:path,
    }

    savedPhotos := len(data.Photos)
    loc := InsertPhoto(photo)
    if len(data.Photos) == savedPhotos {
        panic(fmt.Sprintf("%d, %v", loc, "Same photos"))
    }
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
    for p = loc; p > 0; p-- {
        if data.Photos[p].Date.Sub(data.Photos[p-1].Date).Hours() >= 18 {
            break
        }
    }
    for n = loc; n < len(data.Photos)-1; n++ {
        if data.Photos[n+1].Date.Sub(data.Photos[n].Date).Hours() >= 18 {
            break
        }
    }

    if err := MovePhotos(loc, p, n); err != nil {
        return errors.New("groupphoto: " + err.Error())
    }
    return nil
}

// binary search to insert
/*
func (gs *Nodes) InsertGroup(g *Node) int {
    l := len(*gs)
    if l == 0 {
        *gs = Nodes{g}
        return 0
    }
    return gs.insertGroup(g, 0, l)
}
func (gs *Nodes) insertGroup(g *Node, s, e int) int {
    if s > e {
        return -1
    }
    if s + 1 == e {
        if s == 0 {
            *gs = append(Nodes{g}, *gs...)
            return 0
        } else if e == len(*gs) {
            *gs = append(*gs, g)
            return e
        } else {
            *gs = append(append((*gs)[:s], g), (*gs)[e:]...)
            return s + 1
        }
    }
    m := (s+e) / 2
    if g.Last < (*gs)[m].First {
        return gs.insertGroup(g, s, m)
    } else {
        return gs.insertGroup(g, m, e)
    }
    return -1
}*/

func MovePhotos(l, p, n int) error {
    if l > n || l < p {
        return errors.New("l not in p to n")
    }
    d := data.Photos[l].Date
    dir, err := filepath.Abs(filepath.Join(exportFolder, fmt.Sprintf("%d", d.Year()), fmt.Sprintf("%d-%s", d.Month(), d.Month().String())))
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
                err = os.Rename(path, tmpDir)
                if err != nil {
                    fmt.Printf("%v\n%v\n", path, tmpDir)
                    fmt.Println(tmpDir == path)
                    panic(err)
                }
                data.Photos[i].Path = tmpDir
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

// binary search to insert
func InsertPhoto(p Photo) int {
    l := len(data.Photos)
    if l == 0 {
        data.Photos = Photos{p}
        return 0
    }
    r := insertPhoto(p, 0, l)
    if l == len(data.Photos) {
        panic(fmt.Sprintf("Photo not added! r = %d, len = %d, \n  photo = %v, \n  photo2 = %v", r, l, p, data.Photos[r-1]))
    }
    return r
}
func insertPhoto(p Photo, s, e int) int {
    if s > e {
        return -1
    }
    if s + 1 == e {
        if s == 0 {
            data.Photos = append(Photos{p}, data.Photos...)
            return 0
        } else if e == len(data.Photos) {
            data.Photos = append(data.Photos, p)
            return e
        } else {
            data.Photos = append(append(data.Photos[:s], p), data.Photos[s:]...)
            return s + 1
        }
    }
    m := (s+e) / 2
    if p.Date.Before(data.Photos[m].Date) {
        return insertPhoto(p, s, m)
    } else {
        return insertPhoto(p, m, e)
    }
    return -1
}

func strIn(a string, list []string) bool {
    for _, b := range list {
        if b == a {
            return true
        }
    }
    return false
}
