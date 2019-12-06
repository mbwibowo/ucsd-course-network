# UCSD Course Graph Analysis
## Requirements
See `requirements.txt` and/or `environment.yml` for required packages. Note that `graphviz` is also required for the graph visualization, and is not a Python package.

## Deployment
To deploy on Heroku, use the buildpack `https://github.com/jrkerns/heroku-buildpack-conda.git`.
The Heroku setup uses Conda, since `graphviz`, which is not a Python package, needs to be installed.

## Documentation

### Data preprocessing
The data is scraped from UCSD's Course Catalog and Schedule of Classes in `strip_catalogue.py` where it is further cleaned in `scrapercleaner.py`.

Example usage:
```
import strip_catalogue
import scrapercleaner
# pass any department code as arg
raw_courses = strip_catalogue.get_raw_course_list('ECE')
courses = scrapercleaner.clean_scrape(raw_courses)
```

The output of `clean_scrape()` is a tuple of tuples containing each course with its prerequisites.
```
('35', [['MATH 18', 'MATH 31AH'], ['MATH 20A'], ['MATH 20B'], ['PHYS 2A']])
```
The prerequisite list consists of multiple sublists, which indicate interchangeable courses ("OR" prereqs).
In the example above, MATH 18 and MATH 31AH are interchangeable while the rest are required.

### Graph generation
From `clean_scrape()`, the data is used to generate a directed graph in NetworkX.
`generate_graph()` in the notebook, and `get_dept_info()` and `generate_graph()` in `dash_viz.py` perform this operation.
The Dash visualization code requires a separate function because all the extra data from preprocessing is preserved for displaying on the website.
Also, it attempts to simplify the network visualization by removing redundant edges (e.g. if C requires A and B, but B also requires A), isolated courses (no prereqs and is not a prereq of anything), and courses not offered this year.

In either case, the tuple of courses is split into a list of edge pairs to pass into NetworkX.
Since there is no exact method to indicate alternate paths, we add a weight of `1/len(paths)` for each set of alternate paths, which is only used for the visualization to draw a different line style.

### Graph visualization
Using the `DiGraph` from NetworkX, `graphviz` then attempts to assign positions to each node.
NetworkX does not have native directed graph layout, so it wraps `pygraphviz` to generate one.

The coordinates are then used by Plotly to plot each node and edge.
Since Plotly does not have interactivity (such as hovering and clicking), we use a Dash app (which displays Plotly plots) to do so.

This allows for both selecting different departments, as well as interacting with each node.
The way this is done in Dash is through callbacks, which are run when any targetable action is performed.
If a node is clicked or hovered, the callback retrieves the course data, and traverses the graph to find all of its ancestors (i.e. prereqs, the prereqs of those, and so on), which are then highlighted. The opacity of the other nodes and edges are lowered.

#### Future work (?)
Using Dash and Plotly is quite cumbersome, as they aren't really designed for displaying directed graphs and interacting with them.
For instance, drawing arrows needs to be done separately from edges, and can only be positioned in pixel coordinates, rather than grid coordinates, making it impossible to support different window sizes.
Also, the whole graph is actually sent to the browser for each interaction, which is very inefficient since most of it can be done in the browser with minimal calls to the server.

Since Plotly leverages D3.js, in theory we could cut out the middleman and use D3.js directly, with everything calculated client-side rather than server-side.
