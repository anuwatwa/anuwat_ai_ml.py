"""
Streamlit UI - Construction Quantity Estimation (Simplified)
โปรแกรมประมาณการปริมาณงานก่อสร้าง - เวอร์ชันลด Input

ติดตั้ง: pip install streamlit
รัน: streamlit run app_simplified.py
"""

import streamlit as st
import pickle
import pandas as pd
import os

# ===================================
# Configuration
# ===================================
st.set_page_config(
    page_title="Construction Estimation",
    page_icon="🏗️",
    layout="wide"
)

# ===================================
# Load Model Function
# ===================================
def load_model(model_file):
    """โหลดโมเดล - ลองหาในหลาย path"""
    paths = [
        f"models/{model_file}",
        model_file,
        f"../{model_file}",
        f"../../{model_file}"
    ]
    
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    data = pickle.load(f)
                return data['model'], data['scaler'], data['feature_names']
            except Exception as e:
                continue
    
    return None, None, None

def predict(model, scaler, features, input_data):
    """ทำนายจากโมเดล"""
    try:
        X = pd.DataFrame([input_data])[features]
        from sklearn.linear_model import LinearRegression
        if isinstance(model, LinearRegression):
            X = scaler.transform(X)
        return model.predict(X)[0]
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# ===================================
# Initialize Session State
# ===================================
if 'foundation_items' not in st.session_state:
    st.session_state.foundation_items = []
if 'column_items' not in st.session_state:
    st.session_state.column_items = []
if 'slab_items' not in st.session_state:
    st.session_state.slab_items = []
if 'beam_items' not in st.session_state:
    st.session_state.beam_items = []

# ===================================
# Main App
# ===================================
def main():
    # Header
    st.markdown("# 🏗️ Construction Quantity Estimation")
    st.markdown("### ระบบประมาณการปริมาณงานก่อสร้าง")
    
    # ขอบเขตงาน
    with st.expander("📋 ขอบเขตของงาน - คลิกเพื่ออ่าน", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **1. Foundation (ฐานราก)**
            - Input: Width, Length, Thickness, Count
            - Output: Volume, Formwork
            - ความแม่นยำ: ~99%
            
            **2. Column (เสา)**
            - Input: Width, Depth, Height, Count
            - Output: Volume, Formwork, Steel
            - ความแม่นยำ: ~83%
            """)
        
        with col2:
            st.markdown("""
            **3. Slab (พื้น)**
            - Input: Type (RC/PT), Thickness, Area, Count
            - Output: Volume, Formwork, Steel
            - ความแม่นยำ: ~80-98%
            
            **4. Beam (คาน)**
            - Input: Width (B), Height (H), Length, Count
            - Output: Volume, Formwork, Steel
            - ความแม่นยำ: ~73-91%
            """)
    
    st.markdown("---")
    
    # ===================================
    # 1. FOUNDATION - ลด Input เหลือ 4 ตัว
    # ===================================
    st.markdown("## 1️⃣ Foundation (ฐานราก)")
    
    with st.form("foundation_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            f_width = st.number_input("Width (m)", value=1.20, step=0.1, key="f_width")
            f_length = st.number_input("Length (m)", value=1.20, step=0.1, key="f_length")
        with col2:
            f_thickness = st.number_input("Thickness (m)", value=0.80, step=0.1, key="f_thickness")
        with col3:
            f_count = st.number_input("จำนวน (Count)", value=1, step=1, min_value=1, key="f_count")
        
        submitted_f = st.form_submit_button("➕ เพิ่ม Foundation", type="primary")
        
        if submitted_f:
            # คำนวณค่าอื่นๆ อัตโนมัติ
            f_area = f_width * f_length
            f_perimeter = 2 * (f_width + f_length)
            
            # คำนวณด้วยสูตร
            volume = f_width * f_length * f_thickness * f_count
            formwork = (2 * (f_width + f_length) * f_thickness) * f_count
            
            # ลองใช้โมเดล
            data = {
                'Width': f_width,
                'Length': f_length,
                'Thickness': f_thickness,
                'Area': f_area,
                'Perimeter': f_perimeter,
                'Count': f_count
            }
            
            model_vol, scaler_vol, features_vol = load_model("foundation_volume_model.pkl")
            model_form, scaler_form, features_form = load_model("foundation_formwork_model.pkl")
            
            if model_vol and model_form:
                volume_ml = predict(model_vol, scaler_vol, features_vol, data)
                formwork_ml = predict(model_form, scaler_form, features_form, data)
                if volume_ml and formwork_ml:
                    volume = volume_ml * f_count
                    formwork = formwork_ml * f_count
            
            st.session_state.foundation_items.append({
                'width': f_width,
                'length': f_length,
                'thickness': f_thickness,
                'count': f_count,
                'volume': volume,
                'formwork': formwork
            })
            st.success(f"✅ เพิ่ม Foundation จำนวน {f_count} รายการ")
    
    # แสดงรายการ Foundation
    if st.session_state.foundation_items:
        st.markdown("### 📋 รายการ Foundation")
        for i, item in enumerate(st.session_state.foundation_items):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**รายการ {i+1}:** {item['width']}m × {item['length']}m × {item['thickness']}m × {item['count']} ชิ้น")
            with col2:
                st.write(f"Volume: {item['volume']:.2f} m³")
            with col3:
                if st.button("🗑️ ลบ", key=f"del_f_{i}"):
                    st.session_state.foundation_items.pop(i)
                    st.rerun()
    
    st.markdown("---")
    
    # ===================================
    # 2. COLUMN - ลด Input เหลือ 4 ตัว
    # ===================================
    st.markdown("## 2️⃣ Column (เสา)")
    
    with st.form("column_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            c_width = st.number_input("Width (m)", value=0.30, step=0.05, key="c_width")
            c_depth = st.number_input("Depth (m)", value=0.30, step=0.05, key="c_depth")
        with col2:
            c_height = st.number_input("Height (m)", value=2.80, step=0.1, key="c_height")
        with col3:
            c_count = st.number_input("จำนวน (Count)", value=1, step=1, min_value=1, key="c_count")
        
        submitted_c = st.form_submit_button("➕ เพิ่ม Column", type="primary")
        
        if submitted_c:
            # คำนวณค่าอื่นๆ อัตโนมัติ
            c_perimeter = 2 * (c_width + c_depth)
            c_area = c_width * c_depth
            
            # คำนวณด้วยสูตร
            volume = c_width * c_depth * c_height * c_count
            formwork = c_perimeter * c_height * c_count
            steel = volume * 110
            
            # ลองใช้โมเดล
            data = {
                'Width': c_width,
                'Depth': c_depth,
                'Length': c_height,
                'Perimeter': c_perimeter,
                'Area Column': c_area
            }
            
            model_vol, scaler_vol, features_vol = load_model("column_volume_model.pkl")
            model_form, scaler_form, features_form = load_model("column_formwork_model.pkl")
            
            if model_vol and model_form:
                volume_ml = predict(model_vol, scaler_vol, features_vol, data)
                formwork_ml = predict(model_form, scaler_form, features_form, data)
                if volume_ml and formwork_ml:
                    volume = volume_ml * c_count
                    formwork = formwork_ml * c_count
                    steel = volume * 110
            
            st.session_state.column_items.append({
                'width': c_width,
                'depth': c_depth,
                'height': c_height,
                'count': c_count,
                'volume': volume,
                'formwork': formwork,
                'steel': steel
            })
            st.success(f"✅ เพิ่ม Column จำนวน {c_count} รายการ")
    
    # แสดงรายการ Column
    if st.session_state.column_items:
        st.markdown("### 📋 รายการ Column")
        for i, item in enumerate(st.session_state.column_items):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**รายการ {i+1}:** {item['width']}m × {item['depth']}m × {item['height']}m × {item['count']} ต้น")
            with col2:
                st.write(f"Volume: {item['volume']:.2f} m³, Steel: {item['steel']:.2f} kg")
            with col3:
                if st.button("🗑️ ลบ", key=f"del_c_{i}"):
                    st.session_state.column_items.pop(i)
                    st.rerun()
    
    st.markdown("---")
    
    # ===================================
    # 3. SLAB - ลด Input เหลือ 4 ตัว
    # ===================================
    st.markdown("## 3️⃣ Slab (พื้น)")
    
    with st.form("slab_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            s_type = st.selectbox("ประเภทพื้น", ["RC Slab", "Post-Tension Slab"], key="s_type")
            s_thickness = st.number_input("Thickness (m)", value=0.15, step=0.01, key="s_thickness")
        with col2:
            s_area = st.number_input("Area (m²)", value=80.0, step=1.0, key="s_area")
        with col3:
            s_count = st.number_input("จำนวน (Count)", value=1, step=1, min_value=1, key="s_count")
        
        submitted_s = st.form_submit_button("➕ เพิ่ม Slab", type="primary")
        
        if submitted_s:
            s_type_code = 0 if s_type == "RC Slab" else 1
            
            # ประมาณ Perimeter จาก Area (สมมติเป็นสี่เหลี่ยมผืนผ้า)
            # ถ้า Area = L × W และสมมติ L/W ≈ 1.5 (อัตราส่วนทั่วไป)
            # Perimeter ≈ 2 × sqrt(Area × 5)
            s_perimeter = 2 * (s_area ** 0.5) * 2.5
            
            # คำนวณด้วยสูตร
            volume = s_area * s_thickness * s_count
            formwork_side = s_perimeter * s_thickness * s_count
            formwork_all = (formwork_side + s_area) * s_count
            steel_per_m3 = 90 if s_type_code == 0 else 60
            steel = volume * steel_per_m3
            
            st.session_state.slab_items.append({
                'type': s_type,
                'thickness': s_thickness,
                'area': s_area,
                'count': s_count,
                'volume': volume,
                'formwork_side': formwork_side,
                'formwork_all': formwork_all,
                'steel': steel
            })
            st.success(f"✅ เพิ่ม {s_type} จำนวน {s_count} รายการ")
    
    # แสดงรายการ Slab
    if st.session_state.slab_items:
        st.markdown("### 📋 รายการ Slab")
        for i, item in enumerate(st.session_state.slab_items):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**รายการ {i+1}:** {item['type']} - {item['area']}m² × {item['thickness']}m × {item['count']} ชิ้น")
            with col2:
                st.write(f"Volume: {item['volume']:.2f} m³, Steel: {item['steel']:.2f} kg")
            with col3:
                if st.button("🗑️ ลบ", key=f"del_s_{i}"):
                    st.session_state.slab_items.pop(i)
                    st.rerun()
    
    st.markdown("---")
    
    # ===================================
    # 4. BEAM - ลด Input เหลือ 4 ตัว
    # ===================================
    st.markdown("## 4️⃣ Beam (คาน)")
    
    with st.form("beam_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            b_b = st.number_input("B - Width (m)", value=0.20, step=0.05, key="b_b")
            b_h = st.number_input("H - Height (m)", value=0.60, step=0.05, key="b_h")
        with col2:
            b_length = st.number_input("Length (m)", value=8.25, step=0.1, key="b_length")
        with col3:
            b_count = st.number_input("จำนวน (Count)", value=1, step=1, min_value=1, key="b_count")
        
        submitted_b = st.form_submit_button("➕ เพิ่ม Beam", type="primary")
        
        if submitted_b:
            # คำนวณด้วยสูตรก่อน
            cut_length = b_length * 0.85  # ประมาณการ 85% ของความยาวเต็ม
            volume_cut = b_b * b_h * cut_length * b_count
            volume_full = b_b * b_h * b_length * b_count
            steel_cut = volume_cut * 110
            steel_full = volume_full * 110
            formwork = 2 * (b_b + b_h) * b_length * b_count
            
            # ลองใช้โมเดล
            data_input = {
                'B': b_b,
                'H': b_h,
                'Length': b_length
            }
            
            model_cut, scaler_cut, features_cut = load_model("beam_cut_length_model.pkl")
            model_form, scaler_form, features_form = load_model("beam_formwork_model.pkl")
            
            if model_cut and model_form:
                cut_length_ml = predict(model_cut, scaler_cut, features_cut, data_input)
                if cut_length_ml:
                    cut_length = cut_length_ml
                    volume_cut = b_b * b_h * cut_length * b_count
                    steel_cut = volume_cut * 110
                    
                    data_with_cut = {
                        'B': b_b,
                        'H': b_h,
                        'Cut Length': cut_length,
                        'Length': b_length
                    }
                    formwork_ml = predict(model_form, scaler_form, features_form, data_with_cut)
                    if formwork_ml:
                        formwork = formwork_ml * b_count
            
            st.session_state.beam_items.append({
                'b': b_b,
                'h': b_h,
                'length': b_length,
                'count': b_count,
                'cut_length': cut_length,
                'volume_cut': volume_cut,
                'volume_full': volume_full,
                'steel_cut': steel_cut,
                'steel_full': steel_full,
                'formwork': formwork
            })
            st.success(f"✅ เพิ่ม Beam จำนวน {b_count} รายการ")
    
    # แสดงรายการ Beam
    if st.session_state.beam_items:
        st.markdown("### 📋 รายการ Beam")
        for i, item in enumerate(st.session_state.beam_items):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**รายการ {i+1}:** {item['b']}m × {item['h']}m × {item['length']}m × {item['count']} เส้น")
            with col2:
                st.write(f"Volume (Full): {item['volume_full']:.2f} m³")
            with col3:
                if st.button("🗑️ ลบ", key=f"del_b_{i}"):
                    st.session_state.beam_items.pop(i)
                    st.rerun()
    
    # ===================================
    # SUMMARY / TOTAL
    # ===================================
    st.markdown("---")
    st.markdown("## 📊 สรุปผลรวมทั้งหมด")
    
    total_volume = 0
    total_formwork = 0
    total_steel = 0
    
    # คำนวณผลรวม Foundation
    for item in st.session_state.foundation_items:
        total_volume += item['volume']
        total_formwork += item['formwork']
    
    # คำนวณผลรวม Column
    for item in st.session_state.column_items:
        total_volume += item['volume']
        total_formwork += item['formwork']
        total_steel += item['steel']
    
    # คำนวณผลรวม Slab
    for item in st.session_state.slab_items:
        total_volume += item['volume']
        total_formwork += item['formwork_all']
        total_steel += item['steel']
    
    # คำนวณผลรวม Beam
    for item in st.session_state.beam_items:
        total_volume += item['volume_full']
        total_formwork += item['formwork']
        total_steel += item['steel_full']
    
    if total_volume > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style='background-color: #e3f2fd; padding: 20px; border-radius: 10px; text-align: center;'>
                <h2 style='color: #1976d2; margin: 0;'>📦 Volume</h2>
                <h1 style='color: #1976d2; margin: 10px 0;'>{total_volume:.2f}</h1>
                <p style='color: #1976d2; margin: 0; font-size: 1.2em;'>m³</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='background-color: #f3e5f5; padding: 20px; border-radius: 10px; text-align: center;'>
                <h2 style='color: #7b1fa2; margin: 0;'>📐 Formwork</h2>
                <h1 style='color: #7b1fa2; margin: 10px 0;'>{total_formwork:.2f}</h1>
                <p style='color: #7b1fa2; margin: 0; font-size: 1.2em;'>m²</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='background-color: #fff3e0; padding: 20px; border-radius: 10px; text-align: center;'>
                <h2 style='color: #e65100; margin: 0;'>🔩 Steel</h2>
                <h1 style='color: #e65100; margin: 10px 0;'>{total_steel:.2f}</h1>
                <p style='color: #e65100; margin: 0; font-size: 1.2em;'>kg ({total_steel/1000:.2f} ตัน)</p>
            </div>
            """, unsafe_allow_html=True)
        
        # ตารางสรุป
        st.markdown("### 📋 รายละเอียดสรุป")
        
        summary_data = []
        
        if st.session_state.foundation_items:
            f_vol = sum(i['volume'] for i in st.session_state.foundation_items)
            f_form = sum(i['formwork'] for i in st.session_state.foundation_items)
            summary_data.append({'ส่วนงาน': 'Foundation', 'Volume (m³)': f"{f_vol:.2f}", 'Formwork (m²)': f"{f_form:.2f}", 'Steel (kg)': '-'})
        
        if st.session_state.column_items:
            c_vol = sum(i['volume'] for i in st.session_state.column_items)
            c_form = sum(i['formwork'] for i in st.session_state.column_items)
            c_steel = sum(i['steel'] for i in st.session_state.column_items)
            summary_data.append({'ส่วนงาน': 'Column', 'Volume (m³)': f"{c_vol:.2f}", 'Formwork (m²)': f"{c_form:.2f}", 'Steel (kg)': f"{c_steel:.2f}"})
        
        if st.session_state.slab_items:
            s_vol = sum(i['volume'] for i in st.session_state.slab_items)
            s_form = sum(i['formwork_all'] for i in st.session_state.slab_items)
            s_steel = sum(i['steel'] for i in st.session_state.slab_items)
            summary_data.append({'ส่วนงาน': 'Slab', 'Volume (m³)': f"{s_vol:.2f}", 'Formwork (m²)': f"{s_form:.2f}", 'Steel (kg)': f"{s_steel:.2f}"})
        
        if st.session_state.beam_items:
            b_vol = sum(i['volume_full'] for i in st.session_state.beam_items)
            b_form = sum(i['formwork'] for i in st.session_state.beam_items)
            b_steel = sum(i['steel_full'] for i in st.session_state.beam_items)
            summary_data.append({'ส่วนงาน': 'Beam', 'Volume (m³)': f"{b_vol:.2f}", 'Formwork (m²)': f"{b_form:.2f}", 'Steel (kg)': f"{b_steel:.2f}"})
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("📝 กรุณาเพิ่มรายการอย่างน้อย 1 ส่วนงานเพื่อดูผลรวม")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px;'>
        <p>⚠️ โปรดทราบ: ผลลัพธ์เป็นการประมาณการ ควรตรวจสอบกับแบบรายละเอียดก่อนใช้งานจริง</p>
        <p>Made with ❤️ for Construction Engineering</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
