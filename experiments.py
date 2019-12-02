from strip_catalogue import get_raw_course_list, get_quarter_offerings
from scrapercleaner import clean_scrape
import re
import string

def get_avg_num_prereqs(courses, undergrad=False):
    """
    Gets average number of prereqs for given courses, optionally only for undergrad.
    Input should be same format as clean_scrape().
    :param courses: list of courses, same as output of clean_scrape()
    :type courses: list or tuple
    :param undergrad: whether only undergrad should be considered
    :type undergrad: true
    :return: int
    """
    assert isinstance(courses, list) or isinstance(courses, tuple)
    sum = 0
    count = 0
    for (course, prereqs) in courses:
        if undergrad:
            num = re.findall('\d+', course)[0]
            if int(num) >= 200:
                continue
        if prereqs:
            sum += len(prereqs)
            count += 1
    return sum/count
if __name__ == "__main__":
    depts = ['ECE', 'CSE', 'MAE', 'BENG', 'NANO', 'SE']
    print("average number of prereqs per department (undergrad only):")
    for dept in depts:
        raw_courses = get_raw_course_list(dept)
        courses = clean_scrape(raw_courses)
        avg = get_avg_num_prereqs(courses, True)
        print("{}: {}".format(dept, avg))
