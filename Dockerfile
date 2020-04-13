# Based on Python
FROM python:alpine

LABEL Name=buzzfeed_reddit_bot Version=0.0.1

# Our bot is in app, so copy that whole folder over to /app on the container filesystem
WORKDIR /app
COPY app .

# Compiler not needed
# RUN apk add build-base

# Using pip:
RUN python3 -m pip install -r requirements.txt

# Make sure log file exists so it can be mounted in compose file
RUN touch Posts_Searched_Today.log
# Start bot
CMD ["python3", "-u", "./parse_article_archives.py"]