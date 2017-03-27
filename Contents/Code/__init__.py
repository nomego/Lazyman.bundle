import datetime

ART = 'nhlbg.jpg'
THUMB = 'nhl_logo.png'
ICON = 'LM.png'

DAYS_TO_SHOW = 10
PAGE_LIMIT = 100
NAME = 'Lazyman'
GetCache = SharedCodeService.gamecache.GetCache

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
		oc.add(VideoClipObject(
			url = "http://mf.svc.nhl.com/m3u8/%s/%s" % (date, f.mediaId),
			title = f.title,
			summary = g.summary)
		)

	for r in game.recaps:
		if r.videos == None:
			continue
		oc.add(getRecapVCO(date, "recaps", r))

	for r in game.extended_highlights:
		if r.videos == None:
			continue
		oc.add(getRecapVCO(date, "extended_highlights", r))

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
