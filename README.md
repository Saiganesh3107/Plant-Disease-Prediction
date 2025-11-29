# 🌿 Project Description

**This project is a full-stack Plant Disease Detection Web Application powered by a Vision Transformer (ViT) deep learning model.
Users can upload a leaf image and instantly receive:**

- 🌱 Leaf Type

- 🍂 Disease Name

- 📊 Prediction Confidence

- 🔥 Severity Estimation

- 🎨 Saliency Map 

- 📄 Downloadable PDF Report

**A complete authentication system and prediction history dashboard make this suitable for farmers, students, research organizations, and real-world agricultural applications.**

## 📦 Dataset

**The model is trained on a structured image dataset with class folders formatted as:**
```
Dataset/
│
├── train/
│   ├── LeafName___DiseaseName/
│   └── ...
├── val/
│   ├── LeafName___DiseaseName/
│   └── ...
└── test/
    ├── LeafName___DiseaseName/
    └── ...
```

## 📁 Project Structure
```
plant-disease-prediction/
│
├── app.py                     
├── model_loader.py            
├── db.py                      
├── classes.json                # Class index → label mapping (Leaf___Disease)
│
├── templates/        
│   ├── plant_disease_ui.html   
│   ├── history.html            
│   ├── login.html              
│   ├── register.html           
│
├── static/
│   ├── uploads/               
│   ├── saliency/                                
│
├── models/
│   └── best_vit.pth            
│
├── schema.sql                  
├── requirements.txt           
├── README.md                 
└── .gitignore  

```


## 🌐 About the Web Application

**The system is a Flask-based full-stack web application with the following features:**

### ✔ User Authentication

- Register

- Login

- Logout

- Session-based user tracking

### ✔ Leaf Image Upload Interface

- Drag-and-drop upload

- Live preview

- Real-time prediction using ViT model

### ✔ Prediction Display

**After uploading, the app shows:**

- Leaf type

- Disease name

- Confidence (%)

- Severity (%)

- Saliency heatmap

### ✔ PDF Report Generator

**Generates a detailed PDF that includes:**

- Uploaded leaf image

- Saliency heatmap

- Prediction summary

- Confidence & severity

- Timestamp

### ✔ Prediction History Dashboard

**Shows all previous predictions for the logged-in user:**

- Images

- Predictions

- Confidence

- Severity

- Date/time

**The UI is lightweight, fast, and built using HTML/CSS + JavaScript.**

## 🧠 Vision Transformer Model (ViT)

**Model used:**
```
vit_base_patch16_224_in21k
```

**Fine-tuned for multi-class leaf disease classification.**

### Output Format
```
{
  "leaf": "Tomato",
  "disease": "Late_blight",
  "confidence": 93.5,
  "severity": 21.3,
  "saliency": "/static/saliency/img123.png"
}
```

## 🏃 How to Run This Project

**Follow these steps to run the project locally.**

### 1️⃣ Install Dependencies

**Create a virtual environment:**
```
python -m venv .venv
source .venv/bin/activate      
```

**Install packages:**
```
pip install -r requirements.txt
pip install reportlab
```

### 2️⃣ Add your trained model

**Place your .pth model inside:**
```
models/best_vit.pth
```

### 3️⃣ Setup MySQL Database

**Run:**
```
mysql -u root -p < schema.sql
```

**Or create manually:**
```
CREATE DATABASE plant_disease_db;
USE plant_disease_db;
```

**Ensure users1 and predictions tables exist (from schema.sql).**

#### Update DB credentials in db.py:
```
host="127.0.0.1"
user="root"
password="YOUR_PASSWORD"
database="plant_disease_db"
```

### 4️⃣ Start the Application

**Run:**
```
python app.py

```

**Open your browser:**
```
http://127.0.0.1:5000
```

## Login Page:
<img width="637" height="576" alt="Screenshot 2025-11-29 144746" src="https://github.com/user-attachments/assets/80e7bd7a-2b6c-4be6-a935-52e2b6434dcb" />

## Register Page:
<img width="695" height="837" alt="Screenshot 2025-11-29 144803" src="https://github.com/user-attachments/assets/012f8784-b5ce-4d0a-8e44-f1ddc111758d" />

## Main Page:
<img width="1623" height="821" alt="Screenshot 2025-11-29 144842" src="https://github.com/user-attachments/assets/aed704fd-e1a2-43bb-a919-c50029775de4" />

## Output Page:
<img width="1147" height="860" alt="Screenshot 2025-11-29 144932" src="https://github.com/user-attachments/assets/b9a43267-87bf-4f44-8749-bc62875cd5da" />

## History Page:
<img width="1525" height="847" alt="Screenshot 2025-11-29 144959" src="https://github.com/user-attachments/assets/4c049f40-cc6b-443a-885c-5faa7538b438" />


## 🌾 Use Cases

- Farmer disease identification

- Agriculture field monitoring

- Research in plant pathology

- AI-based precision farming

- Mobile/web disease diagnosis systems

- College/University deep-learning projects

## 📄 Summary

**This project combines:**

- Deep learning (Vision Transformers)

- Web engineering (Flask)

- Explainability (Saliency Maps)

- Database systems (MySQL)
