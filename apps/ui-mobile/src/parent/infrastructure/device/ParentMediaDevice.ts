import * as Crypto from 'expo-crypto';
import * as FileSystem from 'expo-file-system';
import { base64ToBytes, type BinaryDigestPort } from '../../application/parentRunUploads';

/**
 * Phone side of the Phase B uploads: SHA-256 of the exact bytes (expo-crypto) and the bytes of a
 * recorded file (expo-file-system). Neither value is ever logged; the file stays on the device until
 * the upload session takes it, and nothing here knows a URL, a bucket or a key.
 */
export class ExpoBinaryDigest implements BinaryDigestPort {
  async sha256Hex(bytes: Uint8Array): Promise<string> {
    const digest = await Crypto.digest(Crypto.CryptoDigestAlgorithm.SHA256, bytes as Uint8Array<ArrayBuffer>);
    return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
  }
}

/** Reads a local recording into memory (at most 20,000,000 bytes by the upload limit). */
export async function readLocalFileBytes(uri: string): Promise<Uint8Array> {
  const base64 = await FileSystem.readAsStringAsync(uri, { encoding: FileSystem.EncodingType.Base64 });
  return base64ToBytes(base64);
}
