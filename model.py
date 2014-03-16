from flask import session, redirect, url_for, render_template
import dateutil.parser
import couchdb
from dateutil.relativedelta import relativedelta
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from evernote.edam.type.ttypes import Note, NoteSortOrder
from evernote.api.client import EvernoteClient
from redis_cache import cache_it
import settings

# google api
from apiclient.discovery import build
from oauth2client.client import OAuth2Credentials
import httplib2


@cache_it(expire=settings.CACHE_EXPIRY)
def get_notes(currentDate):
    searchDateLowerLimit = currentDate.strftime("%Y%m%d")
    searchDateUpperLimit = (currentDate + relativedelta(days=+1)).strftime("%Y%m%d")

    foundNotes = _find_evernote_notes("created:{} -created:{}".format(searchDateLowerLimit, searchDateUpperLimit))

    notes = []
    for note in foundNotes:
        notes.append((note.guid, note.title))

    return notes


@cache_it(expire=settings.CACHE_EXPIRY)
def get_calendar_events(currentDate):
    # google calendar
    credentials = OAuth2Credentials.from_json(session['credentials'])

    if credentials == None:
        return redirect(url_for('login'))

    searchDateLowerLimit = currentDate.strftime("%Y-%m-%dT00:00:00{}".format(settings.TIMEZONE_OFFSET))
    searchDateUpperLimit = currentDate.strftime("%Y-%m-%dT23:59:59{}".format(settings.TIMEZONE_OFFSET))

    # https://developers.google.com/apis-explorer/#s/calendar/v3/calendar.events.list
    http = httplib2.Http()
    http = credentials.authorize(http)
    service = build("calendar", "v3", http=http)
    apiEvents = service.events().list(calendarId='primary', singleEvents=True, showDeleted=False, fields='items(description,htmlLink,kind,location,start,summary)', timeMin=searchDateLowerLimit, timeMax=searchDateUpperLimit).execute()['items']

    events = []

    for event in apiEvents:
        if 'date' in event['start']:  # all day events
            eventTime = 'all day'
            sortTime = -1
            if event['start']['date'] != currentDate.strftime("%Y-%m-%d"):
                continue  # for some reason the google API apparently doesn't respect timezone for all day events?
        else:
            parsedTime = dateutil.parser.parse(event['start']['dateTime'])

            eventTime = parsedTime.strftime("%I").lstrip("0")

            if int(parsedTime.strftime("%M")) > 0:
                eventTime = eventTime + ":" + parsedTime.strftime("%M")

            eventTime = eventTime + parsedTime.strftime("%p")[0].lower()
            sortTime = int(parsedTime.strftime("%s"))

        e = {'title': event['summary'],
             'description': event['description'] if 'description' in event else '',
             'link': event['htmlLink'],
             'location': event['location'] if 'location' in event else '',
             'time': eventTime,
             'sortTime': sortTime}

        events.append(e)

    return sorted(events, key=lambda x: x['sortTime'])


def save(values):
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
        'format': "v1",  # to make it easy to migrate documents if structure changes
    }

    doc = db.get(doc_id)
    if doc and '_rev' in doc:
        data['_rev'] = doc['_rev']

    db.save(data)


# @cache_it(expire=settings.CACHE_EXPIRY)
def get_data_for_date(date):
    db = _get_couchdb_connection()
    return db.get(_make_doc_id(date))


def _make_doc_id(date):
    username = "dhumbert"
    return "{}/{}".format(username, date)


def _get_evernote_note_store():
    client = EvernoteClient(token=settings.EVERNOTE_DEV_TOKEN)
    return client.get_note_store()


def _find_evernote_notes(words):
    noteStore = _get_evernote_note_store()
    filter = NoteFilter(words=words, order=NoteSortOrder.CREATED)
    spec = NotesMetadataResultSpec(includeTitle=True)

    noteMetadata = noteStore.findNotesMetadata(settings.EVERNOTE_DEV_TOKEN, filter, 0, 50, spec)

    return noteMetadata.notes


def _get_couchdb_connection():
    couch = couchdb.Server(settings.COUCHDB_SERVER)
    couch.resource.credentials = (settings.COUCHDB_USER, settings.COUCHDB_PASS)

    return couch[settings.COUCHDB_DB]


def get_current_day_formatted(currentDate):
    return "{} {} {}, {}".format(
        currentDate.strftime("%A"),
        currentDate.strftime("%B"),
        currentDate.strftime("%d").lstrip("0"),
        currentDate.strftime("%Y"))
