import glob
import json
#import matplotlib.pyplot as plt
import pandas as pd
import plotly
import plotly.graph_objs as go

results = glob.glob("*/result.json")

score = []
kp = []
ki = []
kd = []
alpha = []
for results_file in results:
    print(results_file)
    with open(results_file) as f:
        try:
            d = json.load(f)
        except:
            continue
        score.append(d['score'])
        kp.append(d['config']['kp']) 
        ki.append(d['config']['ki']) 
        kd.append(d['config']['kd']) 
        alpha.append(d['config']['alpha']) 



#Set marker properties
#markersize = [x * 20 for x in alpha]
markersize = [10 for x in alpha]
markercolor = score

#Make Plotly figure
fig1 = go.Scatter3d(x=kp,
                    y=ki,
                    z=kd,
                    marker=dict(size=markersize,
                                color=markercolor,
                                opacity=0.5,
                                line=dict(width=2,
                                        color='DarkSlateGrey'),
                                reversescale=False,
                                colorscale='blues'),
                    line=dict (width=0.02),
                    mode='markers')

#Make Plot.ly Layout
mylayout = go.Layout(scene=dict(xaxis=dict(title="kp", showexponent = 'all', exponentformat = 'e'),
                                yaxis=dict(title="ki",showexponent = 'all', exponentformat = 'e'),
                                zaxis=dict(title="kd", showexponent = 'all', exponentformat = 'e')))

#Plot and save html
plotly.offline.plot({"data": [fig1],
                     "layout": mylayout},
                     auto_open=True,
                     filename=("5D Plot.html"))

