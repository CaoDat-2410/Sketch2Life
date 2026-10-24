import { DrawScreen } from '../screens/DrawScreen'
import { fireEvent, render } from '@testing-library/react-native'

describe('DrawScreen', () => {
  it('routes the child to ideas, group garden and teacher review', async () => {
    const onIdeas = jest.fn()
    const onReview = jest.fn()
    const onGroup = jest.fn()
    const { getByText } = await render(<DrawScreen onIdeas={onIdeas} onReview={onReview} onGroup={onGroup} />)

    await fireEvent.press(getByText('💡 Gợi ý'))
    await fireEvent.press(getByText('🍃 Vườn nhóm'))
    await fireEvent.press(getByText('Gửi cô duyệt ✓'))

    expect(onIdeas).toHaveBeenCalledTimes(1)
    expect(onGroup).toHaveBeenCalledTimes(1)
    expect(onReview).toHaveBeenCalledTimes(1)
  })
})
