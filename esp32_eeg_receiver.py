import socket
import json
import sys
import pandas as pd
import numpy as np
import threading
import time
from datetime import datetime
from pathlib import Path
import joblib
from scipy.signal import butter, filtfilt, welch

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000
BUFFER_FILE = "eeg_realtime.csv"
LOG_FILE = "eeg_sensor_log.txt"
WINDOW_SIZE = 256
STEP = 128

# ML Model parameters (must match training)
CHANNELS = ['Fp1', 'Fp2', 'O1']
FS = 256
BANDS = {'delta': (0.5, 4.0), 'theta': (4.0, 8.0), 'alpha': (8.0, 13.0), 'beta': (13.0, 30.0)}

# Try to load trained models
try:
    model = joblib.load('model_person_id.pkl')
    scaler = joblib.load('scaler_person_id.pkl')
    le = joblib.load('label_encoder_person.pkl')
    MODELS_LOADED = True
    print("✓ Models loaded successfully")
except:
    MODELS_LOADED = False
    print("⚠ Models not found - will collect data only (no authentication)")

# ═══════════════════════════════════════════════════════════════════════════
# Data Management
# ═══════════════════════════════════════════════════════════════════════════

class DataCollector:
    def __init__(self, buffer_file=BUFFER_FILE):
        self.buffer_file = buffer_file
        self.data_lock = threading.Lock()
        self.total_samples = 0
        self.start_time = datetime.now()
        
        # Initialize CSV if doesn't exist
        if not Path(buffer_file).exists():
            df_empty = pd.DataFrame(columns=CHANNELS + ['timestamp', 'person'])
            df_empty.to_csv(buffer_file, index=False)
            self.log(f"Created {buffer_file}")
    
    def add_samples(self, samples_list):
        """Add samples from ESP and save to CSV"""
        with self.data_lock:
            try:
                # Convert to DataFrame
                df_new = pd.DataFrame(samples_list)
                
                # Read existing data
                if Path(self.buffer_file).exists() and Path(self.buffer_file).stat().st_size > 0:
                    df_existing = pd.read_csv(self.buffer_file)
                    df = pd.concat([df_existing, df_new], ignore_index=True)
                else:
                    df = df_new
                
                # Add placeholder person column if missing
                if 'person' not in df.columns:
                    df['person'] = 'unknown'
                
                # Save
                df.to_csv(self.buffer_file, index=False)
                self.total_samples += len(samples_list)
                
                self.log(f"Added {len(samples_list)} samples (Total: {self.total_samples})")
                
                # Real-time authentication if models loaded
                if MODELS_LOADED and len(df) >= WINDOW_SIZE:
                    self.authenticate_last_window(df)
                
            except Exception as e:
                self.log(f"ERROR adding samples: {e}")
    
    def authenticate_last_window(self, df):
        """Try to authenticate person from latest window"""
        try:
            # Get last window
            window_df = df[CHANNELS].iloc[-WINDOW_SIZE:].copy()
            
            if len(window_df) < WINDOW_SIZE:
                return
            
            # Extract features
            features = extract_features(window_df)
            vec_df = pd.DataFrame([features])
            vec_sc = scaler.transform(vec_df)
            
            # Predict
            proba = model.predict_proba(vec_sc)[0]
            pred_idx = np.argmax(proba)
            confidence = proba.max()
            person = le.inverse_transform([pred_idx])[0]
            
            status = "✓" if confidence >= 0.60 else "✗"
            self.log(f"{status} Person: {person} | Confidence: {confidence*100:.1f}%")
        
        except Exception as e:
            pass  # Silent fail for real-time
    
    def log(self, message):
        """Print and save log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(LOG_FILE, 'a') as f:
            f.write(log_msg + "\n")

# ═══════════════════════════════════════════════════════════════════════════
# Feature Extraction
# ═══════════════════════════════════════════════════════════════════════════

def bandpass_filter(data, lowcut=0.5, highcut=50.0, fs=FS, order=4):
    """Apply zero-phase bandpass filter"""
    data = np.array(data, dtype=np.float64)
    if len(data) <= 3 * order * 2:
        return data
    nyq = 0.5 * fs
    b, a = butter(order, [lowcut/nyq, highcut/nyq], btype='band')
    return filtfilt(b, a, data)

def extract_features(window_df):
    """Extract 30 features per window"""
    features = {}
    for ch in CHANNELS:
        sig = window_df[ch].values.astype(np.float64)
        
        # Time-domain
        features[f"{ch}_mean"] = np.mean(sig)
        features[f"{ch}_std"] = np.std(sig)
        features[f"{ch}_var"] = np.var(sig)
        features[f"{ch}_rms"] = np.sqrt(np.mean(sig ** 2))
        features[f"{ch}_ptp"] = np.max(sig) - np.min(sig)
        features[f"{ch}_zcr"] = np.sum(np.diff(np.sign(sig)) != 0) / len(sig)
        
        # Frequency-domain
        f, Pxx = welch(sig, fs=FS, nperseg=min(len(sig), 128))
        for band, (lo, hi) in BANDS.items():
            idx = (f >= lo) & (f < hi)
            features[f"{ch}_{band}_power"] = np.sum(Pxx[idx])
    
    return features

# ═══════════════════════════════════════════════════════════════════════════
# Server
# ═══════════════════════════════════════════════════════════════════════════

def handle_client(sock, addr, collector):
    """Handle incoming client connections"""
    print(f"🟢 Client connected: {addr}")
    sock.settimeout(2.0)
    buffer = b''
    msg_count = 0
    
    try:
        while True:
            try:
                # Receive chunk
                chunk = sock.recv(8192)
                if not chunk:
                    print(f"  No more data from {addr}")
                    break
                
                buffer += chunk
                print(f"  Received {len(chunk)} bytes, buffer now {len(buffer)} bytes")
                
                # Process complete messages (one per line)
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    line_str = line.decode('utf-8', errors='ignore').strip()
                    
                    if not line_str or line_str == '':
                        continue
                    
                    try:
                        # Try to parse as JSON (assuming each line is a JSON object or array)
                        samples = json.loads(line_str)
                        msg_count += 1
                        print(f"  [{msg_count}] Parsed JSON: {len(samples) if isinstance(samples, list) else 1} samples")
                        
                        # If it's a single object, wrap in list
                        if isinstance(samples, dict):
                            samples = [samples]
                        
                        if isinstance(samples, list) and len(samples) > 0:
                            collector.add_samples(samples)
                        else:
                            print(f"  Invalid sample format")
                    
                    except json.JSONDecodeError as e:
                        # Might be truncated, try accumulating more data
                        print(f"  JSON error, re-buffering: {str(e)[:30]}")
                        buffer = line + b'\n' + buffer
                        break
                    except Exception as e:
                        print(f"  Exception: {str(e)[:40]}")
                        collector.log(f"Error: {str(e)[:40]}")
            
            except socket.timeout:
                #print("  Timeout waiting for data")
                continue
            except Exception as e:
                print(f"  Connection exception: {e}")
                break
    
    except Exception as e:
        print(f"  Outer exception: {e}")
        collector.log(f"Connection error: {e}")
    finally:
        print(f"  Closing connection from {addr} (received {msg_count} messages)")
        sock.close()
        print(f"🔴 Client disconnected: {addr}")

def start_server(port=SERVER_PORT):
    """Start receiving server"""
    collector = DataCollector()
    
    print("\n╔═══════════════════════════════════════════╗")
    print("║   EEG Data Receiver Server (Python)       ║")
    print("╚═══════════════════════════════════════════╝")
    print(f"\n🚀 Listening on {SERVER_HOST}:{port}")
    print(f"   Data file: {BUFFER_FILE}")
    print(f"   Log file: {LOG_FILE}")
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((SERVER_HOST, port))
    server_sock.listen(1)
    
    collector.log("="*50)
    collector.log("SERVER STARTED")
    collector.log("="*50)
    
    try:
        while True:
            sock, addr = server_sock.accept()
            # Handle each client in a thread
            client_thread = threading.Thread(
                target=handle_client, 
                args=(sock, addr, collector)
            )
            client_thread.daemon = True
            client_thread.start()
    
    except KeyboardInterrupt:
        collector.log("Shutting down...")
    finally:
        server_sock.close()

if __name__ == "__main__":
    start_server()
