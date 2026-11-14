import React, { useState } from 'react';
import { Image, Text, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as ImageManipulator from 'expo-image-manipulator';
import * as FileSystem from 'expo-file-system';
import type { SelectedPhoto } from '../navigation/workflowTypes';
import { isWithinOfflinePhotoLimit } from '../navigation/parentFlowV1';
import { Card, Notice, PrimaryButton, SecondaryButton, ScreenFrame, palette } from '../components/ui';

type Props = {
  photo: SelectedPhoto | null;
  stepLabel: string;
  canAnalyze: boolean;
  onPhoto: (photo: SelectedPhoto) => void;
  onContinue: () => void;
  onBack: () => void;
};

type LockedSelectedPhoto = SelectedPhoto & { locked?: boolean };

function resolveImageMediaType(base64: string): SelectedPhoto['mediaType'] | null {
  if (base64.startsWith('/9j/')) return 'image/jpeg';
  if (base64.startsWith('iVBORw0KGgo')) return 'image/png';
  return null;
}

export function CaptureScreen({ photo, stepLabel, canAnalyze, onPhoto, onContinue, onBack }: Props): React.JSX.Element {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const photoLocked = (photo as LockedSelectedPhoto | null)?.locked === true;

  async function chooseImage(source: 'camera' | 'gallery') {
    setError('');
    setBusy(true);
    try {
      if (source === 'camera') {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) {
          setError('Camera chưa được cho phép. Bạn vẫn có thể chọn ảnh từ thư viện.');
          return;
        }
      } else {
        const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!permission.granted) {
          setError('Thư viện ảnh chưa được cho phép. Bạn có thể cho phép truy cập hoặc thử lại.');
          return;
        }
      }
      const result = source === 'camera'
        ? await ImagePicker.launchCameraAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, quality: 0.85, allowsEditing: true, aspect: [1, 1] })
        : await ImagePicker.launchImageLibraryAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, quality: 0.85, allowsEditing: true, aspect: [1, 1] });
      if (result.canceled || !result.assets[0]) return;
      const asset = result.assets[0];
      let sourceBytes = asset.fileSize;
      if (typeof sourceBytes !== 'number' || !Number.isFinite(sourceBytes)) {
        try {
          const info = await FileSystem.getInfoAsync(asset.uri, { size: true });
          sourceBytes = info.exists && typeof info.size === 'number' ? info.size : undefined;
        } catch {
          sourceBytes = undefined;
        }
      }
      if (typeof sourceBytes !== 'number' || !Number.isFinite(sourceBytes)) {
        setError('Chưa thể kiểm tra dung lượng ảnh. Hãy chọn ảnh khác.');
        return;
      }
      if (!isWithinOfflinePhotoLimit(sourceBytes)) {
        setError('Ảnh vượt quá giới hạn 20 MiB. Hãy chọn ảnh nhỏ hơn.');
        return;
      }
      const compressed = await ImageManipulator.manipulateAsync(
        asset.uri,
        [{ resize: { width: 1200 } }],
        { compress: 0.82, format: ImageManipulator.SaveFormat.JPEG, base64: true },
      );
      if (!compressed.base64) {
        setError('Không đọc được ảnh đã chọn. Hãy chọn ảnh khác.');
        return;
      }
      const imageBase64 = compressed.base64.includes(',') ? compressed.base64.slice(compressed.base64.lastIndexOf(',') + 1) : compressed.base64;
      if (imageBase64.length > 6_700_000) {
        setError('Ảnh đã nén vẫn vượt giới hạn gửi đi. Hãy chọn ảnh khác.');
        return;
      }
      const mediaType = resolveImageMediaType(imageBase64);
      if (!mediaType) {
        setError('Ảnh cần có định dạng PNG hoặc JPEG. Hãy chọn ảnh khác.');
        return;
      }
      onPhoto({ uri: compressed.uri, base64: imageBase64, mediaType, fileSizeBytes: sourceBytes });
    } catch {
      setError('Không thể mở ảnh. Hãy thử lại hoặc chọn ảnh từ thư viện.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <ScreenFrame title="Chụp tranh của bé" subtitle="Chụp một bức tranh trên giấy. Có thể dùng thư viện ảnh thay cho camera." step={stepLabel === '4 / 7' ? '3 / 7' : stepLabel} onBack={onBack}>
      <Card>
        <View style={{ height: 270, borderRadius: 15, backgroundColor: '#F2F6FB', borderWidth: 1, borderColor: palette.border, alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
          {photo ? <Image source={{ uri: photo.uri }} resizeMode="contain" style={{ width: '100%', height: '100%' }} /> : <View style={{ alignItems: 'center', gap: 10, padding: 20 }}><Text style={{ fontSize: 42, color: '#95A9C0' }}>＋</Text><Text style={{ color: palette.muted, textAlign: 'center', lineHeight: 20 }}>Ảnh tranh sẽ hiện ở đây</Text></View>}
        </View>
        <PrimaryButton label={photoLocked ? 'Ảnh đã gắn với buổi học' : photo ? 'Chụp lại' : 'Mở camera'} busy={busy} disabled={photoLocked} onPress={() => void chooseImage('camera')} />
        <SecondaryButton label="Chọn từ thư viện ảnh" disabled={busy || photoLocked} onPress={() => void chooseImage('gallery')} />
        {photoLocked ? <Notice text="Mỗi buổi học chỉ nhận một ảnh. Ảnh đã gửi không thể thay bằng ảnh khác." tone="info" /> : null}
        {error ? <Notice text={error} tone="error" /> : null}
        {photo?.analysisError ? <Notice text={photo.analysisError} tone="warning" /> : null}
      </Card>
      <Notice text="Cần có ảnh trước khi gửi tranh đi xem xét." />
      <PrimaryButton label={photo?.analysisError ? 'Kiểm tra trạng thái để tiếp tục' : 'Tiếp tục xem xét tranh'} disabled={!photo || !canAnalyze || busy} onPress={onContinue} />
    </ScreenFrame>
  );
}
