# GT-feed
GT-feed monitors the tracker for new torrents and based on your configured filters downloads the .torrent file (not torrent data) to a specified location. You can set that location to be the watch folder of a torrent client to automatically download that torrent.  
GT-feed keeps track of what .torrent files have been downloaded in a sqlite database and does not download the same .torrent file a second time.


# Installation
```
git clone https://github.com/GeoMSK/gt-feed.git
pip3 install ./gt-feed
```

# Configuration
Run the following to generate the default configuration file:
```
gt-feed –-generate-config
```
or if you like another location for your config
```
gt-feed –-generate-config –c [path to custom location]
```

Then edit the configuration file to suite your needs

- Change the username and password with your credentials
- Set the download_folder to the watch folder of your torrent client
- Replace the dummy filters with yours. All filters must be valid python regular expressions.

Example Config:
```
general:
    username: 'username'
    password: 'password'
    db_path: 'gt.db'  # this is relative to folder containing config.yml
    download_folder: 'C:/Users/user/Downloads'
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'
filtering:
    filters:
    - 'filter1'
    - 'filter2'
    - 'filter3'
    ignore_case: yes
logging:
    logfile: 'gtfeed.log'  # this is relative to folder containing config.yml
    loglevel: 'debug'
```

# Run
You simply run it by executing ```gtfeed –c [path to config]``` or ```python -m gtfeed -c [path to config]```  
Note that if you don't add the ```-c [path to config]``` then the default location of the config file will be used. That is ```[user home]/.gtfeed/config.yml```  
You can also add this to a cron job to execute periodically
