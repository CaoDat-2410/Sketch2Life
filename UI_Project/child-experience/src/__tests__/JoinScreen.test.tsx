import { JoinScreen } from '../screens/JoinScreen'
import { fireEvent, render } from '@testing-library/react-native'

describe('JoinScreen', () => {
  it('submits the shared six-digit room code without choosing a child identity', async () => {
    const onJoin = jest.fn()
    const { getAllByDisplayValue, getByText } = await render(<JoinScreen onJoin={onJoin} />)

    for (const [index, input] of getAllByDisplayValue('').entries()) {
      await fireEvent.changeText(input, String(index + 1))
    }
    await fireEvent.press(getByText('Gửi yêu cầu tham gia ➜'))

    expect(onJoin).toHaveBeenCalledWith('123456')
  })
})
