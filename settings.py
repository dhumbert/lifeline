BASE_URL = "http://localhost:5000/"
SESSION_SECRET_KEY = ""
EVERNOTE_DEV_TOKEN = ""
TIMEZONE_OFFSET = "-07:00"
GOOGLE_API_CLIENT_ID = ""
GOOGLE_API_CLIENT_SECRET = ""
CACHE_EXPIRY = 15 * 60 * 60  # cache data in redis for 15 mins

COUCHDB_SERVER = ""
COUCHDB_USER = ""
COUCHDB_PASS = ""
COUCHDB_DB = ""

try:
    from local_settings import *
except ImportError:
    pass