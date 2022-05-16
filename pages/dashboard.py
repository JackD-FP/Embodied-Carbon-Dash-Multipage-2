# saving this because of the ^3 (m³)
import re
from time import clock_settime

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import numpy as np
import openpyxl  # just so excel upload works
import pandas as pd
import plotly.graph_objects as go
from config import config, graph_colors
from dash import Input, Output, State, callback, dash_table, dcc, html
from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots
from src import building_type_option, dashboard_cards, funcs, uploader

gb_df = pd.read_csv("src/Greenbook _reduced.csv")
epic_df = pd.read_csv("src/epic _reduced.csv")
ice_df = pd.read_csv("src/ice _reduced.csv")

# dmc.Table(create_table(df_new_grouped))


def create_data(x, label):
    x = x.drop(["Element"], axis=1)
    values = x.values
    rows = [html.Tr([html.Td(cell) for cell in row]) for row in values]
    row_label = html.Tr([html.Td(label, rowSpan=len(x) + 1)])
    return [row_label] + rows


def create_table(x):
    # columns, values = x.columns, x.values
    x.rename(
        columns={
            "Mass": "Mass (kg)",
            "Volume": "Volume (m³)",
            "Green Book EC": "Green Book EC (kgCO²e)",
            "Epic EC": "Epic EC (kgCO²e)",
            "Ice EC": "Ice EC (kgCO²e)",
        },
        inplace=True,
    )
    columns = x.columns
    header = [html.Tr([html.Th(col) for col in columns])]
    beam = create_data(x.loc[x["Element"] == "Beam"], "Beam")
    column = create_data(x.loc[x["Element"] == "Column"], "Column")
    slab = create_data(x.loc[x["Element"] == "Slab"], "Slab")
    walls = create_data(x.loc[x["Element"] == "Wall"], "Wall")
    stair = create_data(x.loc[x["Element"] == "Stair"], "Stair")

    rows = column + beam + slab + walls + stair
    table = [html.Thead(header), html.Tbody(rows)]

    return table


layout = html.Div(
    [
        html.H1("Dashboard", className="display-2 mb-5 "),
        html.Hr(),
        html.P(
            "The Embodied Carbon App is built to help architects and designers make informed in order to design a more sustainable building. \
        It is obvious to us that timber is far less carbon intense than concrete and steel. However, when it comes to actual buildings where mixtures of materials are necessary for structural stability, \
        the answer is less obvious. We should all strive to minimise our design's embodied carbon, however, not compromise with structural stability and design excellence.\
        The App can help identify which material is carbon intense and check if there are alternatives less carbon intense to the later. \
        It can also help identify what floor is causing the issue if a redesign or alteration is required.\
        This app free and open source for anyone. At Fitzpatrick and Partners, \
        we believe this is the way to help our industry move forward and achieve a better and sustainable tomorrow."
        ),
        dcc.Upload(
            id="upload-data",
            children=html.Div(
                [
                    dbc.Button(
                        [
                            html.I(className="bi bi-upload", style={"width": "2rem"}),
                            html.P("Drag and Drop or Schedule File"),
                        ],
                        color="light",
                        className="align-center position-absolute top-50 start-50 translate-middle w-100 h-100",
                        id="upload_btn",
                    ),
                ],
                id="uploader_ui",
                style={"height": "10rem", "width": "50%", "margin": "auto"},
            ),
            style={
                "height": "10rem",
                "width": "50%",
                "lineHeight": "60px",
                "textAlign": "center",
                "margin": "auto",
                "marginTop": "2rem",
            },
            className="text-center mb-5 border border-2 rounded-3 shadow-sm bg-light",
            # Allow multiple files to be uploaded
            multiple=True,
        ),
        html.Div(id="display-table"),
        html.Div(
            id="dashboard_graph"
        ),  # could just check but idk ceebs not elegant(?)...no thing is elegant (╯▔皿▔)╯
    ]
)


@callback(
    Output("display-table", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
)
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            uploader.parse_contents(c, n, d, "temp-df-store", "name_1")
            for c, n, d in zip(list_of_contents, list_of_names, list_of_dates)
        ]
        return children


def em_calc(df):
    df = df.groupby(
        by=["Building Materials (All)"], as_index=False
    ).sum()  # create consolidated df
    # materials = []
    volumes = df["Net Volume"].tolist()
    df_mat = df["Building Materials (All)"].tolist()
    mass = df["Mass"].tolist()
    gb_embodied_carbon = []
    epic_embodied_carbon = []
    ice_embodied_carbon = []

    for i, mat in enumerate(df_mat):
        # if mat == "CONCRETE - IN-SITU":
        if re.search("concrete", mat, re.IGNORECASE):
            gb_embodied_carbon.append(volumes[i] * 643)  # Concrete 50 MPa || Green Book
            epic_embodied_carbon.append(volumes[i] * 600)  # Concrete 40 MPa || Epic
            ice_embodied_carbon.append(volumes[i] * 413.4943)  # Concrete 50 MPa || Ice
        # elif mat == "STEEL - STRUCTURAL":
        elif re.search("steel", mat, re.IGNORECASE):
            gb_embodied_carbon.append(
                mass[i] * 2.9
            )  # Steel Universal Section || Green Book
            epic_embodied_carbon.append(
                mass[i] * 2.9
            )  # Steel structural steel section || Epic
            ice_embodied_carbon.append(mass[i] * 1.55)  # steel Section|| Ice
        # elif mat == "TIMBER - STRUCTURAL":
        elif re.search("timber", mat, re.IGNORECASE):
            gb_embodied_carbon.append(
                volumes[i] * 718
            )  # Glue-Laminated Timber (Glu-lam) || Green Book
            epic_embodied_carbon.append(
                volumes[i] * 1718
            )  # Glued laminated timber (glulam) || Epic
            ice_embodied_carbon.append(mass[i] * 0.51)  # Timber Gluelam || Ice
        else:  # if all else fail assume concrete
            gb_embodied_carbon.append(volumes[i] * 643)  # Wood || Green Book
            epic_embodied_carbon.append(volumes[i] * 600)  # Wood || Epic
            ice_embodied_carbon.append(volumes[i] * 413.4943)  # Wood || Ice

        # ADD OTHER MATERIALS LIKE ALUMINIUM AND BRICK!!! (╯‵□′)╯︵┻━┻
        # Also i think it's better if we access dataframe.loc instead of a const
        # like look for the right material type or something.

    return (
        np.around(gb_embodied_carbon, 2),
        np.around(epic_embodied_carbon, 2),
        np.around(ice_embodied_carbon, 2),
    )


def percent_check_return(lo, hi):
    if hi == lo:
        return "Lowest total EC"
    else:
        sub = (hi - lo) * 100
        return "+{}% more than lowest".format(np.around(sub / hi, 2))


@callback(Output("dashboard_graph", "children"), [Input("main_store", "data")])
def make_graphs(data):
    if data is None:
        raise PreventUpdate
    elif data is not None:
        df_ = pd.read_json(data, orient="split")
        df_o = df_.reset_index()
        gb_ec, epic_ec, ice_ec = em_calc(df_o)  # To create database of all the ec

        df = df_.groupby(by=["Building Materials (All)"], as_index=False).sum()
        df_mat = df["Building Materials (All)"].tolist()

        # new calculations for carbon intensity
        mat, vol, mass, floor, element, gbec, epicec, iceec = funcs.mat_interpreter(df_)
        df_new = pd.DataFrame(
            {
                "Floor Level": floor,
                "Element": element,
                "Materials": mat,
                "Mass": mass,
                "Volume": vol,
                "Green Book EC": gbec,
                "EPiC EC": epicec,
                "ICE EC": iceec,
            }
        )
        # df_new.to_csv("temp-df-store.csv", index=False)

        gb_sum = df_new["Green Book EC"].sum()
        epic_sum = df_new["EPiC EC"].sum()
        ice_sum = df_new["ICE EC"].sum()

        df_new_grouped = df_new.groupby(
            by=["Element", "Materials"],
            as_index=False,
        ).sum()
        # there should be a better way to do this
        # TODO: make this one line or something
        df_new_grouped.loc[:, "Mass"] = df_new_grouped["Mass"].map("{:,.2f}".format)
        df_new_grouped.loc[:, "Volume"] = df_new_grouped["Volume"].map("{:,.2f}".format)
        df_new_grouped.loc[:, "Green Book EC"] = df_new_grouped["Green Book EC"].map(
            "{:,.2f}".format
        )
        df_new_grouped.loc[:, "EPiC EC"] = df_new_grouped["EPiC EC"].map(
            "{:,.2f}".format
        )
        df_new_grouped.loc[:, "ICE EC"] = df_new_grouped["ICE EC"].map("{:,.2f}".format)

        embodied_carbon_dict = {
            "Materials": df_mat,
            "Green Book (kgCO²e)": gb_ec,
            "EPiC EC (kgCO²e)": epic_ec,
            "ICE EC (kgCO²e)": ice_ec,
        }

        ec_df = pd.DataFrame(embodied_carbon_dict)

        ec_df.loc[:, "Green Book (kgCO²e)"] = ec_df["Green Book (kgCO²e)"].map(
            "{:,.2f}".format
        )
        ec_df.loc[:, "EPiC EC (kgCO²e)"] = ec_df["EPiC EC (kgCO²e)"].map(
            "{:,.2f}".format
        )
        ec_df.loc[:, "ICE EC (kgCO²e)"] = ec_df["ICE EC (kgCO²e)"].map("{:,.2f}".format)

        fig = make_subplots(
            rows=1,
            cols=3,
            specs=[[{"type": "domain"}, {"type": "domain"}, {"type": "domain"}]],
        )
        # subplot for greenbook
        fig.add_trace(
            go.Pie(
                labels=mat,
                values=gbec,
                name="Green Book DB",
                hole=0.5,
                scalegroup="dashboard_pie",
            ),
            1,
            1,
        )
        fig.add_trace(
            go.Pie(
                labels=mat,
                values=epicec,
                name="EPiC DB",
                hole=0.5,
                scalegroup="dashboard_pie",
            ),
            1,
            2,
        )
        # subplot for greenbookW
        fig.add_trace(
            go.Pie(
                labels=mat,
                values=iceec,
                name="ICE DB",
                hole=0.5,
                scalegroup="dashboard_pie",
            ),
            1,
            3,
        )
        fig.update_layout(
            title_text="Structure Embodied Carbon",
            annotations=[
                dict(text="Greenbook", x=0.12, y=0.50, font_size=16, showarrow=False),
                # dict(
                #     text="{:,.2f} kgCO²e".format(gb_sum),
                #     x=0,
                #     y=0.1,
                #     font_size=32,
                #     showarrow=False,
                # ),
                dict(text="EPiC", x=0.50, y=0.50, font_size=16, showarrow=False),
                # dict(
                #     text="{:,.2f} kgCO²e".format(epic_sum),
                #     x=0.5,
                #     y=0.1,
                #     font_size=32,
                #     showarrow=False,
                # ),
                dict(text="ICE", x=0.87, y=0.50, font_size=16, showarrow=False),
                # dict(
                #     text="{:,.2f} kgCO²e".format(ice_sum),
                #     x=1,
                #     y=0.1,
                #     font_size=32,
                #     showarrow=False,
                # ),
            ],
        ),
        fig.update_traces(
            hoverinfo="label+value",
            textinfo="percent",
            # marker=dict(
            #     colors=[
            #         "#5463FF",
            #         "#FFC300",
            #         "#FF1818",
            #         "#70C1B3",
            #         "#79b159",
            #         "#42D9C8",
            #     ]
            # ),
        )

        # drop embodied carbon if it exist
        if "Embodied Carbon" in df.columns:
            df = df.drop(["Embodied Carbon"], axis=1)
        else:
            pass

        return html.Div(
            [  # consolidated table..
                dcc.Store(id="temp_proc_store", data=df_new.to_json(orient="split")),
                html.H3(
                    [
                        "Uploaded File: ",
                        html.Span(id="file_name", className="display-5"),
                    ],
                    className="my-3",
                ),
                html.P(
                    "Review your uploaded file with the table below. See if there are any errors or missing data.",
                    className="my-3",
                ),
                html.Div(id="error_check"),
                dash_table.DataTable(
                    df_o.to_dict("records"),
                    [{"name": i, "id": i} for i in df_o.columns],
                    page_size=15,
                    style_data_conditional=(
                        [
                            {
                                "if": {
                                    "filter_query": "{{{}}} is blank".format(col),
                                    "column_id": col,
                                },
                                "backgroundColor": "rgb(254,111,94)",
                            }
                            for col in df_o.columns
                        ]
                    ),
                    style_header={"fontWeight": "bold"},
                ),
                dbc.Card(
                    [
                        html.H3("Embodied Carbon(EC) calculation"),
                        dmc.Table(
                            create_table(df_new_grouped),
                            highlightOnHover=True,
                        ),
                        dashboard_cards.cards,
                        dcc.Graph(
                            figure=fig,
                            style={"height": "50vh"},
                            className="mt-3",
                            config=config,
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.H3(
                                        [
                                            "{:,.2f}".format(gb_sum),
                                            html.P(
                                                "kgCO²ₑ", className="fs-5 display-6"
                                            ),
                                        ],
                                        style={"textAlign": "center"},
                                    )
                                ),
                                dbc.Col(
                                    html.H3(
                                        [
                                            "{:,.2f}".format(epic_sum),
                                            html.P(
                                                "kgCO²ₑ", className="fs-5 display-6"
                                            ),
                                        ],
                                        style={"textAlign": "center"},
                                    )
                                ),
                                dbc.Col(
                                    html.H3(
                                        [
                                            "{:,.2f}".format(ice_sum),
                                            html.P(
                                                "kgCO²ₑ", className="fs-5 display-6"
                                            ),
                                        ],
                                        style={"textAlign": "center"},
                                    )
                                ),
                            ]
                        ),
                    ],
                    class_name="my-5 shadow",
                    style={"padding": "4rem"},
                ),
            ]
        )


@callback(
    Output("file_name", "children"),
    Input("project_name", "data"),
)
def filename_update(data):
    return data


@callback(
    Output("error_check", "children"),
    Input("main_store", "data"),
)
def error_update(data):
    df = pd.read_json(data, orient="split")
    return funcs.upload_alert(df)


# @callback(
#     Output("gb_gfa", "children"),
#     # Output("epic_gfa", "children"),
#     # Output("ice_gfa", "children"),
#     Output("gb_benchmark", "children"),
#     Input("gfa_input", "value"),
#     Input("bld_type", "value"),
#     Input("proc_store", "data"),
# )
# def gfa_calc(val, bld_type, data):
#     df = pd.read_json(data, orient="split")
#     # gb_ec, epic_ec, ice_ec = em_calc(df)
#     # df_grouped = df.groupby(by=['Building Materials'], as_index=False).sum()

#     if val is not None:

#         gfa_val = [
#             df["Green Book EC"].sum() / val,
#             df["EPiC EC"].sum() / val,
#             df["ICE EC"].sum() / val,
#         ]

#         gb_gfa_out = "{:,}".format(np.around(gfa_val[0], 2))
#         epic_gfa_out = "{:,}".format(np.around(gfa_val[1], 2))
#         ice_gfa_out = "{:,}".format(np.around(gfa_val[2], 2))

#         def benchmark(Embodied_Carbon, Building_Type):
#             if Building_Type == "2_premium":
#                 if Embodied_Carbon <= 1450 and Embodied_Carbon >= 1160:
#                     return funcs.progress_bar(3, Embodied_Carbon, 1160, 1450)
#                 elif Embodied_Carbon <= 1160 and Embodied_Carbon >= 870:
#                     return funcs.progress_bar(4, Embodied_Carbon, 870, 1160)
#                 elif Embodied_Carbon <= 870:
#                     return funcs.progress_bar(5, Embodied_Carbon, 0, 870)
#                 else:
#                     return html.Div("Improvement Required", className="text-center")

#             elif Building_Type == "2_multi-res":
#                 if Embodied_Carbon <= 990 and Embodied_Carbon >= 790:
#                     return funcs.progress_bar(3, Embodied_Carbon, 790, 990)
#                 elif Embodied_Carbon <= 790 and Embodied_Carbon >= 590:
#                     return funcs.progress_bar(4, Embodied_Carbon, 590, 790)
#                 elif Embodied_Carbon <= 590:
#                     return funcs.progress_bar(5, Embodied_Carbon, 0, 590)
#                 else:
#                     return html.Div("Improvement Required", className="text-center")

#             elif Building_Type == "5_premium":
#                 if Embodied_Carbon <= 1500 and Embodied_Carbon >= 1200:
#                     return funcs.progress_bar(3, Embodied_Carbon, 1200, 1500)
#                 elif Embodied_Carbon <= 1200 and Embodied_Carbon >= 900:
#                     return funcs.progress_bar(4, Embodied_Carbon, 900, 1200)
#                 elif Embodied_Carbon <= 900:
#                     return funcs.progress_bar(5, Embodied_Carbon, 0, 900)
#                 else:
#                     return html.Div("Improvement Required", className="text-center")

#             elif Building_Type == "5_a_grade":
#                 if Embodied_Carbon <= 800 and Embodied_Carbon >= 640:
#                     return funcs.progress_bar(3, Embodied_Carbon, 640, 800)
#                 elif Embodied_Carbon <= 640 and Embodied_Carbon >= 480:
#                     return funcs.progress_bar(4, Embodied_Carbon, 480, 640)
#                 elif Embodied_Carbon <= 480:
#                     return funcs.progress_bar(5, Embodied_Carbon, 0, 480)
#                     # stars_append(5)
#                 else:
#                     return html.Div("Improvement Required", className="text-center")

#             elif Building_Type == "6_regional":
#                 if Embodied_Carbon <= 2150 and Embodied_Carbon >= 1750:
#                     return funcs.progress_bar(3, Embodied_Carbon, 1750, 2150)
#                 elif Embodied_Carbon <= 1720 and Embodied_Carbon >= 1250:
#                     return funcs.progress_bar(4, Embodied_Carbon, 1250, 1720)
#                 elif Embodied_Carbon <= 1290:
#                     return funcs.progress_bar(4, Embodied_Carbon, 0, 1290)
#                 else:
#                     return html.Div("Improvement Required", className="text-center")

#             elif Building_Type == "5_sub_regional":
#                 if Embodied_Carbon <= 1220 and Embodied_Carbon >= 970:
#                     return funcs.progress_bar(3, Embodied_Carbon, 970, 1220)
#                 elif Embodied_Carbon <= 970 and Embodied_Carbon >= 730:
#                     return funcs.progress_bar(4, Embodied_Carbon, 730, 970)
#                 elif Embodied_Carbon <= 730:
#                     return funcs.progress_bar(5, Embodied_Carbon, 0, 730)
#                 else:
#                     return html.Div("Improvement Required", className="text-center")

#         # html.Div(benchmark(gfa_val[0],bld_type))

#         return (
#             gb_gfa_out,
#             html.Div(benchmark(gfa_val[0], bld_type)),
#         )

#     else:
#         raise PreventUpdate
