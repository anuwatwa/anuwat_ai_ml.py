"""
Slab Volume, Formwork & Steel Prediction Model (RC + Post-Tension)
สำหรับทำนาย Volume, Formwork (Side), Formwork (ALL) และ Steel จากข้อมูลพื้น

ขั้นตอนการใช้งาน:
1. ติดตั้ง libraries: pip install pandas openpyxl scikit-learn numpy
2. วางไฟล์ CSV และ Excel ในโฟลเดอร์เดียวกับไฟล์ Python นี้
   - 4.1 RC Floor ปริมาณพื้นคอนกรีตเสริมเหล็ก.csv
   - 4.2 PS Floor ปริมาณพื้นคอนกรีตอัดแรง.csv
   - Steel in ML.xlsx
3. รันโค้ด: python slab_ml.py
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
import warnings
warnings.filterwarnings('ignore')

# ========================================
# 1. โหลดและประมวลผลข้อมูล
# ========================================
def load_slab_data():
    """โหลดไฟล์ Slab ทั้ง RC และ Post-Tension"""
    print("\n" + "="*70)
    print("📂 กำลังโหลดข้อมูลพื้น")
    print("="*70)
    
    all_data = []
    
    # โหลด RC Floor
    print("\n📂 กำลังอ่านไฟล์: 4.1 RC Floor ปริมาณพื้นคอนกรีตเสริมเหล็ก.csv")
    try:
        encodings = ['utf-8', 'utf-8-sig', 'cp874', 'windows-1252']
        df_rc = None
        
        for enc in encodings:
            try:
                # เพิ่ม on_bad_lines='skip' เพื่อข้ามแถวที่มีปัญหา
                df_rc = pd.read_csv('4.1 RC Floor ปริมาณพื้นคอนกรีตเสริมเหล็ก.csv', 
                                   encoding=enc, header=None, on_bad_lines='skip')
                print(f"  ✓ อ่านไฟล์สำเร็จด้วย encoding: {enc}")
                break
            except:
                continue
        
        if df_rc is None:
            raise Exception("ไม่สามารถอ่านไฟล์ RC Floor ได้")
        
        # หาแถวที่เป็น header
        header_row = None
        for idx, row in df_rc.iterrows():
            row_str = ' '.join([str(x) for x in row if pd.notna(x)])
            if 'Type' in row_str or 'Thickness' in row_str or 'Perimeter' in row_str:
                header_row = idx
                break
        
        if header_row is None:
            header_row = 0
        
        # อ่านใหม่ด้วย header ที่ถูกต้อง
        df_rc = pd.read_csv('4.1 RC Floor ปริมาณพื้นคอนกรีตเสริมเหล็ก.csv', 
                           encoding='utf-8', header=header_row, on_bad_lines='skip')
        df_rc = df_rc.dropna(how='all').dropna(axis=1, how='all')
        df_rc = df_rc[df_rc.iloc[:, 0] != 'Type']
        df_rc.columns = df_rc.columns.str.strip()
        
        # เพิ่มคอลัมน์ Type
        df_rc['Slab_Type'] = 0  # 0 = RC
        
        print(f"  ✓ โหลด RC Floor สำเร็จ: {len(df_rc)} แถว")
        print(f"  ✓ คอลัมน์: {df_rc.columns.tolist()}")
        all_data.append(df_rc)
        
    except Exception as e:
        print(f"  ✗ ข้อผิดพลาด: {e}")
    
    # โหลด Post-Tension Floor
    print("\n📂 กำลังอ่านไฟล์: 4.2 PS Floor ปริมาณพื้นคอนกรีตอัดแรง.csv")
    try:
        df_pt = None
        
        for enc in encodings:
            try:
                df_pt = pd.read_csv('4.2 PS Floor ปริมาณพื้นคอนกรีตอัดแรง.csv', 
                                   encoding=enc, header=None, on_bad_lines='skip')
                print(f"  ✓ อ่านไฟล์สำเร็จด้วย encoding: {enc}")
                break
            except:
                continue
        
        if df_pt is None:
            raise Exception("ไม่สามารถอ่านไฟล์ PS Floor ได้")
        
        # หาแถวที่เป็น header
        header_row = None
        for idx, row in df_pt.iterrows():
            row_str = ' '.join([str(x) for x in row if pd.notna(x)])
            if 'Type' in row_str or 'Thickness' in row_str or 'Perimeter' in row_str:
                header_row = idx
                break
        
        if header_row is None:
            header_row = 0
        
        # อ่านใหม่ด้วย header ที่ถูกต้อง
        df_pt = pd.read_csv('4.2 PS Floor ปริมาณพื้นคอนกรีตอัดแรง.csv', 
                           encoding='utf-8', header=header_row, on_bad_lines='skip')
        df_pt = df_pt.dropna(how='all').dropna(axis=1, how='all')
        df_pt = df_pt[df_pt.iloc[:, 0] != 'Type']
        df_pt.columns = df_pt.columns.str.strip()
        
        # เพิ่มคอลัมน์ Type
        df_pt['Slab_Type'] = 1  # 1 = Post-Tension
        
        print(f"  ✓ โหลด PS Floor สำเร็จ: {len(df_pt)} แถว")
        print(f"  ✓ คอลัมน์: {df_pt.columns.tolist()}")
        all_data.append(df_pt)
        
    except Exception as e:
        print(f"  ✗ ข้อผิดพลาด: {e}")
    
    if not all_data:
        raise Exception("❌ ไม่สามารถโหลดไฟล์ใดๆ ได้")
    
    # รวมข้อมูล
    combined = pd.concat(all_data, ignore_index=True)
    print(f"\n✅ รวมข้อมูลทั้งหมด: {len(combined)} แถว")
    print(f"   - RC: {(combined['Slab_Type']==0).sum()} แถว")
    print(f"   - Post-Tension: {(combined['Slab_Type']==1).sum()} แถว")
    
    return combined

def load_steel_data():
    """โหลดไฟล์ Steel Excel"""
    print("\n📂 กำลังอ่านไฟล์: Steel in ML.xlsx")
    
    try:
        # อ่านทุก sheet
        excel_file = pd.ExcelFile('Steel in ML.xlsx')
        print(f"  ✓ พบ sheets: {excel_file.sheet_names}")
        
        # หา sheet ที่เกี่ยวกับ Slab
        steel_data = {}
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel('Steel in ML.xlsx', sheet_name=sheet_name)
            df = df.dropna(how='all').dropna(axis=1, how='all')
            df.columns = df.columns.str.strip()
            
            # เช็คว่าเป็นข้อมูล Slab หรือไม่
            sheet_lower = sheet_name.lower()
            if 'slab' in sheet_lower or 'floor' in sheet_lower or 'พื้น' in sheet_lower:
                if 'rc' in sheet_lower:
                    steel_data['RC'] = df
                    print(f"  ✓ พบข้อมูล RC Slab Steel: {len(df)} แถว")
                elif 'pt' in sheet_lower or 'post' in sheet_lower or 'tension' in sheet_lower or 'อัดแรง' in sheet_lower:
                    steel_data['PT'] = df
                    print(f"  ✓ พบข้อมูล Post-Tension Slab Steel: {len(df)} แถว")
        
        # ถ้าไม่เจอ sheet ที่ชัดเจน ให้อ่าน sheet แรก
        if not steel_data:
            df = pd.read_excel('Steel in ML.xlsx')
            df = df.dropna(how='all').dropna(axis=1, how='all')
            df.columns = df.columns.str.strip()
            steel_data['ALL'] = df
            print(f"  ✓ โหลด Steel (ทั้งหมด): {len(df)} แถว")
        
        return steel_data
        
    except Exception as e:
        print(f"  ✗ ข้อผิดพลาด: {e}")
        return None

# ========================================
# 2. ทำความสะอาดและแปลงข้อมูล
# ========================================
def clean_numeric_column(series):
    """แปลงคอลัมน์เป็นตัวเลข (ลบหน่วยออก)"""
    if series.dtype == 'object':
        series = series.astype(str).str.replace(r'[^\d.-]', '', regex=True)
        series = pd.to_numeric(series, errors='coerce')
    return series

def prepare_slab_data(df_slab, steel_data=None):
    """เตรียมข้อมูลพื้นสำหรับการเทรน"""
    print("\n" + "="*70)
    print("🔍 วิเคราะห์โครงสร้างข้อมูลพื้น")
    print("="*70)
    
    print(f"\nคอลัมน์ทั้งหมด ({len(df_slab.columns)} คอลัมน์):")
    for i, col in enumerate(df_slab.columns, 1):
        print(f"  {i}. {col}")
    
    print("\nตัวอย่างข้อมูล 3 แถวแรก:")
    print(df_slab.head(3).to_string())
    
    # กำหนด feature columns
    feature_keywords = {
        'thickness': ['Thickness', 'หนา', 'Default Thickness'],
        'perimeter': ['Perimeter', 'เส้นรอบรูป'],
        'area': ['Area', 'พื้นที่'],
        'slab_type': ['Slab_Type'],  # Type ที่เราเพิ่มเข้าไป
    }
    
    # หา feature columns
    feature_cols = []
    used_columns = set()
    
    print("\n🔎 ค้นหา Features:")
    for feature_type, keywords in feature_keywords.items():
        for col in df_slab.columns:
            if col in used_columns:
                continue
            col_lower = col.lower()
            
            # ป้องกันไม่ให้เลือก Type, Description, Family
            if col_lower in ['type', 'description', 'family']:
                continue
            
            if any(kw.lower() in col_lower for kw in keywords):
                feature_cols.append(col)
                used_columns.add(col)
                print(f"  ✓ พบ {feature_type}: {col}")
                break
    
    # หา target columns
    target_volume = None
    target_formwork_side = None
    target_formwork_all = None
    target_steel = None
    
    print("\n🎯 ค้นหา Targets:")
    
    # หา Volume
    for col in df_slab.columns:
        if col in feature_cols:
            continue
        col_lower = col.lower()
        if 'volume' in col_lower or 'ปริมาตร' in col_lower:
            target_volume = col
            print(f"  ✓ พบ Volume: {col}")
            break
    
    # หา Formwork (Side)
    for col in df_slab.columns:
        if col in feature_cols:
            continue
        col_lower = col.lower()
        if 'formwork' in col_lower and 'side' in col_lower:
            target_formwork_side = col
            print(f"  ✓ พบ Formwork (Side): {col}")
            break
    
    # หา Formwork (ALL)
    for col in df_slab.columns:
        if col in feature_cols:
            continue
        col_lower = col.lower()
        if 'formwork' in col_lower and 'all' in col_lower:
            target_formwork_all = col
            print(f"  ✓ พบ Formwork (ALL): {col}")
            break
    
    # รวมข้อมูล Steel
    if steel_data:
        print(f"\n🔧 รวมข้อมูล Steel:")
        
        # แยกข้อมูล RC และ PT
        df_rc = df_slab[df_slab['Slab_Type'] == 0].copy()
        df_pt = df_slab[df_slab['Slab_Type'] == 1].copy()
        
        # รวม Steel RC
        if 'RC' in steel_data:
            steel_rc = steel_data['RC']
            for col in steel_rc.columns:
                col_lower = col.lower()
                if 'total' in col_lower and ('steel' in col_lower or 'reinf' in col_lower or 'kg' in col_lower):
                    min_len = min(len(steel_rc), len(df_rc))
                    df_rc = df_rc.head(min_len).copy()
                    df_rc['Steel'] = steel_rc[col].head(min_len).values
                    print(f"  ✓ รวม RC Steel: {min_len} แถว")
                    break
        
        # รวม Steel PT
        if 'PT' in steel_data:
            steel_pt = steel_data['PT']
            for col in steel_pt.columns:
                col_lower = col.lower()
                if 'total' in col_lower and ('steel' in col_lower or 'reinf' in col_lower or 'kg' in col_lower):
                    min_len = min(len(steel_pt), len(df_pt))
                    df_pt = df_pt.head(min_len).copy()
                    df_pt['Steel'] = steel_pt[col].head(min_len).values
                    print(f"  ✓ รวม PT Steel: {min_len} แถว")
                    break
        
        # รวม Steel ทั้งหมด (ถ้ามี sheet เดียว)
        if 'ALL' in steel_data and 'Steel' not in df_slab.columns:
            steel_all = steel_data['ALL']
            for col in steel_all.columns:
                col_lower = col.lower()
                if 'total' in col_lower and ('steel' in col_lower or 'reinf' in col_lower or 'kg' in col_lower):
                    min_len = min(len(steel_all), len(df_slab))
                    df_slab = df_slab.head(min_len).copy()
                    df_slab['Steel'] = steel_all[col].head(min_len).values
                    print(f"  ✓ รวม Steel ทั้งหมด: {min_len} แถว")
                    break
        else:
            # รวม df_rc และ df_pt กลับเข้าไป
            df_slab = pd.concat([df_rc, df_pt], ignore_index=True)
        
        if 'Steel' in df_slab.columns:
            target_steel = 'Steel'
            print(f"  ✓ พบ Steel column")
    
    # ทำความสะอาดข้อมูลตัวเลข
    print("\n🧹 ทำความสะอาดข้อมูล...")
    all_numeric_cols = feature_cols + [c for c in [target_volume, target_formwork_side, target_formwork_all, target_steel] if c and c in df_slab.columns]
    
    for col in all_numeric_cols:
        if col in df_slab.columns and col != 'Slab_Type':
            df_slab[col] = clean_numeric_column(df_slab[col])
    
    # ลบแถวที่มี NaN ในคอลัมน์สำคัญ
    important_cols = [c for c in feature_cols + [target_volume] if c and c in df_slab.columns]
    
    if important_cols:
        before_clean = len(df_slab)
        df_slab = df_slab.dropna(subset=important_cols, how='any')
        print(f"  ✓ ลบแถวที่มี NaN: {before_clean - len(df_slab)} แถว")
        print(f"  ✓ เหลือข้อมูล: {len(df_slab)} แถว")
        print(f"     - RC: {(df_slab['Slab_Type']==0).sum()} แถว")
        print(f"     - PT: {(df_slab['Slab_Type']==1).sum()} แถว")
    
    return df_slab, feature_cols, target_volume, target_formwork_side, target_formwork_all, target_steel

# ========================================
# 3. เทรนโมเดล
# ========================================
def train_model(df, feature_cols, target_col, model_name):
    """เทรนโมเดล ML"""
    if target_col is None or target_col not in df.columns:
        print(f"\n⚠️ ข้ามการเทรน {model_name} (ไม่พบข้อมูล)")
        return None, None, None
    
    print(f"\n{'='*70}")
    print(f"🤖 เทรนโมเดล: {model_name}")
    print(f"{'='*70}")
    
    # เตรียมข้อมูล
    X = df[feature_cols].copy()
    y = df[target_col].copy()
    
    # ตรวจสอบข้อมูล
    valid_mask = ~(X.isnull().any(axis=1) | y.isnull())
    X = X[valid_mask]
    y = y[valid_mask]
    
    print(f"📊 จำนวนข้อมูล: {len(X)} แถว")
    if 'Slab_Type' in X.columns:
        print(f"   - RC: {(X['Slab_Type']==0).sum()} แถว")
        print(f"   - PT: {(X['Slab_Type']==1).sum()} แถว")
    print(f"📊 Features: {X.columns.tolist()}")
    print(f"📊 Target range: {y.min():.2f} - {y.max():.2f}")
    
    if len(X) < 5:
        print(f"❌ ข้อมูลน้อยเกินไป (ต้องการอย่างน้อย 5 แถว)")
        return None, None, None
    
    # แบ่งข้อมูล
    test_size = 0.2 if len(X) >= 10 else 0.1
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )
    
    # Standardize
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # ทดสอบหลายโมเดล
    models = {
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10),
        'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=5),
        'Linear Regression': LinearRegression()
    }
    
    best_model = None
    best_score = -np.inf
    best_name = ""
    
    print("\n📈 ผลการทดสอบโมเดล:")
    for name, model in models.items():
        try:
            if name == 'Linear Regression':
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
            
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            print(f"\n  {name}:")
            print(f"    R² Score: {r2:.4f}")
            print(f"    MAE: {mae:.4f}")
            print(f"    RMSE: {rmse:.4f}")
            
            if r2 > best_score:
                best_score = r2
                best_model = model
                best_name = name
        except Exception as e:
            print(f"  ⚠️ {name} ล้มเหลว: {e}")
    
    if best_model:
        print(f"\n✅ เลือกใช้: {best_name} (R² = {best_score:.4f})")
    
    return best_model, scaler, X.columns.tolist()

# ========================================
# 4. บันทึกและโหลดโมเดล
# ========================================
def save_model(model, scaler, feature_names, filename):
    """บันทึกโมเดล"""
    if model is None:
        return
    
    model_data = {
        'model': model,
        'scaler': scaler,
        'feature_names': feature_names
    }
    
    with open(filename, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"💾 บันทึกที่: {filename}")

def load_and_predict(model_file, input_data):
    """โหลดโมเดลและทำนาย
    
    input_data ต้องมี 'slab_type': 0=RC, 1=Post-Tension
    """
    with open(model_file, 'rb') as f:
        data = pickle.load(f)
    
    model = data['model']
    scaler = data['scaler']
    features = data['feature_names']
    
    # เตรียม input
    X = pd.DataFrame([input_data])[features]
    
    # ทำนาย
    if isinstance(model, LinearRegression):
        X = scaler.transform(X)
    
    return model.predict(X)[0]

# ========================================
# MAIN
# ========================================
if __name__ == "__main__":
    print("\n" + "="*70)
    print(" 🏢  Slab ML Model Training (RC + Post-Tension)")
    print("="*70)
    
    try:
        # 1. โหลดข้อมูล
        df_slab = load_slab_data()
        steel_data = load_steel_data()
        
        # 2. เตรียมข้อมูล
        df, features, vol_col, form_side_col, form_all_col, steel_col = prepare_slab_data(df_slab, steel_data)
        
        if not features:
            print("\n❌ ไม่พบคอลัมน์ features ที่ใช้ได้")
            exit(1)
        
        # 3. เทรนโมเดล Volume
        vol_model, vol_scaler, vol_features = train_model(df, features, vol_col, "Volume")
        if vol_model:
            save_model(vol_model, vol_scaler, vol_features, 'slab_volume_model.pkl')
        
        # 4. เทรนโมเดล Formwork (Side)
        form_side_model, form_side_scaler, form_side_features = train_model(df, features, form_side_col, "Formwork (Side)")
        if form_side_model:
            save_model(form_side_model, form_side_scaler, form_side_features, 'slab_formwork_side_model.pkl')
        
        # 5. เทรนโมเดล Formwork (ALL)
        form_all_model, form_all_scaler, form_all_features = train_model(df, features, form_all_col, "Formwork (ALL)")
        if form_all_model:
            save_model(form_all_model, form_all_scaler, form_all_features, 'slab_formwork_all_model.pkl')
        
        # 6. เทรนโมเดล Steel (เฉพาะแถวที่มีข้อมูล)
        if steel_col and steel_col in df.columns:
            df_steel_only = df[df[steel_col].notna()].copy()
            print(f"\n🔧 เตรียมข้อมูล Steel: {len(df_steel_only)} แถวที่มีข้อมูล Steel")
            
            if len(df_steel_only) >= 5:
                steel_model, steel_scaler, steel_features = train_model(df_steel_only, features, steel_col, "Steel")
                if steel_model:
                    save_model(steel_model, steel_scaler, steel_features, 'slab_steel_model.pkl')
            else:
                print(f"⚠️ ข้อมูล Steel มีแค่ {len(df_steel_only)} แถว (ต้องการอย่างน้อย 5 แถว)")
        
        print("\n" + "="*70)
        print(" ✅ เทรนเสร็จสมบูรณ์! ")
        print("="*70)
        
        # แสดงตัวอย่างการใช้งาน
        print("\n📝 ตัวอย่างการใช้งาน:")
        print("-" * 70)
        print("from slab_ml import load_and_predict")
        print()
        print("# สำหรับ RC Slab")
        print("data_rc = {")
        print("    'Slab_Type': 0,  # 0 = RC")
        for feat in features:
            if feat != 'Slab_Type':
                print(f"    '{feat}': 0.15,  # ใส่ค่าจริง")
        print("}")
        print()
        print("# สำหรับ Post-Tension Slab")
        print("data_pt = {")
        print("    'Slab_Type': 1,  # 1 = Post-Tension")
        for feat in features:
            if feat != 'Slab_Type':
                print(f"    '{feat}': 0.20,  # ใส่ค่าจริง")
        print("}")
        print()
        if vol_model:
            print("volume = load_and_predict('slab_volume_model.pkl', data_rc)")
            print("print(f'Volume: {volume:.2f} m³')")
        
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()