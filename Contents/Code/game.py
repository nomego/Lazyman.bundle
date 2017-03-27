from datetime import datetime

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
    tvStation = None
    mediaId = None
    title = None
    viewable = True

    def __init__(self, tvStation, mediaId, feed_type):
        self.tvStation = tvStation
        self.mediaId = mediaId
        if feed_type == None:
            self.viewable = False
            self.title = "Non-viewable"
        else:
            self.title = feed_type

    @staticmethod
    def fromContent(content, home_abbr, away_abbr):
        def fromItem(item):
            tv_station = item["callLetters"]
            def getTitle(feed_type):
                return {
                    'AWAY': "%s (%s Away)" % (tv_station, away_abbr),
                    'HOME': "%s (%s Home)" % (tv_station, home_abbr),
                    'FRENCH': "%s (French)" % (tv_station),
                    'NATIONAL': "%s (National)" % (tv_station),
                    'COMPOSITE': "3-Way Camera (Composite)",
                    'NONVIEWABLE': "Non-viewable"
                }[feed_type]
            return Feed(tv_station, item["mediaPlaybackId"], getTitle(item["mediaFeedType"]))

        if "media" in content:
            return [fromItem(item)
                    for stream in content["media"]["epg"] if stream["title"] == "NHLTV"
                    for item in stream["items"]]
        else:
            return []

class Recap(object):
    rid = None
    title = None
    summary = None
    year = None
    studio = "NHL"
    tagline = None
    duration = None
    image_url = None
    videos = []

    @staticmethod
    def fromContent(content, content_title):
        def fromItem(item):
            recap = Recap()
            recap.title = item["title"]
            recap.summary = item["description"]
            recap.year = int(item["date"][0:4])
            recap.tagline = item["blurb"]
            recap.rid = item["id"]
            min, sec = item["duration"].split(":")
            recap.duration = (int(min) * 60 + int(sec)) * 1000

            widest = 0
            pcut = None
            for res in item["image"]["cuts"]:
                cut = item["image"]["cuts"][res]
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
        if type == 'recap':
            return self.recaps
        return self.extended_highlights

    @staticmethod
    def fromSchedule(data):
        if data["totalItems"] <= 0 or len(data["dates"]) == 0:
            return []
        games = data["dates"][0]["games"]
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
                return "%s-%s-%s" % (rec["wins"], rec["losses"], rec["ot"])
            game = Game(g["gamePk"])
            away = g["teams"]["away"]["team"]
            home = g["teams"]["home"]["team"]
            game.time = datetime.strptime(g["gameDate"], "%Y-%m-%dT%H:%M:%SZ")
            game.away_abbr = away["abbreviation"]
            game.home_abbr = home["abbreviation"]
            game.state = g["status"]["detailedState"]
            game.time_remaining = remaining(game.state, game.time)
            game.away_full_name = away["name"]
            game.home_full_name = home["name"]
            game.feeds = Feed.fromContent(g["content"], game.home_abbr, game.away_abbr)
            game.recaps = Recap.fromContent(g["content"], "Recap")
            game.extended_highlights = Recap.fromContent(g["content"], "Extended Highlights")

            game.title = "%s @ %s (%s)" % (away["teamName"], home["teamName"], game.time_remaining)
            summary_format = "%s (%s) from %s (%s) hosts %s (%s) from %s (%s) at %s"
            game.summary = summary_format % (
                game.home_full_name, record(g["teams"]["home"]["leagueRecord"]),
                home["division"]["name"], home["conference"]["name"],
                game.away_full_name, record(g["teams"]["away"]["leagueRecord"]),
                away["division"]["name"], away["conference"]["name"],
                g["venue"]["name"]
            )

            return game
        return map(asGame, games)