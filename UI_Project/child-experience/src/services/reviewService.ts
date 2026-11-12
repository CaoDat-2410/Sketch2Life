export async function checkGateAApproval(_artworkId: string): Promise<{ approved: boolean; note?: string }> {
  return { approved: true, note: 'Chiếc lá vẽ rất sáng tạo' }
}
