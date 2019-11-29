import re


def split_at_or(prereq_list):
   '''
   Don't call this
   Splits prereqs 'or' into list
   '''
   for elem in prereq_list:
      yield elem.split('or')



######### Call Function Below ###########
def clean_scrape(raw_course_list):
   '''
   Input is from get_raw_course_list() function
   Cleans up scraper used to get prereq courses

   :returns:list
   '''
   #General HTML clean up
   ece_courses = [   #Course Number,Prereqs
                     [key.partition(' ')[2].partition('.')[0],re.sub(r'<.*?>|border.*?>|\(.*?\)|\)|\*+| +','',a[key][1])]
                     if a[key][1] is not None
                     else [key.partition(' ')[2].partition('.')[0],None]
                     for key in a
                  ]
   print(*ece_courses,sep='\n')
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
   return tuple(zip(ece_course_num,prereq_split_or))
