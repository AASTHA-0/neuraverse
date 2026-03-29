# 🧠 NeuraVerse — Brainwave Powered Digital Identity

> An EEG-based biometric authentication system that uses brainwave signals to identify individuals — like a password, but from your mind.

---

## 📌 Overview

NeuraVerse is a hardware + ML project that captures EEG (electroencephalogram) signals from a person's brain and uses machine learning to authenticate their identity. Combined with heart rate monitoring, it also features an **Emergency Mode** that provides limited access to critical information when the user is in a panic state.

This repository contains the complete ML pipeline — from raw EEG signal processing to real-time authentication.

---

## 🎯 Key Features

- 🔐 **Brainwave Authentication** — uses EEG signals as a unique biometric identifier
- 💓 **Heart Rate Integration** — MAX30102 sensor adds physiological context
- 🚨 **Emergency Mode** — detects panic-level heart rate and grants limited access to emergency contacts and medical info
- 📊 **Multi-model Comparison** — SVM, Random Forest, KNN, Gradient Boosting, Logistic Regression, MLP
- 🧹 **Full Signal Processing Pipeline** — bandpass filtering, artifact removal, differential signals
- 📈 **Feature Extraction** — time domain + frequency domain features from 3 differential EEG pairs

---

## 🧠 How It Works

```
User wears EEG headband + wrist sensor
            ↓
Collect 6 EEG channels (Fp1, Fp2, O1, O2, F3, F4)
            ↓
Compute 3 Differential Signals
  Fp1-Fp2 | O1-O2 | F3-F4
            ↓
Bandpass Filter (0.5 - 50 Hz) + Artifact Removal
            ↓
Feature Extraction (24 features per 1s window)
  mean, std, var, skew, kurt, ptp, rms, zcr
            ↓
Random Forest Classifier
            ↓
  + Heart Rate from MAX30102
            ↓
Smart Authentication Decision:
  Normal HR + High EEG confidence  →  ACCESS GRANTED
  Panic HR  + High EEG confidence  →  EMERGENCY MODE
  Low EEG confidence               →  ACCESS DENIED
```

---

## 📁 Project Structure

```
NeuraVerse/
│
├── neuratrack.ipynb          # Main ML notebook (complete pipeline)
├── features_raw.csv          # Raw EEG dataset (32 channels, 8064 samples)
├── live_auth.py              # Live hardware authentication script
│
├── models/
│   ├── neuraverse_model.pkl          # Trained Random Forest model
│   ├── neuraverse_scaler.pkl         # StandardScaler
│   └── neuraverse_label_encoder.pkl  # LabelEncoder
│
└── README.md
```

---

## 📓 Notebook Walkthrough

| Cell | Description |
|------|-------------|
| 1–6  | Install libraries and imports |
| 7–13 | Load dataset, explore, check missing values |
| 14   | Plot raw EEG signals |
| 15–18 | Compute differential signals, plot |
| 19–21 | Bandpass filter + artifact removal |
| 22–23 | Feature extraction (sliding window) |
| 25–28 | Label generation, train/test split, scaling |
| 31–34 | Train 5 ML models, compare accuracy |
| 36–37 | Best model classification report + confusion matrix |
| 38   | Feature importance plot |
| 39   | PCA visualization |
| 40   | Save model |
| 41   | Authentication function |
| 42–45 | Heart rate integration + Emergency Mode |

---

## 🔧 Hardware Used

| Component | Purpose |
|-----------|---------|
| ESP32 | Microcontroller |
| EEG Click Board (ADS1299) | EEG signal capture |
| MAX30102 | Heart rate sensor |
| ECG Electrodes | EEG signal electrodes |
| Silicone wrist strap + Headband | Wearable form factor |

> ⚠️ Hardware integration is in progress. The notebook currently runs on a pre-recorded EEG dataset. Live hardware connection via ESP32 serial is the next step.

---

## 📊 Results

| Model | Accuracy |
|-------|----------|
| **Random Forest** | **69.23%** ✅ |
| SVM | 61.54% |
| MLP | 61.54% |
| Gradient Boosting | 61.54% |
| Logistic Regression | 53.85% |
| KNN | 30.77% |

> Note: Accuracy is based on simulated identity labels from a single-session EEG recording. Real multi-person data will improve accuracy significantly.

---

## 🚨 Emergency Mode Logic

```python
if eeg_confidence >= 0.75 and heart_rate >= 130:
    # EMERGENCY MODE
    # grant limited access to:
    # - emergency contacts
    # - medical information
    # - location sharing
```

---

## ⚙️ Setup & Run

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/NeuraVerse.git
cd NeuraVerse
```

### 2. Install dependencies
```bash
pip install scikit-learn pandas numpy matplotlib seaborn scipy joblib
```

### 3. Run the notebook
Open `neuratrack.ipynb` in Jupyter Notebook and run cells one by one.

### 4. Live hardware (coming soon)
```bash
pip install pyserial
python live_auth.py
```

---

## 🔮 Future Work

- [ ] Connect live ESP32 data stream to ML pipeline
- [ ] Collect real multi-person EEG data for training
- [ ] Improve accuracy with band power features
- [ ] Add blockchain-based NeuroID storage
- [ ] Build mobile app interface
- [ ] Encrypt NeuroID hash for secure storage

---

## 📚 Dataset

- Source: Pre-recorded EEG dataset
- Channels used: Fp1, Fp2, O1, O2, F3, F4 (6 of 32 channels)
- Sampling rate: 256 Hz
- Total samples: 8064 rows
- Differential pairs: Fp1-Fp2, O1-O2, F3-F4

---

## 👩‍💻 Built With

- Python 3
- scikit-learn
- NumPy / Pandas
- SciPy (signal processing)
- Matplotlib / Seaborn
- ESP32 + Arduino IDE (hardware)

---

## 📄 License

This project is for educational and exhibition purposes.

---

> *"Your brain is the most unique password in the world."*
