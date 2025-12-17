"""
Streamlit UI - Construction Quantity Estimation
โปรแกรมประมาณการปริมาณงานก่อสร้าง

ติดตั้ง: pip install streamlit
รัน: streamlit run app.py
"""

import streamlit as st
import pickle
import pandas as pd

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
    """โหลดโมเดล"""
    try:
        with open(f"models/{model_file}", 'rb') as f:
            data = pickle.load(f)
        return data['model'], data['scaler'], data['feature_names']
    except Exception as e:
        st.error(f"ไม่สามารถโหลดโมเดล {model_file}: {e}")
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
# Main App
# ===================================
def main():
    # Header
    st.markdown("# 🏗️ Construction Quantity Estimation")
    st.markdown("### ระบบประมาณการปริมาณงานก่อสร้าง")
    
    # ขอบเขตงาน
    with st.expander("📋 ขอบเขตของงาน - คลิกเพื่ออ่าน", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **1. Foundation (ฐานราก)**
            - Input: Width, Length, Thickness, Area, Perimeter, Count
            - Output: Volume, Formwork
            - ความแม่นยำ: ~99%
            
            **2. Column (เสา)**
            - Input: Width, Depth, Length, Perimeter, Area
            - Output: Volume, Formwork, Steel
            - ความแม่นยำ: ~83%
            """)
        
        with col2:
            st.markdown("""
            **3. Slab (พื้น)**
            - Input: Type (RC/PT), Thickness, Perimeter, Area
            - Output: Volume, Formwork (Side), Formwork (ALL), Steel
            - ความแม่นยำ: ~80-98%
            
            **4. Beam (คาน)**
            - Input: B, H, Length
            - Output: Cut Length, Volume (Cut/Full), Formwork, Steel
            - ความแม่นยำ: ~73-91%
            """)
    
    st.markdown("---")
    
    # Initialize results
    if 'results' not in st.session_state:
        st.session_state.results = {}
    
    # ===================================
    # Input Sections
    # ===================================
    
    # 1. FOUNDATION
    st.markdown("## 1️⃣ Foundation (ฐานราก)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        f_width = st.number_input("Width (m)", value=1.20, step=0.1, key="f_width")
        f_length = st.number_input("Length (m)", value=1.20, step=0.1, key="f_length")
    with col2:
        f_thickness = st.number_input("Thickness (m)", value=0.80, step=0.1, key="f_thickness")
        f_area = st.number_input("Area (m²)", value=1.44, step=0.1, key="f_area")
    with col3:
        f_perimeter = st.number_input("Perimeter (m)", value=4.8, step=0.1, key="f_perimeter")
        f_count = st.number_input("Count (จำนวน)", value=9, step=1, key="f_count")
    
    if st.button("Calculate Foundation", type="primary", key="calc_foundation"):
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
            volume = predict(model_vol, scaler_vol, features_vol, data)
            formwork = predict(model_form, scaler_form, features_form, data)
            
            st.session_state.results['foundation'] = {
                'volume': volume,
                'formwork': formwork
            }
            
            st.success("✅ คำนวณเสร็จสิ้น!")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Volume", f"{volume:.2f} m³")
            with col2:
                st.metric("Formwork", f"{formwork:.2f} m²")
    
    st.markdown("---")
    
    # 2. COLUMN
    st.markdown("## 2️⃣ Column (เสา)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        c_width = st.number_input("Width (m)", value=1.2, step=0.1, key="c_width")
        c_depth = st.number_input("Depth (m)", value=0.3, step=0.1, key="c_depth")
    with col2:
        c_length = st.number_input("Length/Height (m)", value=2.8, step=0.1, key="c_length")
        c_perimeter = st.number_input("Perimeter (m)", value=3.0, step=0.1, key="c_perimeter")
    with col3:
        c_area = st.number_input("Area Column (m²)", value=0.36, step=0.01, key="c_area")
    
    if st.button("Calculate Column", type="primary", key="calc_column"):
        data = {
            'Width': c_width,
            'Depth': c_depth,
            'Length': c_length,
            'Perimeter': c_perimeter,
            'Area Column': c_area
        }
        
        model_vol, scaler_vol, features_vol = load_model("column_volume_model.pkl")
        model_form, scaler_form, features_form = load_model("column_formwork_model.pkl")
        
        if model_vol and model_form:
            volume = predict(model_vol, scaler_vol, features_vol, data)
            formwork = predict(model_form, scaler_form, features_form, data)
            steel = volume * 110  # สูตร
            
            st.session_state.results['column'] = {
                'volume': volume,
                'formwork': formwork,
                'steel': steel
            }
            
            st.success("✅ คำนวณเสร็จสิ้น!")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Volume", f"{volume:.2f} m³")
            with col2:
                st.metric("Formwork", f"{formwork:.2f} m²")
            with col3:
                st.metric("Steel", f"{steel:.2f} kg")
    
    st.markdown("---")
    
    # 3. SLAB
    st.markdown("## 3️⃣ Slab (พื้น)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        s_type = st.selectbox("Slab Type", ["RC Slab", "Post-Tension Slab"], key="s_type")
        s_type_code = 0 if s_type == "RC Slab" else 1
        s_thickness = st.number_input("Thickness (m)", value=0.15, step=0.01, key="s_thickness")
    with col2:
        s_perimeter = st.number_input("Perimeter (m)", value=60.0, step=1.0, key="s_perimeter")
        s_area = st.number_input("Area (m²)", value=80.0, step=1.0, key="s_area")
    
    if st.button("Calculate Slab", type="primary", key="calc_slab"):
        # ใช้สูตรแทน ML
        volume = s_area * s_thickness
        formwork_side = s_perimeter * s_thickness
        formwork_all = formwork_side + s_area
        steel_per_m3 = 90 if s_type_code == 0 else 60
        steel = volume * steel_per_m3
        
        st.session_state.results['slab'] = {
            'volume': volume,
            'formwork_side': formwork_side,
            'formwork_all': formwork_all,
            'steel': steel
        }
        
        st.success("✅ คำนวณเสร็จสิ้น!")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Volume", f"{volume:.2f} m³")
        with col2:
            st.metric("Formwork (Side)", f"{formwork_side:.2f} m²")
        with col3:
            st.metric("Formwork (ALL)", f"{formwork_all:.2f} m²")
        with col4:
            st.metric("Steel", f"{steel:.2f} kg")
    
    st.markdown("---")
    
    # 4. BEAM
    st.markdown("## 4️⃣ Beam (คาน)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        b_b = st.number_input("B - Width (m)", value=0.20, step=0.01, key="b_b")
    with col2:
        b_h = st.number_input("H - Height (m)", value=0.60, step=0.01, key="b_h")
    with col3:
        b_length = st.number_input("Length (m)", value=8.25, step=0.1, key="b_length")
    
    if st.button("Calculate Beam", type="primary", key="calc_beam"):
        data_input = {
            'B': b_b,
            'H': b_h,
            'Length': b_length
        }
        
        model_cut, scaler_cut, features_cut = load_model("beam_cut_length_model.pkl")
        model_form, scaler_form, features_form = load_model("beam_formwork_model.pkl")
        
        if model_cut and model_form:
            cut_length = predict(model_cut, scaler_cut, features_cut, data_input)
            
            volume_cut = b_b * b_h * cut_length
            volume_full = b_b * b_h * b_length
            steel_cut = volume_cut * 110
            steel_full = volume_full * 110
            
            data_with_cut = {
                'B': b_b,
                'H': b_h,
                'Cut Length': cut_length,
                'Length': b_length
            }
            formwork = predict(model_form, scaler_form, features_form, data_with_cut)
            
            st.session_state.results['beam'] = {
                'cut_length': cut_length,
                'volume_cut': volume_cut,
                'volume_full': volume_full,
                'steel_cut': steel_cut,
                'steel_full': steel_full,
                'formwork': formwork
            }
            
            st.success("✅ คำนวณเสร็จสิ้น!")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Cut Length", f"{cut_length:.2f} m")
                st.metric("Volume (Cut)", f"{volume_cut:.2f} m³")
            with col2:
                st.metric("Volume (Full)", f"{volume_full:.2f} m³")
                st.metric("Steel (Cut)", f"{steel_cut:.2f} kg")
            with col3:
                st.metric("Steel (Full)", f"{steel_full:.2f} kg")
                st.metric("Formwork", f"{formwork:.2f} m²")
    
    # ===================================
    # SUMMARY / TOTAL
    # ===================================
    st.markdown("---")
    st.markdown("## 📊 สรุปผลรวมทั้งหมด")
    
    if st.session_state.results:
        total_volume = 0
        total_formwork = 0
        total_steel = 0
        
        # คำนวณผลรวม
        if 'foundation' in st.session_state.results and st.session_state.results['foundation']:
            r = st.session_state.results['foundation']
            total_volume += r['volume']
            total_formwork += r['formwork']
        
        if 'column' in st.session_state.results and st.session_state.results['column']:
            r = st.session_state.results['column']
            total_volume += r['volume']
            total_formwork += r['formwork']
            total_steel += r['steel']
        
        if 'slab' in st.session_state.results and st.session_state.results['slab']:
            r = st.session_state.results['slab']
            total_volume += r['volume']
            total_formwork += r['formwork_all']
            total_steel += r['steel']
        
        if 'beam' in st.session_state.results and st.session_state.results['beam']:
            r = st.session_state.results['beam']
            total_volume += r['volume_full']
            total_formwork += r['formwork']
            total_steel += r['steel_full']
        
        # แสดงผลรวม
        st.markdown("### 🎯 ผลรวมปริมาณงานทั้งหมด")
        
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
        
        # ตารางสรุปรายส่วน
        st.markdown("### 📋 รายละเอียดแยกตามส่วน")
        
        summary_data = []
        if 'foundation' in st.session_state.results and st.session_state.results['foundation']:
            r = st.session_state.results['foundation']
            summary_data.append({
                'ส่วนงาน': 'Foundation',
                'Volume (m³)': f"{r['volume']:.2f}",
                'Formwork (m²)': f"{r['formwork']:.2f}",
                'Steel (kg)': '-'
            })
        
        if 'column' in st.session_state.results and st.session_state.results['column']:
            r = st.session_state.results['column']
            summary_data.append({
                'ส่วนงาน': 'Column',
                'Volume (m³)': f"{r['volume']:.2f}",
                'Formwork (m²)': f"{r['formwork']:.2f}",
                'Steel (kg)': f"{r['steel']:.2f}"
            })
        
        if 'slab' in st.session_state.results and st.session_state.results['slab']:
            r = st.session_state.results['slab']
            summary_data.append({
                'ส่วนงาน': 'Slab',
                'Volume (m³)': f"{r['volume']:.2f}",
                'Formwork (m²)': f"{r['formwork_all']:.2f}",
                'Steel (kg)': f"{r['steel']:.2f}"
            })
        
        if 'beam' in st.session_state.results and st.session_state.results['beam']:
            r = st.session_state.results['beam']
            summary_data.append({
                'ส่วนงาน': 'Beam',
                'Volume (m³)': f"{r['volume_full']:.2f}",
                'Formwork (m²)': f"{r['formwork']:.2f}",
                'Steel (kg)': f"{r['steel_full']:.2f}"
            })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            st.dataframe(df, use_container_width=True)
    
    else:
        st.info("กรุณาคำนวณอย่างน้อย 1 ส่วนงานเพื่อดูผลรวม")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px;'>
        <p>⚠️ โปรดทราบ: ผลลัพธ์เป็นการประมาณการด้วย ML ควรตรวจสอบกับแบบรายละเอียดก่อนใช้งานจริง</p>
        <p>Made with ❤️ for Construction Engineering</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
