import {useEffect, useRef} from 'react';
import {
  ActivityIndicator,
  BackHandler,
  Pressable,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import WebView, {type WebViewNavigation} from 'react-native-webview';

const PARENT_UI_BUNDLE_URL = 'file:///android_asset/parent-ui/index.html?preview=home';
const ALLOWED_BUNDLE_PREFIX = 'file:///android_asset/parent-ui/';

export function ParentWebPreview(): React.JSX.Element {
  const webViewRef = useRef<WebView<object>>(null);
  const canGoBackRef = useRef(false);

  useEffect(() => {
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => {
      if (!canGoBackRef.current) return false;
      webViewRef.current?.goBack();
      return true;
    });
    return () => subscription.remove();
  }, []);

  const updateNavigationState = (navigation: WebViewNavigation): void => {
    canGoBackRef.current = navigation.canGoBack;
  };

  return (
    <View style={styles.root}>
      <StatusBar hidden />
      <WebView<object>
        ref={webViewRef}
        source={{uri: PARENT_UI_BUNDLE_URL}}
        style={styles.webView}
        originWhitelist={['file://*']}
        allowFileAccess
        javaScriptEnabled
        domStorageEnabled
        mixedContentMode="never"
        setSupportMultipleWindows={false}
        startInLoadingState
        renderLoading={() => (
          <View style={styles.state}>
            <ActivityIndicator color="#286653" size="large" />
            <Text style={styles.stateText}>Đang mở không gian gia đình…</Text>
          </View>
        )}
        renderError={() => (
          <View style={styles.state}>
            <Text style={styles.errorTitle}>Chưa mở được giao diện Parent</Text>
            <Text style={styles.stateText}>Thử tải lại bản xem trước trong ứng dụng.</Text>
            <Pressable accessibilityRole="button" onPress={() => webViewRef.current?.reload()} style={styles.retryButton}>
              <Text style={styles.retryText}>Tải lại</Text>
            </Pressable>
          </View>
        )}
        onNavigationStateChange={updateNavigationState}
        onShouldStartLoadWithRequest={({url}) => url.startsWith(ALLOWED_BUNDLE_PREFIX)}
        onRenderProcessGone={() => webViewRef.current?.reload()}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: {flex: 1, backgroundColor: '#fbf7ea'},
  webView: {flex: 1, backgroundColor: '#fbf7ea'},
  state: {flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12, padding: 28, backgroundColor: '#fbf7ea'},
  stateText: {color: '#626b5b', fontSize: 14, textAlign: 'center'},
  errorTitle: {color: '#30352c', fontSize: 18, fontWeight: '800', textAlign: 'center'},
  retryButton: {marginTop: 8, paddingHorizontal: 20, paddingVertical: 12, borderRadius: 20, backgroundColor: '#286653'},
  retryText: {color: '#fffdf6', fontSize: 14, fontWeight: '800'},
});
