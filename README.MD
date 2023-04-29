# H1emuLeaderboard

Leaderboard aims to provide information to your discord server about player kills and deaths for your H1emu server


See https://github.com/H1emu

### Dependencies:
 - python3
 - python3-pip
 - see requirments.txt
 

## Installation:

### 1. Install dependencies

```
apt update && apt install python3 python3-pip
```

### 2. Clone repository

```
git clone https://github.com/
cd 
```

### 3. (optional) Setup virtualenv

initialize
```
python3 -m venv .venv
```

activate
```
source .venv/bin/activate
```

(exit)
```
deactivate
```

### 4. Install pip packages

```
pip3 install -r requirements.txt
```

### 5. Edit config.ini

Open up the **config.ini** file in your favourite text editor, for example: `nano config.ini`

Look for `Token = CHANGE_ME_TO_YOUR_BOT_TOKEN` change the value to your bot token

Now look for `ChannelId = CHANGE_ME_TO_YOUR_CHANNEL_ID` and change the value to the id of your discord channel

Save your changes and exit the text editor

*Other values can be changed here to suit your needs*

### 6. Start the script

Now that the configuration has been set you can start the script running with the following command:
```
python3 ./leaderboard.py
```
