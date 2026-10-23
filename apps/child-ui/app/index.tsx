import { useRef, useState } from 'react'
import {
  Alert,
  Image,
  LayoutChangeEvent,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native'

type Screen = 'join' | 'lobby' | 'draw' | 'advanced' | 'ideas' | 'review' | 'group' | 'gallery' | 'learn' | 'video' | 'offline' | 'feeling' | 'reconnect'
type Point = { x: number; y: number }
type Stroke = { points: Point[]; color: string; size: number }
type Kid = 'Mây' | 'Lá'
type Tool = 'pen' | 'eraser'

const colors = ['#FFD21F', '#FF596C', '#1685F8', '#31C978', '#9250E8']
const galleryArt: Record<Kid, number> = {
  Mây: require('../assets/gallery-hoa.png'),
  Lá: require('../assets/gallery-la.png'),
}
const avatars: Record<string, number> = {
  Mây: require('../assets/avatar-may.png'),
  Lá: require('../assets/avatar-la.png'),
  Nắng: require('../assets/avatar-nang.png'),
}

function Pill({ children, tone = 'blue' }: { children: React.ReactNode; tone?: 'blue' | 'green' | 'pink' | 'yellow' }) {
  return <View style={[styles.pill, tone === 'green' && styles.pillGreen, tone === 'pink' && styles.pillPink, tone === 'yellow' && styles.pillYellow]}><Text style={[styles.pillText, tone === 'green' && styles.greenText, tone === 'pink' && styles.pinkText, tone === 'yellow' && styles.yellowText]}>{children}</Text></View>
}

function Card({ children, style }: { children: React.ReactNode; style?: object }) {
  return <View style={[styles.card, style]}>{children}</View>
}

function Action({ label, icon, onPress, kind = 'primary', style, compact = false }: { label: string; icon?: string; onPress: () => void; kind?: 'primary' | 'secondary' | 'pink' | 'yellow'; style?: object; compact?: boolean }) {
  const buttonStyle = kind === 'primary' ? styles.actionPrimary : kind === 'pink' ? styles.actionPink : kind === 'yellow' ? styles.actionYellow : styles.actionSecondary
  const textStyle = kind === 'primary' ? styles.actionTextLight : kind === 'secondary' ? styles.actionText : kind === 'pink' ? styles.actionTextPink : styles.actionTextYellow
  return <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [styles.action, compact && styles.actionCompact, buttonStyle, style, pressed && styles.pressed]}><Text style={[styles.actionLabel, compact && styles.actionLabelCompact, textStyle]}>{icon ? `${icon}  ` : ''}{label}</Text></Pressable>
}

function Heading({ children, style }: { children: React.ReactNode; style?: object }) {
  return <Text style={[styles.heading, style]}>{children}</Text>
}

function SmallText({ children, style }: { children: React.ReactNode; style?: object }) {
  return <Text style={[styles.smallText, style]}>{children}</Text>
}

function Brand({ large = false, compact = false }: { large?: boolean; compact?: boolean }) {
  return <View style={styles.brand}><Image source={require('../assets/logo-icon.png')} style={large ? compact ? styles.brandIconCompact : styles.brandIconLarge : styles.brandIcon} /><Text style={large ? compact ? styles.brandNameCompact : styles.brandNameLarge : styles.brandName}>Sketch2Life</Text></View>
}

function TopBar({ screen, name, onBack, onOffline }: { screen: Screen; name: string; onBack: () => void; onOffline: () => void }) {
  const title = screen === 'learn' ? 'Khám phá kiến thức' : screen === 'group' ? 'Khu vườn của chúng mình' : 'Khu vườn của chúng mình'
  return <View style={styles.topBar}>
    <Pressable accessibilityRole="button" accessibilityLabel="Quay lại" onPress={onBack} style={styles.backButton}><Text style={styles.backGlyph}>‹</Text></Pressable>
    <Brand />
    <View style={styles.divider} />
    <Text numberOfLines={1} style={styles.topTitle}>🌱  {title}</Text>
    <Pill tone="green">🍃  Nhóm Lá</Pill>
    <View style={styles.whoPill}><Image source={avatars[name] ?? avatars.Mây} style={styles.whoAvatar} /><Text style={styles.whoText}>{name}{screen === 'feeling' ? ' cảm nhận' : screen === 'learn' ? ' đang xem' : ' đang vẽ'}</Text></View>
    {(screen === 'draw' || screen === 'advanced') && <Pressable accessibilityRole="button" onPress={() => Alert.alert('Đổi lượt', 'Cô/thầy sẽ sắp xếp lượt vẽ cho nhóm.')} style={styles.turnButton}><Text style={styles.turnText}>⇄  Đổi lượt</Text></Pressable>}
    <Pressable accessibilityRole="button" accessibilityLabel={screen === 'reconnect' ? 'Kết nối lại' : 'Mô phỏng mất kết nối'} onPress={onOffline} style={styles.savedButton}>{screen === 'reconnect' ? <Text style={styles.savedText}>☁̸  Kết nối lại</Text> : <><Text style={styles.savedGlyph}>☁</Text><Text style={styles.savedText}>Đã lưu</Text></>}</Pressable>
  </View>
}

function Footnote() {
  return <Text style={styles.footnote}>Dữ liệu minh họa</Text>
}

export default function ChildApp() {
  const [screen, setScreen] = useState<Screen>('join')
  const [resumeScreen, setResumeScreen] = useState<Screen>('draw')
  const [code, setCode] = useState<string[]>(Array(6).fill(''))
  const codeRefs = useRef<Array<TextInput | null>>([])
  const [name, setName] = useState<Kid>('Mây')
  const [viewport, setViewport] = useState({ width: 0, height: 0 })
  const [strokes, setStrokes] = useState<Stroke[]>([])
  const [redo, setRedo] = useState<Stroke[]>([])
  const [draft, setDraft] = useState<Stroke | null>(null)
  const [color, setColor] = useState(colors[2])
  const [brush, setBrush] = useState(9)
  const [tool, setTool] = useState<Tool>('pen')
  const [mood, setMood] = useState('')
  const [note, setNote] = useState('')
  const [playing, setPlaying] = useState(true)
  const [progress, setProgress] = useState(29)
  const [selectedArt, setSelectedArt] = useState<Kid>('Mây')
  const [suggestionsVisible, setSuggestionsVisible] = useState(true)
  const [layers, setLayers] = useState({ friends: true, suggestion: false })
  const [viewportMeasured, setViewportMeasured] = useState(false)
  const compact = viewport.height > 0 && viewport.height <= 440

  const onLayout = (event: LayoutChangeEvent) => {
    setViewport({ width: event.nativeEvent.layout.width, height: event.nativeEvent.layout.height })
    setViewportMeasured(true)
  }
  const updateCode = (index: number, value: string) => {
    const digits = value.replace(/\D/g, '')
    const next = [...code]
    if (!digits) next[index] = ''
    else digits.slice(0, 6 - index).split('').forEach((digit, offset) => { next[index + offset] = digit })
    setCode(next)
    if (digits) codeRefs.current[Math.min(index + digits.length, 5)]?.focus()
  }
  const notice = (title: string, description = 'Yêu cầu đã được ghi nhận trên thiết bị này.') => Alert.alert(title, description)
  const goOffline = () => {
    if (screen === 'reconnect') {
      setScreen(resumeScreen)
      return
    }
    setResumeScreen(screen)
    setScreen('reconnect')
  }
  const back = () => {
    const previous: Partial<Record<Screen, Screen>> = {
      lobby: 'join', draw: 'lobby', advanced: 'lobby', ideas: 'draw', review: 'draw', group: 'draw', gallery: 'group', learn: 'gallery', video: 'gallery', offline: 'learn', feeling: 'offline', reconnect: resumeScreen,
    }
    setScreen(previous[screen] ?? 'join')
  }

  const addPoint = (event: { nativeEvent: { locationX: number; locationY: number } }) => {
    const point = { x: event.nativeEvent.locationX, y: event.nativeEvent.locationY }
    if (tool === 'eraser') {
      setStrokes((all) => all.filter((stroke) => stroke.points.every((p) => Math.hypot(p.x - point.x, p.y - point.y) > 24)))
      setDraft(null)
      return
    }
    setDraft((previous) => previous ? { ...previous, points: [...previous.points, point] } : { points: [point], color, size: brush })
  }
  const finishStroke = () => {
    if (tool === 'eraser') return
    if (draft) {
      setStrokes((all) => [...all, draft])
      setRedo([])
    }
    setDraft(null)
  }
  const undo = () => {
    if (!strokes.length) return
    setRedo((all) => [...all, strokes[strokes.length - 1]])
    setStrokes((all) => all.slice(0, -1))
  }
  const redoStroke = () => {
    if (!redo.length) return
    setStrokes((all) => [...all, redo[redo.length - 1]])
    setRedo((all) => all.slice(0, -1))
  }
  const renderInk = (stroke: Stroke, key: string) => stroke.points.slice(1).map((point, index) => {
    const start = stroke.points[index]
    const dx = point.x - start.x
    const dy = point.y - start.y
    const length = Math.hypot(dx, dy)
    return <View key={`${key}-${index}`} pointerEvents="none" style={[styles.ink, { left: (start.x + point.x - length) / 2, top: (start.y + point.y - stroke.size) / 2, width: Math.max(length, stroke.size), height: stroke.size, borderRadius: stroke.size / 2, backgroundColor: stroke.color, transform: [{ rotate: `${Math.atan2(dy, dx)}rad` }] }]} />
  })

  const canvas = (large = false) => <View style={[styles.canvas, large && styles.canvasLarge]} onStartShouldSetResponder={() => true} onMoveShouldSetResponder={() => true} onResponderGrant={addPoint} onResponderMove={addPoint} onResponderRelease={finishStroke} onResponderTerminate={finishStroke}>
    <View pointerEvents="none" style={styles.canvasArtwork}><Image source={galleryArt[selectedArt]} resizeMode="cover" style={styles.canvasArtworkImage} /></View>
    {layers.suggestion ? <View pointerEvents="none" style={styles.suggestionOverlay}><Text style={styles.suggestionOverlayText}>Gợi ý</Text></View> : null}
    {[...strokes, ...(draft ? [draft] : [])].map((stroke, index) => renderInk(stroke, `stroke-${index}`))}
  </View>

  const joinScreen = <View style={styles.joinLayout}>
    <View style={styles.joinHero}>
      <View style={styles.joinBrand}><Brand large compact={compact} /></View>
      <Image source={require('../assets/join-garden.png')} resizeMode="cover" style={styles.joinGarden} />
      <View style={[styles.joinCopy, compact && styles.joinCopyCompact]}><Heading style={[styles.joinTitle, compact && styles.joinTitleCompact]}>Cùng sáng tạo nhé!</Heading><Text style={[styles.joinSubtitle, compact && styles.joinSubtitleCompact]}>Nhập mã để vào phiên học.</Text></View>
    </View>
    <Card style={[styles.joinCard, compact && styles.joinCardCompact]}>
      <Heading style={[styles.joinCardTitle, compact && styles.joinCardTitleCompact]}>Tham gia phiên học</Heading>
      <View style={[styles.codeRow, compact && styles.codeRowCompact]}>{code.map((digit, index) => <TextInput key={index} ref={(ref) => { codeRefs.current[index] = ref }} accessibilityLabel={`Số thứ ${index + 1} của mã phiên`} keyboardType="number-pad" maxLength={6} placeholder="•" placeholderTextColor="#91A1B8" value={digit} onChangeText={(value) => updateCode(index, value)} onKeyPress={({ nativeEvent }) => { if (nativeEvent.key === 'Backspace' && !code[index] && index > 0) codeRefs.current[index - 1]?.focus() }} style={[styles.codeBox, compact && styles.codeBoxCompact]} />)}</View>
      <Action compact={compact} label="Tham gia" icon="➜" onPress={() => code.some((digit) => !digit) ? notice('Nhập mã phiên', 'Mã phiên gồm sáu chữ số. Con hãy nhập đủ mã nhé!') : setScreen('lobby')} />
      <Action compact={compact} label="Quét mã" icon="▣" kind="secondary" onPress={() => notice('Quét mã', 'Camera sẽ được kết nối khi tích hợp thiết bị. Con có thể nhập mã phiên bằng các ô phía trên.')} />
      <Pressable onPress={() => notice('Nhờ cô/thầy giúp', 'Hãy gọi cô/thầy để được giúp nhập mã phiên nhé.')}><Text style={[styles.helpLink, compact && styles.helpLinkCompact]}>Nhờ cô/thầy giúp</Text></Pressable>
      <View style={[styles.joinTip, compact && styles.joinTipCompact]}><Image source={require('../assets/mascot-leaf.png')} style={[styles.tipLeaf, compact && styles.tipLeafCompact]} /><Text style={[styles.tipText, compact && styles.tipTextCompact]}>Cô/thầy sẽ xác nhận trước khi con vào lớp.</Text></View>
    </Card>
    <Footnote />
  </View>

  const lobbyScreen = <View style={styles.screenBody}>
    <View style={styles.lobbyColumns}>
      <Card style={styles.lobbyHero}>
        <Heading style={styles.lobbyTitle}>Chờ cô/thầy bắt đầu</Heading>
        <Text style={styles.lobbySubtitle}>Hãy sẵn sàng, chúng mình sẽ cùng vẽ thật vui!</Text>
        <Image source={require('../assets/art-garden-wide.png')} resizeMode="cover" style={styles.lobbyGarden} />
        <Image source={require('../assets/mascot-leaf.png')} style={styles.lobbyLeafAvatar} />
        <Action label="Cần giúp" icon="?" kind="pink" onPress={() => notice('Cần giúp', 'Gọi cô/thầy nếu con cần hỗ trợ nhé!')} />
      </Card>
      <View style={styles.lobbyRight}>
        <Card style={styles.pickCard}><Heading style={styles.cardHeading}>Ai đang dùng máy?</Heading><SmallText>Chọn tên của con trước khi vẽ nhé!</SmallText><View style={styles.kidRow}>{(['Mây', 'Lá'] as Kid[]).map((kid) => <Pressable key={kid} accessibilityRole="button" onPress={() => setName(kid)} style={[styles.kidCard, name === kid && styles.kidCardSelected]}><Image source={avatars[kid]} style={styles.kidImage} />{name === kid && <Text style={styles.selectedCheck}>✓</Text>}<Text style={styles.kidName}>{kid}</Text></Pressable>)}</View><Pill>{name} đang dùng máy</Pill></Card>
        <Card style={styles.friendsCard}><Heading style={styles.cardHeading}>Các bạn trong nhóm</Heading><View style={styles.friendRow}>{['Mây', 'Lá', 'Nắng'].map((kid) => <View key={kid} style={styles.friendItem}><Image source={avatars[kid]} style={styles.friendImage} /><Text style={styles.friendName}>{kid}</Text></View>)}</View><Action label="Chưa đến giờ vẽ" icon="🔒" kind="secondary" onPress={() => notice('Chờ cô/thầy nhé', 'Lớp sẽ bắt đầu khi cô/thầy xác nhận.')} /></Card>
      </View>
    </View>
        <Action label="Con đã sẵn sàng" icon="✓" onPress={() => setScreen(name === 'Lá' ? 'advanced' : 'draw')} style={styles.readyButton} />
    <Footnote />
  </View>

  const bottomDrawingTools = (reviewMode = false) => <View style={[styles.drawToolbar, compact && styles.drawToolbarCompact]}>
    <Action compact={compact} label="Bút vẽ" icon="🖌" onPress={() => setTool('pen')} style={[styles.toolAction, compact && styles.toolActionCompact, tool === 'pen' && styles.toolActionSelected]} />
    <Action compact={compact} label="Tẩy" icon="◩" kind="secondary" onPress={() => setTool('eraser')} style={[styles.toolAction, compact && styles.toolActionCompact, tool === 'eraser' && styles.toolActionSelected]} />
    <Action compact={compact} label="Hoàn tác" icon="↶" kind="secondary" onPress={undo} style={[styles.toolAction, compact && styles.toolActionCompact]} />
    {colors.map((value) => <Pressable key={value} accessibilityRole="button" accessibilityLabel={`Chọn màu ${value}`} onPress={() => { setColor(value); setTool('pen') }} style={[styles.colorDot, compact && styles.colorDotCompact, { backgroundColor: value }, value === color && styles.colorDotSelected]} />)}
    <View style={[styles.toolbarDivider, compact && styles.toolbarDividerCompact]} />
    {[5, 9, 14].map((size) => <Pressable key={size} accessibilityRole="button" accessibilityLabel={`Cỡ nét ${size}`} onPress={() => setBrush(size)} style={[styles.brushChoice, compact && styles.brushChoiceCompact, brush === size && styles.brushSelected]}><View style={{ width: compact ? Math.max(4, size - 3) : size, height: compact ? Math.max(4, size - 3) : size, borderRadius: size / 2, backgroundColor: '#263652' }} /></Pressable>)}
    <View style={[styles.toolbarDivider, compact && styles.toolbarDividerCompact]} />
    <Action compact={compact} label="Cần giúp" icon="?" kind="pink" onPress={() => notice('Cần giúp', 'Gọi cô/thầy nếu con cần hỗ trợ nhé!')} style={[styles.smallToolAction, compact && styles.smallToolActionCompact]} />
    <Action compact={compact} label={reviewMode ? 'Tiếp tục vẽ' : 'Gợi ý'} icon={reviewMode ? '🖌' : '☆'} kind={reviewMode ? 'primary' : 'yellow'} onPress={() => setScreen(reviewMode ? 'draw' : 'ideas')} style={[styles.smallToolAction, compact && styles.smallToolActionCompact]} />
  </View>

  const drawingScreen = (advanced = false) => <View style={styles.screenBody}>
    <View style={styles.drawingArea}>
      {advanced ? <View style={styles.advancedTools}>{[['🖌', 'Bút vẽ', () => setTool('pen')], ['◩', 'Tẩy', () => setTool('eraser')], ['↶', 'Hoàn tác', undo], ['↻', 'Làm lại', redoStroke], ['⌕', 'Thu phóng', () => notice('Thu phóng', 'Dùng hai ngón tay để phóng to hoặc thu nhỏ tranh.')], ['◇', 'Hình khối', () => notice('Hình khối', 'Chọn màu và vẽ tự do trên vùng vẽ nhé.')]].map(([icon, label, onPress]) => <Action key={String(label)} label={String(label)} icon={String(icon)} kind={label === 'Bút vẽ' ? 'primary' : 'secondary'} onPress={onPress as () => void} style={styles.advancedTool} />)}</View> : null}
      <Card style={styles.canvasCard}>
        <View style={styles.canvasCardHeader}><Text style={styles.canvasLabel}>Tranh của con</Text><Pill tone="green">☁  Đã lưu</Pill></View>
        {canvas(true)}
      </Card>
      {advanced ? <Card style={styles.advancedPanel}>
        <View style={styles.expandedTools}><Text style={styles.expandedIcon}>🔧</Text><View><Text style={styles.expandedTitle}>Công cụ mở rộng</Text><Text style={styles.expandedSub}>cô/thầy bật</Text></View></View>
        <Heading style={styles.cardHeading}>Lớp vẽ</Heading>
        <Pressable onPress={() => setName('Lá')} style={[styles.layerRow, styles.layerSelected]}><Image source={avatars.Lá} style={styles.layerAvatar} /><View style={styles.memberCopy}><Text style={styles.memberName}>Lớp của Lá</Text><Text style={styles.memberStatus}>Con chỉnh sửa</Text></View><Text style={styles.layerEye}>◉</Text></Pressable>
        <Pressable onPress={() => setLayers((value) => ({ ...value, friends: !value.friends }))} style={styles.layerRow}><Text style={styles.layerIcon}>👥</Text><View style={styles.memberCopy}><Text style={styles.memberName}>Bạn cùng nhóm</Text><Text style={styles.memberStatus}>{layers.friends ? 'Chỉ xem, không chỉnh sửa' : 'Đang ẩn'}</Text></View><Text style={styles.layerEye}>{layers.friends ? '◉' : '⊘'}</Text></Pressable>
        <Pressable onPress={() => setLayers((value) => ({ ...value, suggestion: !value.suggestion }))} style={styles.layerRow}><Text style={styles.layerIcon}>🌿</Text><View style={styles.memberCopy}><Text style={styles.memberName}>Gợi ý tham khảo</Text><Text style={styles.memberStatus}>{layers.suggestion ? 'Đang hiện' : 'Đang ẩn'}</Text></View><Text style={styles.layerEye}>{layers.suggestion ? '◉' : '⊘'}</Text></Pressable>
        <Image source={require('../assets/mascot-leaf.png')} style={styles.advancedMascot} />
      </Card> : <Card style={styles.drawingHelp}>
        <View style={styles.speechBubble}><Text style={styles.speechText}>Con vẽ theo ý mình nhé!</Text></View>
        <Image source={require('../assets/mascot-leaf.png')} style={styles.largeMascot} />
        <Action label="Cùng vẽ nhóm" icon="🍃" kind="secondary" onPress={() => setScreen('group')} />
      </Card>}
    </View>
    {bottomDrawingTools()}
    <Footnote />
  </View>

  const ideaScreen = <View style={styles.screenBody}>
    <Heading style={styles.screenTitle}>✨  Gợi ý để tham khảo  ✨</Heading>
    <View style={styles.ideaColumns}>
      <Card style={styles.ideaCard}><Heading style={styles.cardHeading}>Tranh của con</Heading>{canvas()}<Text style={styles.caption}>Con có thể vẽ theo cách của mình.</Text></Card>
      <Card style={styles.ideaCard}><View style={styles.titleRow}><Heading style={styles.cardHeading}>Gợi ý tham khảo</Heading><Pill tone="green">✓  Cô/thầy đã duyệt</Pill></View>{suggestionsVisible ? <Image source={require('../assets/gallery-hoa.png')} resizeMode="cover" style={styles.ideaArt} /> : <View style={[styles.ideaArt, styles.hiddenSuggestion]}><Text style={styles.hiddenHint}>Gợi ý đã ẩn</Text></View>}<SmallText style={styles.caption}>Hãy xem hình gợi ý rồi vẽ theo cách riêng của con.</SmallText></Card>
    </View>
    <View style={styles.ideaActions}>
      <Action label={suggestionsVisible ? 'Xem gợi ý' : 'Đã ẩn gợi ý'} icon="◎" onPress={() => setSuggestionsVisible(!suggestionsVisible)} style={styles.ideaAction} />
      <Action label="Ẩn gợi ý" icon="◉" kind="secondary" onPress={() => setSuggestionsVisible(false)} style={styles.ideaAction} />
      <Action label="Mình muốn tự vẽ" icon="✎" kind="secondary" onPress={() => setScreen('draw')} style={styles.ideaAction} />
      <Action label="Nhờ cô/thầy duyệt" icon="✓" kind="secondary" onPress={() => setScreen('review')} style={styles.ideaAction} />
    </View>
    {!suggestionsVisible && <Text style={styles.hiddenHint}>Gợi ý đã được ẩn. Con có thể vẽ theo ý mình.</Text>}
    <Footnote />
  </View>

  const reviewScreen = <View style={styles.screenBody}>
    <View style={styles.reviewColumns}><Card style={styles.reviewCanvas}><View style={styles.canvasCardHeader}><Text style={styles.canvasLabel}>Tranh của con</Text><Pill tone="green">☁  Đã lưu</Pill></View>{canvas(true)}{bottomDrawingTools(true)}</Card><Card style={styles.reviewStatus}><View style={[styles.waitArt, compact && styles.waitArtCompact]}><Image source={require('../assets/art-sprout.png')} resizeMode="contain" style={styles.waitArtImage} /><Text style={styles.waitClock}>◷</Text></View><Heading style={[styles.cardHeading, compact && styles.reviewHeadingCompact]}>Chờ cô/thầy xem gợi ý</Heading><SmallText style={compact ? styles.reviewTextCompact : undefined}>Khi cô/thầy duyệt, con mới xem được.</SmallText><Pill>➤  Đã gửi yêu cầu.</Pill><Image source={require('../assets/mascot-leaf.png')} style={[styles.reviewAvatar, compact && styles.reviewAvatarCompact]} /><View style={[styles.speechBubble, styles.reviewSpeech, compact && styles.reviewSpeechCompact]}><Text style={[styles.speechText, compact && styles.reviewTextCompact]}>Con vẫn có thể vẽ theo ý mình.</Text></View></Card></View>
    <Footnote />
  </View>

  const groupScreen = <View style={styles.screenBody}>
    <View style={styles.groupColumns}>
      <Card style={styles.groupBoard}><View style={styles.canvasCardHeader}><Text style={styles.canvasLabel}>Nhóm Lá — Cùng vẽ</Text><Pill tone="green">☁  Đã lưu</Pill></View><View style={styles.sharedCanvas}>
        <Image source={require('../assets/gallery-hoa.png')} resizeMode="cover" style={styles.sharedArtwork} />
        <View pointerEvents="none" style={[styles.memberZone, styles.zoneMay]}><Text style={styles.zoneLabel}>Mây</Text></View>
        {layers.friends && <View pointerEvents="none" style={[styles.memberZone, styles.zoneLa]}><Text style={[styles.zoneLabel, styles.zoneLabelPink]}>Lá</Text></View>}
        <View pointerEvents="none" style={[styles.memberZone, styles.zoneNang]}><Text style={[styles.zoneLabel, styles.zoneLabelYellow]}>Nắng 🔒</Text></View>
      </View></Card>
      <Card style={styles.groupPanel}><Heading style={styles.cardHeading}>Các bạn trong nhóm</Heading>
        {([['Mây', 'Đang vẽ', '✎', 'blue'], ['Lá', 'Đang chờ lượt', '◷', 'green'], ['Nắng', 'Cần cô/thầy giúp', '!', 'yellow']] as const).map(([kid, status, icon, tone]) => <View key={kid} style={[styles.memberCard, tone === 'blue' && styles.memberBlue, tone === 'yellow' && styles.memberYellow]}><Image source={avatars[kid]} style={styles.memberAvatar} /><View style={styles.memberCopy}><Text style={styles.memberName}>{kid}</Text><Text style={styles.memberStatus}>{status}</Text></View><Text style={styles.memberIcon}>{icon}</Text></View>)}
        <View style={styles.mascotHint}><Image source={require('../assets/avatar-la.png')} style={styles.mascotSmall} /><Text style={styles.speechText}>Mỗi bạn có một lượt vẽ.</Text></View>
        <View style={styles.buttonRow}><Action label="Xin đổi lượt" icon="⟳" kind="secondary" onPress={() => notice('Xin đổi lượt', 'Cô/thầy sẽ sắp xếp lượt vẽ cho nhóm.')} style={styles.flexAction} /><Action label="Cần giúp" icon="?" kind="pink" onPress={() => notice('Cần giúp', 'Cô/thầy sẽ tới hỗ trợ con.')} style={styles.flexAction} /></View>
        <View style={styles.buttonRow}><Action label="Mở lượt vẽ" icon="🖌" onPress={() => setScreen(name === 'Lá' ? 'advanced' : 'draw')} style={styles.flexAction} /><Action label="Phòng tranh" icon="▧" kind="secondary" onPress={() => setScreen('gallery')} style={styles.flexAction} /></View>
      </Card>
    </View>
    <Footnote />
  </View>

  const galleryScreen = <View style={styles.screenBody}>
    <View style={styles.galleryHeadingRow}><Heading style={styles.galleryTitle}>🌱  Khu vườn của nhóm mình</Heading><View style={styles.tabSwitch}><Pressable onPress={() => setSelectedArt('Mây')} style={[styles.tabButton, selectedArt === 'Mây' && styles.tabSelected]}><Text style={[styles.tabText, selectedArt === 'Mây' && styles.tabTextSelected]}>▧  Tranh của nhóm</Text></Pressable><Pressable onPress={() => setScreen('ideas')} style={styles.tabButton}><Text style={styles.tabText}>✦  Gợi ý tham khảo</Text></Pressable></View></View>
    <View style={styles.galleryColumns}><Card style={styles.galleryMain}><Image source={galleryArt[selectedArt]} resizeMode="cover" style={styles.galleryImage} /><View style={styles.contributors}>{(['Mây', 'Lá', 'Nắng'] as const).map((kid) => <View key={kid} style={styles.contributor}><Image source={avatars[kid]} style={styles.contributorAvatar} /><Text style={styles.friendName}>{kid}</Text></View>)}<View style={styles.contributorDivider} /><Text style={styles.contributorText}>Đóng góp của Mây, Lá và Nắng</Text><Pill tone="green">✓  Bản đã lưu</Pill></View></Card>
      <Card style={styles.gallerySide}><View style={styles.speechBubble}><Text style={styles.speechText}>Chia sẻ ý tưởng</Text></View><Image source={require('../assets/mascot-leaf.png')} style={styles.galleryMascot} /><Heading style={styles.cardHeading}>Con muốn kể về bức tranh nào?</Heading><Action label="Đề nghị trình bày" icon="▧" onPress={() => notice('Đề nghị trình bày', 'Cô/thầy sẽ sắp xếp lượt chia sẻ cho con.')} /><SmallText style={styles.centerText}>Cô/thầy sẽ sắp xếp lượt.</SmallText><View style={styles.buttonRow}><Action label="Khám phá kiến thức" icon="▶" kind="secondary" onPress={() => setScreen('learn')} style={styles.flexAction} /><Action label="Tạo video" icon="🎬" kind="secondary" onPress={() => setScreen('video')} style={styles.flexAction} /></View></Card>
    </View>
    <Footnote />
  </View>

  const learnScreen = <View style={styles.screenBody}>
    <View style={styles.learnHeader}><Heading style={styles.galleryTitle}>▶  Khám phá kiến thức</Heading><Pill tone="green">✓  Cô/thầy đã duyệt</Pill></View>
    <View style={styles.learnColumns}><View style={styles.learnLeft}><Card style={styles.videoCard}><Image source={require('../assets/gallery-hoa.png')} resizeMode="cover" style={styles.knowledgeVideo} /><Pressable accessibilityRole="button" onPress={() => setPlaying(!playing)} style={styles.videoPlay}><Text style={styles.videoPlayGlyph}>{playing ? 'Ⅱ' : '▶'}</Text></Pressable><View style={styles.videoScrub}><Pressable onPress={() => setPlaying(!playing)}><Text style={styles.videoControlGlyph}>{playing ? 'Ⅱ' : '▶'}</Text></Pressable><Pressable onPress={() => setProgress((value) => Math.min(value + 10, 100))} style={styles.progressTrack}><View style={[styles.progressFill, { width: `${progress}%` }]} /><View style={[styles.progressKnob, { left: `${progress}%` }]} /></Pressable><Text style={styles.videoControlGlyph}>◖))</Text></View></Card><View style={styles.subtitlePill}><Text style={styles.captionStrong}>Bướm hút mật từ hoa.</Text></View></View>
      <Card style={styles.lessonPanel}><View style={styles.lessonTitleBubble}><SmallText>Hôm nay cùng khám phá:</SmallText><Heading style={styles.lessonName}>Hoa và bướm</Heading></View><View style={styles.lessonPoint}><Image source={require('../assets/art-flowers.png')} style={styles.lessonThumbnail} /><Text style={styles.numberBadge}>1</Text><Text style={styles.lessonText}>Hoa có màu sắc rực rỡ và có mật ngọt.</Text></View><View style={styles.lessonPoint}><Image source={require('../assets/gallery-hoa.png')} style={styles.lessonThumbnail} /><Text style={styles.numberBadge}>2</Text><Text style={styles.lessonText}>Bướm dùng vòi hút mật từ hoa để ăn.</Text></View><Image source={require('../assets/mascot-leaf.png')} style={styles.lessonMascot} /><Action label="Hoàn thành" icon="✓" onPress={() => setScreen('offline')} /></Card>
    </View>
    <View style={styles.learnBottom}><View style={styles.learnHelpActions}><Action label="Không nghe rõ" icon="🔊" kind="secondary" onPress={() => notice('Báo lỗi âm thanh', 'Cô/thầy sẽ kiểm tra phần âm thanh.')} style={styles.flexAction} /><Action label="Không xem được" icon="▣" kind="pink" onPress={() => notice('Báo lỗi hình ảnh', 'Cô/thầy sẽ kiểm tra video bài học.')} style={styles.flexAction} /></View><View style={styles.learnHelper}><Image source={require('../assets/mascot-leaf.png')} style={styles.learnHelperImage} /><View style={styles.learnSpeech}><Text style={styles.learnSpeechText}>Hãy nhờ cô/thầy khi cần nhé!</Text></View></View></View>
    <Footnote />
  </View>

  const videoScreen = <View style={styles.screenBody}>
    <View style={styles.videoHeader}><Text style={styles.videoHeaderLabel}>🌱  Khám phá kiến thức　│　🌱  Khu vườn của chúng mình</Text><Pill tone="green">Nhóm Lá</Pill><Pill>{name}</Pill></View>
    <View style={styles.videoWaitColumns}><Card style={styles.videoStory}><Image source={galleryArt.Mây} resizeMode="cover" style={styles.videoStoryArt} /><View style={styles.storyLabel}><Text style={styles.storyLabelText}>🍃  Tranh của nhóm Lá</Text></View><View style={styles.storyPrompt}><Image source={require('../assets/avatar-la.png')} style={styles.storyAvatar} /><Text style={styles.speechText}>Con nhìn thấy những gì trong tranh?</Text></View></Card>
      <Card style={styles.videoWaitCard}><Image source={require('../assets/video-clapper.png')} resizeMode="contain" style={styles.clapper} /><Heading style={styles.videoWaitTitle}>Video đang được chuẩn bị.</Heading><SmallText>Cả lớp cùng chờ cô/thầy nhé.</SmallText><View style={styles.creatingPill}><View style={styles.loadingDots}><Text style={styles.dotBlue}>●</Text><Text style={styles.dotMid}>●</Text><Text style={styles.dotPale}>●</Text></View><Text style={styles.creatingText}>Đang tạo video</Text></View><Action label="Kiểm tra trạng thái" icon="↻" kind="secondary" onPress={() => notice('Video đang được chuẩn bị', 'Cả lớp cùng chờ cô/thầy nhé.')} /><Action label="Quay lại phòng tranh" kind="secondary" onPress={() => setScreen('gallery')} /></Card>
    </View>
    <Footnote />
  </View>

  const offlineScreen = <View style={styles.screenBody}>
    <View style={styles.offlineColumns}><Card style={styles.offlineMain}><Text style={styles.offlineEyebrow}>🍃  Hoạt động ngoài màn hình / Nhóm Lá</Text><Heading style={styles.offlineTitle}>Cắt mây, cùng khám phá!</Heading><Text style={styles.activityTitle}>Trồng một hạt đậu</Text><View style={styles.stepsRow}>{[['Cho đất vào cốc', require('../assets/script-step1.png')], ['Đặt hạt đậu', require('../assets/script-step2.png')], ['Tưới một ít nước', require('../assets/script-step3.png')]].map(([label, image], index) => <View key={String(label)} style={styles.stepItem}><Image source={image as number} resizeMode="contain" style={styles.stepImage} /><View style={styles.stepCaption}><Text style={styles.stepNumber}>{index + 1}</Text><Text style={styles.stepText}>{String(label)}.</Text></View>{index < 2 && <Text style={styles.stepArrow}>➜</Text>}</View>)}</View>
        <View style={styles.materialsBox}><Heading style={styles.cardHeading}>Chuẩn bị những gì?</Heading>{[['🫘', 'Hạt đậu'], ['🥤', 'Cốc'], ['🟤', 'Đất'], ['💧', 'Nước']].map(([icon, label]) => <View key={label} style={styles.materialItem}><Text style={styles.materialIcon}>{icon}</Text><Text style={styles.materialLabel}>{label}</Text></View>)}</View>
      </Card><Card style={styles.activityAside}><View style={styles.speechBubble}><Text style={styles.speechText}>Cùng trồng hạt đậu và chờ xem nó lớn lên nhé!</Text></View><Image source={require('../assets/mascot-leaf.png')} style={styles.activityMascot} /><View style={styles.safetyBox}><Text style={styles.safetyText}>⚠  Nhờ cô/thầy hướng dẫn.</Text><Text style={styles.safetyText}>🚫  Không đưa hạt vào miệng.</Text></View></Card></View>
    <View style={styles.bottomActions}><Action label="Con đã sẵn sàng" icon="✓" onPress={() => setScreen('feeling')} style={styles.readyButton} /><Action label="Cần giúp" icon="?" kind="secondary" onPress={() => notice('Cần giúp', 'Nhờ cô/thầy hướng dẫn hoạt động nhé.')} style={styles.helpButton} /></View>
    <Footnote />
  </View>

  const feelingScreen = <View style={styles.screenBody}>
    <View style={styles.feelingColumns}><Card style={styles.feelingArtCard}><View style={styles.sectionBar}><Text style={styles.sectionBarText}>🍃  Hoạt động của nhóm Lá</Text></View><Image source={galleryArt.Mây} resizeMode="cover" style={styles.feelingArt} /><Image source={require('../assets/art-sprout.png')} resizeMode="cover" style={styles.feelingArt} /></Card>
      <Card style={styles.feelingForm}><Heading style={styles.feelingTitle}>🌱  Hôm nay con thấy thế nào?</Heading><View style={styles.moodRow}>{[['😊', 'Con muốn\nthử thêm'], ['🤔', 'Con cần\ngiúp thêm'], ['😄', 'Con muốn kể\nvới cô/thầy']].map(([face, label]) => <Pressable key={label} accessibilityRole="button" onPress={() => setMood(label.replace('\n', ' '))} style={[styles.moodCard, mood === label.replace('\n', ' ') && styles.moodSelected]}><Image source={require('../assets/avatar-la.png')} style={styles.moodImage} /><Text style={styles.moodFace}>{face}</Text><Text style={styles.moodLabel}>{label}</Text>{mood === label.replace('\n', ' ') && <Text style={styles.moodCheck}>✓</Text>}</Pressable>)}</View><View style={styles.noteBox}><Text style={styles.noteTitle}>✎  Điều con muốn thử lần sau (tùy chọn)</Text><TextInput multiline value={note} onChangeText={setNote} placeholder="Con có thể nhờ cô/thầy ghi lại ở đây nhé!" placeholderTextColor="#92A5C1" style={styles.noteInput} /></View><View style={styles.buttonRow}><Pill>👩🏻‍🏫  Con có thể nhờ cô/thầy ghi lại</Pill><Action label="Để sau" icon="◷" kind="secondary" onPress={() => setScreen('join')} style={styles.flexAction} /><Action label="Gửi cảm nhận" icon="➤" onPress={() => mood ? (notice('Đã gửi cảm nhận', 'Cảm ơn con đã chia sẻ nhé!'), setScreen('join')) : notice('Chọn cảm nhận', 'Con hãy chọn một cảm xúc trước nhé.')} style={styles.flexAction} /></View></Card>
    </View>
    <Footnote />
  </View>

  const reconnectScreen = <View style={styles.screenBody}>
    <View style={styles.reconnectHeader}><Text style={styles.cloudSlash}>☁̸</Text><Heading style={styles.reconnectTitle}>Mây đang mất kết nối</Heading><SmallText>Tranh của con vẫn được giữ để kiểm tra.</SmallText></View>
    <View style={styles.savedColumns}><Card style={styles.savedCard}><View style={styles.savedHeading}><Text style={styles.savedIcon}>☁✓</Text><View><Heading style={styles.cardHeading}>Phần đã lưu</Heading><SmallText>Đã được hệ thống xác nhận lưu.</SmallText></View></View><Image source={require('../assets/gallery-hoa.png')} resizeMode="cover" style={styles.savedArtwork} /></Card><Card style={styles.savedCard}><View style={styles.savedHeading}><Text style={styles.pendingIcon}>✎</Text><View><Heading style={styles.cardHeading}>Phần đang chờ gửi</Heading><SmallText>Chưa gửi lên lớp.</SmallText></View></View>{canvas()}</Card></View>
    <Action label="Thử kết nối lại" icon="⟳" onPress={() => setScreen(resumeScreen)} style={styles.retryButton} />
    <View style={[styles.buttonRow, styles.reconnectButtonRow]}><Action label="Nhờ cô/thầy giúp" icon="👩🏻‍🏫" kind="pink" onPress={() => notice('Nhờ cô/thầy giúp', 'Gọi cô/thầy nếu con cần hỗ trợ nhé.')} style={styles.flexAction} /><Action label="Xem phần đã lưu" icon="▱" kind="secondary" onPress={() => setScreen('draw')} style={styles.flexAction} /></View>
    <View pointerEvents="none" style={[styles.reconnectMascotWrap, compact && styles.reconnectMascotCompact]}><Image source={require('../assets/mascot-leaf.png')} resizeMode="contain" style={styles.reconnectMascotImage} /></View><Text style={styles.waitingNetwork}>●  Đang chờ mạng.</Text><Footnote />
  </View>

  const pages: Record<Screen, React.ReactNode> = {
    join: joinScreen,
    lobby: lobbyScreen,
    draw: drawingScreen(),
    advanced: drawingScreen(true),
    ideas: ideaScreen,
    review: reviewScreen,
    group: groupScreen,
    gallery: galleryScreen,
    learn: learnScreen,
    video: videoScreen,
    offline: offlineScreen,
    feeling: feelingScreen,
    reconnect: reconnectScreen,
  }

  const frameWidth = viewport.width && viewport.height ? compact ? viewport.width : Math.min(viewport.width, viewport.height * 1.65) : undefined
  const frameHeight = viewport.width && viewport.height ? compact ? viewport.height : Math.min(viewport.height, viewport.width / 1.65) : undefined
  return <View style={styles.stage} onLayout={onLayout}><View style={[styles.appFrame, compact && styles.appFrameCompact, viewportMeasured && frameWidth && frameHeight ? { width: frameWidth, height: frameHeight } : styles.fill]}>
    {screen === 'join' ? null : <TopBar screen={screen} name={name} onBack={back} onOffline={goOffline} />}
    {pages[screen]}
  </View></View>
}

const styles = StyleSheet.create({
  stage: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1F8FE' },
  appFrame: { padding: 14, backgroundColor: '#F4FAFF', overflow: 'hidden' },
  appFrameCompact: { padding: 5 },
  fill: { width: '100%', height: '100%' },
  topBar: { height: '9%', minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 3 },
  backButton: { width: 42, height: 42, borderRadius: 13, backgroundColor: '#E5F2FF', alignItems: 'center', justifyContent: 'center' },
  backGlyph: { fontSize: 34, lineHeight: 38, color: '#18356E' },
  brand: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  brandIcon: { width: 35, height: 40, resizeMode: 'contain' },
  brandName: { color: '#087CF2', fontSize: 22, fontWeight: '900' },
  brandIconLarge: { width: 60, height: 64, resizeMode: 'contain' },
  brandNameLarge: { color: '#087CF2', fontSize: 33, fontWeight: '900' },
  brandIconCompact: { width: 38, height: 40, resizeMode: 'contain' }, brandNameCompact: { color: '#087CF2', fontSize: 21, fontWeight: '900' },
  divider: { width: 1, height: 34, backgroundColor: '#D9E8F6', marginHorizontal: 6 },
  topTitle: { flex: 1, color: '#122550', fontSize: 16, fontWeight: '900' },
  pill: { paddingVertical: 9, paddingHorizontal: 14, borderRadius: 25, backgroundColor: '#E2F2FF', alignItems: 'center', justifyContent: 'center' },
  pillGreen: { backgroundColor: '#DDF7E7' }, pillPink: { backgroundColor: '#FFF0F1' }, pillYellow: { backgroundColor: '#FFF7E2' },
  pillText: { color: '#0875DA', fontWeight: '900', fontSize: 14 }, greenText: { color: '#16774C' }, pinkText: { color: '#D94459' }, yellowText: { color: '#B87900' },
  whoPill: { flexDirection: 'row', alignItems: 'center', gap: 7, paddingVertical: 5, paddingLeft: 5, paddingRight: 12, backgroundColor: '#E6F3FF', borderRadius: 25 },
  whoAvatar: { width: 34, height: 34, borderRadius: 18 }, whoText: { color: '#18356F', fontWeight: '800', fontSize: 14 },
  turnButton: { borderWidth: 1, borderColor: '#D8E8F8', backgroundColor: '#FFF', borderRadius: 18, paddingVertical: 9, paddingHorizontal: 12 }, turnText: { color: '#203B6A', fontWeight: '900', fontSize: 13 },
  savedButton: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 8 }, savedGlyph: { fontSize: 27, color: '#19A6F4' }, savedText: { color: '#087FE8', fontWeight: '900', fontSize: 15 },
  joinLayout: { flex: 1, flexDirection: 'row', gap: 16, padding: 5, position: 'relative' },
  joinCopyCompact: { top: '31%' },
  joinHero: { flex: 1.12, borderRadius: 28, overflow: 'hidden', backgroundColor: '#F8FCFF', justifyContent: 'center', alignItems: 'center' },
  joinBrand: { position: 'absolute', left: 20, top: 15, zIndex: 3 },
  joinCopy: { position: 'absolute', top: '28%', width: '92%', alignItems: 'center', zIndex: 2 },
  joinTitle: { fontSize: 36, textAlign: 'center', marginBottom: 6 },
  joinTitleCompact: { fontSize: 25, marginBottom: 2 },
  joinSubtitle: { color: '#697B98', fontSize: 21, fontWeight: '700', textAlign: 'center' },
  joinSubtitleCompact: { fontSize: 14 },
  joinGarden: { position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', transform: [{ scaleX: -1 }] },
  joinSun: { position: 'absolute', top: 5, right: '10%', width: 115, height: 115, opacity: 0.9 },
  card: { backgroundColor: '#FFFFFF', borderRadius: 26, padding: 17, borderColor: '#E5F0F9', borderWidth: 1, shadowColor: '#7D9AB7', shadowOpacity: 0.08, shadowRadius: 12, elevation: 2 },
  joinCard: { flex: 0.88, justifyContent: 'center', paddingHorizontal: 25 },
  joinCardCompact: { padding: 10, paddingHorizontal: 12, borderRadius: 18 },
  joinCardTitle: { fontSize: 28, textAlign: 'center', marginBottom: 15 },
  joinCardTitleCompact: { fontSize: 21, marginBottom: 7 },
  heading: { color: '#101E4C', fontSize: 24, fontWeight: '900' },
  smallText: { color: '#667B9C', fontSize: 15, fontWeight: '600', textAlign: 'center' },
  codeRow: { flexDirection: 'row', justifyContent: 'center', gap: 7, marginBottom: 12 },
  codeRowCompact: { gap: 4, marginBottom: 6 },
  codeBox: { flex: 1, maxWidth: 62, minWidth: 35, height: 64, borderRadius: 16, backgroundColor: '#F2F8FE', borderWidth: 2, borderColor: '#CFE5FC', textAlign: 'center', color: '#132451', fontSize: 27, fontWeight: '900', padding: 0 },
  codeBoxCompact: { minWidth: 0, height: 43, borderRadius: 12, fontSize: 20 },
  action: { minHeight: 49, paddingHorizontal: 13, paddingVertical: 9, borderRadius: 18, alignItems: 'center', justifyContent: 'center', marginVertical: 4 },
  actionCompact: { minHeight: 37, paddingVertical: 5, marginVertical: 3, borderRadius: 14 },
  actionPrimary: { backgroundColor: '#087FF2' }, actionSecondary: { backgroundColor: '#F4F9FE', borderWidth: 1.5, borderColor: '#D8E9FA' }, actionPink: { backgroundColor: '#FFF0F2', borderWidth: 1, borderColor: '#FFE2E5' }, actionYellow: { backgroundColor: '#FFF8E8', borderWidth: 1, borderColor: '#FFEDC4' },
  actionLabel: { fontSize: 16, fontWeight: '900', textAlign: 'center' }, actionTextLight: { color: '#FFFFFF' }, actionText: { color: '#17316A' }, actionTextPink: { color: '#17316A' }, actionTextYellow: { color: '#17316A' },
  actionLabelCompact: { fontSize: 13 },
  pressed: { opacity: 0.76, transform: [{ scale: 0.985 }] },
  helpLink: { color: '#087FF2', textAlign: 'center', textDecorationLine: 'underline', fontWeight: '800', fontSize: 17, padding: 8 },
  helpLinkCompact: { fontSize: 13, padding: 3 },
  joinTip: { borderTopColor: '#E0EDF8', borderTopWidth: 1, marginTop: 9, paddingTop: 10, flexDirection: 'row', alignItems: 'center', gap: 8 },
  joinTipCompact: { marginTop: 4, paddingTop: 5, gap: 5 },
  tipLeaf: { width: 50, height: 55, resizeMode: 'contain' }, tipText: { flex: 1, color: '#334968', fontSize: 14, fontWeight: '700' },
  tipLeafCompact: { width: 34, height: 36 }, tipTextCompact: { fontSize: 11 },
  footnote: { position: 'absolute', right: 10, bottom: 2, color: '#A5B3C5', fontSize: 11, fontWeight: '600' },
  screenBody: { flex: 1, paddingVertical: 4, paddingBottom: 12, position: 'relative' },
  lobbyColumns: { flex: 1, flexDirection: 'row', gap: 14 }, lobbyHero: { flex: 1.78, alignItems: 'center', justifyContent: 'space-around', overflow: 'hidden' }, lobbyTitle: { fontSize: 31, textAlign: 'center', marginTop: 8 }, lobbySubtitle: { color: '#7689A7', fontSize: 17, textAlign: 'center', fontWeight: '700' },
  lobbyGarden: { position: 'absolute', left: 0, right: 0, bottom: 46, width: '100%', height: '68%', opacity: 0.95 }, lobbyLeafAvatar: { width: 92, height: 92, borderRadius: 48 },
  lobbyRight: { flex: 0.94, gap: 11 }, pickCard: { flex: 1.1, justifyContent: 'space-around' }, friendsCard: { flex: 0.9, justifyContent: 'space-around' }, cardHeading: { color: '#142550', fontSize: 19, fontWeight: '900', marginBottom: 5 },
  kidRow: { flexDirection: 'row', gap: 10, marginVertical: 8 }, kidCard: { flex: 1, minHeight: 110, borderWidth: 2, borderColor: '#E7F0F8', borderRadius: 20, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFF', position: 'relative' }, kidCardSelected: { borderColor: '#1685F8', backgroundColor: '#F0F8FF' }, kidImage: { width: 74, height: 74 }, selectedCheck: { position: 'absolute', right: 8, top: 6, backgroundColor: '#1685F8', color: '#FFF', borderRadius: 20, overflow: 'hidden', width: 24, height: 24, textAlign: 'center', fontWeight: '900' }, kidName: { color: '#142550', fontSize: 17, fontWeight: '900' },
  friendRow: { flexDirection: 'row', justifyContent: 'space-around', marginVertical: 7 }, friendItem: { alignItems: 'center', gap: 3 }, friendImage: { width: 58, height: 58 }, friendName: { color: '#182F5D', fontSize: 14, fontWeight: '800' }, readyButton: { width: '45%', alignSelf: 'center', minHeight: 50 },
  lobbyHelp: { marginTop: 4 }, centerText: { textAlign: 'center' },
  drawingArea: { flex: 1, flexDirection: 'row', gap: 12 }, canvasCard: { flex: 1, padding: 12 }, canvasCardHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 7, marginBottom: 6 }, canvasLabel: { color: '#142550', fontSize: 17, fontWeight: '900' }, canvas: { flex: 1, width: '100%', minHeight: 50, backgroundColor: '#FFF', borderRadius: 20, borderWidth: 1.5, borderColor: '#ECF2F8', overflow: 'hidden', position: 'relative' }, canvasLarge: { flex: 1 }, canvasArtwork: { ...StyleSheet.absoluteFillObject }, canvasArtworkImage: { width: '100%', height: '100%' }, ink: { position: 'absolute' },
  drawingHelp: { width: '20%', alignItems: 'center', justifyContent: 'space-around', padding: 12 }, speechBubble: { paddingVertical: 15, paddingHorizontal: 14, borderRadius: 28, backgroundColor: '#DDF0FF', alignItems: 'center', justifyContent: 'center' }, speechText: { color: '#132653', fontSize: 16, fontWeight: '900', textAlign: 'center' }, largeMascot: { width: 115, height: 140, resizeMode: 'contain' }, drawToolbar: { minHeight: 64, marginTop: 9, paddingHorizontal: 7, paddingVertical: 6, gap: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around', backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E6F0F8', borderRadius: 20 }, drawToolbarCompact: { minHeight: 48, marginTop: 5, paddingHorizontal: 4, paddingVertical: 3, gap: 4 }, toolAction: { minWidth: 76, minHeight: 49, paddingHorizontal: 7 }, toolActionCompact: { minWidth: 54, minHeight: 34, paddingHorizontal: 2 }, toolActionSelected: { backgroundColor: '#087FF2', borderColor: '#087FF2' }, colorDot: { width: 35, height: 35, borderRadius: 20, borderWidth: 2, borderColor: '#FFF' }, colorDotCompact: { width: 24, height: 24 }, colorDotSelected: { borderColor: '#162C5A', transform: [{ scale: 1.13 }] }, toolbarDivider: { width: 1, height: 38, backgroundColor: '#E0EAF4', marginHorizontal: 2 }, toolbarDividerCompact: { height: 27, marginHorizontal: 0 }, brushChoice: { width: 39, height: 39, borderRadius: 22, backgroundColor: '#F1F7FD', alignItems: 'center', justifyContent: 'center' }, brushChoiceCompact: { width: 28, height: 28 }, brushSelected: { borderWidth: 2, borderColor: '#1685F8' }, smallToolAction: { minWidth: 79, minHeight: 48, paddingHorizontal: 7 }, smallToolActionCompact: { minWidth: 62, minHeight: 34, paddingHorizontal: 2 },
  advancedTools: { width: '12%', gap: 6, justifyContent: 'space-around' }, advancedTool: { minHeight: 54, paddingHorizontal: 5 }, ageBadge: { position: 'absolute', zIndex: 4, right: 18, top: '10%', backgroundColor: '#E6F4FF', padding: 7, borderRadius: 16 }, ageBadgeText: { color: '#0879E9', fontSize: 11, fontWeight: '900' }, advancedPanel: { width: '23%', padding: 11, justifyContent: 'space-around' }, expandedTools: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#E4F3FF', borderRadius: 17, padding: 8 }, expandedIcon: { fontSize: 29 }, expandedTitle: { color: '#0879E9', fontSize: 14, fontWeight: '900' }, expandedSub: { color: '#547498', fontSize: 11, fontWeight: '700' }, layerRow: { flexDirection: 'row', alignItems: 'center', gap: 6, padding: 6, minHeight: 52, borderRadius: 14, backgroundColor: '#F6F9FC' }, layerSelected: { borderWidth: 1.5, borderColor: '#1685F8', backgroundColor: '#EEF7FF' }, layerAvatar: { width: 38, height: 38 }, layerIcon: { width: 38, textAlign: 'center', fontSize: 25 }, layerEye: { color: '#1685F8', fontSize: 21, fontWeight: '900' }, advancedMascot: { width: 76, height: 76, alignSelf: 'center' }, suggestionOverlay: { ...StyleSheet.absoluteFillObject, borderWidth: 2, borderColor: '#9AC8F4', borderStyle: 'dashed', alignItems: 'center', justifyContent: 'center' }, suggestionOverlayText: { color: '#1685F8', fontWeight: '900', backgroundColor: '#E7F4FF', padding: 8, borderRadius: 12 },
  screenTitle: { textAlign: 'center', fontSize: 28, marginVertical: 4 }, ideaColumns: { flex: 1, flexDirection: 'row', gap: 12 }, ideaCard: { flex: 1, padding: 14 }, titleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 5 }, ideaArt: { flex: 1, width: '100%', borderRadius: 19, marginVertical: 7 }, hiddenSuggestion: { alignItems: 'center', justifyContent: 'center', backgroundColor: '#F5F9FD' }, caption: { textAlign: 'center', color: '#657C9D', fontSize: 14, fontWeight: '700' }, ideaActions: { flexDirection: 'row', gap: 9, marginTop: 8 }, ideaAction: { flex: 1, minHeight: 48, paddingHorizontal: 5 }, hiddenHint: { color: '#55708F', textAlign: 'center', marginTop: 4 },
  reviewColumns: { flex: 1, flexDirection: 'row', gap: 13, minWidth: 0 }, reviewCanvas: { flex: 1.75, minWidth: 0 }, reviewStatus: { flex: 0.82, minWidth: 0, alignItems: 'center', justifyContent: 'space-around' }, waitArt: { width: 160, height: 150, borderRadius: 100, backgroundColor: '#EAF5FE', alignItems: 'center', justifyContent: 'center', position: 'relative' }, waitArtCompact: { width: 76, height: 72 }, waitArtImage: { width: '78%', height: '78%' }, waitClock: { position: 'absolute', right: 18, bottom: 7, color: '#FFBF16', fontSize: 45, fontWeight: '900' }, reviewAvatar: { width: 94, height: 94 }, reviewAvatarCompact: { width: 46, height: 46 }, reviewHeadingCompact: { fontSize: 14, textAlign: 'center', marginBottom: 0 }, reviewTextCompact: { fontSize: 11 }, reviewSpeech: { width: '100%', paddingHorizontal: 9, paddingVertical: 9 }, reviewSpeechCompact: { paddingHorizontal: 6, paddingVertical: 5 },
  groupColumns: { flex: 1, flexDirection: 'row', gap: 13, minWidth: 0 }, groupBoard: { flex: 1.72, minWidth: 0 }, sharedCanvas: { flex: 1, borderRadius: 22, overflow: 'hidden', position: 'relative', backgroundColor: '#FFF' }, sharedArtwork: { ...StyleSheet.absoluteFillObject, width: '100%', height: '100%' }, memberZone: { position: 'absolute', top: 17, bottom: 15, width: '32%', borderWidth: 2, borderStyle: 'dashed', borderRadius: 22 }, zoneMay: { left: 12, borderColor: '#1685F8' }, zoneLa: { left: '34%', borderColor: '#FF6682' }, zoneNang: { right: 12, borderColor: '#FFC32E' }, zoneLabel: { alignSelf: 'center', top: -2, paddingHorizontal: 13, paddingVertical: 7, overflow: 'hidden', borderRadius: 15, color: '#0877DF', backgroundColor: '#E8F4FF', fontWeight: '900' }, zoneLabelPink: { color: '#E34F6B', backgroundColor: '#FFF0F2' }, zoneLabelYellow: { color: '#B77800', backgroundColor: '#FFF5D8' },
  groupPanel: { flex: 0.74, minWidth: 0, justifyContent: 'space-around' }, memberCard: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 8, borderRadius: 19, backgroundColor: '#F4F8FC' }, memberBlue: { backgroundColor: '#E8F5FF' }, memberYellow: { backgroundColor: '#FFF9E9' }, memberAvatar: { width: 52, height: 52 }, memberCopy: { flex: 1 }, memberName: { color: '#152955', fontSize: 17, fontWeight: '900' }, memberStatus: { color: '#617895', fontSize: 13, fontWeight: '700' }, memberIcon: { color: '#1685F8', fontSize: 24, fontWeight: '900' }, mascotHint: { flexDirection: 'row', alignItems: 'center', gap: 7 }, mascotSmall: { width: 60, height: 65 }, buttonRow: { flexDirection: 'row', gap: 8, alignItems: 'center' }, flexAction: { flex: 1, paddingHorizontal: 5, minHeight: 45 },
  galleryHeadingRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 7 }, galleryTitle: { fontSize: 27 }, tabSwitch: { flexDirection: 'row', backgroundColor: '#FFF', borderRadius: 25, padding: 4 }, tabButton: { paddingVertical: 9, paddingHorizontal: 14, borderRadius: 21 }, tabSelected: { backgroundColor: '#087FF2' }, tabText: { color: '#59708F', fontWeight: '800' }, tabTextSelected: { color: '#FFF' }, galleryColumns: { flex: 1, flexDirection: 'row', gap: 13, minWidth: 0 }, galleryMain: { flex: 1.75, minWidth: 0, padding: 13 }, galleryImage: { flex: 1, width: '100%', borderRadius: 19 }, contributors: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingTop: 7 }, contributor: { alignItems: 'center' }, contributorAvatar: { width: 45, height: 45 }, contributorDivider: { width: 1, height: 44, backgroundColor: '#DCE7F1' }, contributorText: { flex: 1, color: '#203A66', fontWeight: '800', fontSize: 14 }, gallerySide: { flex: 0.75, minWidth: 0, alignItems: 'stretch', justifyContent: 'space-around' }, galleryMascot: { width: 118, height: 125, alignSelf: 'center' },
  learnHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, paddingHorizontal: 8 }, learnColumns: { flex: 1, flexDirection: 'row', gap: 12 }, learnLeft: { flex: 1.72 }, videoCard: { flex: 1, padding: 8, position: 'relative', overflow: 'hidden' }, knowledgeVideo: { width: '100%', height: '100%', borderRadius: 17 }, videoPlay: { position: 'absolute', top: '40%', left: '44%', width: 58, height: 58, borderRadius: 30, backgroundColor: '#1C2D44CC', alignItems: 'center', justifyContent: 'center' }, videoPlayGlyph: { color: '#FFF', fontSize: 25, fontWeight: '900' }, videoScrub: { position: 'absolute', left: 12, right: 12, bottom: 12, height: 50, paddingHorizontal: 14, borderRadius: 23, backgroundColor: '#123A3688', flexDirection: 'row', alignItems: 'center', gap: 14 }, videoControlGlyph: { color: '#FFF', fontSize: 19, fontWeight: '900' }, progressTrack: { flex: 1, height: 9, borderRadius: 8, backgroundColor: '#D4E8D0', position: 'relative', justifyContent: 'center' }, progressFill: { height: 9, backgroundColor: '#1685F8', borderRadius: 8 }, progressKnob: { position: 'absolute', width: 16, height: 16, borderRadius: 9, backgroundColor: '#FFF', borderWidth: 2, borderColor: '#1685F8', marginLeft: -8 }, subtitlePill: { alignSelf: 'center', marginTop: 7, padding: 10, backgroundColor: '#E5F3FF', borderRadius: 22, minWidth: '65%', alignItems: 'center' }, captionStrong: { color: '#122B59', fontSize: 16, fontWeight: '900' }, lessonPanel: { flex: 1, justifyContent: 'space-around' }, lessonTitleBubble: { backgroundColor: '#E4F3FF', borderRadius: 30, padding: 13, alignItems: 'center' }, lessonName: { color: '#087FF2', fontSize: 23 }, lessonPoint: { flexDirection: 'row', alignItems: 'center', gap: 7 }, lessonThumbnail: { width: 60, height: 58, borderRadius: 30 }, numberBadge: { width: 31, height: 31, borderRadius: 18, overflow: 'hidden', backgroundColor: '#31C978', color: '#FFF', textAlign: 'center', textAlignVertical: 'center', fontWeight: '900', fontSize: 18 }, lessonText: { flex: 1, color: '#1B315E', fontSize: 14, fontWeight: '800' }, lessonMascot: { width: 82, height: 70, alignSelf: 'center' },
  learnBottom: { height: '18%', minHeight: 58, flexDirection: 'row', alignItems: 'center', gap: 12, paddingTop: 4 },
  learnHelpActions: { width: '62%', flexDirection: 'row', gap: 10 }, learnHelper: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 }, learnHelperImage: { width: 62, height: 66, resizeMode: 'contain' }, learnSpeech: { flex: 1, paddingVertical: 9, paddingHorizontal: 10, borderRadius: 20, backgroundColor: '#DDF0FF' }, learnSpeechText: { color: '#132653', fontSize: 14, fontWeight: '900', textAlign: 'center' },
  videoHeader: { minHeight: 40, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }, videoHeaderLabel: { color: '#142550', fontWeight: '900', flex: 1 }, videoWaitColumns: { flex: 1, flexDirection: 'row', gap: 14 }, videoStory: { flex: 1, justifyContent: 'space-around' }, videoStoryArt: { width: '100%', flex: 1, borderRadius: 17 }, storyLabel: { backgroundColor: '#EAF5FC', borderRadius: 22, padding: 10, marginVertical: 8 }, storyLabelText: { color: '#183462', fontWeight: '900' }, storyPrompt: { flexDirection: 'row', alignItems: 'center', gap: 8, padding: 8, backgroundColor: '#EEF7FF', borderRadius: 23 }, storyAvatar: { width: 65, height: 65 }, videoWaitCard: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 23 }, clapper: { width: '70%', height: '42%' }, videoWaitTitle: { textAlign: 'center', fontSize: 27, marginVertical: 9 }, creatingPill: { flexDirection: 'row', alignItems: 'center', gap: 15, padding: 14, marginVertical: 12, backgroundColor: '#EEF7FE', borderRadius: 28 }, loadingDots: { flexDirection: 'row', gap: 4 }, dotBlue: { color: '#1685F8' }, dotMid: { color: '#69B5FA' }, dotPale: { color: '#B7DDFB' }, creatingText: { color: '#1E3966', fontWeight: '900', fontSize: 17 },
  offlineColumns: { flex: 1, flexDirection: 'row', gap: 13 }, offlineMain: { flex: 1.72, justifyContent: 'space-around' }, activityAside: { width: '28%', alignItems: 'center', justifyContent: 'space-around' }, offlineEyebrow: { color: '#183361', fontWeight: '900', fontSize: 15 }, offlineTitle: { fontSize: 31, marginTop: 2 }, activityTitle: { color: '#182E59', fontSize: 22, fontWeight: '900' }, stepsRow: { flexDirection: 'row', gap: 8, justifyContent: 'space-around', alignItems: 'center' }, stepItem: { flex: 1, alignItems: 'center', position: 'relative' }, stepImage: { width: '100%', height: 115 }, stepCaption: { flexDirection: 'row', gap: 7, alignItems: 'center' }, stepNumber: { width: 30, height: 30, borderRadius: 18, backgroundColor: '#31C978', color: '#FFF', fontWeight: '900', fontSize: 18, textAlign: 'center', textAlignVertical: 'center', overflow: 'hidden' }, stepText: { color: '#132955', fontSize: 15, fontWeight: '900' }, stepArrow: { position: 'absolute', right: -12, top: '43%', color: '#8CC5F4', fontSize: 27 }, materialsBox: { minHeight: 76, borderRadius: 22, backgroundColor: '#EDF6FF', flexDirection: 'row', alignItems: 'center', gap: 8, padding: 10 }, materialItem: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFF', borderRadius: 17, minHeight: 62 }, materialIcon: { fontSize: 23 }, materialLabel: { color: '#24395E', fontWeight: '800', fontSize: 13 }, activityMascot: { width: 135, height: 155 }, safetyBox: { backgroundColor: '#FFF6DE', borderRadius: 18, padding: 12, gap: 10 }, safetyText: { color: '#41334A', fontSize: 15, fontWeight: '900' }, bottomActions: { flexDirection: 'row', gap: 10, alignItems: 'center', justifyContent: 'center', paddingTop: 6 }, helpButton: { width: '27%' },
  feelingColumns: { flex: 1, flexDirection: 'row', gap: 13 }, feelingArtCard: { width: '34%', padding: 12 }, sectionBar: { backgroundColor: '#E8F5FF', borderRadius: 18, padding: 10 }, sectionBarText: { color: '#183260', fontWeight: '900', fontSize: 16 }, feelingArt: { flex: 1, width: '100%', borderRadius: 18, marginTop: 7 }, feelingForm: { flex: 1, justifyContent: 'space-around' }, feelingTitle: { textAlign: 'center', fontSize: 28 }, moodRow: { flexDirection: 'row', gap: 10 }, moodCard: { flex: 1, minHeight: 170, borderWidth: 2, borderColor: '#E6EEF6', borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFF', padding: 9, position: 'relative' }, moodSelected: { borderColor: '#1685F8', backgroundColor: '#EFF8FF' }, moodImage: { width: 78, height: 78 }, moodFace: { position: 'absolute', top: 24, color: '#17305C', fontSize: 25 }, moodLabel: { textAlign: 'center', color: '#152A55', fontSize: 16, fontWeight: '900' }, moodCheck: { position: 'absolute', top: 7, right: 8, borderRadius: 15, overflow: 'hidden', color: '#FFF', backgroundColor: '#1685F8', paddingHorizontal: 7, fontWeight: '900' }, noteBox: { padding: 9, backgroundColor: '#F3F9FE', borderRadius: 19 }, noteTitle: { color: '#1C315D', fontSize: 15, fontWeight: '800' }, noteInput: { minHeight: 58, maxHeight: 90, borderRadius: 15, borderWidth: 1, borderStyle: 'dashed', borderColor: '#C9E0F5', backgroundColor: '#FFF', color: '#17305E', padding: 10, textAlignVertical: 'top', marginTop: 7 },
  reconnectMascotWrap: { position: 'absolute', left: 2, bottom: 22, width: 105, height: 118 }, reconnectMascotCompact: { left: 1, bottom: 35, width: 58, height: 66 }, reconnectMascotImage: { width: '100%', height: '100%' },
  reconnectButtonRow: { marginLeft: 105 },
  reconnectHeader: { alignItems: 'center', paddingVertical: 4 }, cloudSlash: { color: '#6DB8F6', fontSize: 72, lineHeight: 78 }, reconnectTitle: { fontSize: 29 }, savedColumns: { flex: 1, flexDirection: 'row', gap: 13 }, savedCard: { flex: 1, padding: 13 }, savedHeading: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 7 }, savedIcon: { color: '#1387EC', fontSize: 36 }, pendingIcon: { color: '#D49926', fontSize: 36 }, savedArtwork: { width: '100%', flex: 1, borderRadius: 18 }, retryButton: { width: '40%', alignSelf: 'center', marginTop: 8 }, waitingNetwork: { textAlign: 'center', color: '#8494AB', fontWeight: '800', paddingVertical: 4 },
})
