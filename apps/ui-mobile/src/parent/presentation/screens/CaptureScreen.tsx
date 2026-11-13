import React, { useState } from 'react';
import { Image, Text, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as ImageManipulator from 'expo-image-manipulator';
import type { SelectedPhoto } from '../navigation/workflowTypes';
import { Card, Notice, PrimaryButton, SecondaryButton, ScreenFrame, palette } from '../components/ui';

type Props = {
  photo: SelectedPhoto | null;
  stepLabel: string;
  canAnalyze: boolean;
  onPhoto: (photo: SelectedPhoto) => void;
  onContinue: () => void;
  onBack: () => void;
};

function resolveImageMediaType(base64: string): SelectedPhoto['mediaType'] | null {
  if (base64.startsWith('/9j/')) return 'image/jpeg';
  if (base64.startsWith('iVBORw0KGgo')) return 'image/png';
  return null;
}

export function CaptureScreen({ photo, stepLabel, canAnalyze, onPhoto, onContinue, onBack }: Props): React.JSX.Element {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function chooseImage(source: 'camera' | 'gallery') {
    setError('');
    setBusy(true);
    try {
      if (source === 'camera') {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) throw new Error('Cần cho phép dùng camera để chụp tranh.');
      } else {
        const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!permission.granted) throw new Error('Cần cho phép chọn ảnh tranh từ thư viện.');
      }
      const result = source === 'camera'
        ? await ImagePicker.launchCameraAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, quality: 0.85, allowsEditing: true, aspect: [1, 1] })
        : await ImagePicker.launchImageLibraryAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, quality: 0.85, allowsEditing: true, aspect: [1, 1] });
      if (result.canceled || !result.assets[0]) return;
      const compressed = await ImageManipulator.manipulateAsync(
        result.assets[0].uri,
        [{ resize: { width: 1200 } }],
        { compress: 0.82, format: ImageManipulator.SaveFormat.JPEG, base64: true },
      );
      if (!compressed.base64) throw new Error('Không đọc được ảnh đã chọn. Hãy chọn ảnh khác.');
      const imageBase64 = compressed.base64.includes(',') ? compressed.base64.slice(compressed.base64.lastIndexOf(',') + 1) : compressed.base64;
      if (imageBase64.length > 6_700_000) throw new Error('Ảnh quá lớn. Hãy chọn ảnh nhỏ hơn.');
      const mediaType = resolveImageMediaType(imageBase64);
      if (!mediaType) throw new Error('Ảnh cần có định dạng PNG hoặc JPEG. Hãy chọn ảnh khác.');
      onPhoto({ uri: compressed.uri, base64: imageBase64, mediaType });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không thể mở ảnh.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <ScreenFrame title="Chụp tranh của bé" subtitle="Chụp một bức tranh trên giấy. Có thể dùng thư viện ảnh thay cho camera." step={stepLabel} onBack={onBack}>
      <Card>
        <View style={{ height: 270, borderRadius: 15, backgroundColor: '#F2F6FB', borderWidth: 1, borderColor: palette.border, alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
          {photo ? <Image source={{ uri: photo.uri }} resizeMode="contain" style={{ width: '100%', height: '100%' }} /> : <View style={{ alignItems: 'center', gap: 10, padding: 20 }}><Text style={{ fontSize: 42, color: '#95A9C0' }}>＋</Text><Text style={{ color: palette.muted, textAlign: 'center', lineHeight: 20 }}>Ảnh tranh sẽ hiện ở đây</Text></View>}
        </View>
        <PrimaryButton label={photo ? 'Chụp lại' : 'Mở camera'} busy={busy} onPress={() => void chooseImage('camera')} />
        <SecondaryButton label="Chọn từ thư viện ảnh" disabled={busy} onPress={() => void chooseImage('gallery')} />
        {error ? <Notice text={error} tone="error" /> : null}
      </Card>
      <Notice text="Cần có ảnh trước khi gửi tranh đi xem xét." />
      <PrimaryButton label="Tiếp tục xem xét tranh" disabled={!photo || !canAnalyze || busy} onPress={onContinue} />
    </ScreenFrame>
  );
}
