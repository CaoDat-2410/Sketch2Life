export async function postFeeling(childName: string, feeling: string) {
  return { saved: true, child: childName, feeling }
}
