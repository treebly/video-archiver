# Video Archiver
A python script for building your own personal little archive of internet videos, built on the back of ~~youtube-dl~~ yt-dlp. Designed for YouTube, but should work with any popular video sharing site.

## Dependencies
- Python 3 with the following packages
	- yt-dlp
	- click
	- requests
- ffmpeg
- Pushover (optional)

## Usage
### Downloading
The main script is `archive.py`. In it's simplest form, you can download a new video just by passing the URL as an argument:
```sh
./archive.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
```
This will download the video and place it in a directory called `Archives` wherever you run the script from. Information about the download will be logged to `archive.log`. A text file called `download archive.txt` will also be created, which will prevent the video from being downloaded again.

You can also pass a URL to a playlist or youtube channel:
```sh
./archive.py https://www.youtube.com/playlist?list=PLqs5ohhass_RugObMuXClrZh7dP0g4e5l
./archive.py https://www.youtube.com/@videogamedunkey/videos
```
Note that omitting the `/videos` from a channel URL can cause unexpected results.

The archiver can also take a file containing a list of URLs using the `-f` option:

```sh
./archive.py -f channels.txt
```
This file should have one link per line. You can specify a limit to the number of videos to get after each link, separated by a semicolon. For more advanced filtering, you can also specify specific yt-dlp options, separated by two colons. Lines starting with a `#` are ignored.
```
# Example channels.txt
https://www.youtube.com/user/freddiew/videos;5
https://www.youtube.com/user/marcrebillet/videos;5::{"match_filter":"duration < 1800"}
```

### Path Options
By default, the script uses a temporary directory `downloads` to download videos, and then moves them to the `Archives` directory. If you would like to customize this behaviour, you can pass a different downloads directory with `-o`, a different archives directory with `-a`, or have files remain in the downloads directory with `-k`.
```
./archive.py -f channels.txt -o "temporary" -a "My Archives"
./archive.py -f channels.txt -k -o "~/Downloads"
```

### Notifications
The script can optionally notify you using [Pushover](https://pushover.net) when it has completed an update. To enable this functionality:
1. Create a Pushover account
1. Generate a Pushover application token
1. Set the `PUSHOVER_USER` environment variable to your user token
1. set the `PUSHOVER_TOKEN` environment variable to your new application API token

Now when the script is run, it will send a summary of its work and any errors it encounters. Passing the `-n` flag to the script will send notifications for each video that is downloaded, rather than one notification for the whole run.

### More
All the options that the script supports can be seen by running:
```
./archive.py --help
```
For more details on how I run my setup, check out my [blog post](https://treeb.net/2022/12/17/youtube-archiver).

## Add-ons
Included along with the script are two additional components that I find useful.

`Archives.hazelrules` is a pair of rules for the excellent Mac utility [Hazel](https://www.noodlesoft.com) that I use for keeping my `Archives` directory organized.

`oneoffs.sh` is a shell script that enables me to automatically download videos that I save to my watch later list in the app [Play](https://apps.apple.com/us/app/play-save-videos-watch-later/id1596506190). When run, it saves the IDs of any videos that are tagged with `Download`, downloads them, and then removes them from the watch later queue. To interface with Play it relies on two Shortcuts, which you can get here:
- [Get Download IDs](https://www.icloud.com/shortcuts/90914ac81a554ec682077cf298375954)
- [Clear Download IDs](https://www.icloud.com/shortcuts/88565a9fda414493a0470ee9eb2e9d8c)
You'll need to pass a temporary file path to the script, and configure the first shortcut to use that same path.