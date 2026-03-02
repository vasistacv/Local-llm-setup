"""
NOVA Voice Input - Speech-to-Text
==================================
Offline speech recognition using Whisper
"""

import whisper
import sounddevice as sd
import numpy as np
import wave
import tempfile
from pathlib import Path
from loguru import logger
import torch


class VoiceInput:
    """Speech-to-Text using Whisper"""
    
    def __init__(self, config):
        self.config = config
        self.model_name = config.STT_MODEL
        self.language = config.STT_LANGUAGE
        self.sample_rate = config.SAMPLE_RATE
        self.device = "cuda" if config.ENABLE_GPU and torch.cuda.is_available() else "cpu"
        
        logger.info(f"Loading Whisper model '{self.model_name}' on {self.device}...")
        
        try:
            self.model = whisper.load_model(self.model_name, device=self.device)
            logger.info(f"✓ Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def record_audio(self, duration: int = 5, silence_threshold: float = None) -> np.ndarray:
        """
        Record audio from microphone
        
        Args:
            duration: Maximum recording duration in seconds
            silence_threshold: If provided, stop on silence detection
            
        Returns:
            Audio data as numpy array
        """
        logger.info(f"🎤 Recording for {duration} seconds...")
        
        try:
            # Record audio
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()  # Wait for recording to complete
            
            # Convert to 1D array
            audio_data = audio_data.flatten()
            
            logger.info(f"✓ Recording complete ({len(audio_data)} samples)")
            return audio_data
            
        except Exception as e:
            logger.error(f"Recording error: {e}")
            raise
    
    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Audio as numpy array
            
        Returns:
            Transcribed text
        """
        try:
            # Whisper expects float32 audio normalized to [-1, 1]
            audio_data = audio_data.astype(np.float32)
            
            # Transcribe
            logger.info("🎯 Transcribing audio...")
            result = self.model.transcribe(
                audio_data,
                language=self.language,
                fp16=(self.device == "cuda")  # Use FP16 on GPU for speed
            )
            
            text = result['text'].strip()
            logger.info(f"✓ Transcription: '{text}'")
            
            return text
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    def listen_and_transcribe(self, duration: int = 5) -> str:
        """
        Record audio and transcribe in one go
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Transcribed text
        """
        audio = self.record_audio(duration)
        return self.transcribe(audio)
    
    def save_audio(self, audio_data: np.ndarray, filepath: Path):
        """Save audio data to WAV file"""
        try:
            # Convert to int16
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            with wave.open(str(filepath), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())
            
            logger.info(f"✓ Audio saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
    
    def test_microphone(self) -> bool:
        """Test if microphone is working"""
        logger.info("Testing microphone...")
        
        try:
            # Record 1 second of audio
            test_audio = sd.rec(
                int(self.sample_rate),
                samplerate=self.sample_rate,
                channels=1
            )
            sd.wait()
            
            # Check if we got actual audio (not silence)
            if test_audio.max() > 0.01:
                logger.info("✓ Microphone working")
                return True
            else:
                logger.warning("⚠️  Microphone seems to be silent")
                return False
                
        except Exception as e:
            logger.error(f"❌ Microphone test failed: {e}")
            return False
    
    def list_audio_devices(self):
        """List all available audio devices"""
        logger.info("Available audio devices:")
        devices = sd.query_devices()
        
        for i, device in enumerate(devices):
            device_type = "IN" if device['max_input_channels'] > 0 else "OUT"
            logger.info(f"  [{i}] {device['name']} ({device_type})")
    
    def set_device(self, device_id: int = None, device_name: str = None):
        """Set specific audio input device"""
        if device_id is not None:
            sd.default.device = (device_id, sd.default.device[1])
            logger.info(f"Set input device to ID {device_id}")
        elif device_name is not None:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if device_name.lower() in device['name'].lower():
                    sd.default.device = (i, sd.default.device[1])
                    logger.info(f"Set input device to '{device['name']}'")
                    return
            logger.warning(f"Device '{device_name}' not found")


class VoiceActivationDetector:
    """Detect when user starts/stops speaking"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.silence_threshold = 0.01  # Adjust based on your mic
        self.min_silence_duration = 1.0  # Stop after 1s of silence
    
    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Determine if audio chunk contains speech"""
        # Simple energy-based detection
        energy = np.sqrt(np.mean(audio_chunk ** 2))
        return energy > self.silence_threshold
    
    def record_until_silence(self, max_duration: int = 30) -> np.ndarray:
        """
        Record audio until silence is detected
        
        Args:
            max_duration: Maximum recording duration
            
        Returns:
            Recorded audio
        """
        logger.info("🎤 Listening (speak now, I'll detect when you're done)...")
        
        chunks = []
        silence_samples = 0
        max_silence_samples = int(self.min_silence_duration * self.sample_rate)
        
        chunk_size = int(0.1 * self.sample_rate)  # 100ms chunks
        max_chunks = int(max_duration / 0.1)
        
        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='float32') as stream:
                for _ in range(max_chunks):
                    audio_chunk, _ = stream.read(chunk_size)
                    audio_chunk = audio_chunk.flatten()
                    chunks.append(audio_chunk)
                    
                    # Check for speech
                    if self.is_speech(audio_chunk):
                        silence_samples = 0  # Reset silence counter
                    else:
                        silence_samples += len(audio_chunk)
                    
                    # If we've had enough silence and we have some speech, stop
                    if silence_samples >= max_silence_samples and len(chunks) > 10:
                        logger.info("✓ Silence detected, ending recording")
                        break
            
            # Combine all chunks
            audio = np.concatenate(chunks)
            logger.info(f"✓ Recorded {len(audio)/self.sample_rate:.1f} seconds")
            
            return audio
            
        except Exception as e:
            logger.error(f"Recording error: {e}")
            return np.array([])


if __name__ == "__main__":
    # Test voice input
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from config.config import config
    
    voice_input = VoiceInput(config)
    
    # List devices
    voice_input.list_audio_devices()
    
    # Test microphone
    if voice_input.test_microphone():
        print("\n✓ Microphone test passed!")
        print("\nSpeak something (5 seconds)...")
        text = voice_input.listen_and_transcribe(5)
        print(f"\nYou said: '{text}'")
    else:
        print("\n❌ Microphone test failed!")
