# UCSD Course Graph Analysis
## Requirements
See `requirements.txt` and/or `environment.yml` for required packages. Note that `graphviz` is also required for the graph visualization, and is not a Python package.

## Deployment
To deploy on Heroku, use the buildpack `https://github.com/jrkerns/heroku-buildpack-conda.git`.
The Heroku setup uses Conda, since `graphviz`, which is not a Python package, needs to be installed.

To run the website locally, run `dash_viz.py`.

## Analysis
See `chart_viz.ipynb` for network analysis and chart generation from the data.

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

#### Strip Catalogue Overview

**Summary**: Used for gaining raw information from UCSD websites. This information is then parsed in the future by the scraper cleaner. Additionally performs planning tasks using scraped information.

Callable Functions:
1) `get_raw_course_list()`: Returns the raw list of tuples of (course name, description, prereq) in the specified department, then writes to file.
2) `get_quarter_list()`: Returns a list of offered courses in the major in the given quarter and writes to file. NOTE: quarter is of the form WI20, FA19, SP20, etc.
3) `develop_plan()`: Returns the fastest route to completion of the course list over quarters taking `max_num` courses per quarter.
4) `develop_plan_recursion()`: Recursively generates all of the prereqs for a given course list, then runs the course planner.
5) `develop_plan_recursion_helper()`: Returns the prereq mapping for all majors given in `course_list`
6) `iterate_plan()`: Takes the minimum length planner of `num_iterations` executions of `develop_plan`
7) `iterate_plan_recursions()`: Takes the minimum length planner of `num_iterations` executions of `develop_plan` using a
    recursively generated prereqs

**NOTE**: all other functions are meant for behind the scenes processing, but if you wish to learn more, documentation is included within the functions.

#### Scraper Cleaner Overview

**Summary**: Used to transform raw data from Strip Catalogue into useable information for graphing and planning.

The output of `clean_scrape()` is a tuple of tuples containing each course with its prerequisites.
```
('35', [['MATH 18', 'MATH 31AH'], ['MATH 20A'], ['MATH 20B'], ['PHYS 2A']])
```
The prerequisite list consists of multiple sublists, which indicate interchangeable courses ("OR" prereqs).
In the example above, MATH 18 and MATH 31AH are interchangeable while the rest are required.'

**NOTE**: `clean_scrape(raw_course_list)` takes as input the previously mentioned `strip_catalogue.get_raw_course_list(major)`.

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
Currently, the scrapers used in our system (`get_raw_course_list`, `get_quarter_list`, `clear_scrape`) are based off of UCSD's current html formatting. If something were to change in the websites, then we would need to update our regex parsing of the html. This could easily be avoided by either receiving course information directly from UCSD databases, or by notifcation of the html structure change in advance.

Using Dash and Plotly is quite cumbersome, as they aren't really designed for displaying directed graphs and interacting with them.
For instance, drawing arrows needs to be done separately from edges, and can only be positioned in pixel coordinates, rather than grid coordinates, making it impossible to support different window sizes.
Also, the whole graph is actually sent to the browser for each interaction, which is very inefficient since most of it can be done in the browser with minimal calls to the server.

Since Plotly leverages D3.js, in theory we could cut out the middleman and use D3.js directly, with everything calculated client-side rather than server-side.

Even though we had an implementation of a potential planner that could be used, a lot of work could go into refining and consulting with department to check its efficacy. Additionally, more changes could be made to the planner to include the students previous course history. Using this, the planner would give a personalized schedule for the student instead of the current model which assumes that the student has taken no previous courses. To implement this feature, it would take additional correspondance with UCSD's TritonLink, but the feature can be feasibly implemented from the current algorithm.
