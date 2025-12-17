from column_ml import load_and_predict

# ตัวอย่างที่ 1: เสา C01 - 300x1200 mm, สูง 2.80 m
print("=== ตัวอย่างที่ 1: เสา 300x1200 mm ===")
data1 = {
    'Width': 1200,         # 1200 mm = 1.2 m
    'Depth': 300,         # 300 mm = 0.3 m
    'Length': 2.8,        # ความสูง 2.8 m
    'Perimeter': 3000,     # (1.2+0.3)*2 = 3.0 m
    'Area Column': 2160,  # 1.2*0.3 = 0.36 m²
}

volume1 = load_and_predict('column_volume_model.pkl', data1)
formwork1 = load_and_predict('column_formwork_model.pkl', data1)

print(f"Input: {data1['Width']}m x {data1['Depth']}m x {data1['Length']}m")
print(f"ปริมาณคอนกรีต: {volume1:.2f} m³")
print(f"แบบหล่อ: {formwork1:.2f} m²")

# ตัวอย่างที่ 2: เสาขนาดอื่น
print("\n=== ตัวอย่างที่ 2: เสา 400x400 mm ===")
data2 = {
    'Width': 0.4,
    'Depth': 0.4,
    'Length': 3.0,
    'Perimeter': 1.6,     # (0.4+0.4)*2
    'Area Column': 0.16,  # 0.4*0.4
}

volume2 = load_and_predict('column_volume_model.pkl', data2)
formwork2 = load_and_predict('column_formwork_model.pkl', data2)

print(f"Input: {data2['Width']}m x {data2['Depth']}m x {data2['Length']}m")
print(f"ปริมาณคอนกรีต: {volume2:.2f} m³")
print(f"แบบหล่อ: {formwork2:.2f} m²")