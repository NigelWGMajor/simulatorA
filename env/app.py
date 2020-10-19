import io
import random
from flask import Flask, Response, render_template, request
import ternary
from enum import Enum
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from models import Actor, Element, Status, Settings, Data
from utility import *  #rgb_to_hex, init_actor, do_plot

app =  Flask(__name__)

actor:Actor = do_new_case("NewCase")

@app.route('/', methods=['GET','POST'])
def index():
    data = Data(n=1, p=20, caseName = 'TestOne')
    return render_template('index.html', data=data)

@app.route('/plot.png')
def plot_png():
    global actor
    return do_plot(actor)
    
            
@app.route('/test', methods=['GET','POST'])
def test():
    global actor

    action = request.args.get('jsdata')
    s = request.args.get('n')
    t = request.args.get('p')
    algorithm = request.args.get('algorithm')
    caseName = request.args.get('caseName')
    if s is None:
        n = 1
    else:
        n = int(s)
    if t is None:
        p = 50
    else:
        p = int(t)
    
    if action == 'new':
        actor = do_new_case(caseName)
    elif action == 'add':
        actor = do_add_element(actor, n)
    elif action == 'addbiased':
        actor = do_add_element_biased(actor, n)
    elif action == 'recommend':
        actor = do_recommend(actor, algorithm, n)
    elif action == 'accept':
        actor = do_accept_recommendation(actor, n)
    elif action == 'reject':
        actor = do_reject_recommendation(actor, n)    
    elif action == 'more':
        Settings.quantize_more()
    elif action == 'less':
        Settings.quantize_less()       
    elif action == 'cycle':
        actor = do_cycle(actor, n, p, algorithm, caseName)
    elif action == 'video':
        make_video()
    return render_template('summary.html')

# prevent caching of the diagram
@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

# keep at EOF:        
if __name__ == "__main__":
    app.run(debug=True) 
