import datetime
import random
import re

from game import Game

GAME_SCHEDULE_URL = "http://statsapi.web.nhl.com/api/v1/schedule?startDate=%s&endDate=%s&expand=schedule.teams,schedule.linescore,schedule.broadcasts.all,schedule.ticket,schedule.game.content.media.epg"

ART = 'nhlbg.jpg'
THUMB = 'nhl_logo.png'
ICON = 'LM.png'

DAYS_TO_SHOW = 10
PAGE_LIMIT = 100
NAME = 'Lazyman'

GAME_CACHE = {}
STREAM_CACHE = {}

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME
	ObjectContainer.art = R(ART)
	DirectoryObject.art = R(ART)
	DirectoryObject.thumb = R(THUMB)
	VideoClipObject.art = R(ART)
	VideoClipObject.thumb = R(THUMB)

	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.117 Safari/537.36'
	HTTP.CacheTime = 0

####################################################################################################
@handler('/video/lazyman', NAME, art=ART, thumb=ICON)
def MainMenu():

	oc = ObjectContainer()
	time_delta = datetime.timedelta(days=1)
	date = datetime.date.today()

	for i in range(DAYS_TO_SHOW):
		oc.add(DirectoryObject(
			key=Callback(Date, date=date),
			title=date.strftime("%d %B %Y"))
		)
		date = date - time_delta

	return oc 

####################################################################################################
@route('/video/lazyman/date')
def Date(date):

	oc = ObjectContainer(title2="Games on %s" % (date), no_cache=True)
	game_cache = GetCache(date, True)
	for g in game_cache: 
		oc.add(DirectoryObject(
			key=Callback(Feeds, date=date, game_id=g.game_id),
			title=g.title,
			summary=g.summary)
		)
	return oc

def GetCache(date, refresh=False):
    if refresh or date not in GAME_CACHE:
        scheduleUrl = GAME_SCHEDULE_URL % (date, date)
        schedule = JSON.ObjectFromURL(scheduleUrl)
        GAME_CACHE[date] = Game.fromSchedule(schedule)
    return GAME_CACHE[date]  

def getRecapVCO(date, type, recap):
	def getRecapItems(videos):
		objects = []
		for video in videos:
			bitrate = int(video["name"].split("_")[1][0:-1])
			height = int(video["height"])
			objects.insert(0, MediaObject(
				container = Container.MP4,
				video_codec = VideoCodec.H264,
				audio_codec = AudioCodec.AAC,
				video_resolution = height,
				audio_channels = 2,
				height = height,
				width = int(video["width"]),
				parts = [
					PartObject(key=Callback(PlayRecap, url=video["url"]))
				]
			))
		return objects

	return VideoClipObject(
		key = Callback(RecapMetadata, type=type, date=date, recapid=recap.rid),
		rating_key = recap.rid,
		title = recap.title,
		summary = recap.summary,
		studio = recap.studio,
		year = recap.year,
		tagline = recap.tagline,
		duration = recap.duration,
		art = recap.image_url,
		thumb = recap.image_url,
		items = getRecapItems(recap.videos)
	)

def getStreamVCO(date, game, feed):
	def getStreamItems():
		if STREAM_CACHE.get(game.game_id) == None:
			STREAM_CACHE[game.game_id] = {}
		if STREAM_CACHE[game.game_id].get(feed.mediaId) != None:
			return STREAM_CACHE[game.game_id][feed.mediaId]
		
		cdn = 'akc'
		url = "http://mf.svc.nhl.com/m3u8/%s/%s" % (date, feed.mediaId)
		try:
			real_url = HTTP.Request(url + cdn).content
		except:
			return []

		info_pattern = re.compile('EXT-X-STREAM-INF:BANDWIDTH=(\d+),RESOLUTION=(\d+)x(\d+),CODECS=".+"')
		streams = HTTP.Request(real_url).content.split("#")
		objects = []

		for stream in streams:
			if stream.strip() == "EXTM3U" or stream == "":
				continue
			info, url_end = stream.splitlines()
			stream_meta = info_pattern.search(info)
			if stream_meta == None:
				continue
			bw, width_s, height_s = stream_meta.groups()
			res_url = real_url.rsplit('/', 1)[0] + "/" + url_end
			objects.append(
				MediaObject(
					protocol = 'hls',
					video_codec = VideoCodec.H264,
					video_frame_rate = 30,
					audio_codec = AudioCodec.AAC,
					video_resolution = height_s,
					audio_channels = 2,
					optimized_for_streaming = True,
					parts = [
						PartObject(key = HTTPLiveStreamURL(Callback(PlayStream, url=res_url)))
					]
				)
			)

		STREAM_CACHE[game.game_id][feed.mediaId] = objects
		return objects

	return VideoClipObject(
		key = Callback(StreamMetadata, date=date, gameid=game.game_id, mediaId=feed.mediaId),
		rating_key = feed.mediaId,
		title = feed.title,
		summary = game.summary,
		studio = "NHL",
		year = int(date[0:4]),
		art = R(ART),
		thumb = R(THUMB),
		items = getStreamItems()
	)

@route('/video/lazyman/feeds')
def Feeds(date, game_id):
	game = None
	game_cache = GetCache(date)
	for g in game_cache:
		if str(g.game_id) == str(game_id):
			game = g
			break

	oc = ObjectContainer(title2="Feeds for %s" % g.title, no_cache=True)

	for f in filter(lambda f: f.viewable, game.feeds):
		oc.add(getStreamVCO(date, game, f))

	for r in game.recaps:
		if r.videos == None:
			continue
		oc.add(getRecapVCO(date, "recaps", r))

	for r in game.extended_highlights:
		if r.videos == None:
			continue
		oc.add(getRecapVCO(date, "extended_highlights", r))

	return oc

def StreamMetadata(date, gameid, mediaId, **kwargs):
	game = None
	feed = None
	game_cache = GetCache(date)
	for g in game_cache:
		if str(g.game_id) == str(gameid):
			game = g
			for feed in game.feeds:
				if feed.mediaId == mediaId:
					feed = feed
					break
		if game != None:
			break

	oc = ObjectContainer()
	oc.add(getStreamVCO(date, game, feed))
	return oc

def RecapMetadata(type, date, recapid):
	game_cache = GetCache(date)
	recap = None
	for g in game_cache:
		for r in g.getRecaps(type):
			if r.rid == recapid:
				recap = r				
				break
		if recap != None:
			break

	oc = ObjectContainer()
	oc.add(getRecapVCO(date, type, recap))
	return oc

@indirect
def PlayRecap(url, **kwargs):
	Log(' --> Final recap_url: %s' % (url))
	return IndirectResponse(VideoClipObject, key=url)

@indirect
def PlayStream(url, **kwargs):
	Log(' --> Final stream url: %s' % (url))
	return IndirectResponse(VideoClipObject, key=HTTPLiveStreamURL(url))

def GetMediaAuth():
	salt = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
	garbled = ''.join(random.sample(salt, len(salt)))
	auth = ''.join([garbled[int(i * random.random()) % len(garbled)] for i in range(0,241)])
	return auth