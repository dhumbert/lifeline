import json
from flask import session, redirect, url_for
import dateutil.parser
from dateutil.relativedelta import relativedelta
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from evernote.edam.type.ttypes import NoteSortOrder
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

    client = EvernoteClient(token=settings.EVERNOTE_DEV_TOKEN)
    noteStore = client.get_note_store()
    filter = NoteFilter(words="created:{} -created:{}".format(searchDateLowerLimit, searchDateUpperLimit), order=NoteSortOrder.CREATED)
    spec = NotesMetadataResultSpec(includeTitle=True)

    noteMetadata = noteStore.findNotesMetadata(settings.EVERNOTE_DEV_TOKEN, filter, 0, 50, spec)
    notes = []
    for note in noteMetadata.notes:
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


def get_current_day_formatted(currentDate):
    return "{} {} {}, {}".format(
        currentDate.strftime("%A"),
        currentDate.strftime("%B"),
        currentDate.strftime("%d").lstrip("0"),
        currentDate.strftime("%Y"))
