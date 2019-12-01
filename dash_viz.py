import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import plotly.graph_objs as go

from util import format_code, sort_codes
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

    # prune edges which are redundant (i.e. remove the shorter paths since longer ones exist already)
    for n in G.nodes():
        ancestors = nx.algorithms.dag.ancestors(G, n)
        for i in ancestors:
            paths = list(nx.all_simple_paths(G, i, n))
            if len(paths) > 1:
                for p in paths:
                    if len(p) == 2:
                        G.remove_edge(p[0], p[1])
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
        line = dict(color='rgba(127,127,127,{})'.format(i[4]),width=2)
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

depts = ['ECE', 'CSE', 'MAE', 'MATH', 'PHYS']
dropdown = [{'label': i, 'value': i} for i in depts]

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
                dcc.Dropdown(id='dept-select', options=dropdown, value='ECE', clearable=False),
                # TODO: use pattern to limit
                #dcc.Input(id='code',placeholder='Course code (e.g. 123A)',debounce=True)
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

def switch_dept(dept):
    ece_raw = get_raw_course_list(dept)
    ece = clean_scrape(ece_raw)
    # TODO use dict comprehension?
    ece_desc = dict()
    for k, v in ece_raw.items():
        # split into course code, course title, and number of units (unused)
        k_split = k.replace("(", ".").split(".")
        print(k, v)
        ece_desc[k_split[0]] = [k_split[1].strip(), v[0]]

    ece_offered = get_quarter_offerings(dept, "FA19") + get_quarter_offerings(dept, "WI20") + get_quarter_offerings(dept, "SP20")
    # remove the "ECE" tags and draw each department as a single node
    # use weighted edges to show interchangeable prereqs
    ece_courses = []
    ece_prereqs = []
    for course in ece:
        k, v = course
        # remove grad classes and courses not offered this year
        if len(k) >= 3 and k[0] == '2' or k not in ece_offered:
            continue
        if v:
            for i in v:
                weight = len(i)
                for j in i:
                    if j.startswith(dept):
                        # check if the course actually exists in catalog and still offered this year
                        if j in ece_desc and j.split()[1] in ece_offered:
                            ece_prereqs.append([j.split()[1], k, 1/weight])
                    # if from another department, just draw as a single node
                    else:
                        pass
                        #ece_prereqs.append([j.split()[0], k, 1/weight])
        # if no prereqs, add as independent node
        else:
            ece_courses.append(k)

    G = generate_graph(ece_courses, ece_prereqs)

    #print(nx.algorithms.dag.dag_longest_path(G))
    #G.remove_nodes_from(list(nx.isolates(G)))
    fig = generate_figure(G)
    return G, ece_desc, fig

dept_cache = dict()
for i in depts:
    print("caching {}".format(i))
    dept_cache[i] = switch_dept(i)


# TODO fix mobile support for touch/click?
@app.callback([Output('title', 'children'),Output('graph', 'figure'),Output('desc', 'children')],[Input('dept-select', 'value'), Input('graph', 'hoverData'),Input('graph','selectedData')])
        #Input('code','value')])
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
    G, ece_desc, fig = dept_cache[dept]
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

        # obtain full list of prereqs from graph, and fill the description template
        if point:
            desc_list = ece_desc[dept + " " + str(point)]
            prereqs = sort_codes(list(nx.algorithms.dag.ancestors(G, point)))
            if not prereqs:
                prereqs_str = 'None'
            else:
                prereqs_str = ', '.join([dept + " " + str(i) for i in prereqs])
            desc = desc_tmpl.format(dept + " " + str(point), desc_list[0], prereqs_str, desc_list[1])

        # obtain node indices for dash to select
        prereqs.append(point)
        prereq_index = [i for i, e in enumerate(G.nodes()) if e in prereqs]

        # highlight all of the nodes if none are selected
        if not prereq_index:
            prereq_index = list(range(len(G.nodes())))

        fig['data'][0]['selectedpoints'] = prereq_index

        # change the opacity for edges which are on the prerequisite tree for selected course
        for i,(j,k,w) in enumerate(G.edges.data('weight')):
            if j in prereqs and k in prereqs:
                fig['layout']['shapes'][i]['line']['color'] = 'rgba(127,127,127,{})'.format(w)
            else:
                fig['layout']['shapes'][i]['line']['color'] = 'rgba(127,127,127,{})'.format(w*0.5)
    except:
        pass

    return title, fig, desc

if __name__ == '__main__':
    app.run_server(debug=True)
