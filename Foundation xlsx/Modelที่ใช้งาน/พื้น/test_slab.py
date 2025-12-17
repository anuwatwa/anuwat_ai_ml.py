"""
โปรแกรมคำนวณปริมาณพื้นด้วยสูตร (Formula-based)
แม่นยำกว่า ML เมื่อข้อมูลน้อย

วิธีใช้:
1. รัน: python calculate_slab_formula.py
2. ใส่ข้อมูล: Thickness, Perimeter, Area, ประเภทพื้น
3. ได้ผลลัพธ์ที่แม่นยำ
"""

import sys

def clear_screen():
    """ล้างหน้าจอ"""
    print("\n" * 2)

def get_float_input(prompt, min_value=0):
    """รับค่าตัวเลขจากผู้ใช้"""
    while True:
        try:
            value = float(input(prompt))
            if value < min_value:
                print(f"❌ กรุณาใส่ค่ามากกว่าหรือเท่ากับ {min_value}")
                continue
            return value
        except ValueError:
            print("❌ กรุณาใส่ตัวเลขที่ถูกต้อง")
        except KeyboardInterrupt:
            print("\n\n👋 ออกจากโปรแกรม")
            sys.exit(0)

def get_slab_type():
    """เลือกประเภทพื้น"""
    while True:
        print("\n🏢 เลือกประเภทพื้น:")
        print("  1. RC Slab (พื้นคอนกรีตเสริมเหล็ก)")
        print("  2. Post-Tension Slab (พื้นคอนกรีตอัดแรง)")
        
        try:
            choice = input("\nเลือก (1 หรือ 2): ").strip()
            
            if choice == "1":
                return "RC", "RC Slab"
            elif choice == "2":
                return "PT", "Post-Tension Slab"
            else:
                print("❌ กรุณาเลือก 1 หรือ 2 เท่านั้น")
        except KeyboardInterrupt:
            print("\n\n👋 ออกจากโปรแกรม")
            sys.exit(0)

def calculate_slab_formula(thickness, perimeter, area, slab_type):
    """
    คำนวณด้วยสูตรวิศวกรรม
    
    Parameters:
    - thickness: ความหนา (เมตร)
    - perimeter: เส้นรอบรูป (เมตร)
    - area: พื้นที่ (ตารางเมตร)
    - slab_type: "RC" หรือ "PT"
    
    Returns: dict
    """
    
    # 1. Volume of Concrete (m³)
    # สูตร: Volume = Area × Thickness
    volume = area * thickness
    
    # 2. Formwork (Side) - แบบหล่อด้านข้าง (m²)
    # สูตร: Formwork Side = Perimeter × Thickness
    formwork_side = perimeter * thickness
    
    # 3. Formwork (ALL) - แบบหล่อทั้งหมด (m²)
    # สูตร: Formwork ALL = Formwork Side + Area (พื้นที่ใต้พื้น)
    formwork_all = formwork_side + area
    
    # 4. Steel (kg) - ประมาณการ
    # RC Slab: ~80-100 kg/m³ สำหรับพื้นทั่วไป
    # PT Slab: ~50-70 kg/m³ (น้อยกว่า RC)
    if slab_type == "RC":
        steel_per_m3 = 90  # kg/m³
    else:  # PT
        steel_per_m3 = 60  # kg/m³
    
    steel = volume * steel_per_m3
    
    return {
        'volume': volume,
        'formwork_side': formwork_side,
        'formwork_all': formwork_all,
        'steel': steel,
        'steel_per_m3': steel_per_m3
    }

def calculate_slab():
    """ฟังก์ชันหลักสำหรับคำนวณ"""
    
    print("="*70)
    print(" 🏗️  โปรแกรมคำนวณปริมาณพื้น (Formula-based)")
    print("="*70)
    
    # 1. เลือกประเภทพื้น
    slab_type_code, slab_type_name = get_slab_type()
    
    # 2. รับค่า Input
    print("\n" + "="*70)
    print("📝 กรุณาใส่ข้อมูล")
    print("="*70)
    
    # ความหนา (m)
    thickness = get_float_input("\n1. ความหนาพื้น (เมตร, เช่น 0.15): ", min_value=0.05)
    
    # เส้นรอบรูป (m)
    perimeter = get_float_input("\n2. เส้นรอบรูปพื้น (เมตร, เช่น 60): ", min_value=0)
    
    # พื้นที่ (m²)
    area = get_float_input("\n3. พื้นที่พื้น (ตารางเมตร, เช่น 80): ", min_value=0)
    
    # 3. แสดงข้อมูลที่ใส่
    print("\n" + "="*70)
    print("📊 ข้อมูลที่ใส่")
    print("="*70)
    print(f"  ประเภทพื้น     : {slab_type_name}")
    print(f"  ความหนา        : {thickness:.3f} m")
    print(f"  เส้นรอบรูป     : {perimeter:.2f} m")
    print(f"  พื้นที่         : {area:.2f} m²")
    
    # 4. คำนวณด้วยสูตร
    print("\n" + "="*70)
    print("⏳ กำลังคำนวณ...")
    print("="*70)
    
    result = calculate_slab_formula(thickness, perimeter, area, slab_type_code)
    
    print("  ✓ คำนวณเสร็จสมบูรณ์")
    
    # 5. แสดงผลลัพธ์
    print("\n" + "="*70)
    print("🎯 ผลลัพธ์การคำนวณ")
    print("="*70)
    
    print(f"\n  📦 ปริมาณคอนกรีต (Volume)")
    print(f"     ├─ สูตร: Area × Thickness")
    print(f"     ├─ {area:.2f} × {thickness:.3f}")
    print(f"     └─ {result['volume']:.2f} m³")
    
    print(f"\n  📐 แบบหล่อด้านข้าง (Formwork Side)")
    print(f"     ├─ สูตร: Perimeter × Thickness")
    print(f"     ├─ {perimeter:.2f} × {thickness:.3f}")
    print(f"     └─ {result['formwork_side']:.2f} m²")
    
    print(f"\n  📐 แบบหล่อทั้งหมด (Formwork ALL)")
    print(f"     ├─ สูตร: Formwork Side + Area")
    print(f"     ├─ {result['formwork_side']:.2f} + {area:.2f}")
    print(f"     └─ {result['formwork_all']:.2f} m²")
    
    print(f"\n  🔩 น้ำหนักเหล็ก (Steel) - ประมาณการ")
    print(f"     ├─ สูตร: Volume × {result['steel_per_m3']} kg/m³")
    print(f"     ├─ {result['volume']:.2f} × {result['steel_per_m3']}")
    print(f"     └─ {result['steel']:.2f} kg ({result['steel']/1000:.2f} ตัน)")
    
    # 6. คำเตือน
    print("\n" + "="*70)
    print("⚠️  หมายเหตุ")
    print("="*70)
    print(f"""
• น้ำหนักเหล็กเป็นค่าประมาณการ ({result['steel_per_m3']} kg/m³)
  - ค่าจริงขึ้นอยู่กับการออกแบบโครงสร้าง
  - RC Slab ทั่วไป: 80-100 kg/m³
  - Post-Tension Slab: 50-70 kg/m³
  
• ควรตรวจสอบกับแบบรายละเอียดก่อนใช้งานจริง
""")
    
    # 7. สรุปสำหรับ copy
    print("\n" + "="*70)
    print("📋 สรุป (สำหรับ copy)")
    print("="*70)
    print(f"""
ประเภท: {slab_type_name}
ความหนา: {thickness:.3f} m
เส้นรอบรูป: {perimeter:.2f} m
พื้นที่: {area:.2f} m²

ผลลัพธ์:
- Volume: {result['volume']:.2f} m³
- Formwork (Side): {result['formwork_side']:.2f} m²
- Formwork (ALL): {result['formwork_all']:.2f} m²
- Steel (ประมาณการ): {result['steel']:.2f} kg ({result['steel']/1000:.2f} ตัน)
""")
    
    return True

def main():
    """ฟังก์ชันหลัก"""
    while True:
        # คำนวณ
        calculate_slab()
        
        # ถามว่าต้องการคำนวณต่อหรือไม่
        print("\n" + "="*70)
        choice = input("\n🔄 ต้องการคำนวณอีกครั้งหรือไม่? (y/n): ").strip().lower()
        
        if choice != 'y' and choice != 'yes':
            print("\n" + "="*70)
            print(" 👋 ขอบคุณที่ใช้บริการ!")
            print("="*70)
            break
        
        clear_screen()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print(" 👋 ออกจากโปรแกรม")
        print("="*70)