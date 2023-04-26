# Overview
This app fetches your [LIDL-Plus](https://www.lidl.de/c/lidl-plus/s10007388) scanned receipts and allows (simple) aggregations. More to come though.

# Usage
## Requirements
* poetry
* python 3.11
* node 19+

## Install 
Install dependencies by running:
```poetry install```
## Fetch Receipts
### Access/Refresh Token
In order to fetch your receipts you will need to generate an access token for your profile. This is done with the `get-refresh-token.js` script. It will output an access token as well as a refresh token. The refresh token will allow the app to refresh the access token, which means less work for you. The [script](https://gist.github.com/basst85/ef5dae992f75ca4773a75f0249583bc1) was written by [basst85](https://gist.github.com/basst85). 


You can run the script with the following command:
```node get-refresh-token.js```

### Fetch Receipts
After you have retrieved the refresh token you can run the script to fetch all receipts. The script is also expecting a working directory to cache the receipts, which has to exist. 

```poetry run fetch-receipts ${INSERT_YOUR_TOKEN_HERE} ./data```

To check all available options run:

```poetry run fetch-receipts --help```

### Simple Analysis

```poetry run analyze ./data```

# Acknowledgments
* Based on [lidlplus-php-client](https://github.com/bluewalk/lidlplus-php-client) & [LidlApi](https://github.com/KoenZomers/LidlApi)
* script to fetch refresh token by [basst85](https://github.com/basst85)