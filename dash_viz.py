import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import plotly.graph_objs as go
import re

from strip_catalogue import get_raw_course_list, get_quarter_offerings
from scrapercleaner import clean_scrape

def generate_graph(nodes, edges):
    """
    Generates a networkx directed graph based on lists of nodes and weighted edges (see networkx.DiGraph.add_weighted_edges_from()).
    :param nodes: nodes in graph
    :type nodes: list
    :param prereqs: weighted edges in graph
    :type prereqs: list
    :return: networkx.DiGraph
    """
    assert isinstance(nodes, list)
    assert isinstance(edges, list)
    G = nx.DiGraph()
    #G.add_nodes_from(nodes)
    G.add_weighted_edges_from(edges)
    return G

def generate_figure(G):
    """
    Generates a plotly figure of a networkx directed graph.
    :param G: directed graph
    :type G: networkx.DiGraph
    :return: plotly.graph_objs.Figure
    """
    assert isinstance(G, nx.DiGraph)

    # use graphviz for layout, since it is better at generating directed graph layouts with 'dot'
    pos = graphviz_layout(G, prog='dot')

    # extract the edge endpoint coordinates (from graphviz_layout) to use for drawing in dash
    edges = []
    for edge in G.edges.data('weight'):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edges.append((x0,y0,x1,y1, edge[2]))

    # create lines from the previously generated edges
    # TODO add arrow drawing somehow?
    shapes = [dict(
        type='line',
        x0 = i[0],
        y0 = i[1],
        x1 = i[2],
        y1 = i[3],
        layer = 'below',
        line = dict(color='rgb(127,127,127)',width=2,dash='dot' if i[4] < 1 else 'solid')
        ) for i in edges]

    # extract the node coordinates
    node_x, node_y = zip(*[pos[i] for i in G.nodes()])

    # create nodes for each course
    node_trace = go.Scatter(
        customdata= list(G.nodes().keys()),
        x=node_x, y=node_y,
        mode='markers+text',
        # NOTE: hoverinfo determines whether a point will show up on a click event (skip = excluded)
        hoverinfo='none',
        text = list(G.nodes().keys()),
        unselected=dict(marker=dict(opacity=0.5)),
        marker=dict(
            color='LightSkyBlue',
            size=40,
        ))

    # create the figure to display, with click & hover support
    return go.Figure(data=node_trace,
                 layout=go.Layout(
                    shapes = shapes,
                    showlegend=False,
                    clickmode='event+select',
                    hovermode='closest',
                    #dragmode='select',
                    selectdirection='v',
                    margin=dict(b=0,l=0,r=0,t=0),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,fixedrange=True),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,fixedrange=True))
           )

# predefined departments to display
depts = ['ECE', 'CSE', 'MAE', 'BENG', 'NANO', 'SE', 'MATH', 'PHYS']

# external css for 'n columns' class and other various helpers
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# page layout: title, graph, options, description
app.layout = html.Div([
        html.H1('Loading...', id='title'),
        dcc.Graph(id='graph',config={'displayModeBar': False}),
        html.Div(className='row', children = [
            html.Div([
                dcc.Markdown('### Choose a department: '),
                dcc.Dropdown(id='dept-select', options=[{'label': i, 'value': i} for i in depts], value='ECE', clearable=False),
            ], className='three columns'),
            html.Div([dcc.Markdown('',id='desc')], className='nine columns')
        ])
])

# markdown template for course description
desc_tmpl = """
### {}: {}

#### Full Prerequisites: {}

#### Description:
{}
"""

def get_dept_info(dept):
    """
    Gets the full course info for a specific department.
    :param dept: department code
    :type dept: str
    :return: networkx.DiGraph, list, list, list
    """
    raw_courses = get_raw_course_list(dept)
    courses = clean_scrape(raw_courses)
    # strip leading zero from course code (edge case: MAE 02, etc.)
    courses = [(i.lstrip("0"), j) for i, j in courses]
    course_desc = dict()
    for k, v in raw_courses.items():
        # split into course code, course title, and number of units (unused)
        k_split = k.replace("(", ".").split(".")
        # remove leading zero from course code
        course_dept_code = k_split[0].split()
        course_code = course_dept_code[0] + " " + course_dept_code[1].lstrip("0")
        course_desc[course_code] = [k_split[1].strip(), v[0]]

    courses_offered = get_quarter_offerings(dept, "FA19") + get_quarter_offerings(dept, "WI20") + get_quarter_offerings(dept, "SP20")
    # remove the department tags and draw each department as a single node
    # use weighted edges to show interchangeable prereqs
    indep_courses = []
    course_prereqs = []
    for course in courses:
        k, v = course
        # remove grad classes and courses not offered this year
        num = re.findall('\d+', k)[0]
        if int(num) >= 200 or k not in courses_offered:
            continue
        if v:
            for i in v:
                # TODO doesn't show other departments yet
                prereq_group = []
                for j in i:
                    if j.startswith(dept):
                        # check if the course actually exists in catalog and still offered this year
                        course_code = j.split()[1].lstrip("0")
                        if j in course_desc and course_code in courses_offered:
                            prereq_group.append([course_code, k])
                    # if from another department, just draw as a single node
                    else:
                        pass
                        #course_prereqs.append([j.split()[0], k, 1/weight])
                for i in prereq_group:
                    course_prereqs.append(i+[1/len(prereq_group)])

        # if no prereqs, add as independent node
        else:
            indep_courses.append(k)

    G = generate_graph(indep_courses, course_prereqs)

    # break up cycles if they are redundant (ex: class C requires A and B, but B requires A)
    for cycle in nx.cycle_basis(G.to_undirected()):
        # check if there is a distinct head and tail for a cycle, and head is connected directly to tail
        head = None
        tail = None
        for i in cycle:
            others = cycle.copy()
            others.remove(i)
            ancestors = nx.algorithms.dag.ancestors(G, i)
            descendants = nx.algorithms.dag.descendants(G, i)
            if all(o in ancestors for o in others):
                head = i
            elif all(o in descendants for o in others):
                tail = i
        if G.has_edge(tail, head):
            # find the other predecessor of head for the cycle
            other_adj = [adj for adj in cycle if adj in G.predecessors(head) and adj != tail]
            if len(other_adj):
                # check if it's an OR or an AND (don't remove if it's an OR)
                false_pos = False
                for (k, v) in courses:
                    if k == head:
                       for reqs in v:
                           if other_adj[0] in reqs and tail in reqs:
                               false_pos = True
                               break
                       break

            if not false_pos:
                print("removing edge from {} to {}".format(tail,head))
                G.remove_edge(tail,head)

    #print(nx.algorithms.dag.dag_longest_path(G))
    #G.remove_nodes_from(list(nx.isolates(G)))
    fig = generate_figure(G)
    return G, course_desc, fig, courses

# preload the data for specific departments, so they don't need to be fetched every time
dept_cache = dict()
for i in depts:
    print("caching {}".format(i))
    dept_cache[i] = get_dept_info(i)


@app.callback([Output('title', 'children'),Output('graph', 'figure'),Output('desc', 'children')],[Input('dept-select', 'value'), Input('graph', 'hoverData'),Input('graph','selectedData')])
def highlight_prereqs(dept,hoverData,selectedData):
    """
    Callback for click and hover events from Dash.
    Using the event node, it selects a course and its prereqs, and lowers the opacity of unrelated courses (and lines).
    Returns original figure with modified graphics (selection + opacity).

    :param hoverData: hover data
    :type hoverData: dict or None
    :param selectedData: selected data
    :type selectedData: dict or None
    :return: plotly.graph_objs.Figure
    """
    G, course_desc, fig, courses = dept_cache[dept]
    title = "{} Undergraduate Courses".format(dept)
    prereqs = []
    desc = ""
    point = None

    # if there's an error here, that means the selected node is from the old plot, so we don't need to highlight anything
    try:
        # extract the point id from event data
        if hoverData:
            point = hoverData['points'][0]['customdata']
        elif selectedData:
            point = selectedData['points'][0]['customdata']

        # obtain list of immediate prereqs from scraper, full prereqs from graph, and fill the description template
        if point:
            desc_list = course_desc[dept + " " + str(point)]
            prereqs = list(nx.algorithms.dag.ancestors(G, point))
            immediate_prereqs = next(c for c in courses if c[0] == point)[1]
            if not immediate_prereqs:
                prereqs_str = 'None'
            else:
                prereqs_str = ', '.join(" or ".join(i) for i in immediate_prereqs)
            desc = desc_tmpl.format(dept + " " + str(point), desc_list[0], prereqs_str, desc_list[1])

        # obtain node indices for dash to select
        prereqs.append(point)
        prereq_index = [i for i, e in enumerate(G.nodes()) if e in prereqs]

        # highlight all of the nodes if none are selected
        if not prereq_index:
            prereq_index = list(range(len(G.nodes())))

        fig['data'][0]['selectedpoints'] = prereq_index

        # change the opacity for edges which are on the prerequisite tree for selected course
        for i,(j,k) in enumerate(G.edges()):
            if j in prereqs and k in prereqs:
                fig['layout']['shapes'][i]['line']['color'] = 'rgb(127,127,127)'
            else:
                fig['layout']['shapes'][i]['line']['color'] = 'rgba(127,127,127,0.5)'
    except:
        pass

    return title, fig, desc

if __name__ == '__main__':
    app.run_server(debug=True)
