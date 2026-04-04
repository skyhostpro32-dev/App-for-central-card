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
        "🧠 Generative Fill (Pro)"
        "Erase Manually"
    ]
)

# =========================
# BACKGROUND / ENHANCE / REMOVE
# =========================
if uploaded_file and tool not in ["✨ Blur Object Tool", "🧠 Generative Fill (Pro)"]:

    image = Image.open(uploaded_file).convert("RGB")
    image.thumbnail((600, 600))

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

            st.divider()
            st.subheader("✨ Result Image")
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

            st.divider()
            st.subheader("✨ Result Image")
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

            st.divider()
            st.subheader("✨ Result Image")
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

            st.divider()
            st.subheader("✨ Result Image")
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
# ✨ BLUR TOOL (HTML)
# =========================
elif tool == "✨ Blur Object Tool":

    st.subheader("✨ Blur Object Tool")

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
    const apply=document.getElementById("apply");

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

        ctx.fillStyle="rgba(255,0,0,0.3)";
        ctx.beginPath();
        ctx.arc(x,y,size,0,Math.PI*2);
        ctx.fill();
    }

    apply.onclick=()=>{
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
# 🧠 GENERATIVE FILL (FIXED)
# =========================
elif tool == "🧠 Generative Fill (Pro)":

    st.subheader("🧠 AI Generative Fill")

    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")

        # ORIGINAL TOP
        st.subheader("📸 Original Image")
        st.image(image, use_column_width=True)

        st.write("🖌 Draw mask below → Click Apply")

        # CANVAS (NO CRASH)
        canvas_result = st_canvas(
            fill_color="rgba(255, 0, 0, 0.4)",
            stroke_width=25,
            stroke_color="#ff0000",
            background_color="rgba(0,0,0,0)",
            height=500,
            width=500,
            drawing_mode="freedraw",
            key="canvas_fixed",
        )

        if st.button("🚀 Apply AI Remove"):

            if canvas_result.image_data is not None:

                with st.spinner("Generating natural fill..."):

                    mask = canvas_result.image_data[:, :, 3]
                    mask = (mask > 50).astype("uint8") * 255

                    img_np = np.array(image.resize((500, 500)))

                    result = cv2.inpaint(
                        img_np,
                        mask,
                        7,
                        cv2.INPAINT_TELEA
                    )

                st.divider()
                st.subheader("✨ Result Image")
                st.image(result, use_column_width=True)

                st.download_button(
                    "📥 Download Result",
                    data=cv2.imencode(".png", result)[1].tobytes(),
                    file_name="ai_removed.png"
                )

            else:
                st.warning("⚠️ Draw on image first")
# =========================
# 🖌 MANUAL OBJECT ERASER
# =========================
elif tool == "🖌 Manual Object Eraser":

    st.subheader("🖌 Manual Smart Object Remover (Undo + Accurate)")

    components.html("""
    <html>
    <body style="text-align:center; font-family:Arial; margin:0;">

    <h3>Upload → Click Object → Remove</h3>

    <input type="file" id="upload"><br><br>

    Brush Size:
    <input type="range" id="brush" min="10" max="80" value="30"><br><br>

    <div style="margin:20px; display:flex; justify-content:center; gap:10px;">
        
        <button id="apply" style="padding:10px 20px; font-size:16px; background:#4CAF50; color:white; border:none; border-radius:6px;">
            ✨ Apply
        </button>
        
        <button id="undo" style="padding:10px 20px; font-size:16px; background:#f39c12; color:white; border:none; border-radius:6px;">
            ↩ Undo
        </button>
        
        <button id="download" style="padding:10px 20px; font-size:16px; background:#3498db; color:white; border:none; border-radius:6px;">
            ⬇ Download
        </button>

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

            const maxWidth = window.innerWidth * 0.9;
            const maxHeight = window.innerHeight * 0.7;

            const scale = Math.min(maxWidth / img.width, maxHeight / img.height, 1);

            canvas.style.width = (img.width * scale) + "px";
            canvas.style.height = (img.height * scale) + "px";
        }
    }

    canvas.onclick = e => {

        const rect = canvas.getBoundingClientRect();

        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;

        const x = (e.clientX - rect.left) * scaleX;
        const y = (e.clientY - rect.top) * scaleY;

        let size = parseInt(document.getElementById("brush").value);

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
        if (pts.length > 0) {
            pts.pop();
            redraw();
        }
    }

    apply.onclick = () => {

        ctx.drawImage(img, 0, 0);

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;

        pts.forEach(p => {

            const radius = p.size;
            const px = p.x;
            const py = p.y;

            let r = 0, g = 0, b = 0, count = 0;

            for (let y = -radius * 2; y <= radius * 2; y++) {
                for (let x = -radius * 2; x <= radius * 2; x++) {

                    const dist = Math.sqrt(x*x + y*y);

                    if (dist > radius && dist < radius * 2.5) {

                        const sx = Math.floor(px + x);
                        const sy = Math.floor(py + y);

                        if (sx >= 0 && sy >= 0 && sx < canvas.width && sy < canvas.height) {
                            const i = (sy * canvas.width + sx) * 4;
                            r += data[i];
                            g += data[i + 1];
                            b += data[i + 2];
                            count++;
                        }
                    }
                }
            }

            if (count === 0) return;

            r /= count;
            g /= count;
            b /= count;

            for (let y = -radius; y <= radius; y++) {
                for (let x = -radius; x <= radius; x++) {

                    const dist = Math.sqrt(x*x + y*y);

                    if (dist <= radius) {

                        const sx = Math.floor(px + x);
                        const sy = Math.floor(py + y);

                        if (sx >= 0 && sy >= 0 && sx < canvas.width && sy < canvas.height) {

                            const i = (sy * canvas.width + sx) * 4;

                            let alpha = 1 - (dist / radius);
                            alpha = Math.pow(alpha, 1.5);

                            data[i]     = data[i]     * (1 - alpha) + r * alpha;
                            data[i + 1] = data[i + 1] * (1 - alpha) + g * alpha;
                            data[i + 2] = data[i + 2] * (1 - alpha) + b * alpha;

                            data[i]     += Math.random() * 2;
                            data[i + 1] += Math.random() * 2;
                            data[i + 2] += Math.random() * 2;
                        }
                    }
                }
            }
        });

        ctx.putImageData(imageData, 0, 0);
    }

    downloadBtn.onclick = () => {
        const link = document.createElement("a");
        link.download = "cleaned-image.png";
        link.href = canvas.toDataURL("image/png", 1.0);
        link.click();
    }

    </script>

    </body>
    </html>
    """, height=900)
# =========================
# DEFAULT
# =========================
else:
    st.info("👈 Upload image or select tool")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("🚀 All-in-One AI Image Dashboard")
