import os
from django.conf import settings
import matplotlib.pyplot as plt


def save_plot(plot_img_path):
    image_path = os.path.join(settings.MEDIA_ROOT, plot_img_path)
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    plt.savefig(image_path, dpi=150, bbox_inches='tight', pad_inches=0.25)
    plt.close()
    image_url = settings.MEDIA_URL + plot_img_path
    return image_url