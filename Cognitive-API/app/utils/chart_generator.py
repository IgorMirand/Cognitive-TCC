import matplotlib.pyplot as plt
import io
import base64

def generate_chart(df):

    fig, ax = plt.subplots()

    ax.barh(df["atividade"], df["freq"])

    buf = io.BytesIO()

    plt.savefig(buf, format="png")

    buf.seek(0)

    return base64.b64encode(buf.read()).decode()