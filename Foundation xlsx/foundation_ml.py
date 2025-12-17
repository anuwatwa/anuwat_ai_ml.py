"""
Foundation Volume & Formwork Prediction Model (ปรับปรุงแล้ว)
สำหรับทำนาย Volume of Concrete และ Formwork จากข้อมูลฐานราก

ขั้นตอนการใช้งาน:
1. ติดตั้ง libraries: pip install pandas openpyxl scikit-learn numpy
2. วางไฟล์ Excel ในโฟลเดอร์เดียวกับไฟล์ Python นี้
3. รันโค้ด: python foundation_ml.py
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
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
def load_and_clean_excel(file_path):
    """อ่านไฟล์ Excel และทำความสะอาดข้อมูล"""
    print(f"\n📂 กำลังอ่านไฟล์: {file_path}")
    
    # อ่านไฟล์โดยไม่กำหนด header ก่อน
    df_raw = pd.read_excel(file_path, header=None)
    
    # หาแถวที่เป็น header จริง (แถวแรกที่มีคำว่า Type, Width, Length, etc.)
    header_row = None
    for idx, row in df_raw.iterrows():
        row_str = ' '.join([str(x) for x in row if pd.notna(x)])
        if 'Type' in row_str or 'Width' in row_str or 'Count' in row_str:
            header_row = idx
            break
    
    if header_row is None:
        print("  ⚠️ ไม่พบ header ใช้แถวแรกเป็น header")
        header_row = 0
    
    # อ่านใหม่โดยใช้ header ที่ถูกต้อง
    df = pd.read_excel(file_path, header=header_row)
    
    # ลบแถวที่เป็น NaN ทั้งหมด
    df = df.dropna(how='all')
    
    # ลบคอลัมน์ที่เป็น NaN ทั้งหมด
    df = df.dropna(axis=1, how='all')
    
    # ลบแถวที่เป็น header ซ้ำ
    df = df[df.iloc[:, 0] != 'Type']
    
    # ทำความสะอาดชื่อคอลัมน์
    df.columns = df.columns.str.strip()
    
    print(f"  ✓ โหลดสำเร็จ: {len(df)} แถว")
    print(f"  ✓ คอลัมน์: {df.columns.tolist()[:5]}...")
    
    return df

def combine_all_files():
    """รวมไฟล์ทั้งหมด"""
    files = [
        '1.0 Foundation ปริมาณฐานราก.xlsx',
        '1.1 Foundation ปริมาณฐานราก ความลึกไม่เกิน 2 เมตร.xlsx',
        '1.2 Foundation ปริมาณฐานราก ความลึกเกิน 2 เมตร.xlsx'
    ]
    
    all_data = []
    for file in files:
        try:
            df = load_and_clean_excel(file)
            all_data.append(df)
        except Exception as e:
            print(f"  ✗ ข้อผิดพลาด: {e}")
    
    if not all_data:
        raise Exception("❌ ไม่สามารถโหลดไฟล์ได้")
    
    # รวมข้อมูล
    combined = pd.concat(all_data, ignore_index=True)
    print(f"\n✅ รวมข้อมูลทั้งหมด: {len(combined)} แถว")
    
    return combined

# ========================================
# 2. ทำความสะอาดและแปลงข้อมูล
# ========================================
def clean_numeric_column(series):
    """แปลงคอลัมน์เป็นตัวเลข (ลบหน่วยออก)"""
    if series.dtype == 'object':
        # ลบหน่วย เช่น 'm', 'm2', 'm3', 'kg'
        series = series.astype(str).str.replace(r'[^\d.-]', '', regex=True)
        series = pd.to_numeric(series, errors='coerce')
    return series

def prepare_data(df):
    """เตรียมข้อมูลสำหรับการเทรน"""
    print("\n" + "="*70)
    print("🔍 วิเคราะห์โครงสร้างข้อมูล")
    print("="*70)
    
    print(f"\nคอลัมน์ทั้งหมด ({len(df.columns)} คอลัมน์):")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    
    print("\nตัวอย่างข้อมูล 3 แถวแรก:")
    print(df.head(3).to_string())
    
    # ระบุคอลัมน์ที่เป็น features และ targets
    feature_mapping = {
        'width': ['Width', 'กว้าง', 'W'],
        'length': ['Length', 'ยาว', 'L'],
        'thickness': ['Thickness', 'หนา', 'Thk', 'Thick', 'T'],
        'area': ['Area', 'พื้นที่'],
        'perimeter': ['Perimeter', 'เส้นรอบรูป'],
        'count': ['Count', 'จำนวน', 'Qty']
    }
    
    target_mapping = {
        'volume': ['Volume', 'ปริมาตร', 'Concrete', 'คอนกรีต', 'Vol'],
        'formwork': ['Formwork', 'แบบหล่อ', 'Form'],
        'steel': ['Steel', 'เหล็ก', 'Rebar']
    }
    
    # หาคอลัมน์ที่ตรงกับ features
    feature_cols = []
    used_columns = set()  # เก็บคอลัมน์ที่ใช้ไปแล้ว
    
    for feature_type, keywords in feature_mapping.items():
        for col in df.columns:
            if col in used_columns:  # ข้ามถ้าใช้ไปแล้ว
                continue
            col_lower = col.lower()
            # ป้องกันไม่ให้เลือก Type เป็น Thickness
            if feature_type == 'thickness' and col_lower == 'type':
                continue
            # ป้องกันไม่ให้เลือก Count เป็น Thickness
            if feature_type == 'thickness' and col_lower == 'count':
                continue
            if any(kw.lower() in col_lower for kw in keywords):
                feature_cols.append(col)
                used_columns.add(col)
                print(f"  ✓ พบ {feature_type}: {col}")
                break
    
    # หาคอลัมน์ที่ตรงกับ targets
    target_volume = None
    target_formwork = None
    target_steel = None
    
    for col in df.columns:
        col_lower = col.lower()
        
        # ตรวจสอบ Volume (ยืดหยุ่นกว่า ไม่จำเป็นต้องมี m3)
        if target_volume is None:
            for kw in target_mapping['volume']:
                if kw.lower() in col_lower:
                    target_volume = col
                    print(f"  ✓ พบ Volume: {col}")
                    break
        
        # ตรวจสอบ Formwork (ยืดหยุ่นกว่า ไม่จำเป็นต้องมี m2)
        if target_formwork is None:
            for kw in target_mapping['formwork']:
                if kw.lower() in col_lower:
                    target_formwork = col
                    print(f"  ✓ พบ Formwork: {col}")
                    break
        
        # ตรวจสอบ Steel
        if target_steel is None:
            for kw in target_mapping['steel']:
                if kw.lower() in col_lower:
                    target_steel = col
                    print(f"  ✓ พบ Steel: {col}")
                    break
    
    # ทำความสะอาดข้อมูลตัวเลข
    print("\n🧹 ทำความสะอาดข้อมูล...")
    for col in feature_cols + [c for c in [target_volume, target_formwork, target_steel] if c]:
        if col in df.columns:
            df[col] = clean_numeric_column(df[col])
    
    # ลบแถวที่มีค่า NaN ในคอลัมน์สำคัญ
    important_cols = [c for c in feature_cols + [target_volume, target_formwork] if c]
    if important_cols:
        before_clean = len(df)
        df = df.dropna(subset=important_cols, how='any')
        print(f"✓ ลบแถวที่มี NaN: {before_clean - len(df)} แถว")
        print(f"✓ เหลือข้อมูลที่สมบูรณ์: {len(df)} แถว")
    else:
        print(f"⚠️ ไม่พบคอลัมน์สำคัญ เก็บข้อมูลทั้งหมด: {len(df)} แถว")
    
    return df, feature_cols, target_volume, target_formwork, target_steel

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
    if len(X) < 10:
        test_size = 0.1
    else:
        test_size = 0.2
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )
    
    # Standardize
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # ทดสอบหลายโมเดล
    models = {
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42, max_depth=5),
        'Gradient Boosting': GradientBoostingRegressor(n_estimators=50, random_state=42, max_depth=3),
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
    print(" 🏗️  Foundation ML Model Training ")
    print("="*70)
    
    try:
        # 1. โหลดข้อมูล
        df = combine_all_files()
        
        # 2. เตรียมข้อมูล
        df, features, vol_col, form_col, steel_col = prepare_data(df)
        
        if not features:
            print("\n❌ ไม่พบคอลัมน์ features ที่ใช้ได้")
            print("📋 กรุณาตรวจสอบว่าไฟล์มีคอลัมน์: Width, Length, Thickness, Area, Perimeter")
            exit(1)
        
        # 3. เทรนโมเดล Volume
        vol_model, vol_scaler, vol_features = train_model(df, features, vol_col, "Volume")
        if vol_model:
            save_model(vol_model, vol_scaler, vol_features, 'foundation_volume_model.pkl')
        
        # 4. เทรนโมเดล Formwork
        form_model, form_scaler, form_features = train_model(df, features, form_col, "Formwork")
        if form_model:
            save_model(form_model, form_scaler, form_features, 'foundation_formwork_model.pkl')
        
        # 5. เทรนโมเดล Steel
        steel_model, steel_scaler, steel_features = train_model(df, features, steel_col, "Steel")
        if steel_model:
            save_model(steel_model, steel_scaler, steel_features, 'foundation_steel_model.pkl')
        
        print("\n" + "="*70)
        print(" ✅ เทรนเสร็จสมบูรณ์! ")
        print("="*70)
        
        # แสดงตัวอย่างการใช้งาน
        if vol_model or form_model:
            print("\n📝 ตัวอย่างการใช้งาน:")
            print("-" * 70)
            print("from foundation_ml import load_and_predict")
            print()
            print("# ข้อมูล input")
            print("data = {")
            for feat in features:
                print(f"    '{feat}': 1.5,  # ใส่ค่าจริง")
            print("}")
            print()
            if vol_model:
                print("volume = load_and_predict('foundation_volume_model.pkl', data)")
                print("print(f'Volume: {volume:.2f} m³')")
            if form_model:
                print("formwork = load_and_predict('foundation_formwork_model.pkl', data)")
                print("print(f'Formwork: {formwork:.2f} m²')")
        
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()