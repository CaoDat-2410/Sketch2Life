# Demo case 02: xe đạp và an toàn khi đi đường

Đây là bộ input thay thế cho backend workflow demo. Case này khác case 01
(bướm/hoa) và dùng một semantic scene khác để kiểm tra image understanding,
ASR, fusion, age adaptation và activity recommendation trên cùng một CLI flow.

- `input-image-framing-safe.png`: tranh vẽ trẻ em về một chiếc xe đạp đỏ, mũ
  bảo hiểm và đường đi, có khoảng trắng an toàn quanh nội dung.
- `input-image.png`: candidate đầu tiên được giữ lại để audit provenance nhưng
  không được dùng để chạy workflow vì policy phát hiện `IMAGE_FRAMING_RISK`.
- `narration.wav`: lời kể tiếng Việt tương ứng với scene.

Narration source text:

> Chiếc xe đạp màu đỏ đứng bên đường. Chúng mình đội mũ bảo hiểm trước khi đi
> nhé.

Các file là pre-generated test inputs, không phải model-output fixtures. Có
thể thay từng file bằng đường dẫn khác qua CLI mà không cần sửa code.

Chỉ `input-image-framing-safe.png` là input chính thức của case 02.

## Chạy trên Lightning Studio

Từ root repository, sau khi đã export model directories:

```bash
python -m sketch2life.workflow_demo \
  --image ./features/FEAT-023-catalog-contract-hardening/test-assets/demo-case-02/input-image-framing-safe.png \
  --narration-audio ./features/FEAT-023-catalog-contract-hardening/test-assets/demo-case-02/narration.wav \
  --age-mode all \
  --demo-autopilot \
  --emit-debug-evidence \
  --output ./runtime-output/workflow-result-demo-case-02.json
```

Lệnh trên phải gọi real ASR/VLM/fusion và catalog matcher. Không được nạp
recommendation, transcript hoặc vision result dựng sẵn từ thư mục test asset.
