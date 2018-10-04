from flask import Flask, render_template, request, redirect

import requests
import simplejson as json
from bokeh.plotting import figure,show
import pandas as pd
import numpy as np
from bokeh.palettes import Spectral11
from bokeh.palettes import Spectral6
from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8

app = Flask(__name__)


def read_data(url_acr='SIX2_X'):
    ''' Reads url and output json data
        Test data: Stock Prices for Sixt Se St (SIX2) from the
        Frankfurt Stock Exchange
        Other actions from FSE can be used adding their acronym.
    '''

    url='https://www.quandl.com/api/v3/datasets/FSE/'+url_acr+'.json?api_key=-HsqRdH79HqspmzaVufw'

    r = requests.get(url)

    if r.status_code != 200:
        print('Status:', r.status_code,
                  'Problem with the request. Exiting.')
        exit()

    return r


def get_data(r,start_date=None,end_date=None,col_use=None):
    ''' Takes json file downloaded from Quandl
        and outputs pandas dataframe
    '''

    # requests library also comes with a built-in JSON decoder...
    data = r.json()

    # Create a dataframe from the request's json format
    request_df = pd.DataFrame(data)

    # Create a dataframe from the data nested dictionary
    df = request_df['dataset']
    column_names=df['column_names']

    #replace NaN -maybe not needed
    data_values=pd.DataFrame(df['data'],columns=column_names).replace({np.nan:None})

    # sort data based on Date
    data_values=data_values.sort_values('Date').reset_index(drop=True)

    # convert to Datetime - index already set
    data_values['Date'] = pd.to_datetime(data_values['Date'])

    # select only range of data of one month if given by the user
    # otherwise consider the full set
    if not start_date and not end_date:
        start_date=data_values['Date'].min()
        end_date=data_values['Date'].max()

    #select rows to use
    data_values=data_values[(data_values['Date'] >= start_date) & (data_values['Date'] <=end_date)]

    #select column to use
    if not col_use:
        print("no selected columns, use all")
    else:
        col_use_all=['Date']
        col_use_all.extend(col_use)
        data_values=data_values[col_use_all]
        #redefine column names
        column_names=list(data_values)

    return data_values,column_names



    return data_values,column_names

def make_plot(data_values,column_names,title_name='Sixt Se St (SIX2)'):
    ''' Plots data provided in pandas dataframe
        ToDo: currently plotting no more than 6 lines
    '''

    # define tools
    TOOLS="pan,wheel_zoom,box_zoom,reset,save"

    # create a new plot with a a datetime axis type
    p = figure(tools=TOOLS,width=500, height=350, x_axis_type="datetime",
    toolbar_location="below")

    numlines=len(column_names[1:])+1
    mypalette=Spectral6[0:numlines]

    for col_name,palette in zip(column_names[1:],mypalette):
        p.line(data_values['Date'],data_values[col_name],color=palette,
               legend=col_name)


    #customize fonts and stuff
    p.title.text = 'Quandl data for FSE dataset ID='+title_name
    p.title.text_font_size = '15pt'
    p.title.text_font ='palatino'

    p.xaxis.axis_label = 'Date'
    p.yaxis.axis_label = 'Stock Prices'
    p.xaxis.axis_label_text_font_style ='normal'
    p.xaxis.axis_label_text_font ='palatino'
    p.yaxis.axis_label_text_font_style ='normal'
    p.yaxis.axis_label_text_font ='palatino'

    p.xaxis.axis_label_text_font_size = "11pt"
    p.yaxis.axis_label_text_font_size = "11pt"

    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None

    p.legend.border_line_color=None
    p.legend.location = "top_left"
    p.legend.label_text_font_size = '8pt'

    # show the results
    show(p)

    return p


@app.route('/', methods=['GET','POST']) #allow both GET and POST requests
def index():
    '''
    Note: Not clear this is the best implementation
          I have to close the http://localhost:5000
          to clear the previous plots.
    '''
    #this block is only entered when the form is submitted
    if request.method == 'POST':
        print("submitted request")
        url_acr = request.form.get('url_acr')
        start_date=request.form.get('start_date')
        end_date=request.form.get('end_date')
        col_use = request.form.getlist("col_use")

        r=read_data(url_acr)

        data_values,column_names=get_data(r,start_date=start_date,end_date=end_date,
                                            col_use=list(col_use))

        #print("reading",data_values,column_names)

        # Create the plot
        plot= make_plot(data_values,column_names,title_name=url_acr)

        # Embed plot into HTML via Flask Render
        script, div = components(plot)


        return render_template("plot.html", url_acr=url_acr,start_date=start_date,
                                   end_date=end_date,col_use=col_use,script=script,div=div)
    else:


        return render_template("index.html")
        #return render_template("plot.html",script=script,div=div)


#@app.route('/plot_data/', methods=['GET'])
#@app.route('/plot_data/')
#def show_plot_data():
#    plots = []
#    plots.append(plot_data())
#    print()
#    return render_template('plot.html', plots=plots)


@app.route('/plot_data/')
def plot_data():
    ''' Plots default data by cliccing the link.
        ToDo: a second window is open when the request
        for a plot is sent.
    '''
    #read url
    url_acr='SIX2_X'
    start_date='2018-05-01'
    end_date='2018-06-01'
    col_use=['Open', 'High', 'Low', 'Close']

    r=read_data(url_acr)

    #get dataframe and column names
    data_values,column_names=get_data(r,start_date=start_date,end_date=end_date,
                                          col_use=col_use)

  	# Create the plot
    plot= make_plot(data_values,column_names,title_name=url_acr)

    # Embed plot into HTML via Flask Render
    script, div = components(plot)

    return render_template('plot.html',script=script,div=div)


@app.route('/about')
def about():
  return render_template('about.html')

# With debug=True, Flask server will auto-reload
# when there are code changes
if __name__ == '__main__':
  #port=33507
  app.run(port=5000, debug=True)
