from datetime import datetime
from datetime import timedelta

VS_IMGS = {
    "VAN": {
        "MIN": "288086104/1136x640"
    }
}

def GetVsImg(away, home):
    away_vs = VS_IMGS[away]
    if away_vs == None:
        return
    img = away_vs[home]
    if img == None:
        return
    return "https://nhl.bamcontent.com/images/photos/%s/cut.jpeg" % img

class Feed(object):
    mediaId = None
    title = None
    viewable = True

    def __init__(self, mediaId, title, mediaState):
        self.mediaId = mediaId
        self.title = title

        if title == "Non-viewable" or mediaState == "MEDIA_OFF":
            self.viewable = False

    @staticmethod
    def fromContent(content, home_abbr, away_abbr):
        def fromItem(item):
            tv_station = item["callLetters"]
            feed_type = item["mediaFeedType"]
            try:
                feed_name = item["feedName"]
            except KeyError:
                feed_name = ""

            if feed_name != "":
                if tv_station != "":
                    title = "%s (%s %s)" % (feed_name, tv_station, feed_type)
                else:
                    title = "%s (%s)" % (feed_name, feed_type)
            else:
                title = {
                    'AWAY': "%s (%s Away)" % (tv_station, away_abbr),
                    'HOME': "%s (%s Home)" % (tv_station, home_abbr),
                   'FRENCH': "%s (French)" % (tv_station),
                   'NATIONAL': "%s (National)" % (tv_station),
                   'COMPOSITE': "3-Way Camera (Composite)",
                   'ISO': 'Multi-Angle',
                   'NONVIEWABLE': "Non-viewable"
                }.get(feed_type, "%s (%s)" % (tv_station, feed_type))
            if "id" in item:
                return Feed(item["id"], title, item['mediaState'])
            else:
                return Feed(item["mediaPlaybackId"], title, item['mediaState'])
        if "media" in content:
            return [fromItem(item)
                    for stream in content["media"]["epg"] if stream["title"] in ["MLBTV", "NHLTV"]
                    for item in stream["items"]]
        else:
            return []

class Recap(object):
    rid = None
    title = None
    summary = None
    year = None
    studio = None
    tagline = None
    duration = None
    image_url = None
    videos = []

    @staticmethod
    def fromContent(content, content_title, sport):
        def fromItem(item):
            recap = Recap()
            if Prefs['show_scores'] or "Recap" not in item["title"]:
            	recap.title = item["title"]
            else:
            	recap.title = 'Recap'
            recap.summary = item["description"]
            recap.year = int(item["date"][0:4])
            recap.studio = sport
            recap.tagline = item["blurb"]
            recap.rid = item["id"]
            try:
                min, sec = item["duration"].split(":")
                hr = 0
            except ValueError:
                hr, min, sec = item["duration"].split(":")
            recap.duration = (int(hr) * 3600 + int(min) * 60 + int(sec)) * 1000

            widest = 0
            pcut = None
            for res in item["image"]["cuts"]:
                try:
                    cut = item["image"]["cuts"][res]
                except:
                    cut = res
                if cut["width"] > widest:
                    pcut = cut
                    widest = cut["width"]
            
            recap.image_url = pcut["src"]
            recap.videos = [vid for vid in item["playbacks"] if vid["name"][0:5] == "FLASH"]
            
            return recap

        if "media" in content:
            return [fromItem(item)
                    for stream in content["media"]["epg"] if stream["title"] == content_title
                    for item in stream["items"]]
        else:
            return []


class Game:
    game_id = None
    sport = None
    time = None
    state = None
    time_remaining = None

    home_abbr = None
    away_abbr = None
    away_full_name = None
    home_full_name = None

    title = None
    summary = None

    feeds = []
    recaps = []
    extended_highlights = []

    def __init__(self, gameId):
        self.game_id = gameId

    def getRecaps(self, type):
        if type == 'recaps':
            return self.recaps
        return self.extended_highlights

    @staticmethod
    def fromSchedule(data, date):
        if data["totalItems"] <= 0 or len(data["dates"]) == 0:
            return []
        if "MLB" in data["copyright"]:
            sport = "mlb"
        else:
            sport = "nhl"
        for game_date in data["dates"]:
            if game_date["date"] == date:
                games = game_date["games"]
                break
        def asGame(g):
            def remaining(state, time):
                if "In Progress" in state:
                    period = g["linescore"]["currentPeriodOrdinal"]
                    time_left = g["linescore"]["currentPeriodTimeRemaining"]
                    return "%s %s left" % (period, time_left)
                elif state == "Final":
                    return "Final"
                else:
                    delta = time - datetime.utcnow()
                    if delta.days < 0:
                        return "Started"
                    dt = datetime(1,1,1) + delta
                    return "Starts in %sh %sm %ss" % (dt.hour, dt.minute, dt.second)
            def record(rec):
                if "ot" in rec:
                    return "%s-%s-%s" % (rec["wins"], rec["losses"], rec["ot"])
                else:
                    return "%s-%s" % (rec["wins"], rec["losses"])
            game = Game(g["gamePk"])
            away = g["teams"]["away"]["team"]
            home = g["teams"]["home"]["team"]
            game.time = datetime.strptime(g["gameDate"], "%Y-%m-%dT%H:%M:%SZ")
            game.away_abbr = away["abbreviation"]
            game.home_abbr = home["abbreviation"]
            game.state = g["status"]["detailedState"]
            game.sport = sport
            
            if sport == "nhl":
                game.time_remaining = remaining(game.state, game.time)
            game.away_full_name = away["name"]
            game.home_full_name = home["name"]
            game.feeds = Feed.fromContent(g["content"], game.home_abbr, game.away_abbr)
            if sport == "nhl":
                game.recaps = Recap.fromContent(g["content"], "Recap", "NHL")
                game.extended_highlights = Recap.fromContent(g["content"], "Extended Highlights", "NHL")
            else:
                game.recaps = Recap.fromContent(g["content"], "Daily Recap", "MLB")
                game.extended_highlights = Recap.fromContent(g["content"], "Extended Highlights", "MLB")

            if sport == "nhl":
                game.title = "%s @ %s (%s)" % (away["teamName"], home["teamName"], game.time_remaining)
                summary_format = "%s (%s) from %s (%s) hosts %s (%s) from %s (%s) at %s"
				try:
					game.summary = summary_format % (
						game.home_full_name, record(g["teams"]["home"]["leagueRecord"]),
						home["division"]["name"], home["conference"]["name"],
						game.away_full_name, record(g["teams"]["away"]["leagueRecord"]),
						away["division"]["name"], away["conference"]["name"],
						g["venue"]["name"]
					)
				except KeyError:
					game.summary = "Unknown"
            else:
                game.title = "%s @ %s (%s)" % (away["teamName"], home["teamName"], datetime.strftime(game.time-timedelta(hours=4), "%I:%M%p").lstrip("0"))
                summary_format = "%s (%s) from %s hosts %s (%s) from %s at %s"
                game.summary = summary_format % (
                    game.home_full_name, record(g["teams"]["home"]["leagueRecord"]),
                    home["division"]["name"], 
                    game.away_full_name, record(g["teams"]["away"]["leagueRecord"]),
                    away["division"]["name"], g["venue"]["name"]
                )

            return game
        return map(asGame, games)