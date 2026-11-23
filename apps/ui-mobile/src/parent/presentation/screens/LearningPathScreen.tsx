import React from 'react';
import { Ionicons } from '@expo/vector-icons';
import { Text, View } from 'react-native';
import { Card, PrimaryButton, ScreenFrame, SecondaryButton, palette } from '../components/ui';

type Props = { error: string; onTopic: () => void; onLesson: () => void; onBack: () => void };

export function LearningPathScreen({ error, onTopic, onLesson, onBack }: Props): React.JSX.Element {
  return <ScreenFrame title="Bắt đầu buổi học" subtitle="Chọn cách cùng bé khám phá hôm nay." onBack={onBack} visualTone="creative">
    {error ? <Card style={{ borderColor: '#F2C6C6' }}><Text style={{ color: '#9B2C2C', lineHeight: 20 }}>{error}</Text></Card> : null}
    <Card variant="creative" style={{ gap: 12, padding: 16 }}>
      <View style={{ alignItems: 'center', flexDirection: 'row', gap: 12 }}>
        <View style={{ alignItems: 'center', justifyContent: 'center', width: 44, height: 44, borderRadius: 15, backgroundColor: '#F1E7FF' }}>
          <Ionicons name="color-palette-outline" size={24} color={palette.creativePrimary} accessible={false} />
        </View>
        <View style={{ flex: 1, gap: 3 }}>
          <Text style={{ color: palette.creativeInk, fontSize: 17, fontWeight: '800' }}>Theo chủ đề</Text>
          <Text style={{ color: palette.creativeMuted, fontSize: 13, lineHeight: 19 }}>Chọn chủ đề, rồi chọn điều bé muốn vẽ.</Text>
        </View>
      </View>
      <PrimaryButton variant="creative" label="Khám phá chủ đề" onPress={onTopic} />
    </Card>
    <Card variant="creative" style={{ gap: 12, padding: 16 }}>
      <View style={{ alignItems: 'center', flexDirection: 'row', gap: 12 }}>
        <View style={{ alignItems: 'center', justifyContent: 'center', width: 44, height: 44, borderRadius: 15, backgroundColor: '#FFF0D9' }}>
          <Ionicons name="book-outline" size={23} color="#B46A00" accessible={false} />
        </View>
        <View style={{ flex: 1, gap: 3 }}>
          <Text style={{ color: palette.creativeInk, fontSize: 17, fontWeight: '800' }}>Theo bài giảng</Text>
          <Text style={{ color: palette.creativeMuted, fontSize: 13, lineHeight: 19 }}>Dùng bài công khai hoặc được chia sẻ với gia đình.</Text>
        </View>
      </View>
      <SecondaryButton variant="creative" label="Chọn bài giảng" onPress={onLesson} />
    </Card>
  </ScreenFrame>;
}
