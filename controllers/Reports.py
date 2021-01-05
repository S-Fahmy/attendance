

from datetime import datetime, timedelta
from controllers.timeUtils import *


class reportsBuilder():

    # these variables presents the arrival delays or earlies, and leaving early or overtime, for the days in the selected time period
    check_in_calculation_total = 0
    check_out_calculation_total = 0
    days_without_checks = 0
    total_absent_days = 0
    daily_attendances_json = []
    total_work_time = 0

    '''
    return a api ready report response
    -parameters: Schedule model object , Attendance model object

    - calculates each day attendances status:{
        check_in_status: late, on time, early
        check_in_calculation_total: the number is difference between the checkin time and the schedule check in +/-

        check_out_status: late, on time, early
        check_out_calculation: the number is difference between the checkout time and the schedule checkout +/-

    }
    '''
  

    def build_report(self, employee_active_schedule, attendances_list, holidays, start_date, end_date):
        self.reset_class_variables()
        
        # try:
        selected_time_period_days = get_days_between_two_dates(start_date, end_date)
        shift_begins = employee_active_schedule.shift_begins
        shift_ends = employee_active_schedule.shift_ends

        # loops over the attendances in the selected time period. build the required data for the report from each day and also add needed data to a total for the time period
        # for attendance_day in attendances_list:
        att_index = 0
        for day_num in range(selected_time_period_days):
            #day_num and att_index start at 0
            day_date = get_day_date_from_start_date(start_date, day_num)

            if self.is_absent(att_index, attendances_list, day_date, holidays) == False:

                attendance_day = attendances_list[att_index]
                self.calculate_workday(attendance_day, shift_begins, shift_ends, day_date, holidays, employee_active_schedule)
                
                att_index = att_index + 1

        # end loop

        # building the final report json format
        report = self.ready_report_json(employee_active_schedule.title, len(attendances_list), employee_active_schedule.shift_begins, employee_active_schedule.shift_ends,
                                        self.check_in_calculation_total, self.check_out_calculation_total, self.daily_attendances_json, self.days_without_checks, self.total_absent_days)

        
        
        return report

    def calculate_workday(self, attendance_day, shift_begins_time, shift_ends_time, day_date=None, holidays = [], schedule=None):
        
        shift_begins_minutes = get_minutes_from_time(shift_begins_time)
        shift_ends_minutes = get_minutes_from_time(shift_ends_time)
        shift_total_time = shift_ends_minutes - shift_begins_minutes

        check_in_and_out_times = get_check_in_out_times(attendance_day.checkin, attendance_day.checkout, schedule)

        check_in_status = self.get_check_in_status(check_in_and_out_times['check_in'], shift_begins_minutes)
        check_out_status = self.get_check_out_status(check_in_and_out_times['check_out'], shift_ends_minutes)
        
        #TODO: if this day is equal to a weekend day or a holiday day, then handle it
        if get_day_name(day_date) in "Friday Saturday" or any(holiday.date == day_date for holiday in holidays):
                
                check_in_status += "/ Holiday or weekend!"
                check_out_status += "/ Holiday or weekend!"
            
            
        #first before calculating we need to check the 'missing check rule' is set to absent
        if schedule.missing_check_penalty == "A":
             if check_in_and_out_times['check_in'] == None or check_in_and_out_times['check_out'] == None:
                 self.set_absence(day_date, "missing a check")
                 return #end here
             
        # do the checkin
        day_check_in_calculation = self.calculate_checkin_time(check_in_and_out_times['check_in'], shift_begins_minutes, schedule.missing_check_penalty)
        self.check_in_calculation_total += day_check_in_calculation

        # do the checkout
        day_check_out_calculation = self.calculate_checkout_time(check_in_and_out_times['check_out'], shift_ends_minutes, schedule.missing_check_penalty)
        self.check_out_calculation_total += day_check_out_calculation

        day_total_attendance_time = shift_total_time + day_check_in_calculation + day_check_out_calculation
        self.total_work_time += day_total_attendance_time

        # building a list of daily attendances report formatted to json
        self.daily_attendances_json.append(self.format_attendance_for_report(attendance_day, check_in_and_out_times['check_in'], check_in_status, day_check_in_calculation, check_in_and_out_times['check_out'], check_out_status, day_check_out_calculation, day_total_attendance_time))



    def calculate_checkin_time(self, check_in_time=None, shift_begins_minutes=0, missing_check_penalty="0"):

        if check_in_time == None:
            # -230
            day_check_in_calculation = -int(missing_check_penalty)
            self.days_without_checks += 1

        else:
            # arriving late = negative value / arriving early = positive value
            day_check_in_calculation = shift_begins_minutes - get_minutes_from_time(check_in_time)

        return day_check_in_calculation

    def calculate_checkout_time(self, check_out_time=None, shift_ends_minutes=0, missing_check_penalty="0"):

        if check_out_time == None:
            day_check_out_calculation = -int(missing_check_penalty)
            self.days_without_checks += 1

        else:
            # overtime = positive value / leaving early = negative value
            day_check_out_calculation = get_minutes_from_time(check_out_time) - shift_ends_minutes

        return day_check_out_calculation

    def is_absent(self, att_index, attendances_list, day_date, holidays):

        if att_index >= len(attendances_list) or attendances_list[att_index].day > day_date:
            # TODO: get weekends from the db
            # TODO 2:excused absence

            if get_day_name(day_date) in "Friday Saturday" or any(holiday.date == day_date for holiday in holidays):
                #if its a weekend or a holiday just return true but we don't do anything else
                return True
            
            self.set_absence(day_date, "unexcused absence")
            return True

        return False
    
    def set_absence(self, day_date, execuse):
        self.total_absent_days += 1
        self.daily_attendances_json.append(self.format_absent_for_report(day_date, execuse))

    def get_check_in_status(self, checkin_time, shift_begins_minutes):
        if checkin_time == None:
            return "Didn't clock in"
        elif get_minutes_from_time(checkin_time) > shift_begins_minutes:

            return 'Late Arrival'

        elif get_minutes_from_time(checkin_time) < shift_begins_minutes:

            return 'Early Arrival'

        else:
            return 'Arrived on time'

    def get_check_out_status(self, checkout_time, shift_ends_minutes):

        if checkout_time == None:
            return "Didn't clock out"

        elif get_minutes_from_time(checkout_time) > shift_ends_minutes:

            return 'OverTime'

        elif get_minutes_from_time(checkout_time) < shift_ends_minutes:

            return 'Early Leave'

        else:
            return 'Left on time'

    def format_attendance_for_report(self, attendance_day, checkin, check_in_status, day_check_in_calculation, checkout, check_out_status, day_check_out_calculation, day_total_attendance_time):
        return {
            'id': attendance_day.id,
            'user_id': attendance_day.user_id,
            'day': str(attendance_day.day),
            "absent": False,
            'checkin': str(checkin),
            'checkout': str(checkout),

            "checkin_status": check_in_status,
            "check_in_calculation": day_check_in_calculation,
            "checkout_status": check_out_status,
            "check_out_calculation": day_check_out_calculation,
            "total_attendance_time": str(get_hms_from_minutes(day_total_attendance_time)),
            "has_or_owes": day_check_in_calculation + day_check_out_calculation

        }

    def format_absent_for_report(self, day, absence_reason):
        return {

            # 'user_id': attendance_day.user_id,
            'day': str(day),
            "absent": True,
            "absence_reason": absence_reason


        }

    def ready_report_json(self, employee_active_schedule_title, attendances_list_length, shift_begins, shift_ends, check_in_calculation_total, check_out_calculation_total, daily_atts_json, days_without_checks, total_absent_days):

        return {
            "schedule_title": employee_active_schedule_title,
            "attendances_days_count": str(attendances_list_length),
            "shift_begins": str(shift_begins),
            "shift_ends": str(shift_ends),
            "shift_total_time": str(get_hms_from_minutes(get_minutes_from_time(shift_ends)-get_minutes_from_time(shift_begins))),
            "overtime": self.is_over_time(self.check_in_calculation_total + self.check_out_calculation_total),
            "undertime": self.is_under_time(self.check_in_calculation_total + self.check_out_calculation_total),

            "arrival_total": check_in_calculation_total,
            "leave_total": check_out_calculation_total,
            "attendances": daily_atts_json,
            "days_without_checks": days_without_checks,
            "total_absent_days": total_absent_days,
            "total_work_time": self.total_work_time
        }

    # if worked time sum is positive then he worked extra time during this time period, negative means he owes

    def is_over_time(self, time):
        if time > 0:
            return time

        return 0

    def is_under_time(self, time):
        if time < 0:
            return time

        return 0
    
    def reset_class_variables(self):
    
        self.check_in_calculation_total = 0
        self.check_out_calculation_total = 0
        self.days_without_checks = 0
        self.total_absent_days = 0
        self.daily_attendances_json *= 0 
        self.total_work_time = 0     

    '''just some functions that print the report data for debugging purposes '''

    def print_day_data(self, check_in_status, day_check_in_calculation, check_out_status, day_check_out_calculation, day_total_attendance_time, daily_json):

        print(check_in_status + ' by: ')
        print(day_check_in_calculation)

        print(check_out_status + ' by: ')
        print(day_check_out_calculation)

        print('total time worked this day:')
        print(str(get_hms_from_minutes(day_total_attendance_time)))
        # print('the json is:')
        # print(daily_json)
        # print(" ")

    def print_time_period_data(self, check_in_calculation_total, check_out_calculation_total, has_or_owes_minutes, report_json):

        print('total checkin time: ')
        print(check_in_calculation_total)
        print("total checkout time")
        print(check_out_calculation_total)
        print("total time spent working")
        print(has_or_owes_minutes)

        print("the json is:")
        for key in report_json:
            if key == "attendances":
                print(key + ": ")
                for att in report_json[key]:
                    print(att)
                    print("  ")
            else:
                print(key + ": " + report_json[key])

    '''
    the times marked as check in or outs imported from the machine, cant be trusts, because they are prone to human error
    in the db the checkin and out are a string of times delimited by ,
    after extracting the times from string i need to find decide if the time is a check in or out by 
    comparing it to the schedule time periods for accepting check ins and check outs
    so far they are manually set and its TODO.
    '''


def get_check_in_out_times(employee_checkins, employee_checkouts, schedule):
    # imaginary schedule rules for the time periods and limits to accept chck ins and checkouts

    # TODO: think about how to handle those time periods
    
    check_ins_start = schedule.clock_in_start
    check_ins_end = schedule.clock_in_end

    check_out_start = schedule.clock_out_start
    check_out_end = schedule.clock_out_end

    # list of check times datetimes. NOTE: cast to set then cast to list if duplicates are a problem
    checks = employee_checkins.split(",") + employee_checkouts.split(",")
    # print(checks)

    # default values
    employee_checkin = None
    employee_checkout = None

    if checks != None and len(checks) >= 1:

        for check in checks:

            # time string will be around 8 letters.
            if len(check) > 5:

                check_time = get_time_with_seconds_from_string(check)

                if check_time >= check_ins_start and check_time <= check_ins_end:
                    # keep the earliest recorded check in
                    if employee_checkin == None or check_time < employee_checkin:
                        employee_checkin = check_time

                elif check_time >= check_out_start and check_time <= check_out_end:
                    # keep the last recorded check out
                    if employee_checkout == None or check_time > employee_checkout:
                        employee_checkout = check_time

    return {"check_in": employee_checkin, "check_out": employee_checkout}


    
 
