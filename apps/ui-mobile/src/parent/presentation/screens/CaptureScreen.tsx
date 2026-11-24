import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Alert, Image, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import * as ImageManipulator from 'expo-image-manipulator';
import * as FileSystem from 'expo-file-system';
import Svg, { Circle, Path, Rect } from 'react-native-svg';
import type { SelectedPhoto } from '../navigation/workflowTypes';
import { isWithinOfflinePhotoLimit } from '../navigation/parentFlowV1';
import { Card, Notice, PrimaryButton, SecondaryButton, ScreenFrame, palette } from '../components/ui';
import { ParentAiLoadingState } from '../components/ParentAiLoadingState';

type Props = {
  photo: SelectedPhoto | null;
  stepLabel: string;
  canAnalyze: boolean;
  analysisBusy?: boolean;
  closingRun?: boolean;
  flowError?: string;
  runExists?: boolean;
  initialCaptureSource?: 'camera' | 'gallery' | null;
  onCaptureIntentHandled?: () => void;
  onPhoto: (photo: SelectedPhoto) => void;
  onContinue: () => void;
  onCloseUnresolvedRun?: () => void;
  onBack: () => void;
};

type LockedSelectedPhoto = SelectedPhoto & { locked?: boolean };

function resolveImageMediaType(base64: string): SelectedPhoto['mediaType'] | null {
  if (base64.startsWith('/9j/')) return 'image/jpeg';
  if (base64.startsWith('iVBORw0KGgo')) return 'image/png';
  return null;
}

export function CaptureScreen({
  photo,
  stepLabel,
  canAnalyze,
  analysisBusy = false,
  closingRun = false,
  flowError = '',
  runExists = false,
  initialCaptureSource = null,
  onCaptureIntentHandled,
  onPhoto,
  onContinue,
  onCloseUnresolvedRun,
  onBack,
}: Props): React.JSX.Element {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const onPhotoRef = useRef(onPhoto);
  const handledCaptureIntent = useRef<'camera' | 'gallery' | null>(null);
  const photoLocked = (photo as LockedSelectedPhoto | null)?.locked === true;

  useEffect(() => {
    onPhotoRef.current = onPhoto;
  }, [onPhoto]);

  const chooseImage = useCallback(async (source: 'camera' | 'gallery') => {
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
      onPhotoRef.current({ uri: compressed.uri, base64: imageBase64, mediaType, fileSizeBytes: sourceBytes });
    } catch {
      setError('Không thể mở ảnh. Hãy thử lại hoặc chọn ảnh từ thư viện.');
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (!initialCaptureSource) {
      handledCaptureIntent.current = null;
      return;
    }
    if (handledCaptureIntent.current === initialCaptureSource) return;
    handledCaptureIntent.current = initialCaptureSource;
    onCaptureIntentHandled?.();
    void chooseImage(initialCaptureSource);
  }, [initialCaptureSource, onCaptureIntentHandled, chooseImage]);

  return (
    <ScreenFrame
      title="Chụp tranh"
      subtitle="Ảnh rõ nét giúp nhận diện tốt hơn."
      step={stepLabel}
      onBack={onBack}
      visualTone="creative"
    >
      <Card variant="creative" style={styles.captureCard}>
        <View style={styles.captureHeading}>
          <View style={styles.captureIcon}>
            <Ionicons name="color-palette-outline" size={19} color={palette.creativePrimary} />
          </View>
          <View style={styles.captureCopy}>
            <Text style={styles.captureTitle}>{photo ? 'Đã chọn bức vẽ' : 'Chọn bức vẽ của bé'}</Text>
          </View>
          <Text style={styles.requiredBadge}>BẮT BUỘC</Text>
        </View>
        <View style={styles.imageFrame}>
          {photo ? <Image source={{ uri: photo.uri }} resizeMode="contain" style={styles.selectedImage} /> : <CaptureIllustration />}
        </View>
        {analysisBusy ? <ParentAiLoadingState
          testID="parent-drawing-ai-loading"
          title="Đang phân tích bức vẽ"
          description="AI đang nhận diện chủ thể và các chi tiết nhìn thấy trong ảnh. Người lớn sẽ xem lại kết quả sau bước này."
          note="Giữ nguyên ảnh đã chọn. Không gửi lại yêu cầu đang xử lý."
        /> : null}
        <PrimaryButton variant="creative" label={photoLocked ? 'Ảnh đã gắn với buổi học' : photo ? 'Chụp lại' : 'Mở camera'} busy={busy} disabled={photoLocked || analysisBusy} onPress={() => void chooseImage('camera')} />
        <SecondaryButton variant="creative" label="Chọn từ thư viện ảnh" disabled={busy || photoLocked || analysisBusy} onPress={() => void chooseImage('gallery')} />
        {photoLocked ? <Notice variant="creative" text="Ảnh đã được gắn với buổi học này và không thể thay đổi." tone="info" /> : null}
        {error ? <Notice variant="creative" text={error} tone="error" /> : null}
        {photo?.analysisError ? <Notice variant="creative" text={photo.analysisError} tone={photo.analysisTerminal ? 'error' : 'warning'} /> : null}
        {photo?.analysisError && !photo.analysisTerminal && runExists && onCloseUnresolvedRun ? <SecondaryButton
          variant="creative"
          label={closingRun ? 'Đang đóng buổi…' : 'Đóng buổi chưa có kết quả'}
          disabled={closingRun || analysisBusy}
          onPress={() => Alert.alert(
            'Đóng buổi chưa có kết quả?',
            'Buổi cũ sẽ được giữ để hệ thống dọn dẹp. Nếu yêu cầu đã tới dịch vụ AI, thao tác này không thu hồi được yêu cầu đó.',
            [
              { text: 'Quay lại', style: 'cancel' },
              { text: 'Đóng buổi', style: 'destructive', onPress: onCloseUnresolvedRun },
            ],
          )}
        /> : null}
      </Card>
      {flowError ? <Notice variant="creative" text={flowError} tone="info" /> : null}
      {!runExists && !photoLocked ? <Notice variant="creative" text="Ảnh chỉ gửi khi bạn bắt đầu nhận diện." tone="info" /> : null}
      {!analysisBusy && photo?.analysisTerminal && runExists && onCloseUnresolvedRun ? <PrimaryButton
        variant="creative"
        label={closingRun ? 'Đang đóng buổi…' : 'Đóng buổi và bắt đầu lại'}
        busy={closingRun}
        disabled={closingRun || busy || analysisBusy}
        onPress={onCloseUnresolvedRun}
      /> : !analysisBusy ? <PrimaryButton
        variant="creative"
        label={photo?.analysisRetryable ? 'Thử lại nhận diện tranh' : photo?.analysisError ? 'Kiểm tra trạng thái buổi học' : runExists ? 'Nhận diện tranh' : 'Tạo buổi và nhận diện tranh'}
        disabled={!photo || !canAnalyze || busy || analysisBusy}
        onPress={onContinue}
      /> : null}
    </ScreenFrame>
  );
}

function CaptureIllustration(): React.JSX.Element {
  return (
    <Svg width="100%" height="100%" viewBox="0 0 280 190" preserveAspectRatio="xMidYMid meet" accessible={false}>
      <Rect x="1" y="1" width="278" height="188" rx="18" fill="#F7F0FF" />
      <Rect x="67" y="17" width="146" height="156" rx="12" fill="#FFFEFF" stroke="#DCC8F2" strokeWidth="3" />
      <Path d="M91 134c16-21 34-27 56-10 13-12 25-12 39 0" fill="none" stroke="#89CBB8" strokeWidth="6" strokeLinecap="round" />
      <Circle cx="177" cy="53" r="14" fill="#FFD77A" />
      <Path d="M122 123V82m0 17c-14-6-19-15-17-25 12 1 19 9 17 25Zm2-11c13-7 16-16 12-25-11 4-16 13-12 25Z" fill="#D8F0E6" stroke="#59A994" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <Path d="m146 86 14-34 12 5-14 34-13 8 1-13Z" fill="#A56CEB" stroke="#7435D5" strokeWidth="3" strokeLinejoin="round" />
      <Path d="m157 61 12 5" stroke="#E6D2FF" strokeWidth="4" strokeLinecap="round" />
      <Path d="M49 46h9m-4-5v10m165 63h10m-5-5v10" stroke="#E8A900" strokeWidth="3" strokeLinecap="round" />
      <Circle cx="47" cy="133" r="4" fill="#7435D5" />
      <Circle cx="233" cy="49" r="4" fill="#F49A76" />
    </Svg>
  );
}

const styles = StyleSheet.create({
  captureCard: { gap: 13 },
  captureHeading: { flexDirection: 'row', alignItems: 'center', gap: 9, minWidth: 0 },
  captureIcon: { width: 40, height: 40, borderRadius: 14, backgroundColor: palette.creativeLavender, alignItems: 'center', justifyContent: 'center' },
  captureCopy: { flex: 1, minWidth: 0, gap: 2 },
  captureTitle: { color: palette.creativeInk, fontSize: 14, lineHeight: 19, fontWeight: '800' },
  requiredBadge: { alignSelf: 'flex-start', textAlignVertical: 'center', color: palette.creativePrimary, fontSize: 8, lineHeight: 12, fontWeight: '800', borderRadius: 999, paddingHorizontal: 8, paddingVertical: 5, backgroundColor: palette.creativeLavender },
  imageFrame: { width: '100%', aspectRatio: 1.42, minHeight: 176, borderRadius: 19, backgroundColor: palette.creativeLavender, borderWidth: 1.2, borderColor: palette.creativeBorder, alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  selectedImage: { width: '100%', height: '100%' },
});
