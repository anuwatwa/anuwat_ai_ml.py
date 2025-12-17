# 🏗️ Construction Quantity Estimation ML Models

Machine Learning models สำหรับประมาณการปริมาณงานก่อสร้าง (Volume, Formwork, Steel) สำหรับงานโครงสร้างคอนกรีต

## 📋 สารบัญ

- [ภาพรวม](#ภาพรวม)
- [โมเดลที่มี](#โมเดลที่มี)
- [ติดตั้ง](#ติดตั้ง)
- [การใช้งาน](#การใช้งาน)
- [ความแม่นยำ](#ความแม่นยำ)
- [โครงสร้างโปรเจกต์](#โครงสร้างโปรเจกต์)
- [สัญญาอนุญาต](#สัญญาอนุญาต)

---

## ภาพรวม

โปรเจกต์นี้ใช้ Machine Learning เพื่อทำนายปริมาณงานก่อสร้างจากขนาดโครงสร้าง รองรับ:

- ✅ **Foundation** (ฐานราก) - ความแม่นยำ ~99%
- ✅ **Column** (เสา) - ความแม่นยำ ~83%
- ✅ **Slab** (พื้น) - RC + Post-Tension - ความแม่นยำ ~80-98%
- ✅ **Beam** (คาน) - ความแม่นยำ ~73-91%

---

## โมเดลที่มี

### 1. Foundation (ฐานราก)

| Input | Output | R² Score |
|-------|--------|----------|
| Width, Length, Thickness, Area, Perimeter, Count | Volume | 99.98% |
| | Formwork | 99.42% |

**ไฟล์โมเดล:**
- `foundation_volume_model.pkl`
- `foundation_formwork_model.pkl`

---

### 2. Column (เสา)

| Input | Output | R² Score |
|-------|--------|----------|
| Width, Depth, Length, Perimeter, Area Column | Volume | 83.12% |
| | Formwork | 83.14% |

**ไฟล์โมเดล:**
- `column_volume_model.pkl`
- `column_formwork_model.pkl`

**หมายเหตุ:** Steel ใช้สูตรคำนวณ (110 kg/m³) เพราะโมเดล ML ไม่แม่นพอ

---

### 3. Slab (พื้น) - RC + Post-Tension

| Input | Output | R² Score |
|-------|--------|----------|
| Slab_Type (0=RC, 1=PT), Thickness, Perimeter, Area | Volume | 79.71% |
| | Formwork (Side) | 92.48% |
| | Formwork (ALL) | 97.56% |

**ไฟล์โมเดล:**
- `slab_volume_model.pkl`
- `slab_formwork_side_model.pkl`
- `slab_formwork_all_model.pkl`

**หมายเหตุ:** 
- Steel ใช้สูตรคำนวณ (RC: 90 kg/m³, PT: 60 kg/m³)
- สำหรับ Slab แนะนำใช้ `calculate_slab_formula.py` (สูตรคำนวณ) แทน ML

---

### 4. Beam (คาน)

| Input | Output | R² Score |
|-------|--------|----------|
| B, H, Length | Cut Length | (ยังไม่ทดสอบ) |
| B, H, Cut Length, Length | Volume | 73.13% |
| | Formwork | 90.90% |

**ไฟล์โมเดล:**
- `beam_cut_length_model.pkl`
- `beam_volume_model.pkl`
- `beam_formwork_model.pkl`

**หมายเหตุ:** Steel ใช้สูตรคำนวณ (110 kg/m³)

---

## ติดตั้ง

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/construction-ml-models.git
cd construction-ml-models
```

### 2. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

**หรือติดตั้งทีละตัว:**
```bash
pip install pandas openpyxl scikit-learn numpy matplotlib seaborn
```

### 3. ตรวจสอบโมเดล

โมเดลทั้งหมดอยู่ในโฟลเดอร์ `models/`

---

## การใช้งาน

### วิธีที่ 1: ใช้โมเดลที่เทรนแล้ว (แนะนำ)

#### Foundation
```python
from training.foundation_ml import load_and_predict

data = {
    'Width': 1.20,
    'Length': 1.20,
    'Thickness': 0.80,
    'Area': 1.44,
    'Perimeter': 4.8,
    'Count': 9
}

volume = load_and_predict('models/foundation_volume_model.pkl', data)
formwork = load_and_predict('models/foundation_formwork_model.pkl', data)

print(f"Volume: {volume:.2f} m³")
print(f"Formwork: {formwork:.2f} m²")
```

#### Column
```python
from training.column_ml import load_and_predict

data = {
    'Width': 1.2,
    'Depth': 0.3,
    'Length': 2.8,
    'Perimeter': 3.0,
    'Area Column': 0.36
}

volume = load_and_predict('models/column_volume_model.pkl', data)
formwork = load_and_predict('models/column_formwork_model.pkl', data)
```

#### Beam
```python
from training.beam_ml import load_and_predict

# ใส่ B, H, Length
data_input = {
    'B': 0.20,
    'H': 0.60,
    'Length': 8.25
}

# ทำนาย Cut Length
cut_length = load_and_predict('models/beam_cut_length_model.pkl', data_input)

# คำนวณ Volume
volume_cut = data_input['B'] * data_input['H'] * cut_length
volume_full = data_input['B'] * data_input['H'] * data_input['Length']

# คำนวณ Steel
steel_cut = volume_cut * 110  # kg/m³
steel_full = volume_full * 110

# ทำนาย Formwork
data_with_cut = {
    'B': 0.20,
    'H': 0.60,
    'Cut Length': cut_length,
    'Length': 8.25
}
formwork = load_and_predict('models/beam_formwork_model.pkl', data_with_cut)
```

---

### วิธีที่ 2: ใช้ไฟล์ทดสอบ Interactive

```bash
# Foundation
python testing/test_foundation.py

# Column
python testing/test_column.py

# Slab (แนะนำใช้สูตร)
python testing/calculate_slab_formula.py

# Beam
python testing/calculate_beam.py
```

---

### วิธีที่ 3: เทรนโมเดลใหม่

ถ้าคุณมีข้อมูลใหม่:

```bash
# วางไฟล์ข้อมูลใน data/
python training/foundation_ml.py
python training/column_ml.py
python training/slab_ml.py
python training/beam_ml.py
```

โมเดลใหม่จะถูกบันทึกในโฟลเดอร์ `models/`

---

## ความแม่นยำ

### สรุปความแม่นยำแต่ละโมเดล

| Element | Target | Algorithm | R² Score | Status |
|---------|--------|-----------|----------|--------|
| **Foundation** | Volume | Gradient Boosting | 99.98% | ✅ ดีมาก |
| | Formwork | Linear Regression | 99.42% | ✅ ดีมาก |
| **Column** | Volume | Random Forest | 83.12% | ✅ ดี |
| | Formwork | Random Forest | 83.14% | ✅ ดี |
| **Slab** | Volume | Gradient Boosting | 79.71% | ✅ ดี |
| | Formwork (Side) | Linear Regression | 92.48% | ✅ ดีมาก |
| | Formwork (ALL) | Linear Regression | 97.56% | ✅ ดีมาก |
| **Beam** | Volume | Linear Regression | 73.13% | ⚠️ พอใช้ |
| | Formwork | Random Forest | 90.90% | ✅ ดีมาก |
| **Steel (ทั้งหมด)** | - | Formula | - | ⚠️ ใช้สูตร |

### หมายเหตุ:
- ✅ **R² > 90%** = ดีมาก แนะนำใช้
- ✅ **R² 80-90%** = ดี ใช้ได้
- ⚠️ **R² 70-80%** = พอใช้ ควรระวัง
- ❌ **R² < 70% หรือติดลบ** = ไม่แนะนำ ใช้สูตรแทน

---

## โครงสร้างโปรเจกต์

```
construction-ml-models/
├── README.md
├── requirements.txt
├── .gitignore
│
├── models/              # โมเดลที่เทรนแล้ว (.pkl)
│
├── training/            # โค้ดเทรนโมเดล
│   ├── foundation_ml.py
│   ├── column_ml.py
│   ├── slab_ml.py
│   └── beam_ml.py
│
├── testing/             # โค้ดทดสอบโมเดล
│   ├── test_foundation.py
│   ├── test_column.py
│   ├── calculate_slab_formula.py
│   └── calculate_beam.py
│
├── data/                # ข้อมูลสำหรับเทรน (Excel/CSV)
│
└── docs/                # เอกสารแนะนำการใช้งาน
```

---

## คำเตือน

⚠️ **สำคัญ:**
- โมเดล ML เป็นเครื่องมือช่วยประมาณการ **ไม่ใช่การคำนวณแบบแม่นยำ 100%**
- **ควรตรวจสอบกับแบบรายละเอียด** และวิศวกรโครงสร้างก่อนใช้งานจริง
- Steel ใช้สูตรประมาณการ (ค่าจริงขึ้นอยู่กับการออกแบบ)

---

## เทคโนโลยีที่ใช้

- **Python 3.13**
- **scikit-learn** - Machine Learning
- **pandas** - Data Processing
- **openpyxl** - Excel Support
- **numpy** - Numerical Computing

---

## สัญญาอนุญาต

MIT License - ใช้งานได้อย่างอิสระ

---

## ผู้พัฒนา

Developed by [Your Name]

---

## การสนับสนุน

หากพบปัญหาหรือต้องการคำแนะนำ:
- 📧 Email: your.email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/YOUR_USERNAME/construction-ml-models/issues)

---

## Changelog

### v1.0.0 (2025-01-XX)
- ✅ Foundation Model (Volume, Formwork)
- ✅ Column Model (Volume, Formwork)
- ✅ Slab Model (Volume, Formwork Side/ALL) - RC + PT
- ✅ Beam Model (Cut Length, Volume, Formwork)
- ✅ Interactive Testing Scripts
- ✅ Formula-based Calculators

---

## Roadmap

- [ ] ปรับปรุงโมเดล Steel ให้แม่นยำขึ้น
- [ ] เพิ่มโมเดล Wall (ผนัง)
- [ ] สร้าง Web Interface
- [ ] เพิ่มข้อมูลเทรนให้มากขึ้น
- [ ] API Endpoint สำหรับใช้งานผ่าน REST API

---

Made with ❤️ for Construction Engineering
