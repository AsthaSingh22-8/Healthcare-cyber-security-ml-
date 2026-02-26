import pyshark
import datetime

FEATURE_NAMES = [
    'duration', 'protocol_type', 'service', 'flag', 'src_bytes',
    'dst_bytes', 'hot', 'num_failed_logins', 'num_compromised', 'root_shell',
    'su_attempted', 'num_root', 'num_file_creations', 'num_shells',
    'num_access_files', 'num_outbound_cmds', 'is_host_login',
    'is_guest_login', 'count', 'srv_count'
]

class LivePacketFeatureExtractor:
    def __init__(self, interface='Wi-Fi'):
        self.interface = interface

    def capture_and_extract(self, packet_limit=10):
        capture = pyshark.LiveCapture(interface=self.interface)
        features_list = []
        count = 0
        for packet in capture:
            features = self.extract_features(packet)
            if features:
                features_list.append(features)
            count += 1
            if count >= packet_limit:
                break
        return features_list

    def extract_features(self, packet):
        features = {name: 0 for name in FEATURE_NAMES}
        try:
            features['duration'] = float(getattr(packet, 'sniff_timestamp', 0))
            features['protocol_type'] = packet.highest_layer if hasattr(packet, 'highest_layer') else 'other'
            features['src_bytes'] = int(packet.length) if hasattr(packet, 'length') else 0
            features['dst_bytes'] = 0
        except Exception as e:
            print(f"Error extracting features: {e}")
            return None
        return features

if __name__ == '__main__':
    extractor = LivePacketFeatureExtractor(interface='Wi-Fi')
    feats = extractor.capture_and_extract(packet_limit=5)
    for i, f in enumerate(feats):
        print(f"Packet {i+1} features: {f}")
import pyshark
import datetime

# The correct feature set for your model (20 features)
FEATURE_NAMES = [
    'duration', 'protocol_type', 'service', 'flag', 'src_bytes',
    'dst_bytes', 'hot', 'num_failed_logins', 'num_compromised', 'root_shell',
    'su_attempted', 'num_root', 'num_file_creations', 'num_shells',
    'num_access_files', 'num_outbound_cmds', 'is_host_login',
    'is_guest_login', 'count', 'srv_count'
]

class LivePacketFeatureExtractor:
    def __init__(self, interface='Wi-Fi'):
        self.interface = interface

    def capture_and_extract(self, packet_limit=10):
        capture = pyshark.LiveCapture(interface=self.interface)
        features_list = []
        count = 0
        for packet in capture:
            features = self.extract_features(packet)
            if features:
                features_list.append(features)
            count += 1
            if count >= packet_limit:
                break
        return features_list

    def extract_features(self, packet):
        # Initialize all features to 0 or default
        features = {name: 0 for name in FEATURE_NAMES}
        try:
            # Example feature extraction (customize as needed)
            features['duration'] = float(getattr(packet, 'sniff_timestamp', 0))
            features['protocol_type'] = packet.highest_layer if hasattr(packet, 'highest_layer') else 'other'
            features['src_bytes'] = int(packet.length) if hasattr(packet, 'length') else 0
            features['dst_bytes'] = 0  # Not directly available; set to 0 or estimate
            # Add more extraction logic as needed for your dataset
            # For categorical features, you may need to map protocol/service/flag to your label encoders
        except Exception as e:
            print(f"Error extracting features: {e}")
            return None
        return features

if __name__ == "__main__":
    extractor = LivePacketFeatureExtractor(interface='Wi-Fi')
    features = extractor.capture_and_extract(packet_limit=10)
    for i, feat in enumerate(features):
        print(f"Packet {i+1} features: {feat}")
