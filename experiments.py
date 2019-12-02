from strip_catalogue import get_raw_course_list, get_quarter_offerings
from scrapercleaner import clean_scrape
import networkx as nx
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

def generate_graph(dept, courses, undergrad=False):
    indep_courses = []
    prereqs = []
    for course in courses:
        k, v = course
        # remove grad classes
        if undergrad:
            num = re.findall('\d+', k)[0]
            if int(num) >= 200:
                continue
        if v:
            for i in v:
                weight = len(i)
                for j in i:
                    if j.startswith(dept):
                        prereqs.append([j.split()[1], k, 1/weight])
        # if no prereqs, add as independent node
        else:
            indep_courses.append(k)

    G = nx.DiGraph()
    G.add_nodes_from(indep_courses)
    G.add_weighted_edges_from(prereqs)
    return G

def find_root(G, child):
    """
    Find the root of any given node.
    """
    assert isinstance(G, nx.classes.digraph.DiGraph)
    assert isinstance(child, str)

    parent = list(G.predecessors(child))
    if len(parent) == 0:
        return child
    else:
        return find_root(G, parent[0])

def get_flexibility(G):
    heads = set()
    for i in G.nodes:
        r = find_root(G, i)
        if r != i:
            heads.add(r)
    tails = [n for n in G.nodes() if G.out_degree(n) == 0]
    sum = 0
    for h in heads:
        for t in tails:
            sum += len(list(nx.all_simple_paths(G,h,t)))
    return sum

if __name__ == "__main__":
    depts = ['ECE', 'CSE', 'MAE', 'BENG', 'NANO', 'SE']
    for dept in depts:
        raw_courses = get_raw_course_list(dept)
        courses = clean_scrape(raw_courses)
        avg = get_avg_num_prereqs(courses, True)
        print("average number of prereqs for {} (undergrad): {}".format(dept, avg))

        G = generate_graph(dept, courses, True)
        print("out-degree of each course:")
        for (course, out_deg) in G.out_degree:
            print("{}, {}".format(course, out_deg))

        print("ancestor count of each course:")
        for n in G.nodes():
            print("{}, {}".format(n, len(nx.algorithms.dag.ancestors(G, n))))
        print("flexibility: {}".format(get_flexibility(G)/G.number_of_nodes()))

