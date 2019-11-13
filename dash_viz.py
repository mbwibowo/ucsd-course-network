import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import plotly.graph_objs as go

from util import format_code, sort_codes

# handmade 'dataset', listing courses (nodes) and edges (prereqs)
ece_courses = [5, 15, 16, 17, 25, 30, 35, 45, 65, 100, 101, 102, 103, 107, 109, 111, 115, 120, '121A', 123, 124, '125A', '125B', '128C',
              134, '135A', '135B', '136L', '138L', '140A', '140B', '141A', '141B', 143, 144, '145L', 148, 150, 153, '154A', 155, 156,
               '157A', '157B', '158A', '158B', 159, '161A','161B','161C',163,164,165,166,'171A','171B','172A',174,'175A','175B',180,181,
              182,183,184,185,187]
ece_prereqs = [(16, 15), (30, 15), (30, 25), (45, 35), (65, 35), (100, 45), (100, 65), (101, 45), (102, 65), (102, 100), (103, 65),
               (107, 45), (111, 25), (115, 16), ('121A', 35), ('121B', '121A'), (123, 107), (124, '121B'), (124, '125A'), ('125A', '121A'),
               ('125B', '125A'), ('128B', 35), ('128B', '128A'), ('128C', '128B'), ('135A',103),('135B','135A'),('136L','135B'),
               ('140A',15),('140B', '140A'),('141A',30),('141B','141A'),(143,16),(144,15),('145L',107),(148, 15),(153,109),('154A',101),
               ('154A',153),(155,101),(155,109),(155,153),('157A',109),('157A','161A'),('157B','154A'),('158A',109),('158B','158A'),
               (159,153),('161A',101),('161B','161A'),('161C','161A'),(163,101),(163,102),(164,102),(165,102),(166,102),(166,107),
               ('171A',45),('171B','171A'),('172A',101),(174,15),(174,109),('175A',109),('175A',174),('175B','175A'),(181,103),(181,107),
               (182,103),(182,107),(183,103),(183,107),(184,182),(185,183),(187,101)]
# flip the order to show direction
ece_prereqs = [(j,i) for i,j in ece_prereqs]

def generate_graph(nodes, edges):
    """
    Generates a networkx directed graph based on lists of nodes and edges.
    :param nodes: nodes in graph
    :type nodes: list
    :param prereqs: edges in graph
    :type prereqs: list
    :return: networkx.DiGraph
    """
    assert isinstance(nodes, list)
    assert isinstance(edges, list)
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
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
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edges.append((x0,y0,x1,y1))

    # create lines from the previously generated edges
    # TODO add arrow drawing somehow?
    shapes = [dict(
        type='line',
        x0 = i[0],
        y0 = i[1],
        x1 = i[2],
        y1 = i[3],
        layer = 'below',
        line = dict(color='rgba(127,127,127,0.5)',width=2)
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

# create a directed graph, since prereqs have a 'direction' (requirements -> course)
G = generate_graph(ece_courses, ece_prereqs)

# remove non-connected nodes for better rendering
G.remove_nodes_from(list(nx.isolates(G)))

#print(nx.algorithms.dag.dag_longest_path(G))

fig = generate_figure(G)

# external css for 'n columns' class and other various helpers
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# page layout: title, graph, options, description
app.layout = html.Div([
        html.H1('ECE Undergraduate Courses'),
        dcc.Graph(id='graph',config={'displayModeBar': False}),
        html.Div(className='row', children = [
            html.Div([
                dcc.Markdown('### Options: '),
                dcc.Dropdown(options=[{'label': 'ECE', 'value': 'ECE'}],placeholder='Choose a department'),
                dcc.Checklist(options=[{'label': 'Hide other departments', 'value': 'T'}])
                # TODO: use pattern to limit
                #dcc.Input(id='code',placeholder='Course code (e.g. 123A)',debounce=True)
            ], className='three columns'),
            html.Div([dcc.Markdown('',id='desc')], className='nine columns')
        ])
])

# markdown template for course description
desc_tmpl = """
### Course: {}

#### Full Prerequisites: {}

#### Description:
{}
"""


# TODO fix mobile support for touch/click?
@app.callback([Output('graph', 'figure'),Output('desc', 'children')],[Input('graph', 'hoverData'),Input('graph','selectedData')])
        #Input('code','value')])
def highlight_prereqs(hoverData,selectedData):
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
    prereqs = []
    desc = ""
    point = None

#    if code and not hoverData and not selectedData:
#        try:
#            point = format_code(code)
#        except ValueError:
#            point = None

    # extract the point id from event data
    if hoverData:
        #print('hover: ' + str(hoverData))
        point = hoverData['points'][0]['customdata']
    elif selectedData:
        #print('select: ' + str(selectedData))
        point = selectedData['points'][0]['customdata']

    # obtain full list of prereqs from graph, and fill the description template
    if point:
        prereqs = sort_codes(list(nx.algorithms.dag.ancestors(G, point)))
        if not prereqs:
            prereqs_str = 'None'
        else:
            prereqs_str = ', '.join(['ECE ' + str(i) for i in prereqs])
        desc = desc_tmpl.format('ECE ' + str(point), prereqs_str, '')

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

    return fig, desc

if __name__ == '__main__':
    app.run_server(debug=True)
