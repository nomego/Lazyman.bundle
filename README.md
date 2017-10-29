# Lazyman.bundle
Lazyman Plex Channel to access Lazyman streams along with recaps and extended highlights.


## Streaming and Transcoding
As far as I gather, the Plex Media Server where the plug-in is installed need to be powerful enough to transcode the HLS (HTTP Live Streaming) streams.
It might work with a transcoding client such as Plex Media Player or OpenPHT on a computer, not verified.
Installing the plug-in on a weaker NAS and using a limited client will not work.

### Recaps and Highlights
Recaps and highlights are not part of the Lazyman solution but is offered in the same NHL API and are added for convenience. These are MP4 files and not streams so they should generally work better on most devices. They will also work (or not work) without changes to your `hosts` file.


## Prerequisites
### Modify hosts file
 * Modify your `hosts` file to work with Lazyman on the machine running Plex Media Server:
   * *The location of this file and how you modify it can vary depending on OS. Please see [this page](https://www.siteground.com/kb/how_to_use_the_hosts_file/) for relevant instructions to most systems.
 1. From a command prompt or terminal window, type `ping zipstreams.net` and note the IP address supplied in the output.
 2. Locate and modify the hosts file for your OS to include the following two lines:
 ```
 x.x.x.x mf.svc.nhl.com
 x.x.x.x mlb-ws-mf.media.mlb.com
 ```
 *Where x.x.x.x is the IP address noted from step 1.*


## Installation
### Unsupported AppStore Method
*If you already have WebTools/UAS installed, skip to step 2.*
1. Install the [WebTools](https://github.com/ukdtom/WebTools.bundle/wiki/V2Home) PMS Plug-in.
2. Connect to the WebTools interface, sign in, and navigate to the Unsupported AppStore module.
3. Click the **Video** tab and locate the LazyMan entry (Note: you can also search for 'lazyman' using the search box).
4. On the LazyMan entry, click **Install**.  
*Note: If the above steps don't help to locate the plugin, you can also copy this repo URL and paste into the GitHub installer section.*
### Manual Method
1. [Find your Plex Media Server Plug-in directory](https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder-)
2. [Install git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
3. In the Plug-in folder, clone the repo (install the plugin): `git clone https://github.com/nomego/Lazyman.bundle`


## Updating
### Unsupported AppStore Method
1. Connect to the WebTools interface, sign in, and navigate to the Unsupported AppStore module.
2. Click the **Video** tab and locate the LazyMan entry (Note: you can also search for 'lazyman' using the search box).
3. On the LazyMan entry, click **Re-Install with latest available**.
### Manual Method
1. Enter the `Lazyman.bundle` folder in your Plug-in folder and run `git pull`


## Clients
### Working
* Web client
* Android app
* Casting from the Android/iOS app to Chromecast
* Plex Media Player on macOS
* OpenPHT (unspecified)
* Playstation 4 app
  * Direct Play / Direct Stream needs to be turned off in settings (Thanks Sinematikz)
* Roku (unconfirmed)
  * Plex app can only play recaps/highlights
  * Roku Media Player can only play streams (replays, live) (Thanks Sinematikz)
### Non-Working
* iOS app
  * Workaround: Copy and modify the iOS.xml profile to your Plex data directory to disable Direct Play of HTTPS Live Streaming content.
  * *Note: This should also work for the tvOS.xml profile.*
 1. Locate the iOS.xml file in the Plex install directory (note this location for later).
 2. Locate your Plex [data directory](https://support.plex.tv/hc/en-us/articles/202915258-Where-is-the-Plex-Media-Server-data-directory-located-) and create a new folder called **Profiles**.
 3. Copy the iOS.xml file (from the directory noted in step 1) to the newly created **Profiles** folder.
 4. Modify the iOS.xml file and ensure the following lines are commented out (top line is already a comment, use the `<!--` and `-->` notation on the next line to match). Your file should have two lines that look like this:  
```
<!-- Allow Direct Play of HLS content  -->
<!-- <VideoProfile protocol="hls" container="mpegts" codec="h264" audioCodec="aac" /> -->
```
 5. Save the file and restart PMS.
