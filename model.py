from flask import session, redirect, url_for
import dateutil.parser
import couchdb
from dateutil.relativedelta import relativedelta
from datetime import date
from redis_cache import cache_it, SimpleCache
import settings
from lib import libevernote, libgcal


class Day:
    def __init__(self, currentDate):
        if isinstance(currentDate, (str, unicode)):
            currentDate = dateutil.parser.parse(currentDate)

        self._date = currentDate
        self._data = None #self._load_data_from_db()

    def is_today(self):
        return self._date == date.today()

    @cache_it(expire=settings.CACHE_EXPIRY)
    def _load_data_from_db(self):
        db = _get_couchdb_connection()
        return db.get(_make_doc_id(self._date))

    @cache_it(expire=settings.CACHE_EXPIRY)
    def get_notes(self):
        if not self.is_today():  # if it's today, keep loading fresh
            if self._data:  # if we have data in db
                return self._data['notes']  # just return data from db

        return self._get_notes_from_source()

    def _get_notes_from_source(self):
        return libevernote.get_notes(self._date)

    @cache_it(expire=settings.CACHE_EXPIRY)
    def get_events(self):
        if not self.is_today():  # if it's today, keep loading fresh
            if self._data:  # if we have data in db
                return self._data['events']  # just return data from db

        return self._get_events_from_source()

    def _get_events_from_source(self):
        return libgcal.get_events(self._date, session['credentials'])

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

    def save(self, values):
        values = dict((k, v[0]) for k, v in values.iteritems())  # each value is a list, pop the first off

        doc_id = _make_doc_id(values['date'])

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
            'events': self.get_events(),
            'notes': self.get_notes(),
            'format': "v1",  # to make it easy to migrate documents if structure changes
        }

        doc = db.get(doc_id)
        if doc and '_rev' in doc:
            data['_rev'] = doc['_rev']

        db.save(data)
        invalidate_cache()


def invalidate_cache():
    cache = SimpleCache(hashkeys=True, namespace=invalidate_cache.__module__)
    cache.expire_all_in_set()


def _make_doc_id(date):
    username = "dhumbert"
    return "{}/{}".format(username, date)


def _get_couchdb_connection():
    couch = couchdb.Server(settings.COUCHDB_SERVER)
    couch.resource.credentials = (settings.COUCHDB_USER, settings.COUCHDB_PASS)

    return couch[settings.COUCHDB_DB]


