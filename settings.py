BASE_URL = "http://localhost:5000/"
SESSION_SECRET_KEY = ""
TIMEZONE_OFFSET = "-07:00"
GOOGLE_API_CLIENT_ID = ""
GOOGLE_API_CLIENT_SECRET = ""
CACHE_EXPIRY = 5 * 60 * 60  # cache data in redis for 5 mins

COUCHDB_SERVER = ""
COUCHDB_USER = ""
COUCHDB_PASS = ""
COUCHDB_DB = "lifeline"
COUCHDB_AUTH_DB = "lifeline_users"

try:
    from local_settings import *
except ImportError:
    pass