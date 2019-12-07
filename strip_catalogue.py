import requests
import re
import os
import time
import random
import scrapercleaner
from bs4 import BeautifulSoup

def get_courses_for_major(major):
    '''
    Returns a list of tuples of (course name, description, raw prereqs), and then saves the result to file
    NOTE: PREREQ STILL IN RAW FORM NEEDS TO BE PARSED

    :param: major
    :type: str

    :return: list
    '''
    assert type(major) is str, 'major error: type must be string'
    assert major != '', 'major error: cannot be empty string'

    # retrieve html from url
    split_text = get_lines_from_url('https://www.ucsd.edu/catalog/courses/'+major+'.html')

    # iterate over the lines of html
    course_names = {}
    for i in range(len(split_text)):

        # try to identify course
        course_name, offset = find_ending_helper(split_text, '<p class=\"course-name\">', '.*', '</p>', i)

        # if course name found
        if course_name != '':

            # try to identify description
            description, dummy = find_ending_helper(split_text, 'class=\"course-descriptions\">', '.*', '</p>', i + 1 + offset)
            # remove the prereq string from the description (since its added from a different source later)
            prereq_len = 0
            prereq_strip = re.search('<.*', description)

            if prereq_strip != None:
                prereq_len = len(prereq_strip.group())

            # if no prereq string, keep as is, otherwise trim
            if prereq_len != 0:
                course_names[course_name] = description[:-prereq_len]
            else:
                course_names[course_name] = description

    # find the prereqs for every course
    course_map = {}
    for course in course_names:
        course_compact = re.search(major+'.*\.', course)

        if course_compact:
            course_compact = course_compact.group().replace(' ', '')[:-1]
            raw_prereq = get_prereq_helper(course_compact)

            course_map[course] = (course_names[course], raw_prereq)

    # write results to file
    try:
        f_write = open("./raw_course_data/" + major + ".txt", "w+", encoding="utf-8")
        f_write.write(str(course_map))
        f_write.close()
    except:
        print('unable to write course info to directory')

    return course_map

def get_prereq_helper(course_code):
    '''
    Retrieves the prereqs for the given course code.
    NOTE: STILL IN RAW FORM NEEDS TO BE PARSED

    :param: course_code
    :type: str

    :return: str
    '''
    assert type(course_code) is str, 'course_code error: type must be string'
    assert course_code != '', 'course_code error: cannot be empty string'

    # retrieve html from url
    prereq_url = 'https://act.ucsd.edu/scheduleOfClasses/scheduleOfClassesPreReq.htm?termCode='
    term_code = 'WI20'
    new_url = prereq_url + term_code + '&courseId=' + course_code

    # convert to list
    prereq_lines = get_lines_from_url(new_url)
    prereq_str_raw_list = []
    # iterate over html, searching for course string matches
    for i in range(len(prereq_lines)):

        box_match, offset = find_ending_helper(prereq_lines, '<td style=\"border-style:solid;', '.*', '\">', i)
        course_check, _ = find_ending_helper(prereq_lines, '<span class=\"bold_text\">', '.*', '</span>', i + 1 + offset)

        # if both box and class have matched, return the result
        if box_match != '' and course_check != '':
            prereq_str_raw, _ = find_ending_helper(prereq_lines, '<td style=\"border-style:solid;', '.*', '</td>', i)
            prereq_str_raw_list.append(prereq_str_raw)

    if prereq_str_raw_list:
        return 'and'.join(prereq_str_raw_list)
    return None

def get_lines_from_url(url):
    '''
    Converts a webpage given by url into a list of strings. Used as helper in all functions.

    :param: url
    :type: str

    :return: list
    '''
    assert type(url) is str, 'url error: type must be string'
    assert url != '', 'major error: cannot be empty string'

    # send get request to url and parse the result
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    webtext = str(soup.getText)

    return webtext.splitlines()

def find_ending_helper(full_text, begin_str, mid_str, end_str, cur_index):
    '''
    Iterates over following strings of the webpage full_text, matching the begin_str, mid_str, and end_str
    over multiple lines. Used as a helper for get_courses_for_major(). Returns the first list of strings that match
    the parameter

    :param: full_text
    :type: list

    :param: begin_str
    :type: str

    :param: mid_str
    :type: str

    :param: end_str
    :type: str

    :param: cur_index
    :type: int

    :return: list
    '''
    assert type(full_text) is list, 'full_text error: type must be list'

    assert type(begin_str) is str, 'begin_str error: type must be string'
    assert begin_str != '', 'begin_str error: cannot be empty string'
    assert type(mid_str) is str, 'mid_str error: type must be string'
    assert mid_str != '', 'mid_str error: cannot be empty string'
    assert type(end_str) is str, 'end_str error: type must be string'
    assert end_str != '', 'end_str error: cannot be empty string'

    assert type(cur_index) is int, 'cur_index error: type must be int'
    assert cur_index >= 0, 'cur_index error: cannot be negative'

    # if the current index is more than length, then return none
    if cur_index >= len(full_text):
        return ('', 0)

    # strip the first two lines
    full_stripped_result = re.search(begin_str+mid_str+end_str, full_text[cur_index])
    temp_stripped_result = re.search(begin_str+mid_str, full_text[cur_index])

    # get the length of the matching strings
    begin_strip_len = len(begin_str)
    end_strip_len = len(end_str)

    # iterate over all the lines of the html
    stripped_string = ''
    j = 0
    if full_stripped_result == None and temp_stripped_result != None:

        # view result of first string
        stripped_string = temp_stripped_result.group()[begin_strip_len:]
        temp_stripped_result = full_stripped_result

        # iterate until the match is found
        while temp_stripped_result == None:

            # if iterated over webpag ewithout match, then return since no match found
            j += 1
            if cur_index + j >= len(full_text):
                return ('', 0)

            # get the next string and saved the previous stripped result
            temp_stripped_result = re.search(mid_str+end_str, full_text[cur_index + j])
            stripped_string += ' ' + full_text[cur_index + j].lstrip()

            # break if matches the end_str
            if temp_stripped_result != None:
                stripped_string = stripped_string[:-end_strip_len]
                break

    # remove the matching strings
    elif full_stripped_result != None:
        stripped_string = full_stripped_result.group()[begin_strip_len:-end_strip_len]

    return (stripped_string, j)

def get_quarter_offerings(major, quarter):
    '''
    Returns the list of courses offered in the given quarter and saves to file.

    :param: major
    :type: str

    :param: quarter
    :type: str

    :return: list
    '''
    assert type(major) is str, 'major error: type must be string'
    assert major != '', 'major error: cannot be empty string'
    assert type(quarter) is str, 'quarter error: type must be string'
    assert quarter != '', 'quarter error: cannot be empty string'

    try:
        unique_list = []
        with open('./quarter_data/' + major + "_" + quarter + '.txt', 'r', encoding='utf-8') as f:
            for line in f:
                unique_list.append(line.strip())
        return unique_list
    except:
        # url for retrieving the class quarter schedule
        test_url = 'https://act.ucsd.edu/scheduleOfClasses/scheduleOfClassesStudentResult.htm'

        # headers for html post
        data = {
            'selectedTerm': quarter,
            'loggedIn': 'false',
            'selectedSubjects': major,
            '_selectedSubjects': 1,
            'schedOption1': True,
            'schedOption11': True,
            'schedOption12': True,
            'schedOption2': True,
            'schedOption4': True,
            'schedOption5': True,
            'schedOption3': True,
            'schedOption7': True,
            'schedOption8': True,
            'schedOption13': True,
            'schedOption10': True,
            'schedOption9': True,
        }

        # start the html session and post to url
        s = requests.Session()
        first_page = s.post(test_url, data).text

        # get the first list of courses
        course_list = get_quarter_helper(first_page)

        # iterate over remaining pages
        i = 2
        cur_page = s.get('https://act.ucsd.edu/scheduleOfClasses/scheduleOfClassesStudentResult.htm?page=' + str(i)).text
        while re.search('<title>Apache Tomcat/8.0.33 - Error report</title>', ''.join(cur_page)) == None:

            # extend the current course list
            course_list.extend(get_quarter_helper(cur_page))
            i += 1

            # get the html of the next page
            cur_page = s.get(
                'https://act.ucsd.edu/scheduleOfClasses/scheduleOfClassesStudentResult.htm?page=' + str(i)).text

        # unique the course list
        unique_list = list(set(course_list))

        # write to file, appending course num to major
        try:
            f_write = open('./quarter_data/' + major + "_" + quarter + '.txt', 'w+', encoding='utf-8')
            f_write.writelines(str(course)+"\n" for course in unique_list)
            f_write.close()
        except:
            print('unable to write course info to directory')

        return unique_list

def get_quarter_helper(webpage):
    '''
    Used to identify course number for get_quarter_offerings(). Returns unique list
    of course numbers

    :param: webpage
    :type: str

    :return: list
    '''
    assert type(webpage) is str, 'webpage error: type must be string'
    assert webpage != '', 'webpage error: cannot be empty string'

    # iterate over lines of webpage to find course number
    course_list = []
    for line in webpage.splitlines():
        search_res = re.search('class=\"crsheader\">.+</td>', line)

        if search_res != None:

            course_list.append(search_res.group()[18:-5])

    # return unique numbers
    return list(set(course_list))


def get_clean_course_prereq(major):
    '''
    Convenience function that wraps clean_scrape and get_raw_course_list.
    :param major:
    :type major: str
    :return: tuple
    '''
    assert isinstance(major, str)
    return scrapercleaner.clean_scrape(get_raw_course_list(major))

"""

======================================
ONLY CALL FUNCTIONS BELOW THIS COMMENT
======================================

- Loge

"""


def get_raw_course_list(major):
    '''
    Returns the raw list of tuples of (course name, description, prereq).
    STILL IN RAW FORM: PREREQ NEEDS TO BE PARSED

    :param: major
    :type: str

    :return: list
    '''
    assert type(major) is str, 'major error: type must be string'
    assert major != '', 'major error: cannot be empty string'

    # check if save directory exists, if not create
    if not os.path.isdir("./raw_course_data/"):
        os.mkdir('./raw_course_data/')

    # if already searched, pull from file
    if os.path.exists("./raw_course_data/" + major + ".txt"):
        f_read = open("./raw_course_data/" + major + ".txt", "r", encoding="utf-8")
        course_dict = f_read.read()
        f_read.close()

        return eval(course_dict)
    else:
        return get_courses_for_major(major)


def get_quarter_list(major, quarter):
    '''
    Returns a list of offered courses in the major in the given quarter. NOTE: quarter
    is of the form WI20, FA19, SP20, etc.

    :param: major
    :type str

    :param: quarter
    :type: str

    :return: list
    '''
    assert type(major) is str, 'major error: type must be string'
    assert major != '', 'major error: cannot be empty string'
    assert type(quarter) is str, 'quarter error: type must be string'
    assert quarter != '', 'quarter error: cannot be empty string'

    # check if save directory exists, if not create
    if not os.path.isdir("./quarter_data/"):
        os.mkdir('./quarter_data/')

    # if already searched, pull from file
    if os.path.exists("./quarter_data/" + major + "_" + quarter + ".txt"):
        f_read = open("./quarter_data/" + major + "_" + quarter + ".txt", "r", encoding="utf-8")
        course_list = f_read.read().splitlines()
        f_read.close()

        return course_list
    else:
        return get_quarter_offerings(major, quarter)

def develop_plan(course_list, max_num, start_qtr):
    '''
    Returns the fastest route to completion of the course list over quarters taking max_num courses per quarter.

    :param course_list: list
    :param max_num: int
    :param start_qtr: int
    :return: list
    '''
    assert isinstance(course_list, list)
    assert isinstance(max_num, int)
    assert isinstance(start_qtr, int)
    assert max_num > 0 and start_qtr > 0

    major_list = set()
    for course in course_list:
        major_list.add(re.search('[a-zA-Z]+', course).group())

    fa_list = []
    wi_list = []
    sp_list = []
    prereq_map = {}
    for major in major_list:
        fa_major_list = get_quarter_list(major, 'FA19')
        fa_list.extend([major + ' ' + course for course in fa_major_list])

        wi_major_list = get_quarter_list(major, 'WI19')
        wi_list.extend([major + ' ' + course for course in wi_major_list])

        sp_major_list = get_quarter_list(major, 'SP19')
        sp_list.extend([major + ' ' + course for course in sp_major_list])

        prereq_list = get_clean_course_prereq(major)
        prereq_map.update({major + ' ' + val[0]:val[1] or [] for val in prereq_list})

    fa_courses = [course for course in course_list if course in fa_list]

    wi_courses = [course for course in course_list if course in wi_list]
    sp_courses = [course for course in course_list if course in sp_list]
    combined_courses = fa_courses.copy()
    combined_courses.extend(wi_courses)
    combined_courses.extend(sp_courses)

    course_quarter_list = []
    course_quarter_list.append(fa_courses)
    course_quarter_list.append(wi_courses)
    course_quarter_list.append(sp_courses)

    final_plan = []
    cur_quarter = start_qtr
    found_courses = [course for course in course_list if course in combined_courses]
    needed_courses = set([course for course in found_courses if course in prereq_map.keys()])

    while len(needed_courses) != 0:
        offered_quarter_courses = [course for course in course_quarter_list[cur_quarter % 3] if course in needed_courses]

        eligible_courses = [t_course for t_course in offered_quarter_courses \
                            if not set([list(set(sublist).intersection(set(found_courses)))[random.randrange(len(set(sublist).intersection(set(found_courses))))]
                                        for sublist in prereq_map[t_course] if list(set(sublist).intersection(set(found_courses))) != []]).intersection(needed_courses)]

        if cur_quarter % 150 == 0:
            print('ERROR')
            print(cur_quarter)
            print(needed_courses)
            print([prereq_map[p_course] for p_course in needed_courses])
            print(offered_quarter_courses)
            print(eligible_courses)
            return final_plan

        if len(eligible_courses) > max_num:
            eligible_courses = eligible_courses[:max_num]

        final_plan.append(eligible_courses.copy())
        needed_courses.difference_update(eligible_courses)
        cur_quarter += 1

    return final_plan

def develop_plan_recursion(course_list, max_num, start_qtr):
    '''
    Recursively generates all of the prereqs for a given course list, then runs the course planner.

    :param course_list: list
    :param max_num: int
    :param start_qtr: int
    :return: list
    '''
    assert isinstance(course_list, list)
    assert isinstance(max_num, int)
    assert isinstance(start_qtr, int)
    assert max_num > 0 and start_qtr > 0

    all_courses = set(course_list)
    last_courses = set()

    cur_prereq_map_simple = develop_plan_recursion_helper(course_list)
    while not last_courses == all_courses:
        last_courses = all_courses.copy()

        for course in last_courses:
            if course in cur_prereq_map_simple:
                all_courses.update(cur_prereq_map_simple[course])
        cur_prereq_map_simple = develop_plan_recursion_helper(all_courses)

    return develop_plan(all_courses, max_num, start_qtr)

def develop_plan_recursion_helper(course_list):
    '''
    Returns the prereq mapping for all majors given in course_list

    :param course_list: list
    :return: list
    '''
    assert isinstance(course_list, list)

    major_list = set()
    for course in course_list:
        major_list.add(re.search('[a-zA-Z]+', course).group())

    prereq_map_init = {}
    for major in major_list:
        prereq_list = get_clean_course_prereq(major)
        prereq_map_init.update({major + ' ' + val[0]: val[1] or [] for val in prereq_list})

    return {course: [sublist[random.randrange(len(sublist))] for sublist in prereq_map_init[course]] \
            for course in prereq_map_init}

def iterate_plan(course_list, max_num, start_qtr, num_iterations):
    '''
    Takes the minimum length planner of num_interations executions of develop_plan

    :param course_list: list
    :param max_num: int
    :param start_qtr: int
    :param num_iterations: int
    :return: list
    '''
    assert isinstance(course_list, list)
    assert isinstance(max_num, int)
    assert isinstance(start_qtr, int)
    assert max_num > 0 and start_qtr > 0 and num_iterations > 0

    return min([develop_plan(course_list, max_num, start_qtr) for i in range(num_iterations)], key=len)


def iterate_plan_recursions(course_list, max_num, start_qtr, num_iterations):
    '''
    Takes the minimum length planner of num_interations executions of develop_plan using a
    recursively generated prereqs

    :param course_list: list
    :param max_num: int
    :param start_qtr: int
    :param num_iterations: int
    :return: list
    '''
    assert isinstance(course_list, list)
    assert isinstance(max_num, int)
    assert isinstance(start_qtr, int)
    assert isinstance(num_iterations, int)
    assert max_num > 0 and start_qtr > 0 and num_iterations > 0

    return min([develop_plan_recursion(course_list, max_num, start_qtr) for i in range(num_iterations)], key=len)


'''

BELOW ARE PRESET TO TRY USING OUR FUNCTIONS

'''

ece_preset = ['MATH 10A', 'ECE 5', 'ECE 25', 'ECE 30', 'ECE 35', 'ECE 45', 'ECE 65', 'ECE 15', 'ECE 17', 'MATH 18', 'MATH 20A', \
              'MATH 20B', 'MATH 20C', 'MATH 20D', 'MATH 20E', 'CHEM 6A', 'PHYS 2A', 'PHYS 2B', 'PHYS 2C', 'ECE 100', \
              'ECE 101', 'ECE 107', 'ECE 109', 'ECE 171A', 'ECE 174', 'ECE 175A', 'ECE 171B', 'ECE 111', 'ECE 153', \
              'ECE 161A', 'ECE 161B', 'ECE 161C', 'ECE 164', 'ECE 143', 'ECE 158A', 'ECE 158B', 'ECE 16', 'ECE 102']
cse_preset = ['CSE 8B', 'CSE 12', 'CSE 15L', 'CSE 20', 'CSE 21', 'CSE 30', 'CSE 3', 'CSE 7', 'MATH 20A', 'MATH 20B', \
              'MATH 20C', 'MATH 18', 'PHYS 2A', 'PHYS 2B', 'CSE 103', 'CSE 100', 'CSE 101', 'CSE 105', 'CSE 110', \
              'CSE 140', 'CSE 141', 'CSE 120', 'CSE 130', 'CSE 107', 'CSE 150A', 'ECE 174', 'ECE 153', 'CSE 151', \
              'CSE 152', 'CSE 154', 'CSE 156', 'CSE 166']
nano_preset = ['MATH 18', 'MATH 20A', 'MATH 20B', 'MATH 20C','MATH 20D', 'MATH 20E', 'PHYS 2A', 'PHYS 2B', 'PHYS 2C', \
               'PHYS 2D', 'CHEM 6A', 'CHEM 6B', 'CHEM 6C', 'NANO 15', 'NANO 106', 'NANO 107', 'NANO 1', 'NANO 101', \
               'NANO 102', 'NANO 103', 'NANO 104', 'NANO 110', 'NANO 111', 'NANO 112', 'NANO 120A', 'NANO 120B', \
               'NANO 141A', 'NANO 141B', 'NANO 108', 'NANO 148', 'NANO 158', 'NANO 174', 'NANO 168']
se_preset = ['MATH 20A', 'MATH 20B', 'MATH 20C', 'SE 1', 'SE 3', 'CHEM 6A', 'PHYS 2A', 'PHYS 2B', 'MATH 20D', 'MATH 18', \
             'MATH 20E', 'SE 101A', 'SE 101B', 'SE 9', 'PHYS 2C', 'SE 110A', 'SE 110B', 'SE 104', 'SE 101C', 'SE 115', \
             'SE 131', 'SE 121A', 'SE 121B', 'SE 130B', 'SE 130A', 'SE 125', 'SE 140A', 'SE 140B', 'SE 167', 'SE 168', \
             'SE 163', 'SE 160A', 'SE 160B']
mae_preset = ['MATH 20B', 'MATH 20C', 'PHYS 2A', 'PHYS 2B', 'MAE 3', 'MATH 18', 'MATH 20E', 'MAE 8', 'MAE 30A', 'MAE 30B' \
              'MAE 131A', 'MAE 101A', 'MAE 101B', 'MAE 143A', 'MAE 143B', 'MAE 170', 'MAE 160', 'MAE 171A', 'MAE 156B', \
              'MAE 156A', 'MATH 20A', 'CHEM 6A', 'MATH 20D', 'PHYS 2C', 'ESYS 101', 'MAE 3', 'CENG 100', 'MAE 105', \
              'MAE 107', 'CHEM 171', 'MAE 101C', 'MAE 150', 'MAE 122', 'ECE 174', 'MAE 120', 'ECE 143', 'MAE 130']
beng_preset = ['BENG 1', 'BILD 1', 'CHEM 6A', 'CHEM 6B', 'MAE 8', 'MATH 20A', 'MATH 20B', 'MATH 20C', 'PHYS 2A', \
               'PHYS 2B', 'PHYS 2BL', 'BENG 100', 'BENG 109', 'CHEM 7L', 'MAE 3', 'MAE 140', 'MATH 20D', 'MATH 20E', \
               'MATH 20F', 'PHYS 2C', 'PHYS 2CL', 'BENG 101', 'BENG 103B', 'BENG 110', 'BENG 112A', 'BENG 140A', \
               'BENG 140B', 'BENG 172', 'BENG 186B', 'BENG 187A', 'BENG 191', 'MAE 170', 'BENG 122A', 'BENG 125', \
               'BENG 130', 'BENG 186A', 'BENG 187B', 'BENG 187C', 'BENG 187D', 'BENG 169A', 'BENG 169B', 'BENG 191', \
               'MAE 107', 'MAE 150', 'ECE 171', 'ECE 174']
