"""
NOVA Voice Output - Text-to-Speech
===================================
Offline speech synthesis using Piper TTS
"""

import subprocess
from pathlib import Path
from loguru import logger
import sounddevice as sd
import soundfile as sf
import numpy as np
from typing import Optional
import tempfile


class VoiceOutput:
    """Text-to-Speech using Piper"""
    
    def __init__(self, config):
        self.config = config
        self.voice = config.TTS_VOICE
        self.speed = config.TTS_SPEED
        self.piper_path = self._find_piper()
        self.model_path = config.PIPER_MODEL_DIR / f"{self.voice}.onnx"
        
        if self.piper_path:
            logger.info(f"✓ Piper TTS ready (voice: {self.voice})")
        else:
            logger.warning("⚠️  Piper not found, falling back to alternative TTS")
    
    def _find_piper(self) -> Optional[Path]:
        """Find Piper executable"""
        # Check in models directory
        piper_exe = self.config.PIPER_MODEL_DIR / "piper.exe"
        if piper_exe.exists():
            return piper_exe
        
        # Check if in PATH
        try:
            result = subprocess.run(
                ["piper", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return Path("piper")  # Available in PATH
        except:
            pass
        
        logger.warning("Piper executable not found")
        return None
    
    def speak(self, text: str, wait: bool = True) -> bool:
        """
        Convert text to speech and play it
        
        Args:
            text: Text to speak
            wait: Wait for speech to complete
            
        Returns:
            True if successful
        """
        if not text:
            return False
        
        logger.info(f"🔊 Speaking: '{text[:50]}...'")
        
        try:
            if self.piper_path:
                return self._speak_piper(text, wait)
            else:
                return self._speak_fallback(text, wait)
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return False
    
    def _speak_piper(self, text: str, wait: bool) -> bool:
        """Speak using Piper TTS"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_path = Path(temp_audio.name)
            
            # Run Piper to generate audio
            cmd = [
                str(self.piper_path),
                "--model", str(self.model_path),
                "--output_file", str(temp_path)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            process.communicate(input=text.encode('utf-8'), timeout=30)
            
            # Play the generated audio
            if temp_path.exists():
                self._play_audio(temp_path, wait)
                temp_path.unlink()  # Remove temp file
                return True
            else:
                logger.error("Piper didn't generate audio file")
                return False
                
        except Exception as e:
            logger.error(f"Piper TTS error: {e}")
            return False
    
    def _speak_fallback(self, text: str, wait: bool) -> bool:
        """Fallback TTS using Windows SAPI (pyttsx3)"""
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            engine.setProperty('rate', int(150 * self.speed))
            
            if wait:
                engine.say(text)
                engine.runAndWait()
            else:
                engine.say(text)
                engine.startLoop(False)
                engine.iterate()
                engine.endLoop()
            
            return True
        except ImportError:
            logger.error("No TTS engine available. Install pyttsx3 or Piper.")
            return False
        except Exception as e:
            logger.error(f"Fallback TTS error: {e}")
            return False
    
    def _play_audio(self, audio_path: Path, wait: bool = True):
        """Play audio file"""
        try:
            # Load audio file
            audio_data, sample_rate = sf.read(str(audio_path))
            
            # Apply speed adjustment if needed
            if self.speed != 1.0:
                audio_data = self._change_speed(audio_data, self.speed)
            
            # Play audio
            sd.play(audio_data, sample_rate)
            
            if wait:
                sd.wait()  # Wait until audio finishes
            
            logger.info("✓ Audio played successfully")
            
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
    
    def _change_speed(self, audio: np.ndarray, speed: float) -> np.ndarray:
        """Change audio playback speed"""
        # Simple speed change by resampling
        indices = np.round(np.arange(0, len(audio), speed))
        indices = indices[indices < len(audio)].astype(int)
        return audio[indices]
    
    def save_speech(self, text: str, output_path: Path) -> bool:
        """
        Generate speech and save to file
        
        Args:
            text: Text to convert
            output_path: Where to save the audio
            
        Returns:
            True if successful
        """
        try:
            if self.piper_path:
                cmd = [
                    str(self.piper_path),
                    "--model", str(self.model_path),
                    "--output_file", str(output_path)
                ]
                
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                process.communicate(input=text.encode('utf-8'), timeout=30)
                
                if output_path.exists():
                    logger.info(f"✓ Speech saved to {output_path}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error saving speech: {e}")
            return False
    
    def test_speaker(self) -> bool:
        """Test if speaker is working"""
        logger.info("Testing speaker...")
        
        try:
            # Generate a simple beep
            duration = 0.5  # seconds
            frequency = 440  # Hz (A4 note)
            sample_rate = 44100
            
            t = np.linspace(0, duration, int(sample_rate * duration))
            beep = np.sin(2 * np.pi * frequency * t) * 0.3
            
            sd.play(beep, sample_rate)
            sd.wait()
            
            logger.info("✓ Speaker working (did you hear the beep?)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Speaker test failed: {e}")
            return False
    
    def set_voice(self, voice_name: str):
        """Change the TTS voice"""
        self.voice = voice_name
        self.model_path = self.config.PIPER_MODEL_DIR / f"{voice_name}.onnx"
        logger.info(f"Voice changed to: {voice_name}")
    
    def set_speed(self, speed: float):
        """Change speech speed (1.0 = normal)"""
        self.speed = max(0.5, min(2.0, speed))  # Clamp between 0.5x and 2.0x
        logger.info(f"Speed set to: {self.speed}x")


class BeepPlayer:
    """Play notification beeps"""
    
    @staticmethod
    def play_activation_beep():
        """Play beep when NOVA activates"""
        try:
            # Two-tone beep: low-high
            sample_rate = 44100
            duration = 0.1
            
            t = np.linspace(0, duration, int(sample_rate * duration))
            beep1 = np.sin(2 * np.pi * 440 * t) * 0.2  # A4
            beep2 = np.sin(2 * np.pi * 554 * t) * 0.2  # C#5
            
            # Combine with a tiny gap
            gap = np.zeros(int(0.05 * sample_rate))
            full_beep = np.concatenate([beep1, gap, beep2])
            
            sd.play(full_beep, sample_rate)
            
        except Exception as e:
            logger.error(f"Beep error: {e}")
    
    @staticmethod
    def play_error_beep():
        """Play error beep"""
        try:
            sample_rate = 44100
            duration = 0.15
            
            t = np.linspace(0, duration, int(sample_rate * duration))
            beep = np.sin(2 * np.pi * 200 * t) * 0.3  # Low tone
            
            sd.play(beep, sample_rate)
            
        except Exception as e:
            logger.error(f"Beep error: {e}")


if __name__ == "__main__":
    # Test voice output
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from config.config import config
    
    voice_output = VoiceOutput(config)
    
    # Test speaker
    if voice_output.test_speaker():
        print("\n✓ Speaker test passed!")
        
        # Test TTS
        print("\nTesting TTS...")
        voice_output.speak("Hello! I am NOVA, your personal AI assistant.", wait=True)
        
        # Test beeps
        print("\nTesting activation beep...")
        BeepPlayer.play_activation_beep()
        sd.wait()
        
        print("\nAll tests complete!")
    else:
        print("\n❌ Speaker test failed!")
