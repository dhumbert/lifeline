import dateutil.parser
from apiclient.discovery import build
from oauth2client.client import OAuth2Credentials
import httplib2
import settings


class GcalNotAuthorizedError(Exception):
    pass


def get_events(forDate, credential_json):
    try:
        credentials = OAuth2Credentials.from_json(credential_json)

        if credentials == None:
            raise GcalNotAuthorizedError()

        searchDateLowerLimit = forDate.strftime("%Y-%m-%dT00:00:00{}".format(settings.TIMEZONE_OFFSET))
        searchDateUpperLimit = forDate.strftime("%Y-%m-%dT23:59:59{}".format(settings.TIMEZONE_OFFSET))

        # https://developers.google.com/apis-explorer/#s/calendar/v3/calendar.events.list
        http = httplib2.Http()
        http = credentials.authorize(http)
        service = build("calendar", "v3", http=http)
        apiEvents = service.events().list(calendarId='primary', singleEvents=True, showDeleted=False, fields='items(description,htmlLink,kind,location,start,summary)', timeMin=searchDateLowerLimit, timeMax=searchDateUpperLimit).execute()['items']
    except:
        raise GcalNotAuthorizedError()
    else:
        events = []

        for event in apiEvents:
            if 'date' in event['start']:  # all day events
                eventTime = 'all day'
                sortTime = -1
                if event['start']['date'] != forDate.strftime("%Y-%m-%d"):
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