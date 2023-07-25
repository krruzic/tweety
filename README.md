# tweety
Forked from `tweety-ns`. High performance reverse engineered API to twitter. Supports search, user tweets and more. No login required!

## Installation: 
```bash
pip install https://github.com/krruzic/tweety
```

## Keep synced with latest fixes

##### **Pip might not be always updated , so to keep everything synced.**

```bash
pip install https://github.com/krruzic/tweety/archive/main.zip --upgrade --force-reinstall
```

## A Quick Example:
```python
  from tweety.bot import Twitter
  
  app = Twitter()
  
  all_tweets = app.get_tweets("elonmusk")
  for tweet in all_tweets:
      print(tweet)
```

Full Documentation and Changelogs are [here](https://tweety.readthedocs.io/en/latest/) but may be outdated
