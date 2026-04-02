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
# MAIN LAYOUT
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
        st.sidebar.subheader("🎨 Settings")

        color_hex = st.sidebar.color_picker("Pick Background Color", "#00ffaa")
        color = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))

        if st.sidebar.button("🚀 Apply Background"):
            with st.spinner("Processing..."):
                img_array = np.array(image)
                gray = np.mean(img_array, axis=2)
                mask = gray > 200
                img_array[mask] = color
                result = Image.fromarray(img_array)

            with col2:
                st.subheader("✅ Result")
                st.image(result, use_column_width=True)

            buf = io.BytesIO()
            result.save(buf, format="PNG")
            st.download_button("📥 Download", buf.getvalue(), "background.png")

    # ✨ ENHANCE
    elif tool == "✨ Enhance Image":
        st.sidebar.subheader("✨ Settings")

        strength = st.sidebar.slider("Sharpness", 1, 5, 2)

        if st.sidebar.button("🚀 Enhance"):
            with st.spinner("Enhancing..."):
                result = image
                for _ in range(strength):
                    result = result.filter(ImageFilter.SHARPEN)

            with col2:
                st.subheader("✅ Result")
                st.image(result, use_column_width=True)

            buf = io.BytesIO()
            result.save(buf, format="PNG")
            st.download_button("📥 Download", buf.getvalue(), "enhanced.png")

    # 🧍 PERSON REMOVE
    elif tool == "🧍 Auto Person Remove":
        st.sidebar.subheader("🧍 Settings")

        if st.sidebar.button("🚀 Remove Person"):
            with st.spinner("Removing..."):
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
                st.subheader("✅ Person Removed")
                st.image(result, use_column_width=True)

            st.download_button(
                "📥 Download",
                data=cv2.imencode(".png", inpainted)[1].tobytes(),
                file_name="no_person.png"
            )

    # 🌄 BACKGROUND REMOVAL
    elif tool == "🌄 Background Removal":
        st.sidebar.subheader("🌄 Settings")

        if st.sidebar.button("🚀 Remove Background"):
            with st.spinner("Removing background..."):
                output_image = remove(image.convert("RGBA"))

            with col2:
                st.subheader("✅ Background Removed")
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
# ✨ MAGIC ERASER PRO
# =========================
elif tool == "✨ Magic Eraser (Pro)":

    st.subheader("✨ Smart Magic Eraser (Natural Fill)")

    components.html("""
    <!DOCTYPE html>
    <html>
    <body style="text-align:center;">
    <h3>Upload → Click → Smart Remove</h3>

    <input type="file" id="upload"><br>
    <input type="range" id="brush" min="10" max="60" value="25">

    <br><br>
    <button onclick="apply()">🚀 Apply</button>
    <a id="download" download="result.png" style="display:none;">📥 Download</a>

    <br><br>
    <canvas id="c"></canvas>

    <script>
    let c=document.getElementById("c");
    let ctx=c.getContext("2d");
    let img=new Image();
    let pts=[];

    upload.onchange=e=>{
        img.src=URL.createObjectURL(e.target.files[0]);
        img.onload=()=>{
            c.width=img.width;
            c.height=img.height;
            ctx.drawImage(img,0,0);
        }
    }

    c.onclick=e=>{
        let r=c.getBoundingClientRect();
        let x=(e.clientX-r.left)*(c.width/r.width);
        let y=(e.clientY-r.top)*(c.height/r.height);
        let size=document.getElementById("brush").value;
        pts.push({x,y,size});
    }

    function apply(){
        let data=ctx.getImageData(0,0,c.width,c.height);
        let d=data.data;

        pts.forEach(p=>{
            for(let dy=-p.size;dy<p.size;dy++){
                for(let dx=-p.size;dx<p.size;dx++){
                    let dist=Math.sqrt(dx*dx+dy*dy);
                    if(dist<p.size){
                        let px=Math.floor(p.x+dx);
                        let py=Math.floor(p.y+dy);
                        let i=(py*c.width+px)*4;
                        d[i]=d[i+4];
                        d[i+1]=d[i+5];
                        d[i+2]=d[i+6];
                    }
                }
            }
        });

        ctx.putImageData(data,0,0);

        let dl=document.getElementById("download");
        dl.href=c.toDataURL();
        dl.style.display="inline";
    }
    </script>
    </body>
    </html>
    """, height=650)

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
