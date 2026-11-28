export const RECORDING_SAMPLE_RATE = 16000;
export const MAX_RECORDING_SAMPLES = RECORDING_SAMPLE_RATE * 120;

/** Downmix and linearly resample decoded audio to a bounded 16-bit PCM WAV. */
export function encodeRecordingWav(audio: AudioBuffer): Blob {
  const count = Math.min(MAX_RECORDING_SAMPLES, Math.floor(audio.length * RECORDING_SAMPLE_RATE / audio.sampleRate));
  const bytes = new ArrayBuffer(44 + count * 2);
  const view = new DataView(bytes);
  const write = (offset: number, text: string) => { for (let i = 0; i < text.length; i++) view.setUint8(offset + i, text.charCodeAt(i)); };
  write(0, "RIFF"); view.setUint32(4, 36 + count * 2, true); write(8, "WAVE");
  write(12, "fmt "); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
  view.setUint16(22, 1, true); view.setUint32(24, RECORDING_SAMPLE_RATE, true);
  view.setUint32(28, RECORDING_SAMPLE_RATE * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  write(36, "data"); view.setUint32(40, count * 2, true);
  const channels = Array.from({ length: audio.numberOfChannels }, (_, i) => audio.getChannelData(i));
  for (let i = 0; i < count; i++) {
    const position = i * audio.sampleRate / RECORDING_SAMPLE_RATE;
    const left = Math.floor(position), right = Math.min(left + 1, audio.length - 1), fraction = position - left;
    let sample = 0;
    for (const channel of channels) sample += channel[left] * (1 - fraction) + channel[right] * fraction;
    sample = Math.max(-1, Math.min(1, sample / channels.length));
    view.setInt16(44 + i * 2, sample < 0 ? sample * 32768 : sample * 32767, true);
  }
  return new Blob([bytes], { type: "audio/wav" });
}
