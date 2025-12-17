from foundation_ml import load_and_predict

# ข้อมูลทดสอบ - เพิ่ม Thickness
data = {
    'Width': 1.20,# เมตร
    'Length': 1.20,# เมตร
    'Thickness': 0.80,# เมตร  
    'Count': 9,# จำนวน
    'Area': 12.96, # m²
    'Perimeter': 43.20,
}

volume = load_and_predict('foundation_volume_model.pkl', data)
formwork = load_and_predict('foundation_formwork_model.pkl', data)

print(f"ปริมาณคอนกรีต: {volume:.2f} m³")
print(f"แบบหล่อ: {formwork:.2f} m²")