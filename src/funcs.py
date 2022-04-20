import math
import re

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import numpy as np
import pandas as pd
from config import graph_colors
from dash import html

gb_df = pd.read_csv("src/Greenbook _reduced.csv")
epic_df = pd.read_csv("src/epic _reduced.csv")
ice_df = pd.read_csv("src/ice _reduced.csv")


def total_ec_comparison(base, val1, val2, val1_db, val2_db):
    str = [
        checker(base, val1, val1_db,),
        "\n",
        checker(base, val2, val2_db),
    ]
    return str

def checker(base, val, val_db):
    if base <=  val:
        val1_percent = (val/base) * 100
        return "{} is 🔺 by +{:,.2f}%, ".format(val_db, val1_percent)
    else:
        val1_percent = (val/base) * 100
        return "{} is 🔻 by {:,.2f}%".format(val_db, val1_percent)

def find(df, ice):

    structure_concrete = 0
    structure_steel = 0
    structure_timber = 0

    if ice != True:
        for index, row in df.iterrows():
            if re.search("concrete", row["Building Materials (All)"], re.IGNORECASE):
                structure_concrete = row["Volume (Net)"]
            elif re.search("steel", row["Building Materials (All)"], re.IGNORECASE):
                structure_steel = row["Mass"]
            elif re.search("timber", row["Building Materials (All)"], re.IGNORECASE):
                structure_timber = row["Volume (Net)"]
            else:
                pass
    else:
        for index, row in df.iterrows():
            if re.search("concrete", row["Building Materials (All)"], re.IGNORECASE):
                structure_concrete = row["Volume (Net)"]
            elif re.search("steel", row["Building Materials (All)"], re.IGNORECASE):
                structure_steel = row["Mass"]
            elif re.search("timber", row["Building Materials (All)"], re.IGNORECASE):
                structure_timber = row["Mass"]
            else:
                pass
    return structure_concrete, structure_steel, structure_timber


def find2(df, ice):
    """Creates tupled list declared units of building material

    Args:
        df (_dataframe_): _pd dataframe of uploaded schedule_
        ice (_bool_): _bool to determine if ice is present

    Returns:
        _List_: tuple list of declared units of building material -> ([structure_concrete], [structure_steel], [structure_timber])
    """

    structure_concrete = []
    structure_steel = []
    structure_timber = []

    if ice != True:
        for index, row in df.iterrows():
            if re.search("concrete", row["Building Materials (All)"], re.IGNORECASE):
                structure_concrete.append(row["Volume (Net)"])
            elif re.search("steel", row["Building Materials (All)"], re.IGNORECASE):
                structure_steel.append(row["Mass"])
            elif re.search("timber", row["Building Materials (All)"], re.IGNORECASE):
                structure_timber.append(row["Volume (Net)"])
            else: #if it doesn't know it'll assume it's concrete
                structure_concrete.append(row["Volume (Net)"])
    else:
        for index, row in df.iterrows():
            if re.search("concrete", row["Building Materials (All)"], re.IGNORECASE):
                structure_concrete.append(row["Volume (Net)"])
            elif re.search("steel", row["Building Materials (All)"], re.IGNORECASE):
                structure_steel.append(row["Mass"])
            elif re.search("timber", row["Building Materials (All)"], re.IGNORECASE):
                structure_timber.append(row["Mass"])
            else: #if it doesn't know it'll assume it's concrete
                structure_concrete.append(row["Volume (Net)"])
    return structure_concrete, structure_steel, structure_timber


def label_colours_update(l, type_):
    color_list = []
    color_dict = {}
    if type_ == "list":

        for i, iter in enumerate(l):
            if re.search("concrete", iter, re.IGNORECASE):
                color_list.append(graph_colors[0])
            elif re.search("steel", iter, re.IGNORECASE):
                color_list.append(graph_colors[1])
            elif re.search("timber", iter, re.IGNORECASE):
                color_list.append(graph_colors[2])
        return color_list

    else :

        for i, iter in enumerate(l):
            if re.search("concrete", iter, re.IGNORECASE):
                # color_dict.append(graph_colors[0])
                color_dict.update({iter: graph_colors[0]})
            elif re.search("steel", iter, re.IGNORECASE):
                # color_dict.append(graph_colors[1])
                color_dict.update({iter: graph_colors[1]})
            elif re.search("timber", iter, re.IGNORECASE):
                # color_dict.append(graph_colors[2])
                color_dict.update({iter: graph_colors[2]})

        return color_dict


'''
        ADD OTHER MATERIALS LIKE ALUMINIUM AND BRICK!!! (╯‵□′)╯︵┻━┻
        - create flexibilities for other materials
'''

def em_calc(db, df, conc_val, steel_val, timber_val):
    """em_calc() calculates the EC of each material based on the database

    Args:
        db { String }: name of databse to use. "gb", "epic" or "ice"
        df { dataframe }: pd dataframe from the uploaded schedule
        conc_val { float }: concrete EC value from db eg. 643 from Concrete 50 MPa
        steel_val { float }: steel EC value from db eg. 2.9 from Steel Universal Section
        timber_val { float }: timber EC value from db eg. 718 from Glue-Laminated Timber (Glu-lam)

    Returns:
        [ list ]: returns a list of the EC of input db
    """

    df = df.groupby(by=['Building Materials (All)'], as_index=False).sum() # create consolidated df
    volumes = df["Volume (Net)"].tolist()
    df_mat = df["Building Materials (All)"].tolist()
    mass = df["Mass"].tolist()

    gb_embodied_carbon = []
    epic_embodied_carbon = []
    ice_embodied_carbon = []

    for i, mat in enumerate(df_mat):
        # if mat == "CONCRETE - IN-SITU":
        if re.search("concrete", mat, re.IGNORECASE):
            gb_embodied_carbon.append(volumes[i]*conc_val) #Concrete 50 MPa || Green Book
            epic_embodied_carbon.append(volumes[i]*conc_val) #Concrete 40 MPa || Epic 
            ice_embodied_carbon.append(volumes[i]*conc_val) # Concrete 50 MPa || Ice
        # elif mat == "STEEL - STRUCTURAL":
        elif re.search("steel", mat, re.IGNORECASE):
            gb_embodied_carbon.append(mass[i]*steel_val) #Steel Universal Section || Green Book
            epic_embodied_carbon.append(mass[i]*steel_val) #Steel structural steel section || Epic  
            ice_embodied_carbon.append(mass[i]*steel_val) # steel Section|| Ice
        # elif mat == "TIMBER - STRUCTURAL":
        elif re.search("timber", mat, re.IGNORECASE):
            gb_embodied_carbon.append(volumes[i]*timber_val) #Glue-Laminated Timber (Glu-lam) || Green Book
            epic_embodied_carbon.append(volumes[i]*timber_val) #Glued laminated timber (glulam) || Epic 
            ice_embodied_carbon.append(mass[i]*timber_val) # Timber Gluelam || Ice
        else: # if all else fail assume concrete
            gb_embodied_carbon.append(volumes[i]*conc_val) # Green Book
            epic_embodied_carbon.append(volumes[i]*conc_val) # Epic
            ice_embodied_carbon.append(volumes[i]*conc_val) # Ice       

    if db == "gb":
        return gb_embodied_carbon
    elif db == "epic":
      return epic_embodied_carbon
    elif db == "ice":
        return ice_embodied_carbon


def stars_append(n):
    stars = []
    for i in range(n):
        stars.append(html.I(className="bi bi-star-fill mx-2"))
        star_outline = 4-i
    for j in range(star_outline):
        stars.append(html.I(className="bi bi-star mx-2"))
    return html.Div(stars, className="text-center")

def progress_bar(n_stars, ec_val, lower, upper):
    """Progress bar for EC values

    Args:
        n_stars ( int ): number of stars
        ec_val ( float ): the EC value
        lower ( float ): lower bounds of benchmark
        upper ( float ): upper bounds of benchmark

    Returns:
        list: return list of components to render
    """

    val = (ec_val - lower)/(upper - lower)
    val = val * 100

    if lower == 0:
        label = "Design is {}% away from 4 stars. Please note that value will never reach 0 EC per meter.".format(100-int(val)) 
    else:
        label = "{}% more for the next star".format(int(val)),

    return html.Div([
        stars_append(n_stars),
        html.Div([
            html.P(lower, className="text-start mb-0"),
            dmc.Tooltip(
                label=label,
                transition="pop",
                width=220,
                transitionDuration=300,
                transitionTimingFunction="ease",
                withArrow=True,
                children=[
                    dbc.Progress(label="{}%".format(int(val)), value=val),
                ],
                class_name="w-75"
            ),
            html.P(upper, className="text-end mb-0"),
        ], className="hstack mt-5", style={"justify-content": "space-between"}),
        html.Div([
            html.P(["kgCO", html.Sub("e"), html.Sup("2"), "/m", html.Sup("2")], className="text-start text-secondary"),
            html.P(["kgCO", html.Sub("e"), html.Sup("2"), "/m", html.Sup("2")], className="text-start text-secondary"),
        ], className="hstack", style={"justify-content": "space-between"})    
    ], className="mx-5")

def upload_alert(df):
    """checks for errors and returns a message

    Args:
        df ( dataframe ): dataframe from the uploaded schedule

    Returns:
        list: components to render
    """
    df = df.reset_index()
    nan_check = sum(df.isna().sum().tolist())
    nan_values = df[df.isna().any(axis=1)]
    nan_values_list = nan_values.index.tolist()

    if nan_check > 0:
        return dbc.Alert([
            html.H3([
                html.Span(
                    html.I(className="bi bi-exclamation-circle-fill me-3")
                ),"Warning:"], 
                className="mb-3"
            ),
            html.P(["Please note that there are ", html.Strong("{}".format(nan_check)), " missing values in your input file. This will cause errors in the Analysis Page."]),
            dmc.Divider(class_name="my-3"),
            html.P(["missing values can be found in row/s: ", html.Strong(",".join(str(e+1) for e in nan_values_list))]),
            html.P("You can edit the value on excel or other spreadsheet software and upload again."),
            dbc.Table.from_dataframe(nan_values, striped=False, bordered=True, hover=True, responsive=True),
            
            ],
            "Please fill in all the fields", 
            color="warning",
            dismissable=True,
            is_open=True,
        )
    else:
        return dbc.Alert([
            html.H3([
                html.Span(
                    html.I(className="bi bi-exclamation-circle-fill me-3")
                ),"No errors found 😁"], 
                className="mb-3"
            ),
            html.P(["there was no missing values in your input file. You can proceed to the Analysis Page."]),
            ],
            "Please fill in all the fields", 
            color="success",
            dismissable=True,
            is_open=True,
            duration=2000,

        )

def mass2vol(mass, density):
    """converts mass to volume

    Args:
        mass ( float ): mass in kg
        density ( float ): density in kg/m3

    Returns:
        float: volume in m3
    """
    return mass/density

def cyl2vol(diameter, height):
    """converts cylinder to volume

    Args:
        diameter ( float ): diameter in m
        height ( float ): height in m

    Returns:
        float: volume in m3
    """
    return math.pi*(diameter/2)**2*height

