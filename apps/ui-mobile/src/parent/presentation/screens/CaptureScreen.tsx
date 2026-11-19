import React, { useState } from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as ImageManipulator from 'expo-image-manipulator';
import * as FileSystem from 'expo-file-system';
import Svg, { Circle, Path, Rect } from 'react-native-svg';
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
          setError('Máy ảnh chưa được cấp quyền. Bạn vẫn có thể chọn tranh từ thư viện ảnh.');
          return;
        }
      } else {
        const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!permission.granted) {
          setError('Thư viện ảnh chưa được cấp quyền. Bạn có thể cấp quyền hoặc thử lại.');
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
    <ScreenFrame title="Chụp hoặc chọn tranh" subtitle="Ảnh tranh giấy là bắt buộc." step={stepLabel === '4 / 7' ? '3 / 7' : stepLabel} onBack={onBack}>
      <Card style={styles.captureCard}>
        <Text style={styles.requiredBadge}>BẮT BUỘC</Text>
        <View style={styles.imageFrame}>
          {photo ? <Image source={{ uri: photo.uri }} resizeMode="contain" style={styles.selectedImage} /> : <CaptureIllustration />}
        </View>
        {!photo ? <Text style={styles.emptyText}>Ảnh tranh giấy sẽ hiện ở đây</Text> : null}
        <PrimaryButton label={photoLocked ? 'Ảnh đã gắn với buổi học' : photo ? 'Chụp lại' : 'Mở camera'} busy={busy} disabled={photoLocked} onPress={() => void chooseImage('camera')} />
        <SecondaryButton label="Chọn từ thư viện ảnh" disabled={busy || photoLocked} onPress={() => void chooseImage('gallery')} />
        {photoLocked ? <Notice text="Mỗi buổi học chỉ nhận một ảnh. Ảnh đã gửi không thể thay bằng ảnh khác." tone="info" /> : null}
        {error ? <Notice text={error} tone="error" /> : null}
        {photo?.analysisError ? <Notice text={photo.analysisError} tone="warning" /> : null}
      </Card>
      <Notice text="Chỉ tiếp tục sau khi có một ảnh tranh hợp lệ. Chưa mở buổi học trước ảnh." />
      <PrimaryButton label={photo?.analysisError ? 'Kiểm tra trạng thái buổi học' : 'Tiếp tục sau khi chọn ảnh'} disabled={!photo || !canAnalyze || busy} onPress={onContinue} />
    </ScreenFrame>
  );
}

function CaptureIllustration(): React.JSX.Element {
  return (
    <Svg width="100%" height="100%" viewBox="0 0 280 190" preserveAspectRatio="xMidYMid meet" accessible={false}>
      <Rect x="1" y="1" width="278" height="188" rx="15" fill="#FFFEF8" />
      <Circle cx="213" cy="48" r="19" fill="#FFF0B8" stroke="#493A2F" strokeWidth="4" />
      <Path d="M211 18v9m0 42v9m-30-30h-9m78 0h-9m-50-21-7-7m55 55-7-7m0-41 7-7m-55 55 7-7" stroke="#493A2F" strokeWidth="4" strokeLinecap="round" />
      <Path d="M34 145c19-8 29-7 45 0 16-12 31-10 45 0 18-10 32-9 48 0 20-11 40-10 73 0" fill="none" stroke="#234D2A" strokeWidth="6" strokeLinecap="round" />
      <Path d="M104 143V86m0 23c-18-8-24-20-22-32 16 2 25 12 22 32Zm2-14c17-10 20-22 16-33-15 5-22 18-16 33Z" fill="#DDF1D8" stroke="#493A2F" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      <Path d="M43 67c8-12 20-13 28 0m-31 8h35m96 44c8-9 18-9 26 0" fill="none" stroke="#9B5A19" strokeWidth="5" strokeLinecap="round" />
    </Svg>
  );
}

const styles = StyleSheet.create({
  captureCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  requiredBadge: { alignSelf: 'flex-start', minHeight: 24, textAlignVertical: 'center', color: palette.ink, fontSize: 9, lineHeight: 13, fontWeight: '800', borderWidth: 1, borderColor: palette.outline, borderRadius: 999, paddingHorizontal: 8, paddingVertical: 4 },
  imageFrame: { width: '100%', aspectRatio: 280 / 190, minHeight: 190, borderRadius: 15, backgroundColor: palette.background, borderWidth: 1.5, borderColor: palette.outline, alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  selectedImage: { width: '100%', height: '100%' },
  emptyText: { color: palette.muted, fontSize: 12, lineHeight: 17, textAlign: 'center', minWidth: 0, flexShrink: 1 },
});
