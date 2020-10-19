import io
import os
# os import mkdir, path, listdir
import cv2
import math
import random
from flask import Flask, Response, render_template, request
import ternary
from enum import Enum
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib import *
from models import Actor, Element, Status, Location, scale, Settings, get_adjacent, ElementList

##############################################################################
## Actions that can be initiated by the interface or a simulation

caseCount = 0
cycleCount = 0
title = ""
local_path = "data\\"

def do_new_case(caseName):
    global caseCount
    global cycleCount
    global title
    title = caseName
    caseCount += 1
    cyclecount = 1
    return Actor()

def do_recommend(actor: Actor, algorithm, n):
    while n > 0:             
        candidates = []
        actor.Elements.clear()
        
        if False:
            # Algorithm1:
            ## get owned Elements
            latest = [element for element in actor.Elements if element.state == Status.NEW or element.state == Status.OWNED or element.state == Status.ACCEPTED]
            ## sort newest first (sorts in place)
            latest.sort(key = lambda x : x.serial, reverse=True)
            ## take the top four
            latest = latest[:4]
            ## see if any adjacencies
            for element in latest:
            ## Get any adjacent candidates
                results = list(get_adjacent(actor.Elements, element, 1))
                ## Pick one at random (substitute for weighted results) 
                random.shuffle(results) # shuffles in place
                for element in results:
                    actor.Elements.add_element(element.location, Status.RECOMMENDED)
        
        if algorithm == 'a':        
            # original algorithm:
            ## take random 6, random 2 of those adjacent        
            x = actor.Elements.get_eligible().take_random(6)
            results = ElementList()
            for element in x:
                candidates = actor.Elements.new_adjacent(element).take_random(2)
                results.append_list(candidates)     
                more = 2 - len(candidates)
                if more > 0:
                    candidates = actor.Elements.new_close(element).take_random(more)
                    results.append_list(candidates)
            for candidate in results:
                actor.Elements.add_element(candidate.location, Status.RECOMMENDED)
        
        elif algorithm == 'b':
            candidates = ElementList()
            # add the latest 2 items
            eligible = actor.Elements.get_eligible()
            candidates.append_list(eligible.take(2, 0))
            # add a couple from the next 4
            eligible.drop_head(2)
            candidates.append_list(eligible.take(4, 0).take_random(2))
            # add another 2 from deeper
            eligible.drop_head(4)
            candidates.append_list(eligible.take_random(2))
            results = ElementList()
            for element in candidates:
                adjacencies = actor.Elements.new_adjacent(element).take_random(3)
                results.append_list(adjacencies)     
                more = 3 - len(adjacencies)
                if more > 0:
                    adjacecies = actor.Elements.new_close(element).take_random(more)
                    results.append_list(adjacencies)
            for candidate in results.take_random(12):
                actor.Elements.add_element(candidate.location, Status.RECOMMENDED)
        n -= 1
    return actor

def do_add_element(actor: Actor, n: int):
    while n > 0: 
        actor.Elements.add_new_element()
        n -= 1
    return actor

def do_add_element_biased(actor: Actor, n: int):
    while n > 0:
        actor.Elements.add_new_element_biased()
        n -= 1
    return actor

def do_accept_recommendation(actor, n: int):
    while n > 0:
        x = [Element for Element in actor.Elements if Element.state == Status.RECOMMENDED]
        if (len(x) != 0):
            index = random.randint(0, len(x) - 1)
            x[index].state = Status.ACCEPTED
            n -= 1
    return actor

def do_reject_recommendation(actor, n: int):
    while n > 0:
        x = [Element for Element in actor.Elements if Element.state == Status.RECOMMENDED]
        if (len(x) != 0):
            index = random.randint(0, len(x) - 1)
            x[index].state = Status.REJECTED
        n -= 1
    return actor

def do_cycle(actor, n:int, p: int, algorithm, caseName):
    global cycleCount
    global title
    title = caseName
    while n > 0:
        cycleCount += 1
        if len(actor.Elements) == 0:
            actor = do_new_case()
        actor = do_add_element_biased(actor, 1)
        actor = do_recommend(actor, algorithm, 1)
        x = random.randint(0, 100)
        if x <= p:
            do_accept_recommendation(actor, 1)
        if n > 1:
          renderImage(actor)
        n -= 1
    return actor 
##############################################################################
## PRESENTATION STUFF

def do_plot(actor: Actor):
    global caseCount
    global cycleCount
    ##pyplot.close('all')
    image = renderImage(actor)
    
    return Response(image, mimetype='image/png')

def renderImage(actor):
    fig = show_ternary(actor)
    xoutput = io.BytesIO()
    FigureCanvas(fig).print_png(xoutput)
    fig = None
    
    ## write png files 
    if os.path.isdir(local_path) == False:
        os.mkdir(local_path)
    if os.path.isdir(local_path + title) == False:
        os.mkdir(local_path + title)
    current = local_path + title + "\sim" + str(1000*caseCount + cycleCount) + ".png"
    image = xoutput.getvalue()
    with open(current, 'wb') as out:
        out.write(image)
    return image

def show_ternary(actor: Actor):
    global quantize
    global scale
 
    figure, tax = ternary.figure(scale=scale)
    figure.set_size_inches(6,  6)

    # Set ticks
    tax.ticks(axis='lbr', linewidth=1, multiple=5, offset=0.03)

    # Remove default Matplotlib Axes
    tax.clear_matplotlib_ticks()
    tax.get_axes().axis('off')

    tax.horizontal_line(16)
    tax.left_parallel_line(10, linewidth=2., color='red', linestyle="--")
    tax.right_parallel_line(20, linewidth=3., color='blue')

    #scale = 100
    figure, tax = ternary.figure(scale=scale)
    tax.boundary(linewidth=0.3)
    tax.gridlines(multiple=Settings.get_quantize(), color="gray")

    tax.ax.axis('off')

    size = Settings.get_quantize() / scale * 150    
    
    #simulate stale
    stale = [Element.location for Element in actor.Elements if Element.state == Status.STALE] 
    for p in stale:
        q = [p.coordinates()]
        tax.plot(q, marker='o', color="white", markersize=size*0.8, alpha=0.05, markeredgecolor='gray', markeredgewidth=4.0)
    
    # simulate rejections
    rejected = [Element.location for Element in actor.Elements if Element.state == Status.REJECTED] 
    for p in rejected:
        q = [p.coordinates()]
        tax.plot(q, marker='^', color="white", markersize=size, alpha=0.2 ,markeredgecolor='black', markeredgewidth=1.0  )    
    
    #simulate acceptances
    accepted = [Element.location for Element in actor.Elements if Element.state == Status.ACCEPTED] 
    for p in accepted:
        q = [p.coordinates()]
        tax.plot(q, marker='*', color=p.to_color_string(), markersize=size*1.2, alpha=1.0 )
    
    #highlight new point:
    new = [Element.location for Element in actor.Elements if Element.state == Status.NEW] 
    for p in new:
        q = [p.coordinates()]
        tax.plot(q, marker='o', color=p.to_color_string(), markersize=size+4, alpha=0.9,markeredgecolor='yellow', markeredgewidth=4)
        
    # actor owned Elements:
    owned = [Element.location for Element in actor.Elements if Element.state == Status.OWNED] 
    for p in owned:
        q = [p.coordinates()]
        tax.plot(q, marker='o', color=p.to_color_string(), markersize=size, alpha=1)
    
    # simulate recommendations 
    recommended = [Element.location for Element in actor.Elements if Element.state == Status.RECOMMENDED] 
    for p in recommended:
        q = [p.coordinates()]
        tax.plot(q, marker='*', color="yellow", markersize=size, alpha= 0.8)  
    return figure 

# convert (x, y, z) to associated rgb value
def rgb_to_hex(rgb):
    result = '#' + ''.join('{:02X}'.format(abs(int(x))) for x in rgb)


def make_video():
    global local_path
    global title
    image_folder = local_path + title
    video_name = local_path + title + '_video.mp4'

    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape
    # (name, FourCC code, fps, size)
    # 0 = avi
    
    video = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), 4, (width,height))

    for image in images:
        video.write(cv2.imread(os.path.join(image_folder, image)))

    cv2.destroyAllWindows()
    video.release()
    os.system(video_name)