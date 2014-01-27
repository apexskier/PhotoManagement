package main

import (
    "os"
    "fmt"
    "time"
    "github.com/rwcarlsen/goexif/exif"
    // "path"
    "path/filepath"
)

func main() {
    in_folder := "Import"
    //export_folder := "Photos"

    img_exts := []string{".jpg", ".jpeg", ".tiff", ".tif", ".gif", ".png"}
    //vid_exts := []string{".mov", ".m4v", ".3gp"}
    //all_exts := append(img_exts, vid_exts...)

    cwd, _ := os.Getwd()
    fmt.Println(cwd)

    err := filepath.Walk(in_folder, func(f_path string, f os.FileInfo, _ error) error {
        if f.Mode().IsRegular(); strIn(filepath.Ext(f_path), img_exts) {
            f, err := os.Open(f_path)
            var date time.Time
            if err != nil {
                fmt.Printf("[Error] Opening %v.\n", f_path)
                return nil
            }
            x, err := exif.Decode(f)
            defer f.Close()
            if err != nil {
                goto L
            } else {
                d, err := x.Get(exif.DateTimeOriginal)
                if err != nil {
                    fmt.Printf("[Error] Error getting date for %v.\n", f_path)
                    goto L
                }
                date, err = time.Parse("2006:01:02 15:04:05", d.StringVal())
                if err != nil {
                    fmt.Printf("[Error] Parsing date for %v.\n", f_path)
                }
                fmt.Printf("%s: %v\n", f_path, date)
            }
            return nil

            L:
            s, err := f.Stat()
            date = s.ModTime()
            if err != nil {
                fmt.Printf("[Error] Error getting date for %v.\n", f_path)
                return nil
            }
            fmt.Printf("%s: %s\n", f_path, date)
        }
        return nil
    })
    if err != nil {
        fmt.Println("[Error] Walking through import folder.")
        os.Exit(1)
    }
}

func DoFolder(dir string, action func) {
    fmt.Println("Testing")
}

func strIn(a string, list []string) bool {
    for _, b := range list {
        if b == a {
            return true
        }
    }
    return false
}
