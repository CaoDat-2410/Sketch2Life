import { FeelingScreen } from '../screens/FeelingScreen'
import { fireEvent, render } from '@testing-library/react-native'

describe('FeelingScreen', () => {
  it('submits the feeling selected by the child', async () => {
    const onSubmit = jest.fn()
    const { getByText } = await render(<FeelingScreen onSubmit={onSubmit} />)

    await fireEvent.press(getByText('Tự hào'))
    await fireEvent.press(getByText('Gửi cảm nhận cho cô/thầy ✓'))

    expect(onSubmit).toHaveBeenCalledWith('Tự hào')
  })
})
