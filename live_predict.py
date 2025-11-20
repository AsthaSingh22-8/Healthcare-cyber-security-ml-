
from live_packet_features import LivePacketFeatureExtractor, FEATURE_NAMES
import joblib
import numpy as np

# Load your trained model
model = joblib.load('model.sav')

# Load label encoders if available
try:
    label_encoders = joblib.load('label_encoders.sav')
except FileNotFoundError:
    label_encoders = {}

# Create the extractor and capture one packet's features
extractor = LivePacketFeatureExtractor(interface='Wi-Fi')
features_list = extractor.capture_and_extract(packet_limit=1)

for features_dict in features_list:
    processed_features = []
    for name in FEATURE_NAMES:
        value = features_dict[name]
        # Encode categorical features if encoder exists
        if name in label_encoders:
            try:
                value = label_encoders[name].transform([value])[0]
            except Exception:
                value = 0  # fallback if unseen label
        processed_features.append(float(value))
    features = np.array(processed_features).reshape(1, -1)
    prediction = model.predict(features)
    print(f"Prediction: {prediction[0]}")