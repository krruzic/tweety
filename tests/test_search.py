from tweety.bot import Twitter

app = Twitter()

# print("-------------------------")
# print("SCRAPING ELON PROFILE")
# print("-------------------------")

# all_tweets = app.get_tweets("elonmusk", replies=True, pages=1)
# print(len(all_tweets))
# for tweet in all_tweets:
#     print(
#         f"[DATE: {tweet.date}, AUTHOR: {tweet.author.username} FOLLOWERS: {tweet.author.followers_count}] {tweet.text}"
#     )
print("-------------------------")
print("SEARCHING ALL TWEETS BY ELON")
print("-------------------------")
user_tweets = app.iter_tweets("elonmusk", retweets=False, pages=10)
y = next(user_tweets)
print(y)
search_tweets = app.iter_search("blah", pages=2, wait_time=0)
x = next(search_tweets)
for tweet in x[1]:
    print(tweet.id)
# search_tweets.to_xlsx()
# print(len(search_tweets))
# for tweet in search_tweets:
#     print(
#         f"[DATE: {tweet.date}, AUTHOR: {tweet.author.username} FOLLOWERS: {tweet.author.followers_count}] {tweet.text}"
#     )
