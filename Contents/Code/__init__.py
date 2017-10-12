import datetime
import random
import re

from game import Game

GAME_SCHEDULE_URL_NHL = "http://statsapi.web.nhl.com/api/v1/schedule?startDate=%s&endDate=%s&expand=schedule.teams,schedule.linescore,schedule.broadcasts.all,schedule.ticket,schedule.game.content.media.epg"
GAME_SCHEDULE_URL_MLB = "http://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=%s&endDate=%s&hydrate=team,linescore,flags,liveLookin,person,stats,probablePitcher,game(content(summary,media(epg)),tickets)&language=en"

ART_NHL = 'nhlbg.jpg'
ART_MLB = 'mlbbg.jpg'
THUMB_NHL = 'nhl_logo.png'
THUMB_MLB = 'mlb_logo.jpg'
ICON = 'LM.png'

DAYS_TO_SHOW = 10
GAMES_TO_SHOW = 30
PAGE_LIMIT = 100
NAME = 'Lazyman'

GAME_CACHE = {}
STREAM_CACHE = {}

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME

	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.117 Safari/537.36'
	HTTP.CacheTime = 0

####################################################################################################
@handler('/video/lazyman', NAME, art=ICON, thumb=ICON)
def MainMenu():
	oc = ObjectContainer()
	oc.add(DirectoryObject(
		key=Callback(SelectDate, sport="nhl"),
		title="NHL"
	))
	oc.add(DirectoryObject(
		key=Callback(SelectDate, sport="mlb"),
		title="MLB"
	))
	return oc

def SelectDate(sport):
	oc = ObjectContainer(title2="Select Date")
	date = datetime.date.today()

	if sport == "mlb":
		time_delta = datetime.timedelta(days=1)
		for i in range(DAYS_TO_SHOW):
	 		oc.add(DirectoryObject(
	 			key=Callback(Date, date=date, sport=sport),
				title=date.strftime("%d %B %Y")),
	 		)
			date = date - time_delta
	else:
		time_delta = datetime.timedelta(days=30)

		while len(oc.objects) < GAMES_TO_SHOW:
			# Look 'time_delta' days back for games that have occurred
			scheduleUrl = GAME_SCHEDULE_URL_NHL % (date - time_delta, date)
			schedule = JSON.ObjectFromURL(scheduleUrl)

			# Add any dates that had games occur to a list of dates for later
			# use
			if schedule["totalItems"] > 0 or len(schedule["dates"]) != 0:

				# The list is reversed so we get more recent dates first
				for day in reversed(schedule['dates']):
					# The string is in YEAR-MONTH-DAY format
					splitDate = day['date'].split('-')

					# Create a 'date' object
					tempDate = datetime.date(int(splitDate[0]), int(splitDate[1]), int(splitDate[2]))

					# Add the date
					oc.add(DirectoryObject(
						key=Callback(Date, date=tempDate, sport=sport),
						title=day['date']),
					)
			# Change the date by 'time_delta' to contine looking for more games
			date = date - time_delta

	return oc 

####################################################################################################
@route('/video/lazyman/date')
def Date(date, sport):

	oc = ObjectContainer(title2="Games on %s" % (date), no_cache=True)
	game_cache = GetCache(date, sport, True)
	for g in game_cache:
		if sport=="mlb":
			thumb = R(THUMB_MLB)
		else:
			thumb = R(THUMB_NHL)
		if len(g.recaps) > 0:
			thumb = g.recaps[0].image_url
		oc.add(DirectoryObject(
			key=Callback(Feeds, date=date, game_id=g.game_id, sport=g.sport),
			title=g.title,
			summary=g.summary,
			thumb=thumb)
		)
	return oc

def GetCache(date, sport, refresh=False):
	if refresh or date not in GAME_CACHE:
		if sport == "mlb":
			scheduleUrl = GAME_SCHEDULE_URL_MLB % (date, date)
		else:
			scheduleUrl = GAME_SCHEDULE_URL_NHL % (date, date)
		schedule = JSON.ObjectFromURL(scheduleUrl)
		GAME_CACHE[date] = Game.fromSchedule(schedule)
	return GAME_CACHE[date]  

def getRecapVCO(date, type, recap, sport):
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
		key = Callback(RecapMetadata, type=type, date=date, recapid=recap.rid, sport=sport),
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
		
		if Prefs['cdn'] == "Level 3":
			cdn = "l3c"
		else:
			cdn = "akc"
		if game.sport == "nhl":
			url = "http://mf.svc.nhl.com/m3u8/%s/%s" % (date, feed.mediaId)
		else:
		   url = "http://nhl.zipstreams.net/mlb/m3u8/%s/%s" % (date, feed.mediaId)
		try:
			real_url = HTTP.Request(url + cdn).content
		except:
			return []

		streams = HTTP.Request(real_url).content.split("#")
		objects = []

		best_fps = 0
		best_height = 0

		for stream in streams:
			try:
				info, url_end = stream.splitlines()
			except ValueError:
				continue

			info = info.split(':')

			# If we don't see 'EXT-X-STREAM-INF' we can skip this one
			if 'EXT-X-STREAM-INF' not in info[0]:
				continue

			# We only need the keys/values now
			info = info[1]

			# All of the key/value pairs are split by commas
			info = info.split(',')

			width_s = 0
			height_s = 0
			bw = 0
			fps_s = 30

			# Search each key/value for needed keys
			# If the key is found, the key/value are split by '=' and we can then
			# extract the value
			for keyval in info:
				if 'RESOLUTION' in keyval:
					width_s = keyval.split('=')[1].split('x')[0]
					height_s = keyval.split('=')[1].split('x')[1]

				if 'BANDWIDTH' in keyval:
					bw = keyval.split('=')[1]

				if 'FRAME-RATE' in keyval:
					fps_s = keyval.split('=')[1]

			if width_s and height_s and bw and fps_s:
				res_url = real_url.rsplit('/', 1)[0] + "/" + url_end
				media_object = MediaObject(
						protocol = 'hls',
						video_codec = VideoCodec.H264,
						video_frame_rate = fps_s,
						audio_codec = AudioCodec.AAC,
						video_resolution = height_s,
						audio_channels = 2,
						optimized_for_streaming = True,
						parts = [
							PartObject(key = HTTPLiveStreamURL(Callback(PlayStream, url=res_url)))
						]
					)

				if Prefs['quality'] == 'Auto':
					if int(height_s) < best_height or float(fps_s) < best_fps:
						objects.append(media_object)
					else:
						best_height = int(height_s)
						best_fps = float(fps_s)
						objects.insert(0, media_object)
				elif Prefs['quality'] == '720p60' and float(fps_s) == 59.94:
					objects.append(media_object)
				elif Prefs['quality'] == media_object.video_resolution+'p':
					objects.append(media_object)
									
		STREAM_CACHE[game.game_id][feed.mediaId] = objects
		return objects

	if game.sport == "mlb":
		thumb = R(THUMB_MLB)
		art = R(ART_MLB)
	else:
		thumb = R(THUMB_NHL)
		art = R(ART_NHL)
		
	if len(game.recaps) > 0:
		thumb = game.recaps[0].image_url

	return VideoClipObject(
		key = Callback(StreamMetadata, date=date, gameid=game.game_id, mediaId=feed.mediaId, sport=game.sport),
		rating_key = feed.mediaId,
		title = feed.title,
		summary = game.summary,
		studio = game.sport.upper(),
		year = int(date[0:4]),
		art = art,
		thumb = thumb,
		items = getStreamItems()
	)

@route('/video/lazyman/feeds')
def Feeds(date, game_id, sport):
	game = None
	game_cache = GetCache(date, sport)
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
		oc.add(getRecapVCO(date, "recaps", r, sport))

	for r in game.extended_highlights:
		if r.videos == None:
			continue
		oc.add(getRecapVCO(date, "extended_highlights", r, sport))

	return oc

def StreamMetadata(date, gameid, mediaId, sport, **kwargs):
	game = None
	feed = None
	game_cache = GetCache(date, sport)
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

def RecapMetadata(type, date, recapid, sport):
	game_cache = GetCache(date, sport)
	recap = None
	for g in game_cache:
		for r in g.getRecaps(type):
			if r.rid == recapid:
				recap = r				
				break
		if recap != None:
			break

	oc = ObjectContainer()
	oc.add(getRecapVCO(date, type, recap, sport))
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