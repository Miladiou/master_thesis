import twint

import numpy as np
import time
import furl
import re
import requests


# Controversial topic
topic = "trump military cemeteries"

# Source website
website = "socialnewsdaily.com"

# Clear file
open("data.csv", "w").close()

# Configure
c = twint.Config()

#c.Username = "kilianj"
c.Search = topic + " " + website
#c.Format = "Date: {date} | Username: {username} | Tweet: {tweet}"
c.Lang = "en"
#c.Limit = 1000
c.Since = "2018-01-14"
#c.Until = "2017-07-20"
#c.Timedelta = 1
#c.Media = True

c.Store_csv = True
c.Custom = ["id", "date", "tweet"]
c.Output = "data.csv"
c.Count = True


# Run
start_time = time.time()

twint.run.Search(c)
#twint.run.Followers(c)
#twint.run.Profile(c)


# Post-treatment
my_file = open("data.csv", "r")
your_file = open("links.csv", "w")

# Get the links
for line in my_file:

    # Requires tweet to be the last of three custom parameters
    index = [pos for pos, char in enumerate(line) if char == ","][1]
    tweet = line[index + 1: -1]
    flag_indices = [m.start() for m in re.finditer("http", tweet)]
    if len(flag_indices) != 0:
        for i in flag_indices:
            index = tweet.find(chr(160) or chr(32), i)
            link = tweet[i:index]
            your_file.write(link + "\n")

your_file.close()


# Remove duplicates and shortened links
your_file = open("links.csv", "r")
lines_seen = set()
for line in your_file:
    flag_index = [m.start() for m in re.finditer(website, line)]
    if len(flag_index) != 0:

        # Removes queries
        line = furl.furl(line[:-1]).remove(args=True, fragment=True).url + "\n"
        # Removes URL first parts
        line = line[flag_index[0]:]

        if line[-2] == "/":
            line = line[:-2] + "\n"
        index_list = [pos for pos, char in enumerate(line) if char == "/"]
        if len(index_list) != 0:
            index = index_list[-1]
            words_sep = [pos for pos, char in enumerate(line[index:]) if char == "-"]
            # Removes links that are too shorts and may not be articles (4 words minimum)
            if len(words_sep) > 1:
                if len(words_sep) > 2:
                    line = line[:index + words_sep[2]] + "\n"

        # START LOOKING FOR "-" FROM THE START
        #index = [pos for pos, char in enumerate(line) if char == "-"]
        #number = len([pos for pos, char in enumerate(website) if char == "-"])
        #if len(index) - number > 2:
        #if len(line) > len(website) + 15:
            # Shortens the links enough to be able to find them all during the next search step
            # i.e. more than four words
            #if len(index) - number > 3:
                #line = line[:index[3 + number]]
            #if line[-1] != "\n":
                #line = line + "\n"

            #if line[-2] == "/":
                #line = line[:-2] + "\n"
            #index = [pos for pos, char in enumerate(line) if char == "/"]
            # There might still be some residuals
            #if len(index) > 1:
                #line = line[:index[1]] + "\n"

                if line not in lines_seen:
                    lines_seen.add(line)

your_file.close()

your_file = open("links.csv", "w")
for line in lines_seen:
    your_file.write(line)

# If one wants to keep shortened URLs
#session = requests.Session()
# Returns unshortened URL. OBS ! Very time consuming...
#if len(line) < 25:
    #resp = session.head(line[:-1], allow_redirects = True)
    #your_file.write(resp.url + "\n")

my_file.close()
your_file.close()


# Clear file
open("data.csv", "w").close()
your_file = open("links.csv", "r")
c.Custom = ["date", "username", "user_id", "tweet"]

# Search for the collected links
for line in your_file:

    c.Search = line[:-1]
    twint.run.Search(c)


elapsed_time = time.time() - start_time
print("Running time: " + str(elapsed_time) + " seconds")
