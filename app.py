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
# IMAGE TOOLS
# =========================
if uploaded_file and tool not in ["✨ Blur Object Tool", "🧠 Generative Fill (Pro)", "🖌 Manual Object Eraser"]:

    image = Image.open(uploaded_file).convert("RGB")
    image.thumbnail((600, 600))

    st.subheader("📸 Original Image")
    st.image(image, use_column_width=True)

    if tool == "🎨 Background Change":
        color_hex = st.sidebar.color_picker("Pick Background Color", "#00ffaa")
        color = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))

        if st.sidebar.button("🚀 Apply Background"):
            img_array = np.array(image)
            gray = np.mean(img_array, axis=2)
            mask = gray > 200
            img_array[mask] = color
            result = Image.fromarray(img_array)

            st.image(result, use_column_width=True)
            buf = io.BytesIO()
            result.save(buf, format="PNG")
            st.download_button("📥 Download", buf.getvalue(), "background.png")

    elif tool == "✨ Enhance Image":
        strength = st.sidebar.slider("Sharpness", 1, 5, 2)

        if st.sidebar.button("🚀 Enhance"):
            result = image
            for _ in range(strength):
                result = result.filter(ImageFilter.SHARPEN)

            st.image(result, use_column_width=True)
            buf = io.BytesIO()
            result.save(buf, format="PNG")
            st.download_button("📥 Download", buf.getvalue(), "enhanced.png")

    elif tool == "🧍 Auto Person Remove":
        if st.sidebar.button("🚀 Remove Person"):
            mask_img = remove(image)
            mask = np.array(mask_img)

            alpha = mask[:, :, 3] if mask.shape[2] == 4 else cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
            _, binary_mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)

            img_np = np.array(image)
            result = cv2.inpaint(img_np, binary_mask, 3, cv2.INPAINT_TELEA)

            st.image(result, use_column_width=True)
            st.download_button("📥 Download", data=cv2.imencode(".png", result)[1].tobytes(), file_name="no_person.png")

    elif tool == "🌄 Background Removal":
        if st.sidebar.button("🚀 Remove Background"):
            output_image = remove(image.convert("RGBA"))

            st.image(output_image, use_column_width=True)
            buf = io.BytesIO()
            output_image.save(buf, format="PNG")
            st.download_button("📥 Download", buf.getvalue(), "bg_removed.png")

# =========================
# BLUR TOOL
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
# GENERATIVE FILL
# =========================
elif tool == "🧠 Generative Fill (Pro)":

    st.subheader("🧠 AI Generative Fill")

    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, use_column_width=True)

        canvas_result = st_canvas(
            fill_color="rgba(255,0,0,0.4)",
            stroke_width=25,
            height=500,
            width=500,
            drawing_mode="freedraw",
            key="canvas"
        )

        if st.button("🚀 Apply AI Remove") and canvas_result.image_data is not None:
            mask = canvas_result.image_data[:, :, 3]
            mask = (mask > 50).astype("uint8") * 255

            img_np = np.array(image.resize((500, 500)))
            result = cv2.inpaint(img_np, mask, 7, cv2.INPAINT_TELEA)

            st.image(result, use_column_width=True)
            st.download_button("📥 Download", data=cv2.imencode(".png", result)[1].tobytes())

# =========================
# MANUAL ERASER (NEW)
# =========================
elif tool == "🖌 Manual Object Eraser":

    st.subheader("🖌 Manual Object Eraser")

    components.html("""
    <html>
    <body style="text-align:center;">

    <h3>Upload → Click → Remove</h3>
    <input type="file" id="upload"><br><br>

    <input type="range" id="brush" min="10" max="80" value="30"><br><br>

    <button id="apply">Apply</button>
    <button id="undo">Undo</button>
    <button id="download">Download</button>

    <canvas id="c"></canvas>

    <script>
    const canvas=document.getElementById("c");
    const ctx=canvas.getContext("2d");

    let img=new Image();
    let pts=[];

    document.getElementById("upload").onchange=e=>{
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
        redraw();
    }

    function redraw(){
        ctx.drawImage(img,0,0);
        pts.forEach(p=>{
            ctx.fillStyle="rgba(255,0,0,0.3)";
            ctx.beginPath();
            ctx.arc(p.x,p.y,p.size,0,Math.PI*2);
            ctx.fill();
        });
    }

    document.getElementById("undo").onclick=()=>{
        pts.pop();
        redraw();
    }

    document.getElementById("apply").onclick=()=>{
        ctx.drawImage(img,0,0);
    }

    document.getElementById("download").onclick=()=>{
        const link=document.createElement("a");
        link.download="result.png";
        link.href=canvas.toDataURL();
        link.click();
    }
    </script>

    </body>
    </html>
    """, height=700)

# =========================
# DEFAULT
# =========================
else:
    st.info("👈 Upload image or select tool")

st.markdown("---")
st.caption("🚀 All-in-One AI Image Dashboard")
