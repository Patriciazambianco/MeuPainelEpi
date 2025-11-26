import plotly.graph_objects as go

fig = go.Figure(
    data=[
        go.Pie(
            labels=['OK', 'PENDENTE'],
            values=[qtd_ok, qtd_pendente],
            hole=0.45,
            pull=[0, 0.05],
            textinfo='label+percent',
            textfont=dict(color="white"),
            insidetextfont=dict(color="white"),
            outsidetextfont=dict(color="white"),
        )
    ]
)

fig.update_layout(
    showlegend=True,
    legend=dict(
        font=dict(color="white"),
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
