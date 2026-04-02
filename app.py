import streamlit as st
from PIL import Image, ImageFilter
import numpy as np
import io
import cv2
from rembg import remove
import streamlit.components.v1 as components

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="AI Image Dashboard", layout="wide")
st.title("✨ AI Image Dashboard")

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🧰 Tools")

uploaded_file = st.sidebar.file_uploader(
    "📤 Upload Image", type=["png", "jpg", "jpeg"]
)

tool = st.sidebar.radio(
    "Select Tool",
    [
        "🎨 Background Change",
        "✨ Enhance Image",
        "🧍 Auto Person Remove",
        "🧽 Smart Erase Tool",
        "🌄 Background Removal",
        "✨ Blur Object Tool"   # ✅ UPDATED NAME
    ]
)

# =========================
# LAYOUT
# =========================
col1, col2 = st.columns(2)

# =========================
# IMAGE BASED TOOLS
# =========================
if uploaded_file and tool not in ["🧽 Smart Erase Tool", "✨ Blur Object Tool"]:
    image = Image.open(uploaded_file).convert("RGB")
    image.thumbnail((600, 600))

    with col1:
        st.subheader("📸 Original Image")
        st.image(image, use_column_width=True)

    # 🎨 BACKGROUND CHANGE
    if tool == "🎨 Background Change":
        color_hex = st.sidebar.color_picker("Pick Background Color", "#00ffaa")
        color = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))

        if st.sidebar.button("🚀 Apply Background"):
            img_array = np.array(image)
            gray = np.mean(img_array, axis=2)
            mask = gray > 200
            img_array[mask] = color
            result = Image.fromarray(img_array)

            with col2:
                st.image(result, use_column_width=True)

            buf = io.BytesIO()
            result.save(buf, format="PNG")
            st.download_button("📥 Download", buf.getvalue(), "background.png")

    # ✨ ENHANCE
    elif tool == "✨ Enhance Image":
        strength = st.sidebar.slider("Sharpness", 1, 5, 2)

        if st.sidebar.button("🚀 Enhance"):
            result = image
            for _ in range(strength):
                result = result.filter(ImageFilter.SHARPEN)

            with col2:
                st.image(result, use_column_width=True)

            buf = io.BytesIO()
            result.save(buf, format="PNG")
            st.download_button("📥 Download", buf.getvalue(), "enhanced.png")

    # 🧍 PERSON REMOVE
    elif tool == "🧍 Auto Person Remove":
        if st.sidebar.button("🚀 Remove Person"):
            mask_img = remove(image)
            mask = np.array(mask_img)

            if mask.shape[2] == 4:
                alpha = mask[:, :, 3]
            else:
                alpha = cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)

            _, binary_mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)

            img_np = np.array(image)
            inpainted = cv2.inpaint(img_np, binary_mask, 3, cv2.INPAINT_TELEA)

            result = Image.fromarray(inpainted)

            with col2:
                st.image(result, use_column_width=True)

            st.download_button(
                "📥 Download",
                data=cv2.imencode(".png", inpainted)[1].tobytes(),
                file_name="no_person.png"
            )

    # 🌄 BACKGROUND REMOVAL
    elif tool == "🌄 Background Removal":
        if st.sidebar.button("🚀 Remove Background"):
            output_image = remove(image.convert("RGBA"))

            with col2:
                st.image(output_image, use_column_width=True)

            buf = io.BytesIO()
            output_image.save(buf, format="PNG")

            st.download_button(
                "📥 Download",
                buf.getvalue(),
                "background_removed.png",
                "image/png"
            )

# =========================
# 🧽 SMART ERASE TOOL
# =========================
elif tool == "🧽 Smart Erase Tool":

    st.subheader("🧽 Smart Manual Erase Tool")

    components.html("""
    <html><body style="text-align:center;">
    <h3>Upload → Click → Erase</h3>
    <input type="file" id="upload"><br><br>
    <canvas id="c"></canvas>

    <script>
    const upload = document.getElementById("upload");
    const c = document.getElementById("c");
    const ctx = c.getContext("2d");
    let img = new Image();

    upload.onchange = e => {
        img.src = URL.createObjectURL(e.target.files[0]);
        img.onload = () => {
            c.width = img.width;
            c.height = img.height;
            ctx.drawImage(img,0,0);
        }
    };

    c.onclick = e => {
        const rect = c.getBoundingClientRect();
        const x = (e.clientX - rect.left) * (c.width / rect.width);
        const y = (e.clientY - rect.top) * (c.height / rect.height);

        ctx.globalCompositeOperation="destination-out";
        ctx.beginPath();
        ctx.arc(x,y,30,0,Math.PI*2);
        ctx.fill();
        ctx.globalCompositeOperation="source-over";
    };
    </script>
    </body></html>
    """, height=600)

# =========================
# ✨ BLUR OBJECT TOOL (FIXED)
# =========================
elif tool == "✨ Blur Object Tool":

    st.subheader("✨ Blur Object Tool")

    components.html("""
    <!DOCTYPE html>
    <html>
    <body style="text-align:center;font-family:Arial;">

    <h3>Upload → Click → Blur Object</h3>

    <input type="file" id="upload"><br><br>

    <label>Brush Size:</label>
    <input type="range" id="brush" min="10" max="80" value="30">

    <br><br>

    <button id="applyBtn">🚀 Apply Blur</button>
    <a id="download" download="blurred.png"
       style="display:none;background:green;color:white;padding:10px;border-radius:5px;">
       📥 Download
    </a>

    <br><br>

    <canvas id="canvas"></canvas>

    <script>
    const upload = document.getElementById("upload");
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");
    const applyBtn = document.getElementById("applyBtn");

    let img = new Image();
    let points = [];

    upload.onchange = function(e){
        img.src = URL.createObjectURL(e.target.files[0]);

        img.onload = function(){
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img,0,0);
            points = [];
        }
    }

    canvas.onclick = function(e){
        const rect = canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) * (canvas.width / rect.width);
        const y = (e.clientY - rect.top) * (canvas.height / rect.height);
        const size = document.getElementById("brush").value;

        points.push({x,y,size});

        ctx.fillStyle = "rgba(255,0,0,0.3)";
        ctx.beginPath();
        ctx.arc(x,y,size,0,Math.PI*2);
        ctx.fill();
    }

    applyBtn.onclick = function(){

        if(points.length === 0){
            alert("Click on image first!");
            return;
        }

        ctx.drawImage(img,0,0);

        points.forEach(p => {
            ctx.save();
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI*2);
            ctx.clip();

            ctx.filter = "blur(12px)";
            ctx.drawImage(img,0,0);

            ctx.restore();
        });

        ctx.filter = "none";

        const dl = document.getElementById("download");
        dl.href = canvas.toDataURL("image/png");
        dl.style.display = "inline-block";
    }
    </script>

    </body>
    </html>
    """, height=700)

# =========================
# DEFAULT
# =========================
else:
    st.info("👈 Upload image or select a tool")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("🚀 All-in-One AI Image Dashboard")
