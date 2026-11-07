# NeuraVerse: EEG-Based Biometric Authentication (Prototype)

NeuraVerse explores whether a person can be identified from their brainwave (EEG) signals, like a password that comes from the user rather than something they remember.

This repository contains two parts:

1. **ML pipeline (notebook):** signal filtering, feature extraction, and a comparison of several classifiers on a pre-recorded EEG dataset.
2. **ESP32 acquisition prototype (scripts):** an ESP32 that streams 3-channel signals over WiFi to a PC, plus scripts to label and retrain.

> **Project status: prototype.** The ML results below come from a pre-recorded dataset with simulated identity labels, not from real multi-person recordings made with this hardware. See [Limitations](#limitations).

---

## How it works

```
EEG source (pre-recorded dataset / ESP32 stream)
        |
Differential signals (Fp1-Fp2, O1-O2, F3-F4)
        |
Bandpass filter (0.5 - 50 Hz) + artifact removal
        |
Sliding 1-second windows -> features per window
  (mean, std, var, skew, kurtosis, peak-to-peak, RMS, zero-crossing rate)
        |
Classifier (Random Forest selected as best of 6)
        |
Confidence-based decision: ACCESS GRANTED / ACCESS DENIED
```

**Heart-rate fusion and Emergency Mode** (design concept): combine EEG confidence with heart rate so that a high EEG confidence plus a panic-level heart rate triggers a limited-access emergency mode. Status: logic prototyped in the final notebook cells with simulated heart-rate input; MAX30102 sensor integration is planned, not done.

---

## Repository contents

| File | Purpose |
| --- | --- |
| `neuratrack (2).ipynb` | Main ML notebook: load data, filter, extract features, train and compare models, evaluate |
| `features_raw.csv` | Pre-recorded EEG dataset used by the notebook (see [Dataset](#dataset)) |
| `esp32_eeg_sender.py` | Runs on ESP32 (MicroPython): samples 3 channels and streams them over WiFi |
| `esp32_eeg_receiver.py` | Runs on PC: receives the stream and saves it to `eeg_realtime.csv` |
| `label_and_append.py` | Labels a recorded session with a person name and appends it to a labeled CSV |
| `retrain_model.py` | Executes a training notebook headlessly to regenerate model files |
| `collect_label_retrain.py` | Runs labeling and retraining in one step |
| `WORKFLOW.txt` | Order in which to run the scripts |

---

## Models and results

Evaluated on the pre-recorded dataset:

| Model | Accuracy |
| --- | --- |
| **Random Forest** | **69.23%** |
| SVM | 61.54% |
| MLP | 61.54% |
| Gradient Boosting | 61.54% |
| Logistic Regression | 53.85% |
| KNN | 30.77% |

**Read these numbers with care.** Every accuracy above is a multiple of 1/13, which means the test set contains only about 13 samples, so a single prediction changes the score by roughly 8 points. The identity labels are also simulated from a single recording session. These results show that the pipeline runs end to end; they are **not** evidence of real-world identification accuracy.

---

## ESP32 prototype

- **Board:** ESP32 running MicroPython
- **Channels:** 3 (Fp1, Fp2, O1), read through the ESP32 ADC pins (GPIO 36, 35, 34)
- **Sampling rate:** 256 Hz, sent in batches of 256 samples as JSON over a TCP socket (port 5000)
- **PC side:** `esp32_eeg_receiver.py` listens and writes incoming samples to CSV

### Setup

1. Open `esp32_eeg_sender.py` and set your own `WIFI_SSID`, `WIFI_PASSWORD`, and `SERVER_IP` (your PC's IP). Never commit real credentials.
2. Upload `esp32_eeg_sender.py` to the ESP32 (Thonny or `ampy`).
3. On the PC run `python esp32_eeg_receiver.py`, then start the sender on the ESP32.
4. After a session, run `python label_and_append.py <person_name>` to label the data.

Hardware notes: the current prototype reads the ESP32 ADC directly. Clean EEG acquisition needs a proper analog front-end (for example an ADS1299-based board with correct electrodes and amplification), which is the planned hardware upgrade. Data recorded with the bare ADC should be treated as a connectivity and pipeline test, not as clean EEG.

---

## Dataset

- **Source:** pre-recorded EEG
- **Size:** 8,064 samples, 32 channels; 6 channels used (Fp1, Fp2, O1, O2, F3, F4)
- **Differential pairs:** Fp1-Fp2, O1-O2, F3-F4

---

## Limitations

- Results use pre-recorded data with **simulated identity labels** from a single session. Windows from the same recording can leak between train and test.
- The test set is very small (about 13 samples), so model rankings are not reliable.
- The notebook uses a public dataset with 6 channels; the ESP32 prototype streams 3 channels and has not been used to train or evaluate the published models.
- `retrain_model.py` runs a notebook that reads the ESP32-labeled CSV; this retraining path is not yet connected to the dataset notebook in this repo.
- No evaluation yet on real users, across sessions or across days, and no measurement of false accept / false reject rates (FAR, FRR, EER).
- Impostor handling, spoofing and replay attacks, and EEG template ageing are not addressed.
- Heart-rate fusion and Emergency Mode are a design prototype; the "panic grants access" idea has security trade-offs that need careful review before any real use.

## Next steps

- [ ] Collect real multi-person EEG with a proper analog front-end (ADS1299), across multiple sessions
- [ ] Evaluate with session-wise (and subject-wise) splits and report FAR, FRR, EER
- [ ] Add band-power features (Welch PSD) and compare feature sets
- [ ] Connect the ESP32 stream to live prediction
- [ ] Integrate the MAX30102 heart-rate sensor
- [ ] Review the security of the emergency mode and add impostor / spoofing tests

---

## Tech stack

Python 3, scikit-learn, NumPy, pandas, SciPy, Matplotlib, Seaborn, MicroPython on ESP32.

## License

For educational and exhibition purposes.
