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
# =========================
# 🖌 MANUAL OBJECT ERASER (FINAL - TRUE UNDO FIX)
# =========================
elif tool == "🖌 Manual Object Eraser":

    st.subheader("🖌 Smart Object Eraser (Perfect Undo)")

    components.html("""
    <html>
    <body style="text-align:center; font-family:Arial;">

    <h3>Upload → Click → Remove Object</h3>

    <input type="file" id="upload"><br><br>

    Brush Size:
    <input type="range" id="brush" min="10" max="80" value="30"><br><br>

    <button id="apply">✨ Apply</button>
    <button id="undo">↩ Undo</button>
    <button id="download">⬇ Download</button>

    <br><br>
    <canvas id="c" style="border:1px solid #ccc;"></canvas>

    <script>
    const canvas = document.getElementById("c");
    const ctx = canvas.getContext("2d");

    let img = new Image();
    let pts = [];
    let history = []; // 🔥 REAL HISTORY

    // =========================
    // LOAD IMAGE
    // =========================
    document.getElementById("upload").onchange = e => {
        img.src = URL.createObjectURL(e.target.files[0]);

        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);

            // Fit screen
            let scale = Math.min(window.innerWidth / img.width, 0.8);
            canvas.style.width = img.width * scale + "px";
            canvas.style.height = img.height * scale + "px";

            pts = [];
            history = [];

            // 🔥 Save initial state
            history.push(ctx.getImageData(0, 0, canvas.width, canvas.height));
        }
    }

    // =========================
    // CLICK MASK
    // =========================
    canvas.onclick = e => {
        const r = canvas.getBoundingClientRect();
        const scaleX = canvas.width / r.width;
        const scaleY = canvas.height / r.height;

        const x = (e.clientX - r.left) * scaleX;
        const y = (e.clientY - r.top) * scaleY;

        const size = parseInt(document.getElementById("brush").value);

        pts.push({x, y, size});
        redraw();
    }

    function redraw() {
        ctx.putImageData(history[history.length - 1], 0, 0);

        pts.forEach(p => {
            ctx.fillStyle = "rgba(255,0,0,0.3)";
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    // =========================
    // 🚀 APPLY (REAL FILL)
    // =========================
    document.getElementById("apply").onclick = () => {

        let imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        let data = imageData.data;

        let mask = new Uint8Array(canvas.width * canvas.height);

        pts.forEach(p => {
            for (let y = -p.size; y <= p.size; y++) {
                for (let x = -p.size; x <= p.size; x++) {

                    let dist = Math.sqrt(x*x + y*y);
                    if (dist > p.size) continue;

                    let sx = Math.floor(p.x + x);
                    let sy = Math.floor(p.y + y);

                    if (sx>=0 && sy>=0 && sx<canvas.width && sy<canvas.height) {
                        mask[sy * canvas.width + sx] = 1;
                    }
                }
            }
        });

        for (let iter = 0; iter < 15; iter++) {

            for (let y = 1; y < canvas.height-1; y++) {
                for (let x = 1; x < canvas.width-1; x++) {

                    let idx = y * canvas.width + x;

                    if (mask[idx] === 1) {

                        let sumR=0,sumG=0,sumB=0,count=0;

                        for (let dy=-2; dy<=2; dy++) {
                            for (let dx=-2; dx<=2; dx++) {

                                let nx = x+dx;
                                let ny = y+dy;
                                let nidx = ny * canvas.width + nx;

                                if (mask[nidx] === 0) {
                                    let i2 = nidx * 4;
                                    sumR += data[i2];
                                    sumG += data[i2+1];
                                    sumB += data[i2+2];
                                    count++;
                                }
                            }
                        }

                        if (count > 0) {
                            let i4 = idx * 4;
                            data[i4]     = sumR / count;
                            data[i4 + 1] = sumG / count;
                            data[i4 + 2] = sumB / count;
                            mask[idx] = 0;
                        }
                    }
                }
            }
        }

        ctx.putImageData(imageData, 0, 0);

        // 🔥 SAVE NEW STATE
        history.push(ctx.getImageData(0, 0, canvas.width, canvas.height));

        pts = [];
    }

    // =========================
    // 🔁 UNDO (100% WORKING)
    // =========================
    document.getElementById("undo").onclick = () => {

        if (history.length > 1) {
            history.pop(); // remove current
            ctx.putImageData(history[history.length - 1], 0, 0);
        }

        pts = [];
    }

    // =========================
    // DOWNLOAD
    // =========================
    document.getElementById("download").onclick = () => {
        let link = document.createElement("a");
        link.download = "result.png";
        link.href = canvas.toDataURL();
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
