from flask import Flask, render_template, request, session,redirect,abort,flash
from flask_datepicker import datepicker

import requests
import simplejson as json
from bokeh.plotting import figure,show, reset_output
import pandas as pd
import numpy as np
from bokeh.palettes import Spectral11
from bokeh.palettes import Spectral6
from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
import time

app = Flask(__name__)
datepicker(app)
app.secret_key = 'some_secret'

def read_data(url_acr='SIX2_X'):
    ''' Reads url and output json data
        Default data: Stock Prices for Sixt Se St (SIX2) from the
        Frankfurt Stock Exchange
        Other actions from FSE can be shown with their symbol.
    '''

    url='https://www.quandl.com/api/v3/datasets/FSE/'+url_acr+'.json?api_key=-HsqRdH79HqspmzaVufw'

    try:
        r = requests.get(url,timeout=10)
        err_msg=r.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("Http Error:",errh)
        err_msg=errh
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:",errc)
        err_msg=errc
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:",errt)
        err_msg=errt
    except requests.exceptions.RequestException as err:
        print("Something Else",err)
        err_msg=err

    return r,err_msg


def get_data(r,start_date=None,end_date=None,col_use=None):
    ''' Takes json file downloaded from Quandl, converts that in a
        pandas data frame, selects data range and the output columns.
        Returns final pandas dataframe and column names
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

    #check if keywords for starting date and end date are
    # given, if not give min value
    if not start_date and not end_date:
        start_date=data_values['Date'].min()
        end_date=data_values['Date'].max()
    elif  not start_date:
        start_date=data_values['Date'].min()
    elif not end_date:
        end_date=data_values['Date'].max()

    #select rows to use
    data_values=data_values[(data_values['Date'] >= start_date) & (data_values['Date'] <=end_date)]

    #select columns
    if col_use:
        col_use_all=['Date']
        col_use_all.extend(col_use)
        data_values=data_values[col_use_all]
        #redefine column names
        column_names=list(data_values)
    else:
        print("no selected columns, use all provided here")
        col_use_all=['Date']
        col_use_all.extend(['Open', 'High', 'Low', 'Close'])
        data_values=data_values[col_use_all]
        column_names=list(data_values)

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
    p.yaxis.axis_label = 'Stock Prices [€]'
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


def is_date_valid(datestring):
    if datestring:
        try:
            time.strptime(datestring, '%Y-%m-%d')
        except ValueError:
            return False
        else:
            return True
    else:
        return False


def xstr(s):
    if s is '':
        return None
    else:
        return str(s)


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

        # to convert empty string to None as we want later
        start_date=xstr(start_date)
        end_date=xstr(end_date)

        print(start_date,end_date,is_date_valid(start_date),is_date_valid(end_date))

        #check format dates
        #if start_date or end_date:
        if ((start_date is not None and not is_date_valid(start_date))
           or (end_date is not None and not is_date_valid(end_date))):
            print("***ERROR dates***")
            err_dates = True
        else:
            err_dates=False
        #else:
        #    err_dates=False

        #read url and get data and err_messages
        r,err_msg=read_data(url_acr)


        if err_msg:
            flash("Invalid FSE Ticker Symbol: "+url_acr+". \n Please check the valid symbols at https://www.quandl.com/data/FSE-Frankfurt-Stock-Exchange?keyword=","error")
            #abort(404)
            return render_template("index.html")
        elif err_dates:
            flash("Invalid dates entered! Please write a date as YYYY-MM-DD")
            return render_template("index.html")

        else:
            data_values,column_names=get_data(r,start_date=start_date,end_date=end_date,
                                                col_use=list(col_use))


            reset_output()

            # Create the plot
            plot= make_plot(data_values,column_names,title_name=url_acr)

            # Embed plot into HTML via Flask Render
            script, div = components(plot)


            return render_template("plot.html", url_acr=url_acr,start_date=start_date,
                                    end_date=end_date,col_use=col_use,script=script,div=div)
    else:

        return render_template("index.html")


# With debug=True, Flask server will auto-reload
# when there are code changes
if __name__ == '__main__':
  #port=33507
  app.run(port=5000, debug=True)
