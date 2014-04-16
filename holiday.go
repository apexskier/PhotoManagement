package main

import (
    "fmt"
    "time"
    "regexp"
    "strconv"
)

var (
    format = "2-Jan-2006"
    Events map[string][2]string = make(map[string][2]string)
    EventRe1 *regexp.Regexp = regexp.MustCompile(`(\d{1,2})-(\d{1,2})`)
    EventRe2 *regexp.Regexp = regexp.MustCompile(`(\d{1,2})(Mon|Tue|Wed|Thu|Fri|Sat|Sun)-(\d{1,2})`)
    Birthdays map[time.Time]string = make(map[time.Time]string)
)

func init() {
    Events["1-1"] = [2]string{"New Year's", ""}
    Events["14-2"] = [2]string{"Valentine's Day", ""}
    Events["3Mon-2"] = [2]string{"Presidents' Day", "Weekend"}
    Events["17-3"] = [2]string{"St. Patrick's Day", ""}
    Events["2Sun-5"] = [2]string{"Mothers' Day", ""}
    Events["3Sun-6"] = [2]string{"Father's Day", ""}
    Events["4-7"] = [2]string{"Fourth of July", "Weekend"}
    Events["1Mon-9"] = [2]string{"Labor Day", "Weekend"}
    Events["31-10"] = [2]string{"Halloween", ""}
    Events["11-11"] = [2]string{"Veterans Day", "Weekend"}
    Events["4Thu-11"] = [2]string{"Thanksgiving", "Break"}
    Events["24-12"] = [2]string{"Christmas Eve", ""}
    Events["25-12"] = [2]string{"Christmas", ""}
    Events["31-12"] = [2]string{"New Year's Eve", ""}
    Events["3-9"] = [2]string{"test event", ""}

    t, err := time.Parse(format, "16-Jul-1992")
    if err != nil { panic(err) }
    Birthdays[t] = "Cameron and Emily"
    t, err = time.Parse(format, "04-Sep-1992")
    if err != nil { panic(err) }
    Birthdays[t] = "Jake"
    t, err = time.Parse(format, "12-Sep-1992")
    if err != nil { panic(err) }
    Birthdays[t] = "Aisha"
}

func GetHoliday(date time.Time) (string, error) {
    y := date.Year()
    m := date.Month()
    sm := fmt.Sprintf("%d", m)
    d := date.Day()
    sd := fmt.Sprintf("%d", d)
    wd := date.Weekday().String()[:3]
    for k, v := range Birthdays {
        if k.Month() == m && k.Day() == d {
            return fmt.Sprintf("%v's Birthday", v), nil
        }
    }
    for k, v := range Events {
        if match := EventRe1.FindStringSubmatch(k); match != nil && match[1] == sd && match[2] == sm {
            // 14-3 type
            fmt.Println("event found:", v[0]);
            return v[0], nil
        } else if match := EventRe2.FindStringSubmatch(k); match != nil && match[3] == sm && match[2] == wd {
            // 2Mon-1 type
            prday := time.Date(y, m, 1, 0, 0, 0, 0, nil)
            weeks, err := strconv.Atoi(match[1])
            if err != nil {
                return "", fmt.Errorf("getHoliday: %v", err)
            }
            adj, err := time.ParseDuration(string((int(date.Weekday() - prday.Weekday()) % 7) + (7 * weeks)) + "h")
            if err != nil {
                return "", fmt.Errorf("getHoliday: %v", err)
            }
            prday = prday.Add(adj)
            if prday.Day() == d && prday.Month() == m {
                return v[0], nil
            }
        }
    }
    return "", nil
}
