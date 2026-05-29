import streamlit as st
import tempfile
import os
from pygerber.gerberx3.api.v2 import GerberFile
from PIL import Image

st.title("Gerber Render")

if "cleanup" not in st.session_state:
    st.session_state["cleanup"] = []

files = st.file_uploader("Upload a Gerber file", type=["gbr", "gerber"], accept_multiple_files=True)

if files:
    image_paths = []
    for file in files:
        suffix = os.path.splitext(file.name)[1]
        tmp_gerber = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp_gerber.write(file.getvalue())
        tmp_gerber.close()
        gerber = GerberFile.from_file(tmp_gerber.name).parse()
        tmp_png = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        gerber.render_raster(destination=tmp_png.name)
        image_paths.append(tmp_png.name)
        st.session_state["cleanup"].append(tmp_png.name)
        st.session_state["cleanup"].append(tmp_gerber.name)

    loaded_images = [Image.open(path).convert("RGBA") for path in image_paths]
    target_width, target_height = loaded_images[0].size
    resized_images = []
    for img in loaded_images:
        if img.size != (target_width, target_height):
            img = img.resize((target_width, target_height), Image.LANCZOS)
        resized_images.append(img)

    def get_colr(filename):
        name = filename.lower()
        if "f" in name and "cu" in name:
            return (255, 0, 0)
        elif "b" in name and "cu" in name:
            return (0, 255, 0)
        elif "edge" in name:
            return (0, 0, 255)
        elif "f" in name and "silk" in name:
            return (255, 255, 0)
        elif "b" in name and "silk" in name:
            return (255, 0, 255)
        elif "f" in name and "mask" in name:
            return (0, 255, 255)
        elif "b" in name and "mask" in name:
            return (0, 135, 204)
        elif "paste" in name and "f" in name:
            return (255, 165, 0)
        elif "paste" in name and "b" in name:
            return (255, 69, 0)
        else:
            return (255, 173, 216)

    processed_layers = []
    layer_info = [] 
    
    for i, img in enumerate(resized_images):
        filename = files[i].name
        r, g, b = get_colr(filename)
        layer_info.append((filename, r, g, b))
        
        data = img.getdata()
        new_data = [(r, g, b, 0) if cr == 0 and cg == 0 and cb == 0 else (r, g, b, 255) for cr, cg, cb, ca in data]
        new_img = Image.new("RGBA", img.size)
        new_img.putdata(new_data)
        processed_layers.append(new_img)

    for filename, r, g, b in layer_info:
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        st.markdown(
            f"<span style='background-color:{hex_color}; padding:10px 20px; border-radius:5px; margin-right:10px;'>"
            f"</span> <b>{filename}</b>",
            unsafe_allow_html=True
        )

    base = processed_layers[0]
    for layer in processed_layers[1:]:
        if layer.size != base.size:
            layer = layer.resize(base.size, Image.LANCZOS)
        base = Image.alpha_composite(base, layer)

    st.image(base)