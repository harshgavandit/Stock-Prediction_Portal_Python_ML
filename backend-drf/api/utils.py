"""Return chart bytes in the response rather than persisting server-local files."""
import base64
from io import BytesIO


def plot_data_uri(figure):
    output = BytesIO()
    figure.savefig(output, format="png", dpi=100, bbox_inches="tight", pad_inches=0.2)
    figure.clear()
    return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")
