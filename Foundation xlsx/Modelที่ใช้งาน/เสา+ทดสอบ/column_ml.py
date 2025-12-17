"""
Column Volume, Formwork & Steel Prediction Model
สำหรับทำนาย Volume of Concrete, Formwork และ Steel จากข้อมูลเสา

ขั้นตอนการใช้งาน:
1. ติดตั้ง libraries: pip install pandas openpyxl scikit-learn numpy
2. วางไฟล์ CSV และ Excel ในโฟลเดอร์เดียวกับไฟล์ Python นี้
   - 2.0 Column ปริมาณเสา.csv
   - Steel in ML.xlsx
3. รันโค้ด: python column_ml.py
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
def load_column_data():
    """โหลดไฟล์ Column CSV"""
    print("\n📂 กำลังอ่านไฟล์: 2.0 Column ปริมาณเสา.csv")
    
    try:
        # ลองอ่านด้วย encoding หลายแบบ
        encodings = ['utf-8', 'utf-8-sig', 'cp874', 'windows-1252']
        df_raw = None
        
        for enc in encodings:
            try:
                df_raw = pd.read_csv('2.0 Column ปริมาณเสา.csv', encoding=enc, header=None)
                print(f"  ✓ อ่านไฟล์สำเร็จด้วย encoding: {enc}")
                break
            except:
                continue
        
        if df_raw is None:
            raise Exception("ไม่สามารถอ่านไฟล์ CSV ได้")
        
        # หาแถวที่เป็น header จริง
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
        df = pd.read_csv('2.0 Column ปริมาณเสา.csv', encoding='utf-8', header=header_row)
        
        # ลบแถวที่เป็น NaN ทั้งหมด
        df = df.dropna(how='all')
        
        # ลบคอลัมน์ที่เป็น NaN ทั้งหมด
        df = df.dropna(axis=1, how='all')
        
        # ลบแถวที่เป็น header ซ้ำ
        df = df[df.iloc[:, 0] != 'Type']
        
        # ทำความสะอาดชื่อคอลัมน์
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
        df = pd.read_excel('Steel in ML.xlsx')
        
        # ลบแถวที่เป็น NaN ทั้งหมด
        df = df.dropna(how='all')
        
        # ลบคอลัมน์ที่เป็น NaN ทั้งหมด
        df = df.dropna(axis=1, how='all')
        
        # ทำความสะอาดชื่อคอลัมน์
        df.columns = df.columns.str.strip()
        
        print(f"  ✓ โหลดสำเร็จ: {len(df)} แถว")
        print(f"  ✓ คอลัมน์: {df.columns.tolist()}")
        
        return df
        
    except Exception as e:
        print(f"  ✗ ข้อผิดพลาด: {e}")
        return None

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

def prepare_column_data(df_column, df_steel=None):
    """เตรียมข้อมูลเสาสำหรับการเทรน"""
    print("\n" + "="*70)
    print("🔍 วิเคราะห์โครงสร้างข้อมูลเสา")
    print("="*70)
    
    print(f"\nคอลัมน์ทั้งหมด ({len(df_column.columns)} คอลัมน์):")
    for i, col in enumerate(df_column.columns, 1):
        print(f"  {i}. {col}")
    
    print("\nตัวอย่างข้อมูล 3 แถวแรก:")
    print(df_column.head(3).to_string())
    
    # กำหนด feature columns ตามที่ระบุ - ปรับให้แม่นยำขึ้น
    feature_keywords = {
        'width': ['Width'],
        'deep': ['Depth'],  # แก้จาก Deep เป็น Depth
        'length': ['Length'],  # ต้องเป็นคอลัมน์ Length ไม่ใช่ Depth
        'perimeter': ['Perimeter'],
        'area': ['Area Column'],  # ระบุชัดเจน
    }
    
    # หา feature columns
    feature_cols = []
    used_columns = set()
    
    print("\n🔎 ค้นหา Features:")
    for feature_type, keywords in feature_keywords.items():
        for col in df_column.columns:
            if col in used_columns:
                continue
            col_lower = col.lower()
            
            # ป้องกันไม่ให้เลือก Type เป็น feature
            if col_lower == 'type':
                continue
            
            # ป้องกันไม่ให้เลือก Family เป็น feature
            if 'family' in col_lower:
                continue
                
            if any(kw.lower() in col_lower for kw in keywords):
                feature_cols.append(col)
                used_columns.add(col)
                print(f"  ✓ พบ {feature_type}: {col}")
                break
    
    # หา target columns
    target_volume = None
    target_formwork = None
    target_steel = None
    
    print("\n🎯 ค้นหา Targets:")
    
    # หา Volume
    for col in df_column.columns:
        col_lower = col.lower()
        if 'volume' in col_lower or 'ปริมาตร' in col_lower:
            target_volume = col
            print(f"  ✓ พบ Volume: {col}")
            break
    
    # หา Formwork (ต้องไม่อยู่ใน feature_cols)
    for col in df_column.columns:
        if col in feature_cols:  # ข้ามถ้าใช้เป็น feature แล้ว
            continue
        col_lower = col.lower()
        if 'formwork' in col_lower or 'แบบหล่อ' in col_lower:
            target_formwork = col
            print(f"  ✓ พบ Formwork: {col}")
            break
    
    # หา Steel จากไฟล์ที่สอง
    if df_steel is not None:
        print(f"  📊 ข้อมูล Steel: {len(df_steel)} แถว, Column: {len(df_column)} แถว")
        
        for col in df_steel.columns:
            col_lower = col.lower()
            if 'total' in col_lower and ('steel' in col_lower or 'reinf' in col_lower or 'kg' in col_lower):
                target_steel = col
                print(f"  ✓ พบ Steel: {col} (จากไฟล์ Steel)")
                
                # รวมข้อมูล Steel เข้ากับ Column
                # ใช้จำนวนแถวที่น้อยกว่า
                min_len = min(len(df_steel), len(df_column))
                df_column = df_column.head(min_len).copy()
                df_column[target_steel] = df_steel[col].head(min_len).values
                print(f"  ✓ รวมข้อมูล Steel: {min_len} แถว")
                break
    
    # ทำความสะอาดข้อมูลตัวเลข
    print("\n🧹 ทำความสะอาดข้อมูล...")
    all_numeric_cols = feature_cols + [c for c in [target_volume, target_formwork, target_steel] if c and c in df_column.columns]
    
    for col in all_numeric_cols:
        if col in df_column.columns:
            df_column[col] = clean_numeric_column(df_column[col])
    
    # ลบแถวที่มี NaN ในคอลัมน์สำคัญ - แยกการเช็ค Steel ออก
    important_cols = [c for c in feature_cols + [target_volume, target_formwork] if c and c in df_column.columns]
    
    if important_cols:
        before_clean = len(df_column)
        df_column = df_column.dropna(subset=important_cols, how='any')
        print(f"  ✓ ลบแถวที่มี NaN ใน Volume/Formwork: {before_clean - len(df_column)} แถว")
        print(f"  ✓ เหลือข้อมูลสำหรับ Volume/Formwork: {len(df_column)} แถว")
    
    # แยกจัดการ Steel - ไม่บังคับให้มีครบทุกแถว
    if target_steel and target_steel in df_column.columns:
        steel_valid_count = df_column[target_steel].notna().sum()
        print(f"  ✓ ข้อมูล Steel ที่มี: {steel_valid_count} แถว")
    
    return df_column, feature_cols, target_volume, target_formwork, target_steel

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
    
    print("\n ผลการทดสอบโมเดล:")
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
    print(" 🏛️  Column ML Model Training ")
    print("="*70)
    
    try:
        # 1. โหลดข้อมูล
        df_column = load_column_data()
        df_steel = load_steel_data()
        
        if df_column is None:
            print("\n❌ ไม่สามารถโหลดไฟล์ Column ได้")
            exit(1)
        
        # 2. เตรียมข้อมูล
        df, features, vol_col, form_col, steel_col = prepare_column_data(df_column, df_steel)
        
        if not features:
            print("\n❌ ไม่พบคอลัมน์ features ที่ใช้ได้")
            print("📋 กรุณาตรวจสอบว่าไฟล์มีคอลัมน์: Width, Deep, Length, Perimeter, Area")
            exit(1)
        
        # 3. เทรนโมเดล Volume (ไม่รวม Steel)
        vol_model, vol_scaler, vol_features = train_model(df, features, vol_col, "Volume of Concrete")
        if vol_model:
            save_model(vol_model, vol_scaler, vol_features, 'column_volume_model.pkl')
        
        # 4. เทรนโมเดล Formwork (ไม่รวม Steel)
        form_model, form_scaler, form_features = train_model(df, features, form_col, "Formwork")
        if form_model:
            save_model(form_model, form_scaler, form_features, 'column_formwork_model.pkl')
        
        # 5. เทรนโมเดล Steel (เฉพาะแถวที่มีข้อมูล Steel)
        if steel_col and steel_col in df.columns:
            df_steel_only = df[df[steel_col].notna()].copy()
            print(f"\n🔧 เตรียมข้อมูล Steel: {len(df_steel_only)} แถวที่มีข้อมูล Steel")
            
            if len(df_steel_only) >= 5:
                steel_model, steel_scaler, steel_features = train_model(df_steel_only, features, steel_col, "Steel")
                if steel_model:
                    save_model(steel_model, steel_scaler, steel_features, 'column_steel_model.pkl')
            else:
                print(f"⚠️ ข้อมูล Steel มีแค่ {len(df_steel_only)} แถว (ต้องการอย่างน้อย 5 แถว)")
        else:
            print("\n⚠️ ไม่มีข้อมูล Steel")
        
        print("\n" + "="*70)
        print(" ✅ เทรนเสร็จสมบูรณ์! ")
        print("="*70)
        
        # แสดงตัวอย่างการใช้งาน
        if vol_model or form_model or steel_model:
            print("\n📝 ตัวอย่างการใช้งาน:")
            print("-" * 70)
            print("from column_ml import load_and_predict")
            print()
            print("# ข้อมูล input")
            print("data = {")
            for feat in features:
                print(f"    '{feat}': 0.5,  # ใส่ค่าจริง (หน่วย: เมตร)")
            print("}")
            print()
            if vol_model:
                print("volume = load_and_predict('column_volume_model.pkl', data)")
                print("print(f'Volume: {volume:.2f} m³')")
            if form_model:
                print("formwork = load_and_predict('column_formwork_model.pkl', data)")
                print("print(f'Formwork: {formwork:.2f} m²')")
            if steel_model:
                print("steel = load_and_predict('column_steel_model.pkl', data)")
                print("print(f'Steel: {steel:.2f} kg')")
        
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()