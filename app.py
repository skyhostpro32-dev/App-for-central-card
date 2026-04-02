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
        "✨ Magic Eraser (Pro)"
    ]
)

# =========================
# LAYOUT
# =========================
col1, col2 = st.columns(2)

# =========================
# IMAGE BASED TOOLS
# =========================
if uploaded_file and tool not in ["🧽 Smart Erase Tool", "✨ Magic Eraser (Pro)"]:
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

    # 🧍 AUTO PERSON REMOVE
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
# ✨ MAGIC ERASER PRO (FIXED)
# =========================
elif tool == "✨ Magic Eraser (Pro)":

    st.subheader("✨ Smart Magic Eraser (Natural Fill)")

    components.html("""
    <!DOCTYPE html>
    <html>
    <body style="font-family:Arial;text-align:center;background:#f5f5f5;">

    <h3>Upload → Click → Smart Remove</h3>

    <input type="file" id="upload"><br><br>

    <label>Brush Size:</label>
    <input type="range" id="brush" min="10" max="60" value="25">

    <br><br>

    <button id="applyBtn">🚀 Apply Remove</button>
    <a id="download" download="result.png"
       style="display:none;background:green;color:white;padding:10px;border-radius:5px;">
       📥 Download
    </a>

    <br><br>

    <canvas id="original"></canvas>
    <canvas id="edited"></canvas>

    <script>
    const upload = document.getElementById("upload");
    const applyBtn = document.getElementById("applyBtn");

    const original = document.getElementById("original");
    const edited = document.getElementById("edited");

    const ctxO = original.getContext("2d");
    const ctxE = edited.getContext("2d");

    let img = new Image();
    let points = [];

    upload.onchange = function(e){
        const file = e.target.files[0];
        img.src = URL.createObjectURL(file);

        img.onload = function(){
            original.width = edited.width = img.width;
            original.height = edited.height = img.height;

            ctxO.drawImage(img,0,0);
            ctxE.drawImage(img,0,0);

            points = [];
        }
    }

    original.onclick = function(e){
        const rect = original.getBoundingClientRect();
        const x = (e.clientX - rect.left) * (original.width / rect.width);
        const y = (e.clientY - rect.top) * (original.height / rect.height);
        const size = document.getElementById("brush").value;

        points.push({x,y,size});

        ctxO.drawImage(img,0,0);
        ctxO.fillStyle="rgba(255,0,0,0.4)";

        points.forEach(p=>{
            ctxO.beginPath();
            ctxO.arc(p.x,p.y,p.size,0,Math.PI*2);
            ctxO.fill();
        });
    }

    function blendErase(x,y,radius){
        let imageData = ctxE.getImageData(0,0,edited.width,edited.height);
        let data = imageData.data;

        for(let dy=-radius;dy<radius;dy++){
            for(let dx=-radius;dx<radius;dx++){

                let dist = Math.sqrt(dx*dx+dy*dy);
                if(dist<radius){

                    let px = Math.floor(x+dx);
                    let py = Math.floor(y+dy);

                    if(px<1||py<1||px>=edited.width-1||py>=edited.height-1)
                        continue;

                    let i = (py*edited.width+px)*4;

                    let sumR=0,sumG=0,sumB=0,count=0;

                    for(let sy=-3;sy<=3;sy++){
                        for(let sx=-3;sx<=3;sx++){
                            let ni=((py+sy)*edited.width+(px+sx))*4;
                            sumR+=data[ni];
                            sumG+=data[ni+1];
                            sumB+=data[ni+2];
                            count++;
                        }
                    }

                    data[i]=sumR/count;
                    data[i+1]=sumG/count;
                    data[i+2]=sumB/count;
                }
            }
        }

        ctxE.putImageData(imageData,0,0);
    }

    applyBtn.onclick = function(){

        if(points.length===0){
            alert("⚠️ Click on image first");
            return;
        }

        ctxE.drawImage(img,0,0);

        points.forEach(p=>{
            blendErase(p.x,p.y,p.size);
        });

        const dl = document.getElementById("download");
        dl.href = edited.toDataURL("image/png");
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
