# Lazyman.bundle
Lazyman Plex Channel to access Lazyman streams along with recaps and extended highlights.

## Streaming and transcoding
As far as I gather, the Plex Media Server where the plug-in is installed need to be powerful enough to transcode the HLS (HTTP Live Streaming) streams.
It might work with a transcoding client such as Plex Media Player or OpenPHT on a computer, not verified.
Installing the plug-in on a weaker NAS and using a limited client will not work.

## Installation
1. [Setup the /etc/hosts file with the Lazyman configuration](https://www.reddit.com/r/nhl_games/comments/5ur6yp/psa_if_the_app_didnt_modify_your_hosts_file/) on the machine running Plex Media Server
2. [Find your Plex Media Server Plug-in directory](https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder-)
3. [Install git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
4. In the Plug-in folder, clone the repo (install the plugin): `git clone https://github.com/nomego/Lazyman.bundle`

## Updating
1. Enter the Lazyman.bundle folder in your Plug-in folder and run `git pull`

## Setups
### Working
* Web client
* Android client/app
* Casting fro the Android app to Chromecast

### Not working
* Roku (according to Reddit)
* Playstation 4 app (EU version at least)
