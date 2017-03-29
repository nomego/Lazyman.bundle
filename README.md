# Lazyman.bundle
Lazyman Plex Channel to access Lazyman streams along with recaps and extended highlights.

## Streaming and transcoding
As far as I gather, the Plex Media Server where the plug-in is installed need to be powerful enough to transcode the HLS (HTTP Live Streaming) streams.
It might work with a transcoding client such as Plex Media Player or OpenPHT on a computer, not verified.
Installing the plug-in on a weaker NAS and using a limited client will not work.

### Recaps and highlights
Recaps and highlights are not part of the Lazyman solution but is offered in the same NHL API and are added for convenience. These are MP4 files and not streams so they should generally work better on most devices. They will also work (or not work) without `/etc/hosts` changes.

## Installation
1. [Setup the /etc/hosts file with the Lazyman configuration](https://www.reddit.com/r/nhl_games/comments/5ur6yp/psa_if_the_app_didnt_modify_your_hosts_file/) on the machine running Plex Media Server
2. [Find your Plex Media Server Plug-in directory](https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder-)
3. [Install git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
4. In the Plug-in folder, clone the repo (install the plugin): `git clone https://github.com/nomego/Lazyman.bundle`

## Updating
1. Enter the `Lazyman.bundle` folder in your Plug-in folder and run `git pull`

## Setups
### Working
* Web client
* Android app
* Casting from the Android app to Chromecast
* Plex Media Player on macOS
* OpenPHT (unspecified)
* Playstation 4 app
  * Direct Play / Direct Stream needs to be turned off in settings (Thanks Sinematikz)
* Roku (unconfirmed)
  * Plex app can only play recaps/highlights
  * Roku Media Player can only play streams (replays, live) (Thanks Sinematikz)
