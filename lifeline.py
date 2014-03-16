import dateutil.parser
from dateutil.relativedelta import relativedelta
from datetime import date
from flask import Flask, render_template, redirect, request, session, url_for
import model
import settings

# google api
from oauth2client.client import OAuth2WebServerFlow


app = Flask(__name__)
app.secret_key = settings.SESSION_SECRET_KEY


@app.route('/')
def today():
    dateToday = date.today()
    return date_view(dateToday.year, dateToday.month, dateToday.day)


@app.route('/<int:year>/<int:month>/<int:day>')
def date_view(year, month, day):
    currentDate = dateutil.parser.parse("{}-{}-{}".format(year, month, day), yearfirst=True).date()
    currentDateFormatted = model.get_current_day_formatted(currentDate)
    datePagination = get_date_pagination(currentDate)

    isToday = currentDate == date.today()

    notes = model.get_notes(currentDate)
    events = model.get_calendar_events(currentDate)

    return render_template('day.html', notes=notes, events=events, isToday=isToday, currentDateFormatted=currentDateFormatted, datePagination=datePagination)


def get_date_pagination(currentDate):
    previousDate = currentDate + relativedelta(days=-1)
    nextDate = currentDate + relativedelta(days=+1)

    return {
        'previous': url_for('date_view', year=previousDate.year, month=previousDate.month, day=previousDate.day),
        'next': url_for('date_view', year=nextDate.year, month=nextDate.month, day=nextDate.day),
    }


@app.route('/google-auth')
def google_auth():
    # google api
    # change redirect uri: https://console.developers.google.com/project/667824890122/apiui/credential
    flow = OAuth2WebServerFlow(
        client_id=settings.GOOGLE_API_CLIENT_ID,
        client_secret=settings.GOOGLE_API_CLIENT_SECRET,
        scope='https://www.googleapis.com/auth/calendar',
        redirect_uri=settings.BASE_URL + "google-auth-callback",
        access_type='offline',
        approval_prompt='force',
        user_agent='LifeLine/1.0')

    auth_uri = flow.step1_get_authorize_url()
    return redirect(auth_uri)


@app.route('/google-auth-callback')
def google_auth_callback():
  code = request.args.get('code')
  if code:
      # exchange the authorization code for user credentials
      flow = OAuth2WebServerFlow(settings.GOOGLE_API_CLIENT_ID,
                                 settings.GOOGLE_API_CLIENT_SECRET,
                                 "https://www.googleapis.com/auth/calendar")
      flow.redirect_uri = request.base_url
      try:
          credentials = flow.step2_exchange(code)
      except Exception as e:
          print "Unable to get an access token because ", e.message

      # store these credentials for the current user in the session
      # This stores them in a cookie, which is insecure. Update this
      # with something better if you deploy to production land
      session['credentials'] = credentials.to_json()

  return redirect(url_for('today'))


if __name__ == '__main__':
    app.run(debug=True)
