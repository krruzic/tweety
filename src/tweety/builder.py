import json
from typing import Literal, Optional
from urllib.parse import urlencode
import random
import string
from functools import wraps

REQUEST_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
REQUEST_PLATFORMS = ["Linux", "Windows"]


def return_with_headers(func):
    @wraps(func)
    def wrapper(self, *arg, **kw):
        method, url = func(self, *arg, **kw)
        return dict(method=method, headers=self._get_headers(), url=url)

    return wrapper


class UrlBuilder:
    URL_GUEST_TOKEN = "https://api.twitter.com/1.1/guest/activate.json"
    URL_API_INIT = "https://twitter.com/i/api/1.1/branch/init.json"
    URL_USER_BY_SCREEN_NAME = (
        "https://api.twitter.com/graphql/rePnxwe9LZ51nQ7Sn_xN_A/UserByScreenName"
    )
    URL_USER_TWEETS = (
        "https://twitter.com/i/api/graphql/WzJjibAcDa-oCjCcLOotcg/UserTweets"
    )
    URL_USER_TWEETS_WITH_REPLIES = (
        "https://twitter.com/i/api/graphql/nrdle2catTyGnTyj1Qa7wA/UserTweetsAndReplies"
    )
    URL_TRENDS = "https://twitter.com/i/api/2/guide.json"
    URL_TWEET_DETAILS = (
        "https://twitter.com/i/api/graphql/1oIoGPTOJN2mSjbbXlQifA/TweetDetail"
    )
    URL_AUSER_SETTINGS = "https://api.twitter.com/1.1/account/settings.json"  # noqa
    URL_SEARCH = (
        "https://twitter.com/i/api/graphql/gkjsKepM6gl_HmFWoWKfgg/SearchTimeline"
    )
    GQL_FEATURES = {
        "blue_business_profile_image_shape_enabled": False,
        "freedom_of_speech_not_reach_fetch_enabled": False,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": False,
        "interactive_text_enabled": False,
        "longform_notetweets_consumption_enabled": True,
        "longform_notetweets_richtext_consumption_enabled": True,
        "longform_notetweets_rich_text_read_enabled": False,
        "responsive_web_edit_tweet_api_enabled": False,
        "responsive_web_enhance_cards_enabled": False,
        "responsive_web_graphql_exclude_directive_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "responsive_web_graphql_timeline_navigation_enabled": False,
        "responsive_web_text_conversations_enabled": False,
        "responsive_web_twitter_blue_verified_badge_is_enabled": True,
        "spaces_2022_h2_clipping": True,
        "spaces_2022_h2_spaces_communities": True,
        "standardized_nudges_misinfo": False,
        "tweet_awards_web_tipping_enabled": False,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": False,
        "tweetypie_unmention_optimization_enabled": False,
        "verified_phone_label_enabled": False,
        "vibe_api_enabled": False,
        "view_counts_everywhere_api_enabled": False,
        "withDownvotePerspective": False,
        "creator_subscriptions_tweet_preview_api_enabled": False,
        "rweb_lists_timeline_redesign_enabled": False,
        "longform_notetweets_inline_media_enabled": True,
    }

    def __init__(self, cookies=None):
        self.cookies = cookies
        self.user_id = None
        self.guest_token = None

    def _get_headers(self):
        headers = {
            "authority": "twitter.com",
            "accept": "*/*",
            "accept-language": "en-PK,en;q=0.9",
            "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "content-type": "application/x-www-form-urlencoded",
            "referer": "https://twitter.com/",
            "sec-ch-ua": '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": f'"{random.choice(REQUEST_PLATFORMS)}"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": REQUEST_USER_AGENT,
            "x-csrf-token": self._get_csrf(),
            "x-twitter-active-user": "yes",
            "x-twitter-client-language": "en",
        }

        if self.guest_token or self.cookies:
            headers["content-type"] = "application/json"
            # headers['referer'] = f'https://twitter.com/{self.username}'
            headers["sec-fetch-site"] = "same-origin"

            if self.guest_token:
                headers["x-guest-token"] = self.guest_token

        return headers

    def _get_csrf(self):
        if self.cookies and self.cookies.get("ct0"):
            return self.cookies.get("ct0")

        return "".join(random.choices(string.ascii_letters + string.digits, k=32))

    @staticmethod
    def _build(url, params):
        return "?".join([url, params])

    @return_with_headers
    def get_guest_token(self):
        return "POST", self.URL_GUEST_TOKEN

    @return_with_headers
    def init_api(self):
        return "POST", self.URL_API_INIT

    @return_with_headers
    def user_by_screen_name(self, username):
        variables = {
            "screen_name": str(username),
            "withSafetyModeUserFields": True,
            "withSuperFollowsUserFields": True,
            "withDownvotePerspective": False,
            "withReactionsMetadata": False,
            "withReactionsPerspective": False,
            "withSuperFollowsTweetFields": False,
        }
        features = self.GQL_FEATURES

        params = {
            "variables": str(json.dumps(variables)),
            "features": str(json.dumps(features)),
        }

        return "GET", self._build(self.URL_USER_BY_SCREEN_NAME, urlencode(params))

    @return_with_headers
    def search(
        self,
        query: str,
        search_type: Literal["Latest", "users", "photos", "videos"] = "Latest",
        cursor: Optional[str] = None,
    ):
        variables = {
            "rawQuery": query,
            "count": 40,
            "product": search_type,
            "withDownvotePerspective": False,
            "withReactionsMetadata": False,
            "withReactionsPerspective": False,
            "withSuperFollowsTweetFields": False,
        }
        features = self.GQL_FEATURES

        if cursor:
            variables["cursor"] = str(cursor)

        params = {
            "variables": str(json.dumps(variables)),
            "features": str(json.dumps(features)),
        }

        return "GET", self._build(self.URL_SEARCH, urlencode(params))

    @return_with_headers
    def user_tweets(self, user_id, replies=False, cursor=None):
        variables = {
            "userId": str(user_id),
            "count": 40,
            "includePromotedContent": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True,
            "withDownvotePerspective": False,
            "withReactionsMetadata": False,
            "withReactionsPerspective": False,
            "withSuperFollowsTweetFields": False,
            "withSuperFollowsUserFields": False,
        }
        features = self.GQL_FEATURES

        if cursor:
            variables["cursor"] = str(cursor)

        params = {
            "variables": str(json.dumps(variables)),
            "features": str(json.dumps(features)),
        }

        if replies:
            return "GET", self._build(
                self.URL_USER_TWEETS_WITH_REPLIES, urlencode(params)
            )

        return "GET", self._build(self.URL_USER_TWEETS, urlencode(params))

    @return_with_headers
    def trends(self):
        params = {
            "include_profile_interstitial_type": "1",
            "include_blocking": "1",
            "include_blocked_by": "1",
            "include_followed_by": "1",
            "include_want_retweets": "1",
            "include_mute_edge": "1",
            "include_can_dm": "1",
            "include_can_media_tag": "1",
            "include_ext_has_nft_avatar": "1",
            "include_ext_is_blue_verified": "1",
            "include_ext_verified_type": "1",
            "skip_status": "1",
            "cards_platform": "Web-12",
            "include_cards": "1",
            "include_ext_alt_text": "true",
            "include_ext_limited_action_results": "false",
            "include_quote_count": "true",
            "include_reply_count": "1",
            "tweet_mode": "extended",
            "include_ext_collab_control": "true",
            "include_ext_views": "true",
            "include_entities": "true",
            "include_user_entities": "true",
            "include_ext_media_color": "true",
            "include_ext_media_availability": "true",
            "include_ext_sensitive_media_warning": "true",
            "include_ext_trusted_friends_metadata": "true",
            "send_error_codes": "true",
            "simple_quoted_tweet": "true",
            "count": "40",
            "requestContext": "launch",
            "candidate_source": "trends",
            "include_page_configuration": "false",
            "entity_tokens": "false",
            "ext": "mediaStats,highlightedLabel,hasNftAvatar,voiceInfo,enrichments,superFollowMetadata,unmentionInfo,editControl,collab_control,vibe",
        }
        return "GET", self._build(self.URL_TRENDS, urlencode(params))

    @return_with_headers
    def tweet_detail(self, tweet_id):
        variables = {
            "focalTweetId": str(tweet_id),
            "with_rux_injections": False,
            "includePromotedContent": True,
            "withCommunity": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withBirdwatchNotes": True,
            "withDownvotePerspective": False,
            "withReactionsMetadata": False,
            "withReactionsPerspective": False,
            "withVoice": True,
            "withV2Timeline": True,
        }
        features = self.GQL_FEATURES

        params = {
            "variables": str(json.dumps(variables)),
            "features": str(json.dumps(features)),
        }

        return "GET", self._build(self.URL_TWEET_DETAILS, urlencode(params))

    @return_with_headers
    def aUser_settings(self):
        params = {
            "include_mention_filter": "true",
            "include_nsfw_user_flag": "true",
            "include_nsfw_admin_flag": "true",
            "include_ranked_timeline": "true",
            "include_alt_text_compose": "true",
            "ext": "ssoConnections",
            "include_country_code": "true",
            "include_ext_dm_nsfw_media_filter": "true",
            "include_ext_sharing_audiospaces_listening_data_with_followers": "true",
        }
        return "GET", self._build(self.URL_AUSER_SETTINGS, urlencode(params))
