"""
NOVA Wake Word Detection (Phase 2)
====================================
Enterprise-grade always-listening wake word detection
"""

import numpy as np
import sounddevice as sd
from loguru import logger
import threading
import queue
import time
from pathlib import Path


class WakeWordDetector:
    """
    Enterprise wake word detector
    Listens for "Hey Nova" continuously
    """
    
    def __init__(self, config, callback=None):
        self.config = config
        self.callback = callback
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.sample_rate = config.SAMPLE_RATE
        self.wake_word = config.WAKE_WORD.lower()
        self.threshold = config.WAKE_WORD_THRESHOLD
        
        # Energy-based detection parameters
        self.min_energy = 0.01
        self.speech_duration = 1.5  # seconds
        
        logger.info(f"Wake word detector initialized: '{self.wake_word}'")
    
    def start(self):
        """Start always-listening mode"""
        if self.is_listening:
            logger.warning("Wake word detector already running")
            return
        
        self.is_listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        logger.info("🎤 Wake word detector started (always listening)")
    
    def stop(self):
        """Stop listening"""
        self.is_listening = False
        if hasattr(self, 'listen_thread'):
            self.listen_thread.join(timeout=2)
        logger.info("Wake word detector stopped")
    
    def _listen_loop(self):
        """Main listening loop"""
        logger.info("Listening for wake word...")
        
        chunk_size = int(0.1 * self.sample_rate)  # 100ms chunks
        audio_buffer = []
        buffer_duration = 2.0  # Keep 2 seconds of audio
        max_buffer_size = int(buffer_duration * self.sample_rate / chunk_size)
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=chunk_size
            ) as stream:
                while self.is_listening:
                    audio_chunk, _ = stream.read(chunk_size)
                    audio_chunk = audio_chunk.flatten()
                    
                    # Add to buffer
                    audio_buffer.append(audio_chunk)
                    if len(audio_buffer) > max_buffer_size:
                        audio_buffer.pop(0)
                    
                    # Check for wake word
                    if self._detect_wake_word(audio_chunk, audio_buffer):
                        logger.info("✓ Wake word detected!")
                        if self.callback:
                            # Pass last 2 seconds of audio
                            full_audio = np.concatenate(audio_buffer)
                            self.callback(full_audio)
                        else:
                            logger.warning("No callback registered")
                        
                        # Cooldown to avoid multiple triggers
                        time.sleep(2)
                        audio_buffer = []
        
        except Exception as e:
            logger.error(f"Error in wake word detection: {e}")
            self.is_listening = False
    
    def _detect_wake_word(self, chunk, buffer):
        """
        Detect wake word using energy-based method
        (Basic implementation - can be enhanced with actual model)
        """
        # Calculate energy
        energy = np.sqrt(np.mean(chunk ** 2))
        
        # Simple energy threshold detection
        if energy > self.min_energy:
            # Check if we have enough audio
            if len(buffer) >= 10:  # At least 1 second
                full_audio = np.concatenate(buffer[-15:])  # Last 1.5 seconds
                
                # Basic detection: check for speech pattern
                # In production, you'd use actual wake word model here
                avg_energy = np.sqrt(np.mean(full_audio ** 2))
                
                if avg_energy > self.threshold:
                    return True
        
        return False


class AdvancedWakeWordDetector:
    """
    Advanced wake word detector using specialized models
    (OpenWakeWord or Porcupine)
    """
    
    def __init__(self, config, callback=None):
        self.config = config
        self.callback = callback
        self.is_listening = False
        self.sample_rate = 16000
        self.detector = None
        self.detection_method = self._init_detector()
        
    def _init_detector(self):
        """Initialize wake word detection model"""
        # Try OpenWakeWord first
        try:
            from openwakeword import Model
            self.detector = Model(
                wakeword_models=[self.config.MODELS_DIR / "wake_words"],
                inference_framework='onnx'
            )
            logger.info("✓ OpenWakeWord model loaded")
            return "openwakeword"
        except ImportError:
            logger.warning("OpenWakeWord not available")
        except Exception as e:
            logger.warning(f"Could not load OpenWakeWord: {e}")
        
        # Try Porcupine
        try:
            import pvporcupine
            self.detector = pvporcupine.create(
                keywords=["hey-nova"],
                sensitivities=[self.config.WAKE_WORD_THRESHOLD]
            )
            logger.info("✓ Porcupine wake word loaded")
            return "porcupine"
        except ImportError:
            logger.warning("Porcupine not available")
        except Exception as e:
            logger.warning(f"Could not load Porcupine: {e}")
        
        logger.warning("⚠️ No advanced wake word model available, using basic detector")
        return "basic"
    
    def start(self):
        """Start listening"""
        if self.detection_method == "basic":
            # Fall back to basic detector
            basic = WakeWordDetector(self.config, self.callback)
            basic.start()
            return
        
        self.is_listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        logger.info(f"🎤 Advanced wake word detector started ({self.detection_method})")
    
    def stop(self):
        """Stop listening"""
        self.is_listening = False
        if self.detector and self.detection_method == "porcupine":
            self.detector.delete()
    
    def _listen_loop(self):
        """Listening loop for advanced detection"""
        if self.detection_method == "openwakeword":
            self._listen_openwakeword()
        elif self.detection_method == "porcupine":
            self._listen_porcupine()
    
    def _listen_openwakeword(self):
        """OpenWakeWord detection loop"""
        chunk_size = 1280  # OpenWakeWord chunk size
        
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16',
            blocksize=chunk_size
        ) as stream:
            while self.is_listening:
                audio, _ = stream.read(chunk_size)
                prediction = self.detector.predict(audio)
                
                # Check if wake word detected
                if any(score > self.config.WAKE_WORD_THRESHOLD for score in prediction.values()):
                    logger.info("✓ Wake word detected (OpenWakeWord)!")
                    if self.callback:
                        self.callback(audio)
                    time.sleep(2)  # Cooldown
    
    def _listen_porcupine(self):
        """Porcupine detection loop"""
        chunk_size = self.detector.frame_length
        
        with sd.InputStream(
            samplerate=self.detector.sample_rate,
            channels=1,
            dtype='int16',
            blocksize=chunk_size
        ) as stream:
            while self.is_listening:
                audio, _ = stream.read(chunk_size)
                audio_array = audio.flatten()
                
                keyword_index = self.detector.process(audio_array)
                
                if keyword_index >= 0:
                    logger.info("✓ Wake word detected (Porcupine)!")
                    if self.callback:
                        self.callback(audio_array)
                    time.sleep(2)


# Convenience function
def create_wake_word_detector(config, callback=None, advanced=True):
    """
    Factory function to create appropriate wake word detector
    
    Args:
        config: Configuration object
        callback: Function to call when wake word detected
        advanced: Try advanced detectors first
    """
    if advanced:
        return AdvancedWakeWordDetector(config, callback)
    else:
        return WakeWordDetector(config, callback)


if __name__ == "__main__":
    # Test wake word detection
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from config.config import config
    
    def on_wake_word(audio):
        print("\n🔥 WAKE WORD TRIGGERED! 🔥\n")
    
    detector = create_wake_word_detector(config, on_wake_word, advanced=False)
    detector.start()
    
    try:
        print("Say 'Hey Nova' to trigger...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        detector.stop()
