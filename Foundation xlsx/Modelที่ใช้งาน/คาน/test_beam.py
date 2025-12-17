"""
โปรแกรมคำนวณปริมาณคาน (Beam Calculator)
Input: B, H, Length
Output: Cut Length, Volume Cut/Full, Steel Cut/Full, Formwork

วิธีใช้:
1. รัน: python calculate_beam.py
2. ใส่ข้อมูล: B, H, Length
3. ได้ผลลัพธ์ทั้งหมด
"""

from beam_ml import load_and_predict
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

def calculate_beam():
    """ฟังก์ชันหลักสำหรับคำนวณ"""
    
    print("="*70)
    print(" 🏗️  โปรแกรมคำนวณปริมาณคาน (Beam Calculator)")
    print("="*70)
    
    # รับค่า Input
    print("\n" + "="*70)
    print("📝 กรุณาใส่ข้อมูล")
    print("="*70)
    
    # B (กว้าง)
    b = get_float_input("\n1. ความกว้างคาน B (เมตร, เช่น 0.20): ", min_value=0.1)
    
    # H (สูง)
    h = get_float_input("\n2. ความสูงคาน H (เมตร, เช่น 0.60): ", min_value=0.1)
    
    # Length (ความยาวเต็ม)
    length = get_float_input("\n3. ความยาวเต็ม Length (เมตร, เช่น 8.25): ", min_value=0)
    
    # เตรียมข้อมูลสำหรับโมเดล
    data = {
        'B': b,
        'H': h,
        'Length': length,
    }
    
    # แสดงข้อมูลที่ใส่
    print("\n" + "="*70)
    print("📊 ข้อมูลที่ใส่")
    print("="*70)
    print(f"  ความกว้าง (B)    : {b:.3f} m")
    print(f"  ความสูง (H)      : {h:.3f} m")
    print(f"  ความยาวเต็ม     : {length:.2f} m")
    
    # คำนวณด้วยโมเดล
    print("\n" + "="*70)
    print("⏳ กำลังคำนวณ...")
    print("="*70)
    
    try:
        # 1. ทำนาย Cut Length (ML)
        cut_length = load_and_predict('beam_cut_length_model.pkl', data)
        print("  ✓ ทำนาย Cut Length สำเร็จ (ML)")
        
        # 2. คำนวณ Volume Cut และ Full (สูตร)
        volume_cut = b * h * cut_length
        volume_full = b * h * length
        print("  ✓ คำนวณ Volume Cut และ Full สำเร็จ (สูตร)")
        
        # 3. คำนวณ Steel Cut และ Full (สูตร)
        steel_per_m3 = 110  # kg/m³
        steel_cut = volume_cut * steel_per_m3
        steel_full = volume_full * steel_per_m3
        print("  ✓ คำนวณ Steel Cut และ Full สำเร็จ (สูตร)")
        
        # 4. ทำนาย Formwork (ML) - ใช้ Cut Length ที่ทำนายได้
        data_with_cut = {
            'B': b,
            'H': h,
            'Cut Length': cut_length,
            'Length': length,
        }
        formwork = load_and_predict('beam_formwork_model.pkl', data_with_cut)
        print("  ✓ ทำนาย Formwork สำเร็จ (ML)")
        
        # แสดงผลลัพธ์
        print("\n" + "="*70)
        print("🎯 ผลลัพธ์การคำนวณ")
        print("="*70)
        
        print(f"\n  📏 ความยาวตัด (Cut Length) - โดย ML")
        print(f"     ├─ Input: B={b:.2f}, H={h:.2f}, Length={length:.2f}")
        print(f"     └─ {cut_length:.2f} m")
        
        print(f"\n  📦 ปริมาณคอนกรีต (Volume)")
        print(f"     ├─ Volume (Cut):  {volume_cut:.2f} m³")
        print(f"     │  └─ {b:.2f} × {h:.2f} × {cut_length:.2f}")
        print(f"     └─ Volume (Full): {volume_full:.2f} m³")
        print(f"        └─ {b:.2f} × {h:.2f} × {length:.2f}")
        
        print(f"\n  🔩 น้ำหนักเหล็ก (Steel)")
        print(f"     ├─ Steel (Cut):  {steel_cut:.2f} kg ({steel_cut/1000:.2f} ตัน)")
        print(f"     │  └─ {volume_cut:.2f} × {steel_per_m3}")
        print(f"     └─ Steel (Full): {steel_full:.2f} kg ({steel_full/1000:.2f} ตัน)")
        print(f"        └─ {volume_full:.2f} × {steel_per_m3}")
        
        print(f"\n  📐 แบบหล่อ (Formwork) - โดย ML")
        print(f"     └─ {formwork:.2f} m²")
        
        # เปรียบเทียบ
        cut_ratio = (cut_length / length) * 100 if length > 0 else 0
        volume_diff = volume_full - volume_cut
        steel_diff = steel_full - steel_cut
        
        print("\n" + "="*70)
        print("📊 การเปรียบเทียบ Cut vs Full")
        print("="*70)
        print(f"  ความยาว:")
        print(f"     ├─ Cut Length:  {cut_length:.2f} m ({cut_ratio:.1f}% ของความยาวเต็ม)")
        print(f"     └─ Full Length: {length:.2f} m")
        print(f"  ปริมาณคอนกรีต:")
        print(f"     ├─ ส่วนต่าง:    {volume_diff:.2f} m³")
        print(f"     └─ ประหยัด:     {(volume_diff/volume_full*100):.1f}% เมื่อใช้ Cut")
        print(f"  น้ำหนักเหล็ก:")
        print(f"     ├─ ส่วนต่าง:    {steel_diff:.2f} kg")
        print(f"     └─ ประหยัด:     {(steel_diff/steel_full*100):.1f}% เมื่อใช้ Cut")
        
        # คำเตือน
        print("\n" + "="*70)
        print("⚠️  หมายเหตุ")
        print("="*70)
        print(f"""
• Cut Length: ทำนายโดย ML
• Volume: คำนวณด้วยสูตร (B × H × Length)
• Steel: ประมาณการ {steel_per_m3} kg/m³ (คานทั่วไป: 100-120 kg/m³)
• Formwork: ทำนายโดย ML

• ควรตรวจสอบกับแบบรายละเอียดก่อนใช้งานจริง
""")
        
        # สรุปสำหรับ copy
        print("\n" + "="*70)
        print("📋 สรุป (สำหรับ copy)")
        print("="*70)
        print(f"""
ขนาดคาน: {b:.3f}m × {h:.3f}m

Input:
- ความยาวเต็ม (Length): {length:.2f} m

Output:
- Cut Length: {cut_length:.2f} m
- Volume (Cut): {volume_cut:.2f} m³
- Volume (Full): {volume_full:.2f} m³
- Steel (Cut): {steel_cut:.2f} kg = {steel_cut/1000:.2f} ตัน
- Steel (Full): {steel_full:.2f} kg = {steel_full/1000:.2f} ตัน
- Formwork: {formwork:.2f} m²

ประหยัด:
- Volume: {volume_diff:.2f} m³ ({(volume_diff/volume_full*100):.1f}%)
- Steel: {steel_diff:.2f} kg ({(steel_diff/steel_full*100):.1f}%)
""")
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n❌ ไม่พบไฟล์โมเดล: {e}")
        print("   กรุณาตรวจสอบว่ามีไฟล์ .pkl ในโฟลเดอร์เดียวกัน")
        print("   ต้องรัน beam_ml.py ก่อนเพื่อเทรนโมเดล")
        return False
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """ฟังก์ชันหลัก"""
    while True:
        # คำนวณ
        success = calculate_beam()
        
        if not success:
            break
        
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