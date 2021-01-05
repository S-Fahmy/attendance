
from googlecalendar.publicholidays import get_egypt_public_holidays
from models import Holiday, insert_bulk
from datetime import datetime


def syncHolidaysDb(year):
    reset_holidays(year)

    holiday_events = get_egypt_public_holidays(year)
    holidays = []

    if holiday_events != None:

        for event in holiday_events:

            start = event['start'].get(
                'dateTime', event['start'].get('date'))
            holidays.append(Holiday(name=event['summary'], date=start))

        insert_bulk(holidays)

    return holidays


def reset_holidays(year):
    # delete holidays record of the wanted year before proceeding
    existing_holidays = Holiday.query.filter(Holiday.date >= datetime(
        year, 1, 1), Holiday.date < datetime(year+1, 1, 1)).delete()
