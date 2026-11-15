// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { TeacherSvgIllustrationDraftPage } from '../pages/TeacherSvgIllustrationDraftPage'
import { svgIllustrationService } from '../services/svgIllustrationService'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('Teacher SVG illustration draft page', () => {
  it('waits for a real user action and renders the service response as structured SVG', async () => {
    const generate = vi.spyOn(svgIllustrationService, 'generateDraft').mockResolvedValue({
      contract: 'TeacherSvgIllustrationDraftV1',
      request_id: 'request-1',
      modal_call_id: 'fc-call-1',
      status: 'DRAFT',
      review_required: true,
      persisted: false,
      model: { id: 'Qwen/Qwen3.5-9B', revision: 'pinned-revision' },
      title_vi: 'Minh họa chủ đề',
      alt_text_vi: 'Một minh họa vector được tạo cho chủ đề.',
      document: {
        schema_version: 'SvgDocumentV1',
        view_box: '0 0 512 512',
        paths: [
          { path_id: 'p1', d: 'M 1 1 L 10 10 Z', fill: '#A06038', stroke: '#392719', stroke_width: 4 },
          { path_id: 'p2', d: 'M 2 2 L 20 20 Z', fill: '#A06038', stroke: '#392719', stroke_width: 4 },
          { path_id: 'p3', d: 'M 3 3 L 30 30 Z', fill: '#A06038', stroke: '#392719', stroke_width: 4 },
          { path_id: 'p4', d: 'M 4 4 L 40 40 Z', fill: '#A06038', stroke: '#392719', stroke_width: 4 },
        ],
      },
      document_sha256: 'a'.repeat(64),
      path_count: 4,
    })

    render(<TeacherSvgIllustrationDraftPage />)
    expect(generate).not.toHaveBeenCalled()
    fireEvent.change(screen.getByLabelText('Chủ đề'), { target: { value: 'con hươu' } })
    fireEvent.change(screen.getByLabelText('Tuổi mục tiêu theo tháng'), { target: { value: '60' } })
    fireEvent.click(screen.getByRole('button', { name: 'Tạo bản nháp SVG' }))

    expect(await screen.findByRole('img', { name: 'Một minh họa vector được tạo cho chủ đề.' })).toBeTruthy()
    expect(screen.getAllByTestId('svg-document-preview')[0].querySelectorAll('path')).toHaveLength(4)
    expect(screen.getByText(/chưa được duyệt/)).toBeTruthy()
    expect(generate).toHaveBeenCalledWith({
      topic: 'con hươu',
      target_age_months: 60,
      visual_style: 'warm_storybook',
    })
  })
})
