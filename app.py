import dash
import pandas as pd
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table
from dash.dependencies import Input, Output


# Chargement des données
data = pd.read_csv("datasets/data.csv")

# Convertir la colonne Transaction_Date en datetime
data["Transaction_Date"] = pd.to_datetime(data["Transaction_Date"])

# Ajouter une colonne Total_price avec la remise
data["Total_price"] = data["Quantity"] * data["Avg_Price"] * (1 - data["Discount_pct"] / 100)

# Afficher les colonnes pour vérifier les noms
print("Colonnes disponibles dans le DataFrame :")
print(data.columns)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


title_style = {
    "fontSize": "20px",
    "fontWeight": "normal",
    "color": "#424242",
    "marginBottom": "10px"
}


def plot_evolution_chiffre_affaire(data):
    ca_week = (
        data.groupby(pd.Grouper(key="Transaction_Date", freq="W"))["Total_price"]
            .sum()
            .reset_index()
    )

    fig = px.line(
        ca_week,
        x="Transaction_Date",
        y="Total_price",
        title="Evolution du chiffre d'affaires par semaine",
        labels={"Total_price": "Chiffre d'affaires", "Transaction_Date": "Semaine"},
        color_discrete_sequence=["#700DA6"]
    )

    
    fig.update_xaxes(title=None)  
    fig.update_layout(xaxis_title="Semaine")  
    fig.update_yaxes(
        title_text="Chiffre d'affaires",
        tickformat=".2s"
    )

    fig.update_layout(
        height=300,
        margin=dict(t=40, b=80, l=40, r=40),
        xaxis_title="Semaine",
        yaxis_title="Chiffre d'affaires"
    )

    return fig



def format_k(x):
    return f"{x/1000:.0f}k"

def create_indicators(data):
    decembre_data = data[data["Transaction_Date"].dt.month == 12]
    novembre_data = data[data["Transaction_Date"].dt.month == 11]

    total_ca_decembre = decembre_data["Total_price"].sum()
    total_ca_novembre = novembre_data["Total_price"].sum()

    total_transactions_decembre = decembre_data.shape[0]
    total_transactions_novembre = novembre_data.shape[0]

    fig = go.Figure()

    # Indicateur 1 : CA décembre (en k)
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=total_ca_decembre / 1000,  # valeur en k
            number={'font': {'size': 40}, 'suffix': 'k€'},
            delta={
                'reference': total_ca_novembre / 1000,  # delta en k
                'relative': False,
                'valueformat': '.0f',  
                'decreasing': {'color': 'darkred'},
                'font': {'size': 25},
                'suffix': 'k€'
            },
            title={'text': "CA Décembre", 'font': {'size': 20}},
            domain={'x': [0, 0.5], 'y': [0, 1]}
        )
    )

    # Indicateur 2 : Ventes en décembre
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=total_transactions_decembre,
            number={'font': {'size': 40}}, 
            delta={
                'reference': total_transactions_novembre,
                'relative': False,
                'valueformat': '+.0f',  
                'increasing': {'color': 'darkolivegreen'},
                'font': {'size': 25}
            },
            title={'text': "Transactions Décembre", 'font': {'size': 20}},
            domain={'x': [0.5, 1], 'y': [0, 1]}
        )
    )

    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        height=150,
        paper_bgcolor="white"
    )

    return fig

print(data['Gender'].unique()) 
print(data.dtypes) 

def frequence_meilleure_vente(data, top=10, ascending=False):
    """
    Retourne les produits les plus vendus selon la quantité totale.
    - top : nombre de produits à afficher
    - ascending : False pour les meilleures ventes en premier
    """
    ventes = (
        data.groupby('Product_Category')['Quantity']
        .sum()
        .sort_values(ascending=ascending)
        .head(top)
    )
    return ventes

def plot_top_10_ventes(df, mode="group"):
    # Nettoyage du genre
    df = df.copy()
    df["Gender"] = df["Gender"].astype(str).str.strip().str.upper()
    df = df[df["Gender"].isin(["F", "M"])]

    # Top 10 catégories par quantité totale vendue
    top10 = frequence_meilleure_vente(df).index

    # Filtrer et agréger par quantité et genre
    df_top = (
        df[df["Product_Category"].isin(top10)]
        .groupby(["Product_Category", "Gender"])["Quantity"]
        .sum()
        .reset_index()
    )

    # Tri croissant 
    order = (
        df_top.groupby("Product_Category")["Quantity"]
              .sum()
              .sort_values()
              .index
    )

    df_top["Product_Category"] = pd.Categorical(
        df_top["Product_Category"],
        categories=order,
        ordered=True
    )

    # Graphique
    fig = px.bar(
        df_top,
        x="Quantity",
        y="Product_Category",
        color="Gender",
        orientation="h",
        barmode=mode,
        color_discrete_map={"M": "#5a1083", "F": "#f20192"},
        title="Top 10 des catégories par quantité vendue"
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis_title="Quantité totale vendue",
        yaxis_title="Catégorie du produit",
        legend_title="Sexe",
        margin=dict(l=120, r=40, t=60, b=40),
        yaxis=dict(categoryorder="array", categoryarray=order)
    )

    fig.update_xaxes(showgrid=True, gridcolor="#e5e5e5")
    fig.update_yaxes(showgrid=False)

    return fig


def table_100_dernieres_ventes(df):
    df_sorted = df.sort_values("Transaction_Date", ascending=False).head(100)

    # Colonnes à afficher + noms en français
    columns = {
        "Transaction_Date": "Date",
        "Gender": "Sexe",
        "Location": "Zone",
        "Product_Category": "Catégorie",
        "Quantity": "Quantité",
        "Avg_Price": "Prix moyen",
        "Discount_pct": "Remise (%)"
    }

    # On garde uniquement ces colonnes dans cet ordre
    df_sorted = df_sorted[list(columns.keys())]

    return dash_table.DataTable(
    id="table100",
    columns=[{"name": v, "id": k} for k, v in columns.items()],
    data=df_sorted.to_dict("records"),
    page_size=10,

    
    style_table={"height": "100%", "overflowY": "auto"}, 
    style_cell={ "textAlign": "left", "padding": "6px", "fontSize": "13px" }, 
    style_header={ "backgroundColor": "#f2f2f2", "fontWeight": "bold" }
)




app.layout = dbc.Container([

    # Ligne 1: En-tête
    dbc.Row([
        dbc.Col(
            html.H3("ECAP Store", style={"margin": 0, "padding": "10px 20px"}), 
                md=6, 
                style={"backgroundColor": "#D440A8", "border": "none", "height": "70px", "padding":"10px 20px", "display":"flex","alignItems":"center"}),

        dbc.Col(
            dcc.Dropdown(
                id="zones-dropdown",
                options=[{"label": loc, "value": loc} for loc in sorted(data["Location"].dropna().unique())],
                placeholder="Choisissez une ou plusieurs zones",
                multi=True,
                style={"border": "1px solid #ccc", "borderRadius": "10px", "padding": "6px 10px", "fontSize": "15px", "color": "#424242", "backgroundColor": "white", "height": "40px",
                       'width': '100%', 'minWidth': '300px'}
            ),
            md=6,
            style={"backgroundColor": "#D440A8", "border": "none", "height": "70px", "paddingTop": "10px 20px", "display":"flex", "alignItems":"center"}
        ),
    ]),

    # Ligne 2: Contenu principal
    dbc.Row([

        # Colonne gauche
        dbc.Col([

            # Indicateurs
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(
                                id="indicators",
                                figure=create_indicators(data),
                                style={"height": "100%", "width": "100%"},
                                config={"displayModeBar": False}
                            ),
                            style={"height": "100%"}
                        ),
                        style={"height": "200px", "border":"none", "boxShadow" : "none"}
                    ),
                    md=12
                ),
            ]),

            # Top 10 ventes
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(
                                id="top10-ventes",
                                figure=plot_top_10_ventes(data),
                                style={"height": "100%", "width": "100%"},
                                config={"displayModeBar": False}
                            ),
                            style={"height": "100%"}
                        ),
                        style={"height": "500px","border":"none", "boxShadow" : "none"}
                    ),
                    md=12
                ),
            ]),

        ], md=5),

        # Colonne droite
        dbc.Col([

            # Evolution CA
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(
                                id="evolution-ca",
                                figure=plot_evolution_chiffre_affaire(data),
                                style={"height": "100%", "width": "100%"},
                                config={"displayModeBar": False}
                            ),
                            style={"height": "100%", "marginBottom": "0px"}
                        ),
                        style={"height": "auto", "border":"none", "boxShadow" : "none", "marginBottom": "0px"}
                    ),
                    md=12
                ),
            ]),

           # Tableau des 100 dernières ventes
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H6("Tableau des 100 dernières ventes", style=title_style),
                    table_100_dernieres_ventes(data)
                    ],
                    style={"height": "80%", "marginTop": "0px"}
                ),
                style={"height": "350px", "border":"none", "boxShadow" : "none", "marginTop": "0px"}
            ),
            md=12
        )
    ]),

], md=7),

    ]),

], fluid=True)

# Callbacks
@app.callback(
    [
        Output("indicators", "figure"),
        Output("top10-ventes", "figure"),
        Output("evolution-ca", "figure"),
        Output("table100", "data")
    ],
    Input("zones-dropdown", "value")
)
def update_dashboard(selected_zones):
    if selected_zones:
        df_filtered = data[data["Location"].isin(selected_zones)]
    else:
        df_filtered = data.copy()

    # Graphiques
    fig_indic = create_indicators(df_filtered)
    fig_top10 = plot_top_10_ventes(df_filtered)
    fig_evo = plot_evolution_chiffre_affaire(df_filtered)

    # Tableau
    df_sorted = df_filtered.sort_values("Transaction_Date", ascending=False).head(100)
    table_data = df_sorted.to_dict("records")

    return fig_indic, fig_top10, fig_evo, table_data

if __name__ == "__main__":
    app.run(debug=True, port=8057, jupyter_mode="external")

server = app.server
