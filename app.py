import streamlit as st
from PIL import Image, ImageFilter
import numpy as np
import io
import cv2
from rembg import remove
import streamlit.components.v1 as components
from streamlit_drawable_canvas import st_canvas

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
        "🌄 Background Removal",
        "✨ Blur Object Tool",
        "🧠 Generative Fill (Pro)",
        "🖌 Manual Object Eraser"
    ]
)

# =========================
# NORMAL TOOLS
# =========================
if uploaded_file and tool not in ["✨ Blur Object Tool", "🧠 Generative Fill (Pro)", "🖌 Manual Object Eraser"]:

    image = Image.open(uploaded_file).convert("RGB")
    image.thumbnail((600, 600))

    st.image(image, use_column_width=True)

    if tool == "🎨 Background Change":
        color_hex = st.sidebar.color_picker("Pick Background Color", "#00ffaa")
        color = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))

        if st.sidebar.button("Apply"):
            arr = np.array(image)
            mask = np.mean(arr, axis=2) > 200
            arr[mask] = color
            result = Image.fromarray(arr)

            st.image(result)
            buf = io.BytesIO()
            result.save(buf, format="PNG")
            st.download_button("Download", buf.getvalue())

    elif tool == "✨ Enhance Image":
        strength = st.sidebar.slider("Sharpness", 1, 5, 2)

        if st.sidebar.button("Enhance"):
            result = image
            for _ in range(strength):
                result = result.filter(ImageFilter.SHARPEN)

            st.image(result)
            buf = io.BytesIO()
            result.save(buf, format="PNG")
            st.download_button("Download", buf.getvalue())

    elif tool == "🧍 Auto Person Remove":
        if st.sidebar.button("Remove"):
            mask_img = remove(image)
            mask = np.array(mask_img)

            alpha = mask[:, :, 3] if mask.shape[2] == 4 else cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
            _, binary = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)

            result = cv2.inpaint(np.array(image), binary, 3, cv2.INPAINT_TELEA)

            st.image(result)
            st.download_button("Download", cv2.imencode(".png", result)[1].tobytes())

    elif tool == "🌄 Background Removal":
        if st.sidebar.button("Remove BG"):
            out = remove(image.convert("RGBA"))

            st.image(out)
            buf = io.BytesIO()
            out.save(buf, format="PNG")
            st.download_button("Download", buf.getvalue())

# =========================
# BLUR TOOL
# =========================
elif tool == "✨ Blur Object Tool":

    components.html("""
    <html><body style="text-align:center;">
    <h3>Upload → Click → Blur</h3>
    <input type="file" id="upload"><br><br>
    <input type="range" id="brush" min="10" max="80" value="30"><br><br>
    <button id="apply">Apply Blur</button>
    <canvas id="c"></canvas>

    <script>
    const upload=document.getElementById("upload");
    const canvas=document.getElementById("c");
    const ctx=canvas.getContext("2d");

    let img=new Image();
    let pts=[];

    upload.onchange=e=>{
        img.src=URL.createObjectURL(e.target.files[0]);
        img.onload=()=>{
            canvas.width=img.width;
            canvas.height=img.height;
            ctx.drawImage(img,0,0);
        }
    }

    canvas.onclick=e=>{
        let r=canvas.getBoundingClientRect();
        let x=(e.clientX-r.left)*(canvas.width/r.width);
        let y=(e.clientY-r.top)*(canvas.height/r.height);
        let size=document.getElementById("brush").value;

        pts.push({x,y,size});
    }

    document.getElementById("apply").onclick=()=>{
        ctx.drawImage(img,0,0);
        pts.forEach(p=>{
            ctx.save();
            ctx.beginPath();
            ctx.arc(p.x,p.y,p.size,0,Math.PI*2);
            ctx.clip();
            ctx.filter="blur(12px)";
            ctx.drawImage(img,0,0);
            ctx.restore();
        });
        ctx.filter="none";
    }
    </script>
    </body></html>
    """, height=650)

# =========================
# GENERATIVE FILL (FIXED)
# =========================
elif tool == "🧠 Generative Fill (Pro)":

    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        size = 512
        image = image.resize((size, size))

        canvas = st_canvas(
            fill_color="rgba(255,0,0,0.4)",
            stroke_width=30,
            background_image=image,
            height=size,
            width=size,
            drawing_mode="freedraw",
            key="canvas"
        )

        if st.button("Apply AI Remove") and canvas.image_data is not None:
            mask = canvas.image_data[:, :, 3]
            mask = (mask > 10).astype("uint8") * 255

            result = cv2.inpaint(np.array(image), mask, 7, cv2.INPAINT_TELEA)

            st.image(result)
            st.download_button("Download", cv2.imencode(".png", result)[1].tobytes())

# =========================
# MANUAL ERASER (FIXED)
# ========================
elif tool == "🖌 Manual Object Eraser":

    st.subheader("✨ Click → Remove Object (Undo + Perfect UI)")

    components.html("""
    <html>
    <body style="text-align:center; font-family:Arial; margin:0;">

    <h3>Upload → Click Object → Remove</h3>

    <input type="file" id="upload"><br><br>

    Brush Size:
    <input type="range" id="brush" min="10" max="80" value="30"><br><br>

    <div style="margin:20px; display:flex; justify-content:center; gap:10px;">
        <button id="apply">Apply</button>
        <button id="undo">Undo</button>
        <button id="download">Download</button>
    </div>

    <canvas id="c" style="border:1px solid #ccc;"></canvas>

    <script>
    const upload = document.getElementById("upload");
    const canvas = document.getElementById("c");
    const ctx = canvas.getContext("2d");

    const apply = document.getElementById("apply");
    const undoBtn = document.getElementById("undo");
    const downloadBtn = document.getElementById("download");

    let img = new Image();
    let pts = [];

    upload.onchange = e => {
        img.src = URL.createObjectURL(e.target.files[0]);
        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
        }
    }

    canvas.onclick = e => {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;

        const x = (e.clientX - rect.left) * scaleX;
        const y = (e.clientY - rect.top) * scaleY;

        const size = parseInt(document.getElementById("brush").value);
        pts.push({x, y, size});
        redraw();
    }

    function redraw() {
        ctx.drawImage(img, 0, 0);
        pts.forEach(p => {
            ctx.fillStyle = "rgba(255,0,0,0.3)";
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    undoBtn.onclick = () => {
        pts.pop();
        redraw();
    }

    apply.onclick = () => {

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;

        pts.forEach(p => {

            const radius = p.size;
            const px = p.x;
            const py = p.y;

            for (let y = -radius; y <= radius; y++) {
                for (let x = -radius; x <= radius; x++) {

                    const dist = Math.sqrt(x*x + y*y);
                    if (dist > radius) continue;

                    const sx = Math.floor(px + x);
                    const sy = Math.floor(py + y);

                    if (sx < 0 || sy < 0 || sx >= canvas.width || sy >= canvas.height) continue;

                    let bestR=0,bestG=0,bestB=0,minDist=9999;

                    for (let ry = -radius*2; ry <= radius*2; ry++) {
                        for (let rx = -radius*2; rx <= radius*2; rx++) {

                            const d = Math.sqrt(rx*rx + ry*ry);
                            if (d <= radius || d > radius*2) continue;

                            const nx = Math.floor(px + rx);
                            const ny = Math.floor(py + ry);

                            if (nx < 0 || ny < 0 || nx >= canvas.width || ny >= canvas.height) continue;

                            if (d < minDist) {
                                const i2 = (ny * canvas.width + nx) * 4;
                                bestR = data[i2];
                                bestG = data[i2 + 1];
                                bestB = data[i2 + 2];
                                minDist = d;
                            }
                        }
                    }

                    const i = (sy * canvas.width + sx) * 4;

                    let alpha = 1 - (dist / radius);
                    alpha = Math.pow(alpha, 1.8);

                    data[i]     = data[i]     * (1 - alpha) + bestR * alpha;
                    data[i + 1] = data[i + 1] * (1 - alpha) + bestG * alpha;
                    data[i + 2] = data[i + 2] * (1 - alpha) + bestB * alpha;
                }
            }
        });

        ctx.putImageData(imageData, 0, 0);

        // ✅ CRITICAL FIX (PERSIST CHANGE)
        img.src = canvas.toDataURL();
        pts = [];
    }

    downloadBtn.onclick = () => {
        const link = document.createElement("a");
        link.download = "cleaned-image.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
    }

    </script>
    </body>
    </html>
    """, height=800)

# =========================
# DEFAULT
# =========================
else:
    st.info("👈 Upload image or select tool")

st.markdown("---")
st.caption("🚀 All-in-One AI Image Dashboard")
