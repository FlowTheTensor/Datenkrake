import time
import threading
import numpy as np
import subprocess
import json
import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request
from datetime import datetime
import re

# Konfiguration
SAMPLE_RATE = 16000  # Webcam-Mikrofone unterstützen oft nur 16kHz
CHUNK_SIZE = 2048    # Samples pro FFT (bessere Frequenzauflösung)
MAX_FREQ = 5000      # Hz

# MQTT Konfiguration
MQTT_BROKER = '172.29.0.67'#"datenkrake.local"  # Alternativ: IP-Adresse falls mDNS nicht funktioniert
MQTT_PORT = 1883
MQTT_TOPIC = "audio/spectrum"

# MySQL Datenbank Konfiguration
DB_HOST = '172.29.0.67'#"datenkrake.local"
DB_USER = "sensor"
DB_PASSWORD = "changeMeSensor"
DB_NAME = "telemetry"

app = Flask(__name__)

# Spektrum-Daten
spectrum_data = {"freqs": [], "fft_db": [], "peak_freq": 0, "peak_db": 0, "sample_rate": SAMPLE_RATE}
data_lock = threading.Lock()
audio_running = False

# Aufnahme-Status
recording = False
current_label = "gut"  # "gut" oder "schlecht"
record_count = 0

# MQTT Client
mqtt_client = None
mqtt_send_count = {"gut": 0, "schlecht": 0}  # Zähler für gesendete MQTT Nachrichten

def resolve_hostname(hostname):
    """Versucht Hostname aufzulösen, mit Fallback auf alternative Namen"""
    import socket
    
    # Liste von möglichen Hostnamen/IPs zum Ausprobieren
    alternatives = [
        hostname,
        hostname.replace('.local', ''),  # Ohne .local
        f"{hostname.replace('.local', '')}.lan",  # Mit .lan
    ]
    
    for host in alternatives:
        try:
            # Versuche IPv4 zuerst
            socket.gethostbyname(host)
            print(f"Hostname aufgelöst: {host}")
            return host
        except socket.gaierror:
            continue
    
    print(f"Warnung: Konnte {hostname} nicht auflösen")
    return hostname  # Gib Original zurück, vielleicht klappt es später

def setup_mqtt():
    """Initialisiert MQTT Client"""
    global mqtt_client
    try:
        broker = resolve_hostname(MQTT_BROKER)
        mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        mqtt_client.connect(broker, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print(f"MQTT verbunden mit {broker}:{MQTT_PORT}")
        return True
    except Exception as e:
        print(f"MQTT Fehler (wird ohne MQTT fortgesetzt): {e}")
        return False

def publish_mqtt(data):
    """Sendet Daten über MQTT"""
    global mqtt_send_count
    if mqtt_client:
        try:
            mqtt_client.publish(MQTT_TOPIC, json.dumps(data))
            # Zähler erhöhen
            label = data.get('label', 'gut')
            mqtt_send_count[label] = mqtt_send_count.get(label, 0) + 1
            return True
        except:
            pass
    return False

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Audio-Spektrum Sammler</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
    <style>
        body { font-family: Arial; background: #fff; color: #333; margin: 20px; }
        h1 { color: #8b1a1a; margin-left: 20px; }
        
        .header { display: flex; align-items: center; margin-bottom: 20px; }
        .logo { font-family: 'Times New Roman', serif; font-size: 28px; font-weight: normal; color: #333; letter-spacing: 1px; }
        .logo .red-dot { color: #c00; }
        .logo-underline { display: inline-block; border-bottom: 2px solid #333; padding-bottom: 2px; }
        .logo-underline-red { display: inline-block; border-bottom: 2px solid #c00; padding-bottom: 2px; }
        
        .tabs { display: flex; gap: 5px; margin-bottom: 20px; }
        .tab-btn { padding: 12px 30px; font-size: 16px; border: none; border-radius: 8px 8px 0 0; cursor: pointer; background: #f0f0f0; color: #666; }
        .tab-btn.active { background: #8b1a1a; color: #fff; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .main-layout { display: flex; gap: 15px; }
        .main-content { flex: 1; }
        .info { background: #f8f8f8; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: flex; gap: 30px; flex-wrap: wrap; align-items: center; border: 1px solid #ddd; }
        .peak { color: #8b1a1a; font-size: 24px; font-weight: bold; }
        .label { color: #666; }
        .status { color: #c00; }
        #chart-box, #chart-box-inference { background: #f8f8f8; padding: 15px; border-radius: 8px; margin-bottom: 20px; height: 300px; border: 1px solid #ddd; }
        
        .controls { background: #f8f8f8; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #ddd; }
        .controls h2 { color: #8b1a1a; margin-top: 0; }
        
        .label-buttons { display: flex; gap: 15px; margin-bottom: 20px; }
        .label-btn { padding: 15px 40px; font-size: 18px; border: none; border-radius: 8px; cursor: pointer; transition: all 0.3s; }
        .label-btn.gut { background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
        .label-btn.gut.active { background: #28a745; color: #fff; box-shadow: 0 0 10px rgba(40,167,69,0.5); }
        .label-btn.schlecht { background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
        .label-btn.schlecht.active { background: #dc3545; color: #fff; box-shadow: 0 0 10px rgba(220,53,69,0.5); }
        
        .record-btn { padding: 15px 40px; font-size: 18px; border: none; border-radius: 8px; cursor: pointer; margin-right: 15px; }
        .record-btn.start { background: #8b1a1a; color: #fff; }
        .record-btn.stop { background: #dc3545; color: #fff; }
        
        .stats { background: #f8f8f8; padding: 10px; border-radius: 8px; width: 120px; text-align: center; border: 1px solid #ddd; }
        .stats h4 { color: #8b1a1a; margin: 0 0 10px 0; font-size: 11px; }
        .stat-row { display: flex; justify-content: space-between; margin: 5px 0; font-size: 12px; }
        .stat-value { font-weight: bold; }
        .stat-gut { color: #28a745; }
        .stat-schlecht { color: #dc3545; }
        .stat-total { color: #8b1a1a; }
        
        .prediction-box { background: #f8f8f8; padding: 30px; border-radius: 8px; text-align: center; margin-bottom: 20px; border: 1px solid #ddd; }
        .prediction-result { font-size: 48px; font-weight: bold; margin: 20px 0; }
        .prediction-result.gut { color: #28a745; }
        .prediction-result.schlecht { color: #dc3545; }
        .prediction-result.unknown { color: #999; }
        .confidence { font-size: 18px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <span class="logo-underline">jakob</span>-<span class="logo-underline-red">pr<span class="red-dot">e</span>h</span>-<span class="logo-underline">schule</span><span class="red-dot">!</span>
        </div>
        <h1>Audio-Spektrum Sammler für KI-Training</h1>
    </div>
    
    <div class="tabs">
        <button class="tab-btn active" onclick="showTab('collect')">Daten sammeln</button>
        <button class="tab-btn" onclick="showTab('train')">Modell trainieren</button>
        <button class="tab-btn" onclick="showTab('inference')">Modell anwenden</button>
    </div>
    
    <!-- Tab 1: Daten sammeln -->
    <div id="tab-collect" class="tab-content active">
        <div class="main-layout">
            <div class="main-content">
                <div class="controls">
                    <h2>Daten-Aufnahme</h2>
                    
                    <p>1. Wähle den Zustand:</p>
                    <div class="label-buttons">
                        <button class="label-btn gut active" onclick="setLabel('gut')">✓ Guter Zustand</button>
                        <button class="label-btn schlecht" onclick="setLabel('schlecht')">✗ Schlechter Zustand</button>
                    </div>
                    
                    <p>2. Starte die Aufnahme:</p>
                    <button id="recordBtn" class="record-btn start" onclick="toggleRecording()">▶ Aufnahme starten</button>
                    <span id="recordStatus">Bereit</span>
                </div>
                
                <div class="info">
                    <div>Peak: <span class="peak" id="peak">-- Hz</span></div>
                    <div>Magnitude: <span class="peak" id="db">-- dB</span></div>
                    <div><span class="label">Sample-Rate:</span> <span id="rate">--</span> Hz</div>
                    <div><span class="label">Status:</span> <span id="status" class="status">Warte auf Audio...</span></div>
                </div>
                
                <div id="chart-box"><canvas id="chart"></canvas></div>
            </div>
            
            <div class="stats">
                <h4>MQTT gesendet</h4>
                <div class="stat-row"><span>Gut:</span><span class="stat-value stat-gut" id="statGut">0</span></div>
                <div class="stat-row"><span>Schlecht:</span><span class="stat-value stat-schlecht" id="statSchlecht">0</span></div>
                <div class="stat-row"><span>Gesamt:</span><span class="stat-value stat-total" id="statTotal">0</span></div>
            </div>
        </div>
    </div>
    
    <!-- Tab 2: Modell trainieren -->
    <div id="tab-train" class="tab-content">
        <div class="controls" style="display: flex; gap: 28px; align-items: flex-start;">
            <div style="flex: 1; min-width: 0;">
                <h2>KI-Modell trainieren</h2>
                <p>Lade die gesammelten Daten und trainiere ein neuronales Netz direkt im Browser.</p>

                <div style="margin-bottom: 20px;">
                    <button onclick="loadTrainingData()" class="record-btn start">📥 Daten aus Datenbank laden</button>
                </div>

                <div id="dataStats" style="background: #e9f7ef; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: none;">
                    <strong>Geladene Daten:</strong>
                    <span id="dataStatsGut" style="color: #28a745; margin-left: 20px;">Gut: 0</span>
                    <span id="dataStatsSchlecht" style="color: #dc3545; margin-left: 20px;">Schlecht: 0</span>
                    <span id="dataStatsTotal" style="color: #333; margin-left: 20px;">Gesamt: 0</span>
                </div>

                <div style="margin-bottom: 20px;">
                    <label>Epochen: </label>
                    <input type="number" id="epochs" value="50" min="1" max="500" style="padding: 8px; width: 80px; border: 1px solid #ddd; border-radius: 4px;">
                    <label style="margin-left: 20px;">Learning Rate: </label>
                    <input type="number" id="learningRate" value="0.001" step="0.0001" min="0.0001" max="0.1" style="padding: 8px; width: 100px; border: 1px solid #ddd; border-radius: 4px;">
                    <label style="margin-left: 20px;">Optimierer: </label>
                    <select id="optimizerType" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin-left: 6px;">
                        <option value="adam">Adam</option>
                        <option value="rmsprop">RMSprop</option>
                    </select>
                </div>

                <div style="margin-bottom: 20px; background: #fff; border: 1px solid #ddd; border-radius: 6px; padding: 14px;">
                    <strong style="color: #8b1a1a;">Netzwerk-Architektur</strong>
                    <div style="display: flex; gap: 30px; margin-top: 10px; flex-wrap: wrap;">
                        <div>
                            <label style="font-size: 13px; color: #555;">Schicht 1 – Neuronen:</label><br>
                            <input type="number" id="layer1Units" value="64" min="4" max="512" style="padding: 6px; width: 75px; border: 1px solid #ddd; border-radius: 4px; margin-top: 4px;">
                        </div>
                        <div>
                            <label style="font-size: 13px; color: #555;">Schicht 1 – Dropout:</label><br>
                            <input type="number" id="layer1Dropout" value="0.3" step="0.05" min="0" max="0.9" style="padding: 6px; width: 75px; border: 1px solid #ddd; border-radius: 4px; margin-top: 4px;">
                        </div>
                        <div>
                            <label style="font-size: 13px; color: #555;">Schicht 1 – Aktivierung:</label><br>
                            <select id="layer1Act" style="padding: 6px; border: 1px solid #ddd; border-radius: 4px; margin-top: 4px;">
                                <option value="relu">ReLU</option>
                                <option value="tanh">Tanh</option>
                                <option value="sigmoid">Sigmoid</option>
                                <option value="elu">ELU</option>
                                <option value="selu">SELU</option>
                            </select>
                        </div>
                        <div>
                            <label style="font-size: 13px; color: #555;">Schicht 2 – Neuronen:</label><br>
                            <input type="number" id="layer2Units" value="32" min="4" max="512" style="padding: 6px; width: 75px; border: 1px solid #ddd; border-radius: 4px; margin-top: 4px;">
                        </div>
                        <div>
                            <label style="font-size: 13px; color: #555;">Schicht 2 – Dropout:</label><br>
                            <input type="number" id="layer2Dropout" value="0.2" step="0.05" min="0" max="0.9" style="padding: 6px; width: 75px; border: 1px solid #ddd; border-radius: 4px; margin-top: 4px;">
                        </div>
                        <div>
                            <label style="font-size: 13px; color: #555;">Schicht 2 – Aktivierung:</label><br>
                            <select id="layer2Act" style="padding: 6px; border: 1px solid #ddd; border-radius: 4px; margin-top: 4px;">
                                <option value="relu">ReLU</option>
                                <option value="tanh">Tanh</option>
                                <option value="sigmoid">Sigmoid</option>
                                <option value="elu">ELU</option>
                                <option value="selu">SELU</option>
                            </select>
                        </div>
                    </div>
                </div>

                <button id="trainBtn" onclick="startTraining()" class="record-btn start" disabled>🧠 Training starten</button>
                <span id="trainStatus" style="margin-left: 15px;">Erst Daten laden</span>
            </div>

            <div style="width: 370px; min-width: 220px; flex-shrink: 0;">
                <h3 style="color: #8b1a1a; margin-top: 0;">Loss &amp; Accuracy</h3>
                <div style="position: relative; height: 260px; background: #fff; border: 1px solid #e0e0e0; border-radius: 6px; padding: 6px;">
                    <canvas id="lossChart"></canvas>
                </div>
                <div id="trainingProgressInline" style="display: none; margin-top: 10px;">
                    <div style="background: #e0e0e0; border-radius: 4px; height: 8px;">
                        <div id="progressBar" style="background: #8b1a1a; height: 100%; border-radius: 4px; width: 0%; transition: width 0.3s;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 12px; color: #555;">
                        <span id="progressText">Epoche 0 / 0</span>
                        <span id="lossText">Loss: --</span>
                    </div>
                </div>
            </div>
        </div>

        <div id="trainingComplete" style="background: #d4edda; padding: 20px; border-radius: 8px; margin-top: 20px; border: 1px solid #c3e6cb; display: none;">
            <h3 style="color: #155724; margin-top: 0;">✓ Training abgeschlossen!</h3>
            <p id="finalAccuracy">Finale Genauigkeit: --%</p>
            <p>Das Modell ist jetzt im Tab "Modell anwenden" aktiv.</p>
        </div>

        <div id="nnVizBox" style="background: #f8f8f8; padding: 20px; border-radius: 8px; margin-top: 20px; border: 1px solid #ddd; display: none;">
            <h3 style="color: #8b1a1a; margin-top: 0;">Netzwerk-Architektur</h3>
            <p style="color: #666; font-size: 13px; margin-top: -10px;">Farbe der Eingabe-Neuronen zeigt Gewichts-Wichtigkeit (blau = niedrig, rot = hoch)</p>
            <canvas id="nnViz" style="display: block; width: 100%; height: 320px;"></canvas>
        </div>
    </div>
    
    <!-- Tab 3: Modell anwenden -->
    <div id="tab-inference" class="tab-content">
        <div class="prediction-box">
            <h2>KI-Vorhersage</h2>
            <div id="predictionResult" class="prediction-result unknown">--</div>
            <div class="confidence">Konfidenz: <span id="predictionConf">--</span>%</div>
        </div>
        
        <div class="info">
            <div>Peak: <span class="peak" id="peak2">-- Hz</span></div>
            <div>Magnitude: <span class="peak" id="db2">-- dB</span></div>
            <div><span class="label">Status:</span> <span id="status2" class="status">Warte auf Audio...</span></div>
        </div>
        
        <div id="chart-box-inference"><canvas id="chart2"></canvas></div>
    </div>
    
    <script>
        let currentLabel = 'gut';
        let isRecording = false;
        let currentTab = 'collect';
        let trainingData = [];
        let trainedModelSpectrumLength = 0;
        let lossChart = null;

        function normalizeSpectrum(spec) {
            const mean = spec.reduce((a, b) => a + b, 0) / spec.length;
            const variance = spec.reduce((a, b) => a + (b - mean) ** 2, 0) / spec.length;
            const std = Math.sqrt(variance) || 1;
            return spec.map(v => (v - mean) / std);
        }

        function resizeSpectrum(spec, targetLen) {
            if (spec.length === targetLen) return spec;
            if (spec.length > targetLen) return spec.slice(0, targetLen);
            return spec.concat(new Array(targetLen - spec.length).fill(0));
        }
        let trainedModel = null;
        
        function showTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            const tabIndex = tab === 'collect' ? 1 : (tab === 'train' ? 2 : 3);
            document.querySelector('.tab-btn:nth-child(' + tabIndex + ')').classList.add('active');
            document.getElementById('tab-' + tab).classList.add('active');
            if (tab === 'inference') {
                chart2.resize();
            } else if (tab === 'collect') {
                chart.resize();
            }
        }
        
        async function loadTrainingData() {
            document.getElementById('trainStatus').textContent = 'Lade Daten...';
            document.getElementById('trainStatus').style.color = '#666';
            
            try {
                const response = await fetch('/api/training_data');
                const data = await response.json();
                
                // Fehlerprüfung (auch bei HTTP 500)
                if (!response.ok || data.error || !Array.isArray(data)) {
                    document.getElementById('trainStatus').textContent = 'DB-Fehler: ' + (data.error || 'Unbekannter Fehler');
                    document.getElementById('trainStatus').style.color = '#dc3545';
                    return;
                }
                
                trainingData = data;
                
                const gutCount = data.filter(d => d.label === 'gut').length;
                const schlechtCount = data.filter(d => d.label === 'schlecht').length;
                
                document.getElementById('dataStatsGut').textContent = 'Gut: ' + gutCount;
                document.getElementById('dataStatsSchlecht').textContent = 'Schlecht: ' + schlechtCount;
                document.getElementById('dataStatsTotal').textContent = 'Gesamt: ' + data.length;
                document.getElementById('dataStats').style.display = 'block';
                
                if (data.length > 0) {
                    document.getElementById('trainBtn').disabled = false;
                    document.getElementById('trainStatus').textContent = 'Bereit zum Training';
                    document.getElementById('trainStatus').style.color = '#28a745';
                } else {
                    document.getElementById('trainStatus').textContent = 'Keine Daten gefunden';
                    document.getElementById('trainStatus').style.color = '#dc3545';
                }
            } catch (e) {
                document.getElementById('trainStatus').textContent = 'Fehler: ' + e.message;
                document.getElementById('trainStatus').style.color = '#dc3545';
            }
        }
        
        async function startTraining() {
            if (trainingData.length === 0) return;
            
            const epochs = parseInt(document.getElementById('epochs').value);
            const learningRate = parseFloat(document.getElementById('learningRate').value);
            
            document.getElementById('trainBtn').disabled = true;
            document.getElementById('trainingProgressInline').style.display = 'block';
            document.getElementById('trainingComplete').style.display = 'none';
            document.getElementById('trainStatus').textContent = 'Training läuft...';

            // Loss-Chart initialisieren
            if (lossChart) { lossChart.destroy(); }
            lossChart = new Chart(document.getElementById('lossChart').getContext('2d'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        { label: 'Train Loss', data: [], borderColor: '#8b1a1a', backgroundColor: 'rgba(139,26,26,0.08)', fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2.5, yAxisID: 'y' },
                        { label: 'Accuracy',   data: [], borderColor: '#28a745', backgroundColor: 'rgba(40,167,69,0.08)', fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2.5, yAxisID: 'y1' }
                    ]
                },
                options: {
                    animation: false,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            title: { display: true, text: 'Epoche', font: { size: 12 } },
                            ticks: { maxTicksLimit: 10, font: { size: 11 } },
                            grid: { color: 'rgba(0,0,0,0.06)' }
                        },
                        y: {
                            title: { display: true, text: 'Loss', font: { size: 12 } },
                            suggestedMin: 0,
                            ticks: { font: { size: 11 }, callback: v => v.toFixed(3) },
                            grid: { color: 'rgba(0,0,0,0.06)' }
                        },
                        y1: {
                            position: 'right',
                            title: { display: true, text: 'Accuracy (%)', font: { size: 12 }, color: '#28a745' },
                            min: 0,
                            max: 100,
                            ticks: { font: { size: 11 }, color: '#28a745', callback: v => v + '%' },
                            grid: { drawOnChartArea: false }
                        }
                    },
                    plugins: {
                        legend: { position: 'top', labels: { font: { size: 12 }, boxWidth: 20 } },
                        tooltip: { callbacks: { label: ctx => ctx.datasetIndex === 0 ? ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(4) : ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(1) + '%' } }
                    }
                }
            });
            
            // Daten vorbereiten
            const spectrumLength = trainingData[0].spectrum.length;
            trainedModelSpectrumLength = spectrumLength;
            const xs = tf.tensor2d(trainingData.map(d => normalizeSpectrum(resizeSpectrum(d.spectrum, spectrumLength))));
            const ys = tf.tensor2d(trainingData.map(d => d.label === 'gut' ? [1, 0] : [0, 1]));

            const layer1Units   = Math.max(4, parseInt(document.getElementById('layer1Units').value)   || 64);
            const layer1Dropout = Math.min(0.9, parseFloat(document.getElementById('layer1Dropout').value) || 0.3);
            const layer1Act     = document.getElementById('layer1Act').value || 'relu';
            const layer2Units   = Math.max(4, parseInt(document.getElementById('layer2Units').value)   || 32);
            const layer2Dropout = Math.min(0.9, parseFloat(document.getElementById('layer2Dropout').value) || 0.2);
            const layer2Act     = document.getElementById('layer2Act').value || 'relu';
            const optimizerType = document.getElementById('optimizerType').value;
            
            // Modell erstellen
            const model = tf.sequential();
            model.add(tf.layers.dense({units: layer1Units, activation: layer1Act, inputShape: [spectrumLength]}));
            model.add(tf.layers.dropout({rate: layer1Dropout}));
            model.add(tf.layers.dense({units: layer2Units, activation: layer2Act}));
            model.add(tf.layers.dropout({rate: layer2Dropout}));
            model.add(tf.layers.dense({units: 2, activation: 'softmax'}));
            
            const optimizer = optimizerType === 'rmsprop' ? tf.train.rmsprop(learningRate) : tf.train.adam(learningRate);
            model.compile({
                optimizer: optimizer,
                loss: 'categoricalCrossentropy',
                metrics: ['accuracy']
            });
            
            // Training
            await model.fit(xs, ys, {
                epochs: epochs,
                validationSplit: 0.2,
                shuffle: true,
                callbacks: {
                    onEpochEnd: (epoch, logs) => {
                        const progress = ((epoch + 1) / epochs * 100).toFixed(0);
                        document.getElementById('progressBar').style.width = progress + '%';
                        document.getElementById('progressText').textContent = 'Epoche ' + (epoch + 1) + ' / ' + epochs;
                        document.getElementById('lossText').textContent =
                            logs.loss.toFixed(4) + ' | ' + (logs.acc * 100).toFixed(1) + '% Acc';
                        // Chart aktualisieren
                        lossChart.data.labels.push(epoch + 1);
                        lossChart.data.datasets[0].data.push(logs.loss);
                        lossChart.data.datasets[1].data.push(logs.acc != null ? logs.acc * 100 : null);
                        lossChart.update('none');
                    }
                }
            });
            
            // Modell speichern
            trainedModel = model;
            visualizeNetwork(model, spectrumLength, layer1Units, layer2Units, layer1Act, layer2Act);
            
            // Finale Evaluation
            const evalResult = model.evaluate(xs, ys);
            const finalAcc = (await evalResult[1].data())[0] * 100;
            
            document.getElementById('trainBtn').disabled = false;
            document.getElementById('trainStatus').textContent = 'Training abgeschlossen';
            document.getElementById('trainStatus').style.color = '#28a745';
            document.getElementById('trainingComplete').style.display = 'block';
            document.getElementById('finalAccuracy').textContent = 'Finale Genauigkeit: ' + finalAcc.toFixed(1) + '%';
            
            // Speicher freigeben
            xs.dispose();
            ys.dispose();
        }
        
        async function visualizeNetwork(model, spectrumLen, l1Units = 64, l2Units = 32, l1Act = 'relu', l2Act = 'relu') {
            const box = document.getElementById('nnVizBox');
            box.style.display = 'block';
            const canvas = document.getElementById('nnViz');
            canvas.width = canvas.offsetWidth || 700;
            canvas.height = 380;
            const ctx = canvas.getContext('2d');
            const W = canvas.width, H = canvas.height;
            ctx.clearRect(0, 0, W, H);

            const MAX_SHOW = 10;
            const layers = [
                { name: 'Eingabe', total: spectrumLen, color: '#546e7a', sub: spectrumLen + '\u00a0FFT-Bins' },
                { name: 'Dense\u00a0' + l1Units, total: l1Units, color: '#8b1a1a', sub: l1Act.toUpperCase() },
                { name: 'Dense\u00a0' + l2Units, total: l2Units, color: '#8b1a1a', sub: l2Act.toUpperCase() },
                { name: 'Ausgabe', total: 2, color: '#28a745', sub: 'Softmax',
                  nodeColors: ['#28a745', '#dc3545'], nodeLabels: ['gut', 'schlecht'] }
            ];
            const xs = [W * 0.10, W * 0.37, W * 0.63, W * 0.87];
            const nr = 12;

            function nodeYs(total) {
                const n = Math.min(total, MAX_SHOW);
                const spacing = Math.min(38, (H - 120) / (n + 1));
                const start = (H - 60) / 2 - (n - 1) * spacing / 2;
                return Array.from({ length: n }, (_, i) => start + i * spacing);
            }

            // Gewichts-Wichtigkeit aus erster Schicht berechnen
            let inputImportance = null;
            try {
                const wData = await model.layers[0].getWeights()[0].data();
                const importance = new Array(spectrumLen).fill(0);
                for (let i = 0; i < spectrumLen; i++)
                    for (let j = 0; j < l1Units; j++)
                        importance[i] += Math.abs(wData[i * l1Units + j]);
                const maxImp = Math.max(...importance) || 1;
                inputImportance = importance.map(v => v / maxImp);
            } catch (e) {}

            // Verbindungen zeichnen
            for (let li = 0; li < layers.length - 1; li++) {
                const fromYs = nodeYs(layers[li].total);
                const toYs = nodeYs(layers[li + 1].total);
                ctx.lineWidth = 0.7;
                ctx.strokeStyle = 'rgba(140,140,140,0.13)';
                for (const fy of fromYs)
                    for (const ty of toYs) {
                        ctx.beginPath();
                        ctx.moveTo(xs[li], fy);
                        ctx.lineTo(xs[li + 1], ty);
                        ctx.stroke();
                    }
            }

            // Neuronen zeichnen
            for (let li = 0; li < layers.length; li++) {
                const layer = layers[li];
                const ys = nodeYs(layer.total);
                const hasMore = layer.total > MAX_SHOW;
                const midIdx = Math.floor(ys.length / 2);

                for (let ni = 0; ni < ys.length; ni++) {
                    const y = ys[ni];
                    if (hasMore && ni === midIdx) {
                        ctx.fillStyle = '#aaa';
                        ctx.font = 'bold 24px Arial';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText('\u22ef', xs[li], y);
                        continue;
                    }

                    let fillColor = layer.nodeColors ? layer.nodeColors[ni] : layer.color;
                    if (li === 0 && inputImportance) {
                        const dataIdx = ni < midIdx ? ni : spectrumLen - (ys.length - ni);
                        const t = inputImportance[Math.min(dataIdx, inputImportance.length - 1)];
                        const rr = Math.round(84 + t * 171);
                        const gg = Math.round(110 - t * 84);
                        const bb = Math.round(122 - t * 120);
                        fillColor = `rgb(${rr},${gg},${bb})`;
                    }

                    ctx.beginPath();
                    ctx.arc(xs[li], y, nr, 0, Math.PI * 2);
                    ctx.fillStyle = fillColor;
                    ctx.fill();
                    ctx.strokeStyle = 'rgba(255,255,255,0.85)';
                    ctx.lineWidth = 2;
                    ctx.stroke();

                    if (layer.nodeLabels) {
                        ctx.fillStyle = fillColor;
                        ctx.font = 'bold 15px Arial';
                        ctx.textAlign = 'left';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(layer.nodeLabels[ni], xs[li] + nr + 7, y);
                    }
                }

                // Schicht-Bezeichnung
                ctx.textAlign = 'center';
                ctx.textBaseline = 'alphabetic';
                if (hasMore) {
                    ctx.fillStyle = '#999';
                    ctx.font = '13px Arial';
                    ctx.fillText('(' + layer.total + ')', xs[li], H - 52);
                }
                ctx.fillStyle = '#333';
                ctx.font = 'bold 15px Arial';
                ctx.fillText(layer.name, xs[li], H - 32);
                ctx.fillStyle = '#777';
                ctx.font = '13px Arial';
                ctx.fillText(layer.sub, xs[li], H - 13);
            }

            // Legende (Eingabe-Farben)
            if (inputImportance) {
                const legX = W * 0.01, legY = 16, legW = 130, legH = 14;
                const grad = ctx.createLinearGradient(legX, 0, legX + legW, 0);
                grad.addColorStop(0, 'rgb(84,110,122)');
                grad.addColorStop(1, 'rgb(255,26,2)');
                ctx.fillStyle = grad;
                ctx.fillRect(legX, legY, legW, legH);
                ctx.strokeStyle = '#ccc';
                ctx.lineWidth = 1;
                ctx.strokeRect(legX, legY, legW, legH);
                ctx.fillStyle = '#555';
                ctx.font = '12px Arial';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'top';
                ctx.fillText('niedrig', legX, legY + legH + 3);
                ctx.textAlign = 'right';
                ctx.fillText('hoch', legX + legW, legY + legH + 3);
                ctx.textAlign = 'center';
                ctx.fillText('Wichtigkeit', legX + legW / 2, legY + legH + 3);
            }
        }
        
        async function predictWithModel(spectrum) {
            if (!trainedModel) return { prediction: 'unknown', confidence: 0 };

            const adjusted = resizeSpectrum(spectrum, trainedModelSpectrumLength);
            const normalized = normalizeSpectrum(adjusted);
            const input = tf.tensor2d([normalized]);
            const prediction = trainedModel.predict(input);
            const probs = await prediction.data();
            input.dispose();
            prediction.dispose();

            if (probs[0] > probs[1]) {
                return { prediction: 'gut', confidence: probs[0] };
            } else {
                return { prediction: 'schlecht', confidence: probs[1] };
            }
        }
        
        const ctx = document.getElementById('chart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: [{ data: [], borderColor: '#8b1a1a', backgroundColor: 'rgba(139,26,26,0.1)', fill: true, pointRadius: 0, borderWidth: 2 }] },
            options: {
                animation: false,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: 'Frequenz (Hz)', color: '#333' }, ticks: { color: '#666', maxTicksLimit: 20 }, grid: { color: '#ddd' } },
                    y: { title: { display: true, text: 'dB', color: '#333' }, ticks: { color: '#666' }, grid: { color: '#ddd' }, min: -60, max: 0 }
                },
                plugins: { legend: { display: false } }
            }
        });
        
        const ctx2 = document.getElementById('chart2').getContext('2d');
        const chart2 = new Chart(ctx2, {
            type: 'line',
            data: { labels: [], datasets: [{ data: [], borderColor: '#8b1a1a', backgroundColor: 'rgba(139,26,26,0.1)', fill: true, pointRadius: 0, borderWidth: 2 }] },
            options: {
                animation: false,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: 'Frequenz (Hz)', color: '#333' }, ticks: { color: '#666', maxTicksLimit: 20 }, grid: { color: '#ddd' } },
                    y: { title: { display: true, text: 'dB', color: '#333' }, ticks: { color: '#666' }, grid: { color: '#ddd' }, min: -60, max: 0 }
                },
                plugins: { legend: { display: false } }
            }
        });
        
        function setLabel(label) {
            currentLabel = label;
            document.querySelectorAll('.label-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelector('.label-btn.' + label).classList.add('active');
            fetch('/api/set_label', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({label: label})
            });
        }
        
        function toggleRecording() {
            isRecording = !isRecording;
            const btn = document.getElementById('recordBtn');
            const status = document.getElementById('recordStatus');
            
            if (isRecording) {
                btn.textContent = '⏹ Aufnahme stoppen';
                btn.className = 'record-btn stop';
                status.textContent = 'Aufnahme läuft...';
                status.style.color = '#28a745';
            } else {
                btn.textContent = '▶ Aufnahme starten';
                btn.className = 'record-btn start';
                status.textContent = 'Gestoppt';
                status.style.color = '#666';
            }
            
            fetch('/api/set_recording', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({recording: isRecording})
            });
        }
        
        async function update() {
            try {
                const r = await fetch('/api/spectrum');
                const d = await r.json();
                if (d.freqs.length > 0) {
                    // Tab 1 aktualisieren
                    chart.data.labels = d.freqs.map(f => f.toFixed(0));
                    chart.data.datasets[0].data = d.fft_db;
                    chart.update('none');
                    document.getElementById('peak').textContent = d.peak_freq.toFixed(0) + ' Hz';
                    document.getElementById('db').textContent = d.peak_db.toFixed(1) + ' dB';
                    document.getElementById('rate').textContent = d.sample_rate;
                    document.getElementById('status').textContent = 'Aufnahme läuft';
                    document.getElementById('status').style.color = '#28a745';
                    
                    // Tab 2 aktualisieren
                    chart2.data.labels = d.freqs.map(f => f.toFixed(0));
                    chart2.data.datasets[0].data = d.fft_db;
                    chart2.update('none');
                    document.getElementById('peak2').textContent = d.peak_freq.toFixed(0) + ' Hz';
                    document.getElementById('db2').textContent = d.peak_db.toFixed(1) + ' dB';
                    document.getElementById('status2').textContent = 'Aufnahme läuft';
                    document.getElementById('status2').style.color = '#28a745';
                }
                
                // Stats aktualisieren
                const stats = await fetch('/api/stats');
                const s = await stats.json();
                document.getElementById('statGut').textContent = s.gut;
                document.getElementById('statSchlecht').textContent = s.schlecht;
                document.getElementById('statTotal').textContent = s.total;
                
                // Vorhersage aktualisieren (wenn Tab aktiv und Modell trainiert)
                if (currentTab === 'inference' && d.fft_db && d.fft_db.length > 0) {
                    const resultEl = document.getElementById('predictionResult');
                    if (trainedModel) {
                        const p = await predictWithModel(d.fft_db);
                        resultEl.textContent = p.prediction === 'gut' ? '✓ Gut' : '✗ Schlecht';
                        resultEl.className = 'prediction-result ' + p.prediction;
                        document.getElementById('predictionConf').textContent = (p.confidence * 100).toFixed(1);
                    } else {
                        resultEl.textContent = 'Kein Modell';
                        resultEl.className = 'prediction-result unknown';
                        document.getElementById('predictionConf').textContent = '--';
                    }
                }
                
            } catch(e) {
                document.getElementById('status').textContent = 'Fehler: ' + e;
            }
        }
        setInterval(update, 100);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML

@app.route('/api/spectrum')
def api_spectrum():
    with data_lock:
        return jsonify(spectrum_data)

@app.route('/api/set_label', methods=['POST'])
def api_set_label():
    global current_label
    data = request.get_json()
    current_label = data.get('label', 'gut')
    print(f"Label gesetzt: {current_label}")
    return jsonify({"status": "ok", "label": current_label})

@app.route('/api/set_recording', methods=['POST'])
def api_set_recording():
    global recording
    data = request.get_json()
    recording = data.get('recording', False)
    print(f"Aufnahme: {'gestartet' if recording else 'gestoppt'}")
    return jsonify({"status": "ok", "recording": recording})

@app.route('/api/stats')
def api_stats():
    total = mqtt_send_count.get('gut', 0) + mqtt_send_count.get('schlecht', 0)
    return jsonify({"gut": mqtt_send_count.get('gut', 0), "schlecht": mqtt_send_count.get('schlecht', 0), "total": total})

@app.route('/api/predict')
def api_predict():
    """Gibt eine Vorhersage basierend auf dem aktuellen Spektrum zurück"""
    # TODO: Hier später das trainierte Modell einbinden
    # Aktuell: Platzhalter-Vorhersage
    with data_lock:
        if len(spectrum_data.get('fft_db', [])) == 0:
            return jsonify({"prediction": "unknown", "confidence": 0})
        
        # Platzhalter: Zufällige Vorhersage oder basierend auf Peak
        # Später durch echtes Modell ersetzen
        return jsonify({"prediction": "unknown", "confidence": 0})

@app.route('/api/training_data')
def api_training_data():
    """Holt alle Trainingsdaten direkt aus der MySQL-Datenbank"""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute("SELECT label, spectrum FROM audio_spectrum ORDER BY ts ASC")
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        # Spectrum JSON dekodieren (PyMySQL liefert JSON-Spalten je nach Version als str oder dict)
        data = []
        for row in rows:
            spectrum = row['spectrum']
            if spectrum is None:
                spectrum = []
            elif isinstance(spectrum, str):
                spectrum = json.loads(spectrum)
            # sonst: bereits als list/dict geparsed -> direkt verwenden
            data.append({
                'label': row['label'],
                'spectrum': spectrum
            })
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def find_audio_device():
    """Findet automatisch das USB-Mikrofon"""
    try:
        print("=== USB-Geräte prüfen ===")
        # Prüfe ob USB-Gerät überhaupt sichtbar ist
        try:
            usb_result = subprocess.run(['lsusb'], capture_output=True, text=True)
            print(f"lsusb:\n{usb_result.stdout}")
        except:
            print("lsusb nicht verfügbar")
        
        # Prüfe dmesg für USB-Audio
        try:
            dmesg = subprocess.run(['dmesg'], capture_output=True, text=True)
            # Suche nach USB Audio relevanten Zeilen
            for line in dmesg.stdout.split('\n'):
                if 'usb' in line.lower() and ('audio' in line.lower() or 'sound' in line.lower() or 'camera' in line.lower()):
                    print(f"dmesg: {line}")
        except:
            print("dmesg nicht lesbar")
        
        print("=== Suche Audio-Gerät ===")
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        print(f"arecord -l stdout: '{result.stdout}'")
        print(f"arecord -l stderr: '{result.stderr}'")
        
        # Methode 2: /proc/asound/cards
        try:
            with open('/proc/asound/cards', 'r') as f:
                cards = f.read()
                print(f"/proc/asound/cards:\n{cards}")
        except:
            print("/proc/asound/cards nicht lesbar")
        
        # Methode 3: arecord -L (alle PCM devices)
        result2 = subprocess.run(['arecord', '-L'], capture_output=True, text=True)
        print(f"arecord -L (erste 500 Zeichen): {result2.stdout[:500] if result2.stdout else 'leer'}")
        
        output = result.stdout
        
        # Suche in arecord -l Output
        search_patterns = [
            r'card (\d+):.*(?:Camera|Webcam|Web Camera|USB Audio|Mikrofon|Microphone)',
            r'card (\d+):.*USB',
            r'card (\d+):',  # Fallback: erstes Gerät
        ]
        
        for pattern in search_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                card = match.group(1)
                device = "hw:" + card + ",0"
                print(f">>> Gefunden via arecord -l: {device}")
                return device
        
        # Fallback: Suche in arecord -L nach plughw oder hw
        if result2.stdout:
            # Suche nach plughw:X,0 oder hw:X,0
            match = re.search(r'(plughw:\d+,\d+|hw:\d+,\d+)', result2.stdout)
            if match:
                device = match.group(1)
                print(f">>> Gefunden via arecord -L: {device}")
                return device
        
        # Letzter Fallback
        print(">>> Kein Gerät gefunden, verwende 'default'")
        return "default"
        
    except Exception as e:
        print(f"Fehler beim Suchen: {e}")
        import traceback
        traceback.print_exc()
        return "default"

def audio_capture_thread():
    """Liest Audio via arecord und berechnet FFT"""
    global spectrum_data, audio_running
    
    # Warte kurz, falls USB noch nicht bereit
    time.sleep(2)
    
    device = find_audio_device()
    print(f"Verwende Audio-Gerät: {device}")
    
    # arecord: 16-bit signed, mono
    cmd = [
        'arecord',
        '-D', device,
        '-f', 'S16_LE',
        '-c', '1',
        '-r', str(SAMPLE_RATE),
        '-t', 'raw',
        '-'
    ]
    
    last_save = 0
    save_interval = 1.0  # Speichere nur jede Sekunde (statt 100ms) um System zu schonen
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            print(f"Starte arecord mit: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            audio_running = True
            print("Audio-Capture gestartet")
            
            # Prüfe ob arecord sofort fehlschlägt
            time.sleep(0.5)
            if process.poll() is not None:
                stderr = process.stderr.read().decode()
                print(f"arecord Fehler: {stderr}")
                retry_count += 1
                # Neues Gerät suchen
                time.sleep(2)
                device = find_audio_device()
                cmd[2] = device
                continue
            
            while audio_running:
                # Lese Chunk (16-bit = 2 Bytes pro Sample)
                raw_data = process.stdout.read(CHUNK_SIZE * 2)
                
                if len(raw_data) < CHUNK_SIZE * 2:
                    if process.poll() is not None:
                        print("arecord beendet, versuche neu...")
                        break
                    continue
                
                # Konvertiere zu numpy array
                samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float64)
                
                # Normalisieren auf -1 bis 1
                samples = samples / 32768.0
                
                # DC-Offset entfernen
                samples = samples - np.mean(samples)
                
                # Hanning-Fenster
                window = np.hanning(len(samples))
                samples = samples * window
                
                # FFT
                fft_result = np.fft.rfft(samples)
                fft_mag = np.abs(fft_result)
                freqs = np.fft.rfftfreq(CHUNK_SIZE, 1.0 / SAMPLE_RATE)
                
                # In dB (normalisiert)
                fft_db = 20 * np.log10(fft_mag / (CHUNK_SIZE / 2) + 1e-10)
                
                # Auf MAX_FREQ begrenzen
                mask = freqs <= MAX_FREQ
                freqs_limited = freqs[mask]
                fft_db_limited = fft_db[mask]
                
                # Peak finden (DC ignorieren)
                if len(fft_db_limited) > 1:
                    peak_idx = np.argmax(fft_db_limited[1:]) + 1
                    peak_freq = freqs_limited[peak_idx]
                    peak_db = fft_db_limited[peak_idx]
                else:
                    peak_freq, peak_db = 0, -60
                
                with data_lock:
                    spectrum_data = {
                        "freqs": freqs_limited.tolist(),
                        "fft_db": fft_db_limited.tolist(),
                        "peak_freq": float(peak_freq),
                        "peak_db": float(peak_db),
                        "sample_rate": SAMPLE_RATE
                    }
                
                # Daten über MQTT senden wenn Aufnahme aktiv
                now = time.time()
                if recording and (now - last_save) >= save_interval:
                    publish_mqtt({
                        "timestamp": datetime.now().isoformat(),
                        "label": current_label,
                        "peak_freq": float(peak_freq),
                        "peak_db": float(peak_db),
                        "spectrum": fft_db_limited.tolist(),
                        "sample_rate": SAMPLE_RATE
                    })
                    last_save = now
            
            # Falls Loop beendet, neu versuchen
            retry_count += 1
            time.sleep(2)
            device = find_audio_device()
            cmd[2] = device
                
        except Exception as e:
            print(f"Audio-Fehler: {e}")
            retry_count += 1
            time.sleep(2)
    
    print("Audio-Capture nach mehreren Versuchen fehlgeschlagen")
    audio_running = False

def start_flask():
    app.run(host='0.0.0.0', port=80, use_reloader=False, threaded=True)

# MQTT verbinden
setup_mqtt()

# Flask in Thread starten
threading.Thread(target=start_flask, daemon=True).start()
print("Webserver auf Port 80")

# Audio-Capture in Thread starten
threading.Thread(target=audio_capture_thread, daemon=True).start()
print("Audio-Capture Thread gestartet")

# Main loop (hält App am Leben)
while True:
    time.sleep(1)
