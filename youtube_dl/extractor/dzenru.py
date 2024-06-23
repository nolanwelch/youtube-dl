# coding: utf-8
from __future__ import unicode_literals

import datetime
import json
import re
from ..utils import parse_iso8601, js_to_json

from .common import InfoExtractor

# Resolves #32654


# https://10.hot-video.dzeninfra.ru/vod/converted-video/vod-content/81/44/77/50/71/16/75/91/33/7/aeb82079-8a7f-4754-b3b9-c120145d10a1/kaltura/desc_32a3373fea9db700e2f74969bb5b5604/8055412469790298525/ysign1=b396cd39786c46ae23aefecb2e63f6f500ffb9e5b329f067bbeb9b04ade6c2f3,abcID=967,from=zen,hot=0,no_cache=1,pfx,ts=66831097/abrt=132455,acodec=mp4a.40.2/fragment-4-f1-a1-x3.m4s?vsid=79c89205bcd7ffd950274a7eb13f7ab5b9a605db3932xZWPx1247x1719001503&t=1719001520853
# https://10.hot-video.dzeninfra.ru/vod/converted-video/vod-content/81/44/77/50/71/16/75/91/33/7/aeb82079-8a7f-4754-b3b9-c120145d10a1/kaltura/desc_32a3373fea9db700e2f74969bb5b5604/8055412469790298525/ysign1=b396cd39786c46ae23aefecb2e63f6f500ffb9e5b329f067bbeb9b04ade6c2f3,abcID=967,from=zen,hot=0,no_cache=1,pfx,ts=66831097/abrt=132455,acodec=mp4a.40.2/fragment-3-f1-a1-x3.m4s?vsid=79c89205bcd7ffd950274a7eb13f7ab5b9a605db3932xZWPx1247x1719001503&t=1719001518720
# https://cdn.dzen.ru/vod/converted-video/vod-content/81/44/77/50/71/16/75/91/33/7/aeb82079-8a7f-4754-b3b9-c120145d10a1/kaltura/desc_32a3373fea9db700e2f74969bb5b5604/8055412469790298525/ysign1=8ad918709a44938e47b1945a3f95cd77d0cacb77a3f5353436226f7212a84b0f,abcID=967,from=zen,pfx,sfx,ts=6682cdfc/master.m3u8?vsid=sj03asjt77nbvy7jb6yzyuisl3dsrlx4p5zh7ldl2q4cxZENx0000x1718984444


class DzenRuIE(InfoExtractor):
    # TODO: Write all valid URL cases & fix regex
    _VALID_URL = r"https?://(?:www\.)?dzen\.ru/[video/watch]|[embed]/(?P<id>[0-9]+)"
    _TESTS = [
        {
            "url": "https://dzen.ru/video/watch/6471e50e06863726828b435c",
            "info_dict": {
                "id": "6471e50e06863726828b435c",
                "ext": "mp4",
                "title": 'ИКЕА под новым брендом? Обзор SWED HOUSE "IKEA" ожидание / реальность',
                "description": "",
                "thumbnail": "https://avatars.dzeninfra.ru/get-zen_doc/9369849/pub_6471e50e06863726828b435c_6471e53797651c7e6bde53a8/smart_crop_516x290",
                "duration": 775,
                "channel": "Ваш дизайнер интерьера",
                "channel_url": "https://dzen.ru/yourinteriordes?co  try_code=ru&amp;lang=ru&amp;parent_rid=1780210364.275.1718984454232.43847&amp;from_parent_id=4818014694485230733&amp;from_parent_type=gif&amp;from_page=other_page",
            },
        },
        # {
        #     "url": "https://dzen.ru/embed/vnVEaPfaSym8?from_block=partner&from=zen&mute=0&autoplay=0&tv=0",
        #     "info_dict": {
        #         "id": "vnVEaPfaSym8",
        #         "ext": "mp4",
        #         "title": 'ИКЕА под новым брендом? Обзор SWED HOUSE "IKEA" ожидание / реальность | Ваш дизайнер интерьера | Дзен',
        #         "description": "",
        #         "thumbnail": r"re:^https?://.*\.jpg$",
        #     },
        # },
    ]

    def _is_embed_url(self, url):
        m = re.match(r"https?://(?:www\.)?dzen\.ru/embed/.*", url)
        return m is not None

    def _get_original_url(self, embed_url):
        webpage = self._download_webpage(embed_url, -1)
        obj = self._search_json(
            r"<script\s[^>]*>\s*Dzen.player.init\s*(",
            webpage,
            "embed url data",
            end_pattern=r"\s*)\s*;.*<\s*/\s*script\s*>",
        )
        return try_get(obj, lambda x: x["data"]["content"]["video_url"], compat_str)

    def _real_extract(self, url):
        url = sanitize_url(url)
        
        if self._is_embed_url(url):
            url = self._get_original_url(url)

        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group("id")
        webpage = self._download_webpage(url, video_id)

        microdata = self._search_json(
            r'<script\s[^>]*?\bid\s*=\s*("|\')video-microdata\1[^>]*>',
            webpage,
            "video microdata",
            video_id,
            end_pattern="</script>",
            default={},
        )

        # TODO: Test this regex
        duration = self._html_search_regex(
            r'<meta\s[^>]*\bproperty\s*=\s*("|\')video:duration\1\s[^>]*\bcontent="(?P<duration>.+)"\s[^>]*/>',
            webpage,
            "duration",
            group="duration",
            fatal=False,
        )

        description = microdata.get("description")
        thumbnail = microdata.get("thumbnailUrl")
        timestamp = parse_iso8601(microdata.get("uploadDate"))
        title = (
            microdata.get("name")
            or self._og_search_title(webpage).split("|")[0].strip()
        )

        duration = parse_duration(self._html_search_meta(
            "video:duration",
            webpage,
            "duration",
            default=None
        )) or parse_duration(microdata.get('duration'))

        # TODO: Rewrite this regex to make it more generic
        channel_regex = r'<a\s[^>]*\bclass\s*=\s*"card-channel-link _is-link card-channel-info__link" aria-label="(?P<channel>.+)" href="(?P<channel_url>.+)" rel="dofollow" target="_blank"></a>'
        channel = self._html_search_regex(
            channel_regex,
            webpage,
            "channel",
            group="channel name",
            fatal=False,
        )
        channel_url = self._html_search_regex(
            channel_regex,
            webpage,
            "channel",
            group="channel url",
            fatal=False,
        )

        view_count = like_count = comment_count = None
        for stat in microdata.get("interactionStatistic", []):
            count = stat.get("userInteractionCount")
            interaction_type = stat.get("interactionType")
            if interaction_type is None:
                continue
            match interaction_type.get("@type"):
                case "WatchAction":
                    view_count = count
                case "LikeAction":
                    like_count = count
                case "CommentAction":
                    comment_count = count

        stream_script = self._html_search_regex(
            r'<script[^>]*>(?P<script>.*\b"streams"\s*:\s*\[.*\].*)</script>',
            webpage,
            "stream script",
        )
        m3u8_src = self._parse_json(
            stream_script.group("script"), video_id, transform_source=js_to_json
        )
        script_settings = m3u8_src["data"]["MICRO_APP_SSR_DATA"]["settings"]
        streams = script_settings["exportData"]["video"]["video"]
        for url in streams:
            if "m3u8" in url:  # TODO: Make this a match on regex?
                m3u8_url = url
                break
        formats = self._extract_m3u8_formats(m3u8_url, video_id)

        # TODO: Add subtitle parsing
        # TODO: Parse comments from HTML

        return {
            "id": video_id,
            "title": title,
            "description": description,
            "thumbnail": thumbnail,
            "release_timestamp": timestamp,
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "duration": duration,
            "channel": channel,
            "channel_url": channel_url,
            "formats": formats,
        }
