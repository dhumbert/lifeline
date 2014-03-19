from flask import session
import dateutil.parser
from datetime import datetime
import couchdb
from dateutil.relativedelta import relativedelta
from datetime import date
from redis_cache import cache_it, SimpleCache
import hashlib
import json
import settings
from lib import libevernote, libgcal


class Day:
    def __init__(self, currentDate):
        if isinstance(currentDate, (str, unicode)):
            currentDate = dateutil.parser.parse(currentDate).date()

        self._date = currentDate
        self._data = self._load_data_from_db()

    def is_today(self):
        return self._date == date.today()

    @cache_it(expire=settings.CACHE_EXPIRY)
    def _load_data_from_db(self, user):
        db = _get_couchdb_connection()
        return db.get(_make_doc_id(user, self._date))

    @cache_it(expire=settings.CACHE_EXPIRY)
    def get_notes(self, user):
        if not self.is_today():  # if it's today, keep loading fresh
            if self._data:  # if we have data in db
                return self._data['notes']  # just return data from db

        return self._get_notes_from_source(user)

    def _get_notes_from_source(self, user):
        token = user.get_notes_token()
        if user.note_service == "evernote":
            return libevernote.get_notes(self._date, token)

    @cache_it(expire=settings.CACHE_EXPIRY)
    def get_events(self, user):
        if not self.is_today():  # if it's today, keep loading fresh
            if self._data:  # if we have data in db
                return self._data['events']  # just return data from db

        return self._get_events_from_source(user)

    def _get_events_from_source(self, user):
        token = user.get_calendar_token()
        if user.calendar_service == "gcal":
            return libgcal.get_events(self._date, token)

    def get_moods(self):
        if self._data and 'moods' in self._data:
            return sorted(self._data['moods'], key=lambda x: x['sortTime'])
        else:
            return []

    def get_data_template(self, render_cb):
        if self._data:
            data_template = render_cb('data.html', data=self._data)
        else:
            data_template = render_cb('data_empty.html')

        return data_template

    def get_formatted(self, format=None):
        if format:
            formatted = self._date.strftime(format)
        else:
            formatted = "{} {} {}, {}".format(
                self._date.strftime("%A"),
                self._date.strftime("%B"),
                self._date.strftime("%d").lstrip("0"),
                self._date.strftime("%Y"))

        return formatted

    def get_date_pagination(self, url_cb):
        previousDate = self._date + relativedelta(days=-1)
        nextDate = self._date + relativedelta(days=+1)

        return {
            'previous': url_cb(year=previousDate.year, month=previousDate.month, day=previousDate.day),
            'next': url_cb(year=nextDate.year, month=nextDate.month, day=nextDate.day),
        }

    def save(self, user, values):
        values = _unpack_form_data(values)

        doc_id = _make_doc_id(user, values['date'])

        db = _get_couchdb_connection()

        checklist = [
            ["fast_food", "Fast Food", 'fast_food' in values],
            ["exercise", "Exercise", 'exercise' in values],
            ["meditation", "Meditation", 'meditation' in values],
        ]

        textboxes = [
            ["happenings", "Anything interesting happen today?", values['happenings']],
            ["improvement", "How are you better today than you were yesterday?", values['improvement']],
            ["reflection", "Reflection", values['reflection']],
        ]

        data = {
            '_id': doc_id,
            'checklist': checklist,
            'textboxes': textboxes,
            'events': self.get_events(user),
            'notes': self.get_notes(user),
            'format': "v1",  # to make it easy to migrate documents if structure changes
        }

        doc = db.get(doc_id)
        if doc and '_rev' in doc:
            data['_rev'] = doc['_rev']

        db.save(data)
        invalidate_cache()

    def save_mood(self, user, values):
        doc_id = _make_doc_id(user, values['date'])
        values = _unpack_form_data(values)

        del values['date']

        notes = values['notes']
        del values['notes']

        if not self._data:
            self._data = {}

        now = datetime.now()
        moodTime = now.strftime("%I").lstrip("0")

        if int(now.strftime("%M")) > 0:
            moodTime = moodTime + ":" + now.strftime("%M")

        moodTime = moodTime + now.strftime("%p")[0].lower()

        sortTime = int(now.strftime("%s"))

        if 'moods' not in self._data:
            self._data['moods'] = []

        moodHash = {
            'time': moodTime,
            'sortTime': sortTime,
            'notes': notes,
            'values': {}
        }

        for mood, value in values.iteritems():
             moodHash['values'][mood] = int(value)

        self._data['moods'].append(moodHash)

        db = _get_couchdb_connection()
        doc = db.get(doc_id)
        if doc and '_rev' in doc:
            self._data['_rev'] = doc['_rev']

        db.save(self._data)
        invalidate_cache()


class User():
    _rev = ""
    username = ""
    password = ""
    note_service = "evernote"
    calendar_service = "gcal"
    tokens = {}

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.username)

    def set_password(self, password):
        self.password = hashlib.sha1(password).hexdigest()

    def get_notes_token(self):
        return self.get_token(self.note_service)

    def get_calendar_token(self):
        return self.get_token(self.calendar_service)

    def get_token(self, key):
        try:
            return self.tokens[key]
        except IndexError:
            return None

    def as_dict(self):
        return {
            '_rev': self._rev,
            '_id': self.username,
            'password': self.password,
            'tokens': self.tokens,
            'calendar_service': self.calendar_service,
            'note_service': self.note_service,
        }

    def save(self):
        db = _get_couchdb_connection(settings.COUCHDB_AUTH_DB)
        db.save(self.as_dict())

    def __repr__(self):
        return unicode(self.username)


@cache_it(expire=settings.CACHE_EXPIRY)
def get_user(username):
    db = _get_couchdb_connection(settings.COUCHDB_AUTH_DB)
    user = db.get(username)
    if user:
        u = User()
        u._rev = user['_rev']
        u.username = username
        u.password = user['password']
        u.tokens['evernote'] = user['tokens']['evernote']
        u.tokens['gcal'] = user['tokens']['gcal']
        u.note_service = user['note_service']
        u.calendar_service = user['calendar_service']
        return u


def authenticate(username, password):
    hashed_pass = hashlib.sha1(password).hexdigest()
    user = get_user(username)

    if user and user.password == hashed_pass:
        return user

    return None


def invalidate_cache():
    cache = SimpleCache(hashkeys=True, namespace=invalidate_cache.__module__)
    cache.expire_all_in_set()


def _unpack_form_data(values):
    return dict((k, v[0]) for k, v in values.iteritems())  # each value is a list, pop the first off


def _make_doc_id(user, date):
    return "{}/{}".format(user.username, date)


def _get_couchdb_connection(db=None):
    couch = couchdb.Server(settings.COUCHDB_SERVER)
    couch.resource.credentials = (settings.COUCHDB_USER, settings.COUCHDB_PASS)

    if not db:
        db = settings.COUCHDB_DB

    return couch[db]


