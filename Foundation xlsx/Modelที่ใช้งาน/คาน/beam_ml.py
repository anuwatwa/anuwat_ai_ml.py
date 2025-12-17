"""
Beam Volume, Cut Length, Length, Formwork & Steel Prediction Model
สำหรับทำนาย Volume, Cut Length, Length, Formwork และ Steel จากข้อมูลคาน

ขั้นตอนการใช้งาน:
1. ติดตั้ง libraries: pip install pandas openpyxl scikit-learn numpy
2. วางไฟล์ในโฟลเดอร์เดียวกับไฟล์ Python นี้
   - 3.0 Framing ปริมาณคาน.csv
   - Steel in ML.xlsx
3. รันโค้ด: python beam_ml.py
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
def load_beam_data():
    """โหลดไฟล์ Beam CSV"""
    print("\n📂 กำลังอ่านไฟล์: 3.0 Framing ปริมาณคาน.csv")
    
    try:
        encodings = ['utf-8', 'utf-8-sig', 'cp874', 'windows-1252']
        df = None
        
        for enc in encodings:
            try:
                df = pd.read_csv('3.0 Framing ปริมาณคาน.csv', 
                               encoding=enc, header=None, on_bad_lines='skip')
                print(f"  ✓ อ่านไฟล์สำเร็จด้วย encoding: {enc}")
                break
            except:
                continue
        
        if df is None:
            raise Exception("ไม่สามารถอ่านไฟล์ Beam ได้")
        
        # หาแถวที่เป็น header
        header_row = None
        for idx, row in df.iterrows():
            row_str = ' '.join([str(x) for x in row if pd.notna(x)])
            if 'Type' in row_str or 'Width' in row_str or 'Length' in row_str:
                header_row = idx
                break
        
        if header_row is None:
            header_row = 0
        
        # อ่านใหม่ด้วย header ที่ถูกต้อง
        df = pd.read_csv('3.0 Framing ปริมาณคาน.csv', 
                        encoding='utf-8', header=header_row, on_bad_lines='skip')
        df = df.dropna(how='all').dropna(axis=1, how='all')
        df = df[df.iloc[:, 0] != 'Type']
        df.columns = df.columns.str.strip()
        
        print(f"  ✓ โหลดสำเร็จ: {len(df)} แถว")
        print(f"  ✓ คอลัมน์: {df.columns.tolist()}")
        
        return df
        
    except Exception as e:
        print(f"  ✗ ข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()
        return None

def load_steel_data():
    """โหลดไฟล์ Steel Excel"""
    print("\n📂 กำลังอ่านไฟล์: Steel in ML.xlsx")
    
    try:
        excel_file = pd.ExcelFile('Steel in ML.xlsx')
        print(f"  ✓ พบ sheets: {excel_file.sheet_names}")
        
        # หา sheet ที่เกี่ยวกับ Beam
        steel_data = None
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel('Steel in ML.xlsx', sheet_name=sheet_name)
            df = df.dropna(how='all').dropna(axis=1, how='all')
            df.columns = df.columns.str.strip()
            
            sheet_lower = sheet_name.lower()
            if 'beam' in sheet_lower or 'framing' in sheet_lower or 'คาน' in sheet_lower:
                steel_data = df
                print(f"  ✓ พบข้อมูล Beam Steel: {len(df)} แถว")
                break
        
        # ถ้าไม่เจอ sheet ที่ชัดเจน ให้อ่าน sheet แรก
        if steel_data is None:
            df = pd.read_excel('Steel in ML.xlsx')
            df = df.dropna(how='all').dropna(axis=1, how='all')
            df.columns = df.columns.str.strip()
            steel_data = df
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

def prepare_beam_data(df_beam, df_steel=None):
    """เตรียมข้อมูลคานสำหรับการเทรน"""
    print("\n" + "="*70)
    print("🔍 วิเคราะห์โครงสร้างข้อมูลคาน")
    print("="*70)
    
    print(f"\nคอลัมน์ทั้งหมด ({len(df_beam.columns)} คอลัมน์):")
    for i, col in enumerate(df_beam.columns, 1):
        print(f"  {i}. {col}")
    
    print("\nตัวอย่างข้อมูล 3 แถวแรก:")
    print(df_beam.head(3).to_string())
    
    # กำหนด feature columns - ปรับเฉพาะ B, H, Length
    feature_keywords_for_cut = {
        'b': ['B', 'Width', 'กว้าง'],
        'h': ['H', 'Height', 'Depth', 'สูง'],
        'length': ['Length', 'ยาว'],
    }
    
    # หา feature columns สำหรับทำนาย Cut Length
    feature_cols_for_cut = []
    used_for_cut = set()
    
    print("\n🔎 ค้นหา Features สำหรับทำนาย Cut Length:")
    for feature_type, keywords in feature_keywords_for_cut.items():
        for col in df_beam.columns:
            if col in used_for_cut:
                continue
            col_lower = col.lower()
            
            # ป้องกันไม่ให้เลือก Type, Description, Family
            if col_lower in ['type', 'description', 'family', 'level', 'count']:
                continue
            
            # ป้องกันไม่ให้เลือก Cut Length, Formwork, Volume เป็น feature
            if 'cut' in col_lower or 'formwork' in col_lower or 'volume' in col_lower:
                continue
            
            if any(kw.lower() in col_lower for kw in keywords):
                feature_cols_for_cut.append(col)
                used_for_cut.add(col)
                print(f"  ✓ พบ {feature_type}: {col}")
                break
    
    # กำหนด feature columns - ใช้ทุกอย่างยกเว้น targets
    feature_keywords = {
        'b': ['B', 'Width', 'กว้าง'],
        'h': ['H', 'Height', 'Depth', 'สูง'],
        'cut_length': ['Cut Length', 'Cut', 'ตัด'],
        'length': ['Length', 'ยาว'],
    }
    
    # หา feature columns
    feature_cols = []
    used_columns = set()
    
    print("\n🔎 ค้นหา Features สำหรับ Volume/Formwork:")
    for feature_type, keywords in feature_keywords.items():
        for col in df_beam.columns:
            if col in used_columns:
                continue
            col_lower = col.lower()
            
            # ป้องกันไม่ให้เลือก Type, Description, Family
            if col_lower in ['type', 'description', 'family', 'level', 'count']:
                continue
            
            # ป้องกันไม่ให้เลือก Formwork, Volume เป็น feature
            if 'formwork' in col_lower or 'volume' in col_lower:
                continue
            
            if any(kw.lower() in col_lower for kw in keywords):
                feature_cols.append(col)
                used_columns.add(col)
                print(f"  ✓ พบ {feature_type}: {col}")
                break
    
    # หา target columns
    target_volume = None
    target_cut_length = None
    target_length = None
    target_formwork = None
    target_steel = None
    
    print("\n🎯 ค้นหา Targets:")
    
    # หา Volume
    for col in df_beam.columns:
        if col in feature_cols:
            continue
        col_lower = col.lower()
        if 'volume' in col_lower or 'ปริมาตร' in col_lower:
            target_volume = col
            print(f"  ✓ พบ Volume: {col}")
            break
    
    # หา Cut Length (ต้องไม่อยู่ใน features_for_cut)
    for col in df_beam.columns:
        if col in feature_cols_for_cut:
            continue
        col_lower = col.lower()
        if 'cut' in col_lower and 'length' in col_lower:
            target_cut_length = col
            print(f"  ✓ พบ Cut Length: {col}")
            break
    
    # หา Length (ที่ไม่ใช่ Cut Length)
    for col in df_beam.columns:
        if col in feature_cols or col == target_cut_length:
            continue
        col_lower = col.lower()
        if 'length' in col_lower and 'cut' not in col_lower:
            target_length = col
            print(f"  ✓ พบ Length: {col}")
            break
    
    # หา Formwork
    for col in df_beam.columns:
        if col in feature_cols:
            continue
        col_lower = col.lower()
        if 'formwork' in col_lower or 'แบบหล่อ' in col_lower:
            target_formwork = col
            print(f"  ✓ พบ Formwork: {col}")
            break
    
    # รวมข้อมูล Steel
    if df_steel is not None:
        print(f"\n🔧 รวมข้อมูล Steel:")
        print(f"  📊 ข้อมูล Steel: {len(df_steel)} แถว, Beam: {len(df_beam)} แถว")
        
        for col in df_steel.columns:
            col_lower = col.lower()
            if 'total' in col_lower and ('steel' in col_lower or 'reinf' in col_lower or 'kg' in col_lower):
                min_len = min(len(df_steel), len(df_beam))
                df_beam = df_beam.head(min_len).copy()
                df_beam['Steel'] = df_steel[col].head(min_len).values
                target_steel = 'Steel'
                print(f"  ✓ รวมข้อมูล Steel: {min_len} แถว")
                break
    
    # ทำความสะอาดข้อมูลตัวเลข
    print("\n🧹 ทำความสะอาดข้อมูล...")
    all_numeric_cols = feature_cols + [c for c in [target_volume, target_cut_length, target_length, target_formwork, target_steel] if c and c in df_beam.columns]
    
    for col in all_numeric_cols:
        if col in df_beam.columns:
            df_beam[col] = clean_numeric_column(df_beam[col])
    
    # ลบแถวที่มี NaN ในคอลัมน์สำคัญ
    important_cols = [c for c in feature_cols + [target_volume] if c and c in df_beam.columns]
    
    if important_cols:
        before_clean = len(df_beam)
        df_beam = df_beam.dropna(subset=important_cols, how='any')
        print(f"  ✓ ลบแถวที่มี NaN: {before_clean - len(df_beam)} แถว")
        print(f"  ✓ เหลือข้อมูล: {len(df_beam)} แถว")
    
    return df_beam, feature_cols, feature_cols_for_cut, target_volume, target_cut_length, target_length, target_formwork, target_steel

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
    """โหลดโมเดลและทำนาย"""
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
    print(" 🏗️  Beam ML Model Training ")
    print("="*70)
    
    try:
        # 1. โหลดข้อมูล
        df_beam = load_beam_data()
        df_steel = load_steel_data()
        
        if df_beam is None:
            print("\n❌ ไม่สามารถโหลดไฟล์ Beam ได้")
            exit(1)
        
        # 2. เตรียมข้อมูล
        df, features, features_for_cut, vol_col, cut_len_col, len_col, form_col, steel_col = prepare_beam_data(df_beam, df_steel)
        
        if not features:
            print("\n❌ ไม่พบคอลัมน์ features ที่ใช้ได้")
            print("📋 กรุณาตรวจสอบว่าไฟล์มีคอลัมน์: B, H, Cut Length, Length")
            exit(1)
        
        # 3. เทรนโมเดล Cut Length (Input: B, H, Length → Output: Cut Length)
        cut_len_model = None
        if cut_len_col and features_for_cut:
            cut_len_model, cut_len_scaler, cut_len_features = train_model(df, features_for_cut, cut_len_col, "Cut Length")
            if cut_len_model:
                save_model(cut_len_model, cut_len_scaler, cut_len_features, 'beam_cut_length_model.pkl')
        
        # 4. เทรนโมเดล Volume
        vol_model = None
        vol_model, vol_scaler, vol_features = train_model(df, features, vol_col, "Volume")
        if vol_model:
            save_model(vol_model, vol_scaler, vol_features, 'beam_volume_model.pkl')
        
        # 5. เทรนโมเดล Length (ถ้ามี)
        len_model = None
        if len_col:
            len_model, len_scaler, len_features = train_model(df, features_for_cut, len_col, "Length")
            if len_model:
                save_model(len_model, len_scaler, len_features, 'beam_length_model.pkl')
        
        # 6. เทรนโมเดล Formwork
        form_model = None
        form_model, form_scaler, form_features = train_model(df, features, form_col, "Formwork")
        if form_model:
            save_model(form_model, form_scaler, form_features, 'beam_formwork_model.pkl')
        
        # 7. เทรนโมเดล Steel (เฉพาะแถวที่มีข้อมูล)
        if steel_col and steel_col in df.columns:
            df_steel_only = df[df[steel_col].notna()].copy()
            print(f"\n🔧 เตรียมข้อมูล Steel: {len(df_steel_only)} แถวที่มีข้อมูล Steel")
            
            if len(df_steel_only) >= 5:
                steel_model, steel_scaler, steel_features = train_model(df_steel_only, features, steel_col, "Steel")
                if steel_model:
                    save_model(steel_model, steel_scaler, steel_features, 'beam_steel_model.pkl')
            else:
                print(f"⚠️ ข้อมูล Steel มีแค่ {len(df_steel_only)} แถว (ต้องการอย่างน้อย 5 แถว)")
        
        print("\n" + "="*70)
        print(" ✅ เทรนเสร็จสมบูรณ์! ")
        print("="*70)
        
        # แสดงตัวอย่างการใช้งาน
        print("\n📝 ตัวอย่างการใช้งาน:")
        print("-" * 70)
        print("from beam_ml import load_and_predict")
        print()
        print("# ข้อมูล input: B, H, Length")
        print("data = {")
        print("    'B': 0.20,      # กว้าง 200mm")
        print("    'H': 0.60,      # สูง 600mm")
        print("    'Length': 8.25  # ความยาวเต็ม")
        print("}")
        print()
        print("# ทำนาย Cut Length")
        if cut_len_model:
            print("cut_length = load_and_predict('beam_cut_length_model.pkl', data)")
            print("print(f'Cut Length: {cut_length:.2f} m')")
            print()
        print("# คำนวณ Volume Cut และ Full")
        print("volume_cut = data['B'] * data['H'] * cut_length")
        print("volume_full = data['B'] * data['H'] * data['Length']")
        print()
        print("# คำนวณ Steel")
        print("steel_cut = volume_cut * 110  # kg/m³")
        print("steel_full = volume_full * 110")
        print()
        if form_model:
            print("# ทำนาย Formwork")
            print("formwork = load_and_predict('beam_formwork_model.pkl', data)")
            print("print(f'Formwork: {formwork:.2f} m²')")
        
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()