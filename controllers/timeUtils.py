from datetime import datetime, timedelta

'''accepts a string time value like this: "9:30" and converts it to datetime time() '''
def get_time_from_string(time_string):
    try:
        if time_string.count(':') == 1:
            print('YES YA KOS OMAK ' + time_string)
            print(time_string.count(':'))
            time = datetime.strptime(time_string, '%H:%M').time()
        else:
            print("NO YA KOS OMEN OMAK")
            time = datetime.strptime(time_string, '%H:%M:%S').time()

    except Exception as e:
        print("KOSOMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK")
        print(e)

    print(time)
    return time

def get_time_with_seconds_from_string(time_string):
    try:
        time = datetime.strptime(time_string, '%H:%M:%S').time()
    except Exception as e:
        print(e)

        
    return time


'''
returns certain time of a day in minutes
24 hours format
'''
def get_minutes_from_time(time):
    #to get total minutes: (hour*60) + minute
    minutes = (time.hour *60) + time.minute
    return minutes


def get_hms_from_minutes(minutes):
    return timedelta(minutes=minutes)


'''
this checks for the string date format first before calling the right function
'''
def get_date_from_string(date):
    #i need to automatically check the date format here, if its y-m-d or m-d-y
    year_or_day = date.split("-")[0]
    
    if int(year_or_day) <= 12:
        return get_date_from_string_mdy(date)
    else:
        return get_date_from_string_ymd(date)
    
def get_date_from_string_mdy(date):
    try:
        time = datetime.strptime(date, '%m-%d-%Y')
    except Exception as e:
        print('im here')
        print(e)
    return time


def get_date_from_string_ymd(date):
    try:
        time = datetime.strptime(date, '%Y-%m-%d')
    except Exception as e:
        print('im here')
        print(e)
    return time
'''
    returns the number of days between a start date and an end date, while also counting the startdate
'''

def get_days_between_two_dates(start_date = None, end_date = None):
    get_date_from_string(end_date)
    delta = get_date_from_string(end_date) - get_date_from_string(start_date)    # 31 days
    # the +1 to count the start date too.
    
    
    return delta.days + 1

def get_day_name(day_date):
    return day_date.strftime("%A")


def get_day_date_from_start_date(start_date, day_num):
    sdate = get_date_from_string(start_date)
    day = sdate + timedelta(days=day_num)
    return day.date()