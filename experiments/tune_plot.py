import sys
import os
import json
import glob
import pandas as pd
import plotly
import plotly.graph_objs as go

if len(sys.argv) != 2:
    print("Usage: python tune_plot.py <result_dir>")
    print("Example: python tune_pot.py ~/ray_results/objective_mean_2021-04-08_00-07-44/") 

result_dir = sys.argv[1]
tune_run = os.path.basename(os.path.normpath(result_dir))
results = glob.glob(os.path.join(result_dir, "*", "result.json"))

score = []
kp = []
ki = []
kd = []
alpha = []
fullPID = False
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
        if 'kd' in d['config']:
            kd.append(d['config']['kd']) 
            fullPID = True
        alpha.append(d['config']['alpha']) 

# 5D plot
if fullPID:
    #Set marker properties
    markersize = [x * 20 for x in alpha]
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
    kp_range = [min(kp), max(kp)]
    ki_range = [min(ki), max(kd)]
    kd_range = [min(ki), max(kd)]
    #ki_range = [0, 6e-6] 
    #kd_range = [0, 6e-6] 

    mylayout = go.Layout(scene=dict(xaxis=dict(title="kp", range=kp_range, showexponent = 'all', exponentformat = 'e'),
                                    yaxis=dict(title="ki", range=ki_range, showexponent = 'all', exponentformat = 'e'),
                                    zaxis=dict(title="kd", range=kd_range, showexponent = 'all', exponentformat = 'e')))

    #Plot and save html
    plotly.offline.plot({"data": [fig1],
                         "layout": mylayout},
                         image = 'png',
                         image_filename = 'tune_analyze_PID.png',
                         auto_open=True,
                         filename=("PID Scores Plot " + tune_run + ".html"))
else:
    #Set marker properties
    #markersize = [x * 20 for x in alpha]
    markersize = [10 for x in alpha]
    markercolor = score

    #Make Plotly figure
    fig1 = go.Scatter3d(x=kp,
                        y=ki,
                        z=alpha,
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
                                    zaxis=dict(title="alpha", showexponent = 'all', exponentformat = 'e')))

    #Plot and save html
    plotly.offline.plot({"data": [fig1],
                         "layout": mylayout},
                         image = 'png',
                         image_filename = 'tune_analyze_PI.png',
                         auto_open=True,
                         filename=("PI Scores Plot "  + tune_run + ".html"))
