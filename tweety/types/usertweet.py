import time
from typing import List, Optional

from ..exceptions import UserNotFound, UserProtected
from . import Excel, Tweet, deprecated


class UserTweets(dict):
    def __init__(
        self,
        user_id,
        http,
        pages: int = 1,
        get_replies: bool = True,
        get_retweets: bool = True,
        wait_time: int = 2,
        cursor: Optional[str] = None,
    ):
        super().__init__()
        self.tweets = []
        self.get_replies = get_replies
        self.get_retweets = get_retweets
        self.cursor = cursor
        self.is_next_page = True
        self.http = http
        self.user_id = user_id
        self.pages = pages
        self.wait_time = wait_time
        # self._get_tweets(pages, wait_time)

    @staticmethod
    def _get_entries(response: dict) -> List[dict]:
        instructions = response["data"]["user_result"]["result"]["timeline_response"][
            "timeline"
        ]["instructions"]
        for instruction in instructions:
            if instruction.get("__typename") == "TimelineAddEntries":
                return instruction["entries"]

        return []

    @staticmethod
    def _get_tweet_content_key(tweet: dict) -> List[dict]:
        if str(tweet["entryId"]).split("-")[0] == "tweet":
            return [tweet["content"]["content"]["tweetResult"]["result"]]

        if str(tweet["entryId"]).split("-")[0] == "homeConversation":
            return [
                item["item"]["content"]["tweetResult"]["result"]
                for item in tweet["content"]["items"]
            ]

        return []

    def get_next_page(self):
        _tweets = []
        if self.is_next_page:
            response = self.http.get_tweets(
                self.user_id, replies=self.get_replies, cursor=self.cursor
            )

            if not response["data"]["user_result"].get("result"):
                raise UserNotFound(
                    error_code=50, error_name="GenericUserNotFound", response=response
                )

            # if (
            #     response["data"]["user_result"]["result"]["__typename"]
            #     == "UserUnavailable"
            # ):
            #     raise UserProtected(403, "UserUnavailable", None)

            entries = self._get_entries(response)

            for entry in entries:
                tweets = self._get_tweet_content_key(entry)
                for tweet in tweets:
                    try:
                        parsed = Tweet(response, tweet, self.http)
                        if parsed.is_retweet and not self.get_retweets:
                            continue
                        _tweets.append(parsed)
                        # yield parsed
                    except BaseException:
                        pass

            self.is_next_page = self._get_cursor(entries)

            for tweet in _tweets:
                self.tweets.append(tweet)

            self["tweets"] = self.tweets
            self["is_next_page"] = self.is_next_page
            self["cursor"] = self.cursor

        return self, _tweets

    def generator(self):
        tweets = []
        for page in range(1, int(self.pages) + 1):
            _, new_tweets = self.get_next_page()
            tweets = tweets + new_tweets

            if self.is_next_page and page != self.pages:
                time.sleep(self.wait_time)

        yield self, tweets

    def _get_cursor(self, entries: List[dict]) -> bool:
        for entry in entries:
            if str(entry["entryId"]).split("-")[0] == "cursor":
                if entry["content"]["cursorType"] == "Bottom":
                    new_cursor = entry["content"]["value"]

                    if new_cursor == self.cursor:
                        return False

                    self.cursor = new_cursor
                    return True

        return False

    def to_xlsx(self):
        return Excel(self.tweets, self.tweets[0].author)

    def __getitem__(self, index: int) -> Tweet:
        return self.tweets[index]

    def __iter__(self):
        for __tweet in self.tweets:
            yield __tweet

    def __len__(self):
        return len(self.tweets)

    def __repr__(self):
        return f"UserTweets(user_id={self.user_id}, count={self.__len__()})"

    @deprecated
    def to_dict(self):
        return self.tweets
