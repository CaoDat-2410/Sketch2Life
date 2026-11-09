import React from "react";

export type SketchTheme = "butterfly" | "caterpillar" | "tree" | "rain" | "fish" | "flower";

export interface ProgressiveStepMeta {
  step: number;
  title: string;
  instruction: string;
}

export function detectSketchTheme(text: string): SketchTheme {
  const lower = text.toLowerCase();
  if (lower.includes("sâu") || lower.includes("kén")) return "caterpillar";
  if (lower.includes("cây") || lower.includes("tán lá") || lower.includes("rễ")) return "tree";
  if (lower.includes("mưa") || lower.includes("mây") || lower.includes("nước")) return "rain";
  if (lower.includes("cá") || lower.includes("đại dương") || lower.includes("biển")) return "fish";
  if (lower.includes("hoa") || lower.includes("hướng dương") || lower.includes("nắng")) return "flower";
  return "butterfly";
}

export function getStepsForTheme(theme: SketchTheme): ProgressiveStepMeta[] {
  switch (theme) {
    case "caterpillar":
      return [
        { step: 1, title: "Bước 1: Vẽ chiếc lá xanh lớn", instruction: "Cô hướng dẫn các bé vẽ đường sống lá cong nhẹ ở giữa trang giấy và viền lá bầu dục bao quanh." },
        { step: 2, title: "Bước 2: Vẽ đầu và thân chú sâu nhỏ", instruction: "Vẽ 4 hình tròn nối tiếp nhau nằm trên chiếc lá để tạo thân chú sâu mũm mĩm." },
        { step: 3, title: "Bước 3: Thêm râu nhỏ, mắt cười và chân", instruction: "Chấm hai mắt tròn, miệng cười tươi, hai chiếc râu xinh và những chiếc chân nhỏ bám trên lá." },
        { step: 4, title: "Bước 4: Vẽ gân lá & trang trí màu sắc", instruction: "Kẻ các nét gân lá hai bên và khuyến khích các bé phối màu xanh non, vàng cam thật sinh động." },
      ];
    case "tree":
      return [
        { step: 1, title: "Bước 1: Vẽ mặt đất và thân cây vững chãi", instruction: "Vẽ đường mặt cỏ ngang phía dưới và hai đường thẳng hơi loe ở gốc làm thân cây." },
        { step: 2, title: "Bước 2: Thêm hai nhánh cành vươn cao", instruction: "Từ phần trên thân cây, vẽ hai nhánh chữ V vươn đều sang trái và sang phải." },
        { step: 3, title: "Bước 3: Vẽ tán lá tròn bồng bềnh", instruction: "Dùng các nét cong nối tiếp nhau bao quanh cành cây để tạo vòm tán lá che mát sân trường." },
        { step: 4, title: "Bước 4: Thêm quả chín, hoa cỏ dưới gốc cây", instruction: "Vẽ thêm vài quả tròn trên tán lá, khóm cỏ nhỏ dưới gốc cây rồi cùng tô màu." },
      ];
    case "rain":
      return [
        { step: 1, title: "Bước 1: Vẽ đám mây lớn bồng bềnh", instruction: "Vẽ các đường cong tròn nối nhau ở nửa trên trang giấy tạo thành đám mây mùa xuân." },
        { step: 2, title: "Bước 2: Thêm đám mây nhỏ và khuôn mặt vui vẻ", instruction: "Vẽ thêm một đám mây bạn bè bên cạnh cùng đôi mắt cười hiền hòa." },
        { step: 3, title: "Bước 3: Vẽ những hạt mưa rơi xiên đều", instruction: "Kéo các nét ngắn xiên nhẹ hoặc hình giọt nước rơi từ đám mây xuống mặt đất." },
        { step: 4, title: "Bước 4: Thêm mầm cây và bông hoa đón mưa", instruction: "Phía dưới trang giấy, vẽ mầm lá non và bông hoa nhỏ đang vươn lên đón hạt mưa mát lành." },
      ];
    case "fish":
      return [
        { step: 1, title: "Bước 1: Vẽ thân cá hình bầu dục", instruction: "Vẽ một hình bầu dục nằm ngang ngay chính giữa bảng giấy làm thân chú cá nhỏ." },
        { step: 2, title: "Bước 2: Thêm chiếc đuôi xòe và vây lưng", instruction: "Ở phía sau thân cá, vẽ hình tam giác cong làm đuôi xòe và thêm vây trên lưng, vây bụng." },
        { step: 3, title: "Bước 3: Vẽ mắt tròn, miệng cười và vảy cá", instruction: "Vẽ đường cong làm mang cá, mắt tròn xoe và các nét cong nhỏ xếp đều trên thân cá." },
        { step: 4, title: "Bước 4: Thêm bong bóng nước và rong biển", instruction: "Vẽ các vòng tròn bong bóng bay lên cùng nhành rong biển uốn lượn dưới đáy đại dương." },
      ];
    case "flower":
      return [
        { step: 1, title: "Bước 1: Vẽ nhụy hoa hình tròn ở giữa", instruction: "Đặt bút vẽ một hình tròn vừa phải ở phần trên trang giấy làm nhụy bông hoa." },
        { step: 2, title: "Bước 2: Xếp đều các cánh hoa xung quanh", instruction: "Vẽ từng cánh hoa cong tròn bao đều quanh nhụy hoa như những tia nắng ấm áp." },
        { step: 3, title: "Bước 3: Kéo cành hoa và đôi lá đối xứng", instruction: "Kẻ hai nét song song từ bông hoa xuống đất làm thân cành, gắn thêm hai chiếc lá hai bên." },
        { step: 4, title: "Bước 4: Thêm ông mặt trời & tô màu rực rỡ", instruction: "Vẽ ông mặt trời ở góc cao và hướng dẫn trẻ chọn màu vàng, cam, xanh lá tô kín bức tranh." },
      ];
    default:
      return [
        { step: 1, title: "Bước 1: Vẽ nét khung đầu và thân bướm", instruction: "Vẽ một hình tròn nhỏ làm đầu và hình bầu dục thon dài bên dưới làm thân chú bướm ở giữa giấy." },
        { step: 2, title: "Bước 2: Vẽ đôi cánh trên lớn đối xứng", instruction: "Từ hai bên thân bướm, kéo hai đường cong rộng đối xứng sang trái và sang phải làm đôi cánh trên." },
        { step: 3, title: "Bước 3: Thêm đôi cánh dưới và hai chiếc râu cong", instruction: "Vẽ tiếp hai cánh dưới tròn trịa và hai chiếc râu uốn cong mềm mại trên đầu chú bướm." },
        { step: 4, title: "Bước 4: Trang trí họa tiết cánh & tô màu sáp", instruction: "Thêm các vòng tròn trang trí đối xứng trên cánh bướm và để các bé sáng tạo màu sáp yêu thích." },
      ];
  }
}

export function ProgressiveWhiteboardSvg({
  theme,
  stepNum,
}: {
  theme: SketchTheme;
  stepNum: number;
}) {
  return (
    <svg
      viewBox="0 0 640 360"
      width="100%"
      height="100%"
      role="img"
      aria-label={`Bảng vẽ hướng dẫn từng bước · Bước ${stepNum}`}
      style={{ display: "block", background: "#FFFFFF" }}
    >
      {/* Subtle classroom composition guide lines */}
      <line x1="320" y1="24" x2="320" y2="336" stroke="#E2E8F0" strokeWidth="1.5" strokeDasharray="6 6" />
      <line x1="48" y1="180" x2="592" y2="180" stroke="#E2E8F0" strokeWidth="1.5" strokeDasharray="6 6" />

      <g fill="none" stroke="#0F172A" strokeWidth="5.5" strokeLinecap="round" strokeLinejoin="round">
        {theme === "butterfly" && (
          <>
            <circle cx="320" cy="106" r="24" />
            <ellipse cx="320" cy="196" rx="18" ry="66" />
            {stepNum >= 2 && (
              <>
                <path d="M302 150 C 190 66, 138 170, 302 206" />
                <path d="M338 150 C 450 66, 502 170, 338 206" />
              </>
            )}
            {stepNum >= 3 && (
              <>
                <path d="M302 206 C 188 220, 210 310, 306 250" />
                <path d="M338 206 C 452 220, 430 310, 334 250" />
                <path d="M310 84 C 294 48, 268 48, 264 62" />
                <path d="M330 84 C 346 48, 372 48, 376 62" />
                <path d="M312 108 Q 320 116 328 108" strokeWidth="4" />
              </>
            )}
            {stepNum >= 4 && (
              <>
                <circle cx="238" cy="154" r="18" stroke="#2563EB" />
                <circle cx="402" cy="154" r="18" stroke="#2563EB" />
                <circle cx="256" cy="244" r="11" stroke="#D97706" />
                <circle cx="384" cy="244" r="11" stroke="#D97706" />
              </>
            )}
          </>
        )}

        {theme === "caterpillar" && (
          <>
            <path d="M120 245 Q 320 195 520 235" />
            <path d="M120 245 C 200 130, 430 125, 520 235 C 430 315, 210 315, 120 245 Z" />
            {stepNum >= 2 && (
              <>
                <circle cx="230" cy="195" r="28" fill="#FFFFFF" />
                <circle cx="280" cy="188" r="28" fill="#FFFFFF" />
                <circle cx="332" cy="192" r="28" fill="#FFFFFF" />
                <circle cx="386" cy="182" r="32" fill="#FFFFFF" />
              </>
            )}
            {stepNum >= 3 && (
              <>
                <circle cx="396" cy="176" r="3.5" fill="#0F172A" />
                <path d="M388 192 Q 398 200 408 190" strokeWidth="4" />
                <path d="M380 150 C 374 128, 360 126, 356 134" strokeWidth="4.5" />
                <path d="M396 150 C 406 128, 420 128, 424 136" strokeWidth="4.5" />
                <line x1="230" y1="223" x2="226" y2="236" strokeWidth="4.5" />
                <line x1="280" y1="216" x2="278" y2="230" strokeWidth="4.5" />
                <line x1="332" y1="220" x2="332" y2="234" strokeWidth="4.5" />
              </>
            )}
            {stepNum >= 4 && (
              <>
                <path d="M210 232 L 185 268" stroke="#059669" strokeWidth="4" />
                <path d="M295 222 L 270 274" stroke="#059669" strokeWidth="4" />
                <path d="M385 220 L 365 272" stroke="#059669" strokeWidth="4" />
                <circle cx="490" cy="92" r="24" stroke="#D97706" strokeWidth="4.5" />
              </>
            )}
          </>
        )}

        {theme === "tree" && (
          <>
            <path d="M120 304 Q 320 290 520 304" />
            <path d="M292 300 C 298 245, 298 205, 294 176" />
            <path d="M348 300 C 342 245, 342 205, 346 176" />
            {stepNum >= 2 && (
              <>
                <path d="M306 196 L 262 152" />
                <path d="M334 196 L 380 150" />
              </>
            )}
            {stepNum >= 3 && (
              <path d="M218 192 C 182 172, 194 114, 242 110 C 254 64, 326 52, 358 84 C 410 74, 452 122, 428 164 C 454 196, 418 232, 372 222 C 334 236, 266 234, 218 192 Z" />
            )}
            {stepNum >= 4 && (
              <>
                <circle cx="268" cy="142" r="10" stroke="#DC2626" />
                <circle cx="348" cy="122" r="10" stroke="#DC2626" />
                <circle cx="386" cy="172" r="10" stroke="#DC2626" />
                <path d="M210 300 L 202 282 M218 300 L 224 282" stroke="#059669" strokeWidth="4" />
                <path d="M420 300 L 412 282 M428 300 L 436 282" stroke="#059669" strokeWidth="4" />
              </>
            )}
          </>
        )}

        {theme === "rain" && (
          <>
            <path d="M196 156 C 164 156, 156 112, 192 104 C 204 68, 260 62, 284 88 C 316 64, 374 78, 376 114 C 412 118, 408 156, 372 156 Z" />
            {stepNum >= 2 && (
              <>
                <path d="M404 136 C 384 136, 382 108, 404 104 C 414 82, 454 82, 464 102 C 488 104, 486 136, 462 136 Z" />
                <circle cx="256" cy="118" r="3" fill="#0F172A" />
                <circle cx="304" cy="118" r="3" fill="#0F172A" />
                <path d="M268 132 Q 280 142 292 132" strokeWidth="4" />
              </>
            )}
            {stepNum >= 3 && (
              <>
                <line x1="214" y1="184" x2="198" y2="218" stroke="#2563EB" />
                <line x1="272" y1="188" x2="256" y2="224" stroke="#2563EB" />
                <line x1="332" y1="184" x2="316" y2="218" stroke="#2563EB" />
                <line x1="418" y1="164" x2="402" y2="198" stroke="#2563EB" />
                <line x1="242" y1="240" x2="228" y2="270" stroke="#2563EB" />
                <line x1="358" y1="236" x2="344" y2="266" stroke="#2563EB" />
              </>
            )}
            {stepNum >= 4 && (
              <>
                <path d="M140 312 Q 320 298 500 312" stroke="#059669" />
                <path d="M316 306 L 316 268" stroke="#059669" />
                <path d="M316 284 C 292 272, 292 254, 316 268" stroke="#059669" />
                <path d="M316 284 C 340 272, 340 254, 316 268" stroke="#059669" />
              </>
            )}
          </>
        )}

        {theme === "fish" && (
          <>
            <path d="M190 180 C 235 110, 365 110, 418 180 C 365 250, 235 250, 190 180 Z" />
            {stepNum >= 2 && (
              <>
                <path d="M418 180 L 484 132 L 472 180 L 484 228 Z" />
                <path d="M284 128 Q 320 88 352 132" />
                <path d="M294 232 Q 320 262 346 228" />
              </>
            )}
            {stepNum >= 3 && (
              <>
                <circle cx="242" cy="168" r="5" fill="#0F172A" />
                <path d="M214 194 Q 228 204 240 194" strokeWidth="4" />
                <path d="M272 146 Q 288 180 272 214" />
                <path d="M318 158 Q 332 172 318 186" strokeWidth="4" />
                <path d="M352 162 Q 366 176 352 190" strokeWidth="4" />
              </>
            )}
            {stepNum >= 4 && (
              <>
                <circle cx="158" cy="142" r="9" stroke="#2563EB" strokeWidth="4" />
                <circle cx="142" cy="106" r="13" stroke="#2563EB" strokeWidth="4" />
                <path d="M126 320 C 114 282, 142 252, 128 214" stroke="#059669" />
                <path d="M518 320 C 504 278, 534 248, 518 208" stroke="#059669" />
              </>
            )}
          </>
        )}

        {theme === "flower" && (
          <>
            <circle cx="320" cy="142" r="32" />
            {stepNum >= 2 && (
              <>
                <circle cx="320" cy="84" r="24" />
                <circle cx="320" cy="200" r="24" />
                <circle cx="262" cy="142" r="24" />
                <circle cx="378" cy="142" r="24" />
                <circle cx="278" cy="100" r="22" />
                <circle cx="362" cy="100" r="22" />
                <circle cx="278" cy="184" r="22" />
                <circle cx="362" cy="184" r="22" />
              </>
            )}
            {stepNum >= 3 && (
              <>
                <line x1="320" y1="224" x2="320" y2="324" />
                <path d="M320 284 C 276 268, 276 242, 320 264" />
                <path d="M320 284 C 364 268, 364 242, 320 264" />
              </>
            )}
            {stepNum >= 4 && (
              <>
                <circle cx="516" cy="78" r="24" stroke="#D97706" strokeWidth="4.5" />
                <line x1="516" y1="40" x2="516" y2="26" stroke="#D97706" strokeWidth="4" />
                <line x1="478" y1="78" x2="464" y2="78" stroke="#D97706" strokeWidth="4" />
                <line x1="488" y1="106" x2="476" y2="118" stroke="#D97706" strokeWidth="4" />
              </>
            )}
          </>
        )}
      </g>
    </svg>
  );
}

export function ClassroomStoryStageSvg({
  sceneIndex,
  playing,
}: {
  sceneIndex: number;
  playing: boolean;
}) {
  const idx = ((sceneIndex % 5) + 5) % 5;
  const skyBg =
    idx === 1
      ? "linear-gradient(180deg, #1E3A8A 0%, #3B82F6 68%, #ECFDF5 100%)"
      : "linear-gradient(180deg, #0284C7 0%, #BAE6FD 68%, #ECFDF5 100%)";

  return (
    <div
      aria-hidden="true"
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        background: skyBg,
        overflow: "hidden",
        pointerEvents: "none",
      }}
    >
      {/* Crisp classroom sun / moon disc */}
      <div
        style={{
          position: "absolute",
          top: "12%",
          right: "11%",
          width: 68,
          height: 68,
          borderRadius: "50%",
          background: "#FDE68A",
          border: "3px solid rgba(255, 255, 255, 0.55)",
        }}
      />
      {/* Rolling garden meadow */}
      <div
        style={{
          position: "absolute",
          left: "-8%",
          right: "-8%",
          bottom: "-12%",
          height: "38%",
          borderRadius: "50% 50% 0 0",
          background: "linear-gradient(180deg, #34D399 0%, #059669 100%)",
        }}
      />

      {/* Unified vector path focal character (≤ 3 fills, zero primitive assembly) */}
      <div
        className={playing ? "tw-float" : undefined}
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          paddingBottom: "4%",
        }}
      >
        <svg viewBox="0 0 260 180" width="260" height="180" aria-hidden="true">
          {idx === 0 && (
            <g strokeLinecap="round" strokeLinejoin="round">
              <path
                d="M20 112 C 88 42, 182 42, 240 112 C 182 162, 88 162, 20 112 Z"
                fill="#34D399"
                stroke="#064E3B"
                strokeWidth="5"
              />
              <path
                d="M78 92 C 78 72, 108 72, 108 92 C 108 72, 138 72, 138 92 C 138 70, 172 70, 172 94 C 172 114, 78 114, 78 92 Z"
                fill="#FBBF24"
                stroke="#1E293B"
                strokeWidth="4.5"
              />
              <path d="M36 112 Q 130 102 224 112" stroke="#064E3B" strokeWidth="3.5" fill="none" />
            </g>
          )}

          {idx === 1 && (
            <g strokeLinecap="round" strokeLinejoin="round">
              <path d="M30 36 Q 130 52 230 32" stroke="#FDE68A" strokeWidth="9" fill="none" />
              <path d="M130 44 L 130 76" stroke="#FDE68A" strokeWidth="4.5" fill="none" />
              <path
                d="M130 74 C 162 74, 166 148, 130 156 C 94 148, 98 74, 130 74 Z"
                fill="#FBBF24"
                stroke="#1E293B"
                strokeWidth="4.5"
              />
              <path
                d="M106 108 Q 130 120 154 108 M108 130 Q 130 142 152 130"
                stroke="#1E293B"
                strokeWidth="3.5"
                fill="none"
              />
            </g>
          )}

          {idx >= 2 && (
            <g strokeLinecap="round" strokeLinejoin="round">
              <path
                d="M120 78 C 44 16, 18 104, 120 120 M140 78 C 216 16, 242 104, 140 120"
                fill="#60A5FA"
                stroke="#1E3A8A"
                strokeWidth="5"
              />
              <path
                d="M120 120 C 58 132, 72 176, 124 146 M140 120 C 202 132, 188 176, 136 146"
                fill="#FBBF24"
                stroke="#1E3A8A"
                strokeWidth="5"
              />
              <path
                d="M130 44 C 142 44, 142 66, 130 66 C 118 66, 118 44, 130 44 Z M130 68 C 142 68, 142 154, 130 154 C 118 154, 118 68, 130 68 Z"
                fill="#1E293B"
              />
              <path
                d="M124 44 C 112 22, 96 22, 92 34 M136 44 C 148 22, 164 22, 168 34"
                stroke="#1E293B"
                strokeWidth="4"
                fill="none"
              />
            </g>
          )}
        </svg>
      </div>
    </div>
  );
}
