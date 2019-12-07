import re

def split_at_or(prereq_list):
   '''
   Don't call this
   Splits prereqs 'or' into list
   :param prereq_list: prereq list
   :type prereq_list: list
   :return: generator(str)
   '''
   assert isinstance(prereq_list, list)
   assert all(isinstance(i, str) for i in prereq_list)
   for elem in prereq_list:
      yield elem.split('or')

def course_splitter(course_str):
    '''
    Used to split MAJORXXX into MAJOR XXX
    :param course_str: course code
    :type course_str: str
    :return: str
    '''
    if not course_str:
       return None

    assert isinstance(course_str, str)
    major_str = ' '.join(re.findall("[a-zA-Z]{2,}\d", course_str))
    num_str = ' '.join(re.findall('\d+[a-zA-Z]*', course_str))

    return major_str[:-1] + " " + num_str

######### Call Function Below ###########
def clean_scrape(raw_course_list):
    '''
    Input is from get_raw_course_list() function
    Cleans up scraper used to get prereq courses

    :param raw_course_list: dict of raw courses
    :type raw_course_list: dict
    :return: tuple
    '''
    assert isinstance(raw_course_list, dict)
    a = raw_course_list

    #General HTML clean up
    ece_courses = [   #Course Number,Prereqs
                     [key.partition(' ')[2].partition('.')[0],re.sub(r'<.*?>|border.*?>|\(.*?\)|\)|\*+| +','',a[key][1])]
                     if a[key][1] is not None
                     else [key.partition(' ')[2].partition('.')[0],None]
                     for key in a
                  ]
    # print(*ece_courses,sep='\n')
    #Gets course num
    ece_course_num = [course[0] for course in ece_courses]



    #General split of prereqs using required classes
    prereq_split_and = [ #produces a list of required classes
                        ' '.join(course[1].split()).split('and')
                        if course[1]
                        else None
                        for course in ece_courses
                     ]

    #Splits 'or' sections
    prereq_split_or = [
                        list(split_at_or(prereq_list))
                        if prereq_list
                        else None
                        for prereq_list in prereq_split_and
                     ]

    final_prereq = [[[course_splitter(course) for course in or_split] for or_split in p_list] if p_list else None for p_list in prereq_split_or]

    return tuple(zip(ece_course_num,final_prereq))

