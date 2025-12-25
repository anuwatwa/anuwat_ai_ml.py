"""
Streamlit UI - Construction Quantity Estimation (Simplified Version)
โปรแกรมประมาณการปริมาณงานก่อสร้างแบบคร่าวๆ

ติดตั้ง: pip install streamlit
รัน: streamlit run app_simple.py
"""

import streamlit as st
import pandas as pd

# ===================================
# Configuration
# ===================================
st.set_page_config(
    page_title="Construction Estimation - Simple",
    page_icon="🏗️",
    layout="wide"
)

# ===================================
# Initialize Session State
# ===================================
if 'items' not in st.session_state:
    st.session_state.items = []

# ===================================
# Calculation Functions
# ===================================
def calculate_foundation(width, length, height, count):
    """คำนวณฐานราก"""
    volume = width * length * height * count
    formwork = 2 * (width + length) * height * count
    steel = volume * 80  # kg/m³
    return {
        'volume': volume,
        'formwork': formwork,
        'steel': steel
    }

def calculate_column(width, height, count):
    """คำนวณเสา (กำหนดความสูง 3m)"""
    column_height = 3.0  # ความสูงมาตรฐาน
    volume = width * width * column_height * count
    formwork = 4 * width * column_height * count
    steel = volume * 120  # kg/m³
    return {
        'volume': volume,
        'formwork': formwork,
        'steel': steel
    }

def calculate_slab(area, thickness, slab_type, count):
    """คำนวณพื้น"""
    volume = area * thickness * count
    formwork = area * count  # พื้นล่าง
    steel_rate = 90 if slab_type == "RC Slab" else 60
    steel = volume * steel_rate
    return {
        'volume': volume,
        'formwork': formwork,
        'steel': steel
    }

def calculate_beam(width, height, length, count):
    """คำนวณคาน"""
    volume = width * height * length * count
    formwork = 2 * (width + height) * length * count
    steel = volume * 110  # kg/m³
    return {
        'volume': volume,
        'formwork': formwork,
        'steel': steel
    }

# ===================================
# Main App
# ===================================
def main():
    # Header
    st.markdown("# 🏗️ ประมาณการปริมาณงานก่อสร้าง (แบบคร่าวๆ)")
    st.markdown("### ระบบประเมินอย่างง่ายสำหรับงานโครงสร้าง")
    
    # คำอธิบาย
    st.info("💡 **วิธีใช้งาน:** เลือกประเภทงาน → กรอกขนาดหลักๆ → เพิ่มรายการ → ดูผลรวมด้านล่าง")
    
    st.markdown("---")
    
    # ===================================
    # Input Section - ใช้ Tabs เพื่อแยกประเภทงาน
    # ===================================
    tab1, tab2, tab3, tab4 = st.tabs(["🔲 ฐานราก", "🏛️ เสา", "⬜ พื้น", "➖ คาน"])
    
    # ==================== TAB 1: FOUNDATION ====================
    with tab1:
        st.markdown("### 🔲 ฐานราก (Foundation)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            f_width = st.number_input("กว้าง (m)", value=1.5, step=0.1, min_value=0.1, key="f_width")
            f_length = st.number_input("ยาว (m)", value=1.5, step=0.1, min_value=0.1, key="f_length")
        
        with col2:
            f_height = st.number_input("หนา (m)", value=0.8, step=0.1, min_value=0.1, key="f_height")
            f_count = st.number_input("จำนวน (ฐาน)", value=1, step=1, min_value=1, key="f_count")
        
        if st.button("➕ เพิ่มฐานราก", type="primary", key="add_f"):
            result = calculate_foundation(f_width, f_length, f_height, f_count)
            st.session_state.items.append({
                'type': 'Foundation',
                'description': f'{f_width}×{f_length}×{f_height}m ({f_count} ฐาน)',
                'volume': result['volume'],
                'formwork': result['formwork'],
                'steel': result['steel']
            })
            st.success(f"✅ เพิ่มฐานราก {f_count} ฐาน")
            st.rerun()
    
    # ==================== TAB 2: COLUMN ====================
    with tab2:
        st.markdown("### 🏛️ เสา (Column)")
        st.caption("*กำหนดความสูงเสามาตรฐาน 3.0m*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            c_width = st.number_input("ขนาดเสา (m)", value=0.4, step=0.05, min_value=0.1, key="c_width", 
                                     help="เสาสี่เหลี่ยมจตุรัส เช่น 0.4m = 40×40cm")
        
        with col2:
            c_count = st.number_input("จำนวน (ต้น)", value=1, step=1, min_value=1, key="c_count")
        
        st.info(f"📏 เสา {c_width*100:.0f}×{c_width*100:.0f}cm สูง 3m")
        
        if st.button("➕ เพิ่มเสา", type="primary", key="add_c"):
            result = calculate_column(c_width, 3.0, c_count)
            st.session_state.items.append({
                'type': 'Column',
                'description': f'{c_width*100:.0f}×{c_width*100:.0f}cm H=3m ({c_count} ต้น)',
                'volume': result['volume'],
                'formwork': result['formwork'],
                'steel': result['steel']
            })
            st.success(f"✅ เพิ่มเสา {c_count} ต้น")
            st.rerun()
    
    # ==================== TAB 3: SLAB ====================
    with tab3:
        st.markdown("### ⬜ พื้น (Slab)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            s_area = st.number_input("พื้นที่ (m²)", value=100.0, step=10.0, min_value=1.0, key="s_area")
            s_thickness = st.number_input("หนา (m)", value=0.15, step=0.01, min_value=0.05, key="s_thickness")
        
        with col2:
            s_type = st.selectbox("ประเภท", ["RC Slab", "Post-Tension Slab"], key="s_type")
            s_count = st.number_input("จำนวน (ชั้น)", value=1, step=1, min_value=1, key="s_count")
        
        if st.button("➕ เพิ่มพื้น", type="primary", key="add_s"):
            result = calculate_slab(s_area, s_thickness, s_type, s_count)
            st.session_state.items.append({
                'type': 'Slab',
                'description': f'{s_type}: {s_area}m² หนา {s_thickness}m ({s_count} ชั้น)',
                'volume': result['volume'],
                'formwork': result['formwork'],
                'steel': result['steel']
            })
            st.success(f"✅ เพิ่มพื้น {s_count} ชั้น")
            st.rerun()
    
    # ==================== TAB 4: BEAM ====================
    with tab4:
        st.markdown("### ➖ คาน (Beam)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            b_width = st.number_input("กว้าง (m)", value=0.25, step=0.05, min_value=0.1, key="b_width")
            b_height = st.number_input("สูง (m)", value=0.6, step=0.05, min_value=0.1, key="b_height")
        
        with col2:
            b_length = st.number_input("ยาว (m)", value=6.0, step=0.5, min_value=0.5, key="b_length")
            b_count = st.number_input("จำนวน (เส้น)", value=1, step=1, min_value=1, key="b_count")
        
        st.info(f"📏 คาน {b_width*100:.0f}×{b_height*100:.0f}cm ยาว {b_length}m")
        
        if st.button("➕ เพิ่มคาน", type="primary", key="add_b"):
            result = calculate_beam(b_width, b_height, b_length, b_count)
            st.session_state.items.append({
                'type': 'Beam',
                'description': f'{b_width*100:.0f}×{b_height*100:.0f}cm L={b_length}m ({b_count} เส้น)',
                'volume': result['volume'],
                'formwork': result['formwork'],
                'steel': result['steel']
            })
            st.success(f"✅ เพิ่มคาน {b_count} เส้น")
            st.rerun()
    
    # ===================================
    # รายการที่เพิ่มแล้ว
    # ===================================
    st.markdown("---")
    st.markdown("## 📋 รายการที่เพิ่มแล้ว")
    
    if st.session_state.items:
        # แสดงรายการโดยไม่ใช้ DataFrame
        for i, item in enumerate(st.session_state.items):
            col1, col2, col3 = st.columns([1, 4, 1])
            
            with col1:
                st.write(f"**{i+1}.**")
            
            with col2:
                st.write(f"**{item['type']}:** {item['description']}")
                st.caption(f"Vol: {item['volume']:.2f}m³ | Form: {item['formwork']:.2f}m² | Steel: {item['steel']:.2f}kg")
            
            with col3:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.items.pop(i)
                    st.rerun()
        
        st.markdown("---")
        
        # ปุ่มลบทั้งหมด
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🗑️ ลบทั้งหมด", type="secondary", use_container_width=True):
                st.session_state.items = []
                st.rerun()
    else:
        st.info("📝 ยังไม่มีรายการ กรุณาเพิ่มรายการจากด้านบน")
    
    # ===================================
    # SUMMARY / TOTAL
    # ===================================
    if st.session_state.items:
        st.markdown("---")
        st.markdown("## 📊 สรุปผลรวม")
        
        total_volume = sum(item['volume'] for item in st.session_state.items)
        total_formwork = sum(item['formwork'] for item in st.session_state.items)
        total_steel = sum(item['steel'] for item in st.session_state.items)
        
        # แสดงผลรวมแบบสวยงาม
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style='background-color: #e3f2fd; padding: 30px; border-radius: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h3 style='color: #1976d2; margin: 0;'>📦 คอนกรีต</h3>
                <h1 style='color: #1976d2; margin: 15px 0; font-size: 3em;'>{total_volume:.1f}</h1>
                <p style='color: #1976d2; margin: 0; font-size: 1.3em;'>ลูกบาศก์เมตร (m³)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='background-color: #f3e5f5; padding: 30px; border-radius: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h3 style='color: #7b1fa2; margin: 0;'>📐 แบบหล่อ</h3>
                <h1 style='color: #7b1fa2; margin: 15px 0; font-size: 3em;'>{total_formwork:.1f}</h1>
                <p style='color: #7b1fa2; margin: 0; font-size: 1.3em;'>ตารางเมตร (m²)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='background-color: #fff3e0; padding: 30px; border-radius: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h3 style='color: #e65100; margin: 0;'>🔩 เหล็กเสริม</h3>
                <h1 style='color: #e65100; margin: 15px 0; font-size: 3em;'>{total_steel/1000:.1f}</h1>
                <p style='color: #e65100; margin: 0; font-size: 1.3em;'>ตัน ({total_steel:.0f} kg)</p>
            </div>
            """, unsafe_allow_html=True)
        
        # ตารางสรุปแยกตามประเภท
        st.markdown("### 📋 สรุปแยกตามประเภท")
        
        summary_by_type = {}
        for item in st.session_state.items:
            item_type = item['type']
            if item_type not in summary_by_type:
                summary_by_type[item_type] = {'volume': 0, 'formwork': 0, 'steel': 0, 'count': 0}
            summary_by_type[item_type]['volume'] += item['volume']
            summary_by_type[item_type]['formwork'] += item['formwork']
            summary_by_type[item_type]['steel'] += item['steel']
            summary_by_type[item_type]['count'] += 1
        
        summary_data = []
        for item_type, values in summary_by_type.items():
            summary_data.append({
                'ประเภท': item_type,
                'จำนวนรายการ': values['count'],
                'คอนกรีต (m³)': f"{values['volume']:.2f}",
                'แบบหล่อ (m²)': f"{values['formwork']:.2f}",
                'เหล็ก (kg)': f"{values['steel']:.2f}"
            })
        
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)
        
        # ประมาณการค่าใช้จ่าย (คร่าวๆ)
        st.markdown("### 💰 ประมาณการค่าใช้จ่าย (คร่าวๆ)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            concrete_price = st.number_input("ราคาคอนกรีต (บาท/m³)", value=3000, step=100)
        with col2:
            formwork_price = st.number_input("ราคาแบบหล่อ (บาท/m²)", value=200, step=50)
        with col3:
            steel_price = st.number_input("ราคาเหล็ก (บาท/kg)", value=25, step=1)
        
        cost_concrete = total_volume * concrete_price
        cost_formwork = total_formwork * formwork_price
        cost_steel = total_steel * steel_price
        total_cost = cost_concrete + cost_formwork + cost_steel
        
        st.markdown(f"""
        <div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; margin-top: 20px;'>
            <h3 style='color: #2e7d32; margin-top: 0;'>รวมค่าใช้จ่ายประมาณ</h3>
            <ul style='font-size: 1.1em; color: #2e7d32;'>
                <li>คอนกรีต: {cost_concrete:,.0f} บาท</li>
                <li>แบบหล่อ: {cost_formwork:,.0f} บาท</li>
                <li>เหล็กเสริม: {cost_steel:,.0f} บาท</li>
            </ul>
            <h2 style='color: #1b5e20; margin-bottom: 0;'>รวมทั้งหมด: {total_cost:,.0f} บาท</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px;'>
        <p>⚠️ <strong>คำเตือน:</strong> ผลลัพธ์เป็นการประมาณการคร่าวๆ สำหรับการวางแผนเบื้องต้นเท่านั้น</p>
        <p>กรุณาใช้แบบรายละเอียดและปรึกษาวิศวกรโครงสร้างก่อนการก่อสร้างจริง</p>
        <p style='margin-top: 20px;'>Made with ❤️ for Construction Engineering</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
