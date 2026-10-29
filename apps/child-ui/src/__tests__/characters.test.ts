import { CHARACTERS } from '../constants/characters'

describe('characters constants', () => {
  it('defines May and La profiles', () => {
    expect(CHARACTERS.May.name).toBe('Mây')
    expect(CHARACTERS.La.name).toBe('Lá')
  })
})
