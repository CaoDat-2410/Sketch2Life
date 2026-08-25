from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
BASE_DIR = ROOT / "data" / "activity-catalog" / "mvp"
OUT_DIR = ROOT / "data" / "activity-catalog" / "golden" / "v1"
SCHEMA_DIR = ROOT / "packages" / "domain-montessori" / "schemas"
REVIEW_PATH = (
    ROOT
    / "features"
    / "FEAT-013-montessori-golden-hardening"
    / "approvals"
    / "OWNER_CONTENT_REVIEW.v1.json"
)

BASE_FILE_HASHES = {
    "activities.v1.json": "d148a979e28af72ee107577f6bbf57164839925c4f4e847cbf6e09786e89949c",
    "learning-objectives.v1.json": "d32b2ddd61a67b3d1771272c1de21cf852ce7a8039c89556b3f05b1796a26311",
    "hard-rules.v1.json": "9a395757fdbdcb41c80f14843ce223a9decf37d1a5bbb5565e32b29e6dba0b46",
    "provenance.v1.json": "0e12e91dc6329c5b095f882c4fda58e6119bbe169c26b7b7d46e6cff5c4e1600",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_value(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


SPECS: dict[str, dict[str, Any]] = {
    "ACT-0004": {
        "age": (8, 24),
        "readiness": [
            (
                "READY_SEARCH_PARTLY_HIDDEN",
                "tìm một đồ vật quen thuộc khi còn nhìn thấy một phần",
            )
        ],
        "purpose": "Duy trì chú ý khi đồ vật tạm rời khỏi tầm nhìn.",
        "direct": "Tìm và lấy lại một đồ vật được che dần bằng khăn.",
        "indirect": ["phối hợp mắt-tay", "ngôn ngữ gọi tên đồ vật"],
        "setup": "Trải thảm sàn; đặt một đồ vật quen thuộc và khăn ở giữa tầm với, bỏ mọi vật nhỏ khỏi khu vực.",
        "presentation": [
            "Cho trẻ nhìn và chạm đồ vật, gọi tên đồ vật một lần.",
            "Che khoảng một nửa đồ vật bằng khăn rồi dừng để trẻ tự tìm.",
            "Khi trẻ thành công, che hoàn toàn trong 1-2 giây và chờ trẻ kéo khăn.",
            "Kết thúc sau ba lượt hoặc khi trẻ quay đi; không giữ tay hay kiểm tra trẻ.",
        ],
        "child_work": ["tự kéo khăn", "lấy đồ vật", "yêu cầu hoặc tự lặp lại"],
        "restore": ["đặt đồ vật lại giữa thảm", "gấp lỏng khăn và cất cùng giỏ"],
        "isolation": "Chỉ một đồ vật và một khăn; thay đổi duy nhất là mức độ che.",
        "control": "Trẻ nhìn thấy và chạm được đúng đồ vật sau khi kéo khăn.",
        "duration": (3, 7),
        "repeatability": "Tối đa ba lượt liên tiếp; đổi đồ vật ở lần làm việc sau.",
        "supervision": "DIRECT",
        "hazards": [
            "khăn quấn quanh cổ hoặc che mặt",
            "đồ vật có chi tiết rời gây hóc",
        ],
        "stop": [
            "khăn che đường thở",
            "trẻ đưa chi tiết vật liệu vào miệng",
            "trẻ khó chịu hoặc quay đi liên tục",
        ],
        "material": (
            "khăn voan nhẹ 40 x 40 cm và bóng vải liền khối đường kính tối thiểu 8 cm",
            "khăn cotton mỏng và thú nhồi bông nguyên khối dài tối thiểu 12 cm",
            "khăn thoáng, không dây/rìa; đồ vật sạch, không pin, không chi tiết rời",
            [
                "túi nilon",
                "khăn dài có dây",
                "đồ vật lọt hoàn toàn qua lõi giấy vệ sinh",
            ],
        ),
        "secondary": ["OBJ_RECEPTIVE_LANGUAGE"],
        "prereq": [],
        "successors": ["ACT-0016"],
    },
    "ACT-0016": {
        "age": (16, 35),
        "readiness": [
            (
                "READY_STABLE_SEATED_TRANSFER",
                "ngồi vững và chủ động đặt một vật lớn vào hộp",
            )
        ],
        "purpose": "Tổ chức chuyển động có điểm bắt đầu, điểm kết thúc và trật tự rõ ràng.",
        "direct": "Chuyển từng vật lớn từ bát trái sang bát phải bằng một tay.",
        "indirect": ["chuẩn bị phối hợp hai tay", "trật tự trái sang phải"],
        "setup": "Đặt hai bát chống trượt ngang nhau; bát trái chứa sáu vật lớn giống nhau.",
        "presentation": [
            "Đặt hai tay lên mép khay, chỉ bát có vật rồi bát trống.",
            "Cầm một vật bằng cả bàn tay, chuyển chậm sang bát phải và thả nhẹ.",
            "Lặp lại từng vật, giữ bát đứng yên và không nói trong lúc chuyển.",
            "Khi hết vật, đổi vị trí hai bát để trẻ có thể lặp lại.",
        ],
        "child_work": ["chuyển từng vật", "nhặt vật rơi", "tự quyết định lặp lại"],
        "restore": ["gom đủ sáu vật vào bát trái", "đặt hai bát trở lại khay"],
        "isolation": "Các vật cùng kích thước; chỉ luyện chuyển từ một vật chứa sang vật chứa khác.",
        "control": "Bát trái rỗng và bát phải có đủ sáu vật; vật rơi nhìn thấy được.",
        "duration": (4, 8),
        "repeatability": "Cho phép đổi chiều tối đa ba chu kỳ khi trẻ còn tập trung.",
        "supervision": "DIRECT",
        "hazards": ["vật chuyển quá nhỏ", "bát vỡ hoặc cạnh sắc"],
        "stop": ["trẻ ngậm vật", "bát nứt/vỡ", "trẻ ném vật về phía người khác"],
        "material": (
            "hai bát silicone đường kính 12-15 cm và sáu bóng vải đường kính tối thiểu 5 cm",
            "hai hộp nhựa thấp và sáu đôi tất trẻ em cuộn chặt thành cuộn lớn",
            "mọi vật phải lớn hơn kích thước gây hóc, sạch và không bung chi tiết",
            ["hạt đậu", "cúc áo", "bi", "bát thủy tinh"],
        ),
        "secondary": ["OBJ_MOVEMENT_COORDINATION"],
        "prereq": [],
        "successors": ["ACT-0020", "ACT-0026"],
    },
    "ACT-0019": {
        "age": (24, 35),
        "readiness": [
            (
                "READY_FOLLOWS_WASH_SEQUENCE",
                "làm theo hai chỉ dẫn liên tiếp và đứng vững cạnh chậu thấp",
            )
        ],
        "purpose": "Thực hiện chuỗi tự chăm sóc có mở đầu, trình tự và phục hồi môi trường.",
        "direct": "Làm ướt, dùng xà phòng, xoa, xả và lau khô hai tay.",
        "indirect": ["ghi nhớ trình tự", "ý thức chăm sóc cơ thể"],
        "setup": "Người lớn kiểm tra nhiệt độ nước, đặt lượng xà phòng nhỏ và khăn khô trong tầm với.",
        "presentation": [
            "Xắn tay áo và mở nước thành dòng yếu hoặc rót lượng nước đã định.",
            "Làm ướt hai tay, lấy một lần xà phòng rồi xoa lòng bàn tay, mu bàn tay và kẽ ngón.",
            "Xả sạch xà phòng, khóa nước và quan sát khu vực quanh chậu.",
            "Lau khô từ ngón đến cổ tay; treo khăn và lau giọt nước bắn ra ngoài.",
        ],
        "child_work": [
            "thực hiện chuỗi rửa tay",
            "tự lấy khăn",
            "phục hồi khu vực ướt",
        ],
        "restore": [
            "treo hoặc đặt khăn vào giỏ đồ bẩn",
            "đặt xà phòng đúng vị trí và lau sàn khô",
        ],
        "isolation": "Một lần bơm xà phòng và một khăn; tập trung vào thứ tự rửa tay.",
        "control": "Không còn bọt xà phòng; tay và khu vực đứng không còn nước chảy.",
        "duration": (4, 8),
        "repeatability": "Thực hiện ở thời điểm vệ sinh thực tế; không lặp gây lãng phí nước.",
        "supervision": "DIRECT",
        "hazards": ["nước nóng", "sàn trơn", "nuốt xà phòng"],
        "stop": [
            "nước vượt 38°C",
            "nước đổ thành vũng dưới chân",
            "xà phòng vào mắt hoặc miệng",
        ],
        "material": (
            "chậu rửa thấp, xà phòng dịu dạng bánh và khăn cotton nhỏ",
            "bồn rửa có bục chống trượt, một liều xà phòng lỏng do người lớn cấp và khăn riêng",
            "nước ấm dưới 38°C; sản phẩm phù hợp da trẻ; bục và sàn không trượt",
            ["chất tẩy rửa gia dụng", "nước nóng", "ghế không chống trượt"],
        ),
        "secondary": ["OBJ_PRACTICAL_LIFE_SEQUENCE"],
        "prereq": [],
        "successors": ["ACT-0020"],
    },
    "ACT-0020": {
        "age": (18, 35),
        "readiness": [
            (
                "READY_NOTICES_SMALL_SPILL",
                "nhìn theo chỉ dẫn đến một vết nước nhỏ và cầm khăn bằng cả bàn tay",
            )
        ],
        "purpose": "Chăm sóc môi trường bằng một chuỗi ngắn có kết quả trực quan.",
        "direct": "Thấm và lau một vết nước nhỏ trong phạm vi được đánh dấu.",
        "indirect": ["định hướng không gian", "trách nhiệm với môi trường"],
        "setup": "Tạo vết nước sạch tối đa 30 ml trong khay thấp; đặt khăn gấp trong giỏ bên phải.",
        "presentation": [
            "Chỉ đường viền vết nước và lấy một khăn từ giỏ.",
            "Đặt khăn lên giữa vết nước, ấn bằng lòng bàn tay để thấm trước khi kéo.",
            "Lau từ mép ngoài vào giữa bằng các đường ngắn để nước không lan rộng.",
            "Sờ bằng mu bàn tay để kiểm tra khô rồi đặt khăn ướt vào giỏ riêng.",
        ],
        "child_work": [
            "lấy một khăn",
            "thấm và lau trong giới hạn",
            "kiểm tra bề mặt khô",
        ],
        "restore": ["đặt khăn ướt vào giỏ giặt", "cất khay khi mặt bàn và sàn đã khô"],
        "isolation": "Chỉ dùng nước sạch và một vùng nhỏ được giới hạn bằng khay.",
        "control": "Vết bóng của nước biến mất và khăn chuyển từ khô sang ẩm.",
        "duration": (3, 6),
        "repeatability": "Một vết nước mỗi lần; dừng khi trẻ đã phục hồi khu vực.",
        "supervision": "DIRECT",
        "hazards": ["trượt ngã", "tiếp xúc chất lỏng không rõ nguồn"],
        "stop": [
            "nước lan xuống sàn",
            "chất lỏng không phải nước sạch",
            "trẻ vắt khăn vào miệng",
        ],
        "material": (
            "khay nhựa thấp, 30 ml nước sạch, hai khăn cotton 15 x 15 cm và giỏ khăn ướt",
            "tấm lót chống thấm, cốc đo nhỏ và hai miếng vải cotton sạch màu khác nhau",
            "chỉ dùng nước sạch; khăn không xơ rời; khu vực đứng phải chống trượt",
            ["hóa chất lau sàn", "nước nóng", "chất lỏng cơ thể", "mảnh kính vỡ"],
        ),
        "secondary": ["OBJ_ORDER_GRACE_COURTESY"],
        "prereq": ["ACT-0016"],
        "successors": ["ACT-0023"],
    },
    "ACT-0023": {
        "age": (24, 35),
        "readiness": [
            (
                "READY_CARRIES_SMALL_CONTAINER",
                "mang cốc nhỏ bằng hai tay và dừng theo lời nhắc một bước",
            )
        ],
        "purpose": "Chăm sóc cây sống bằng lượng nước được giới hạn trước.",
        "direct": "Rót đúng một cốc nước nhỏ vào đất quanh gốc cây.",
        "indirect": ["điều chỉnh lực rót", "chăm sóc môi trường sống"],
        "setup": "Đặt cây không độc trong khay chống thấm; người lớn đo sẵn 40-60 ml nước.",
        "presentation": [
            "Chạm nhẹ mặt đất để quan sát khô/ẩm mà không bẻ lá.",
            "Dùng hai tay mang ca đến gần chậu và đặt vòi sát mặt đất.",
            "Nghiêng ca chậm, đi một vòng ngắn quanh gốc rồi dựng ca khi hết lượng nước.",
            "Dùng khăn thấm giọt nước trên khay và trả ca về vị trí.",
        ],
        "child_work": [
            "kiểm tra đất cùng người lớn",
            "rót lượng nước đã định",
            "lau khay",
        ],
        "restore": ["đặt cây lại nơi đủ sáng", "cất ca rỗng và khăn ẩm đúng giỏ"],
        "isolation": "Một cây và một lượng nước đo sẵn; không để trẻ tự mở vòi.",
        "control": "Ca rỗng, nước nằm trong đất/khay và không có vũng trên sàn.",
        "duration": (4, 7),
        "repeatability": "Chỉ thực hiện khi cây cần nước; không tưới lặp trong cùng ngày.",
        "supervision": "DIRECT",
        "hazards": ["cây độc hoặc gai", "đất/phân bón vào miệng", "nước gây trượt"],
        "stop": [
            "không xác định cây an toàn",
            "trẻ bốc đất cho vào miệng",
            "nước tràn khỏi khay",
        ],
        "material": (
            "cây gia dụng được xác nhận không độc, ca 60 ml, khay chống thấm và khăn nhỏ",
            "chậu rau thơm ăn được, cốc nhựa có miệng rót, đĩa lót và khăn cotton",
            "không dùng phân bón trong hoạt động; cây không gai, không nhựa kích ứng",
            ["xương rồng", "cây không rõ loài", "thuốc trừ sâu", "bình tưới nặng"],
        ),
        "secondary": ["OBJ_INDEPENDENCE_SELF_CARE"],
        "prereq": ["ACT-0020"],
        "successors": [],
    },
    "ACT-0026": {
        "age": (42, 71),
        "readiness": [
            (
                "READY_CONTROLLED_TWO_HAND_POUR",
                "dùng hai tay nâng bình nhẹ và dừng khi vật liệu chạm vạch",
            )
        ],
        "purpose": "Luyện chuỗi rót khô chính xác và tự sửa phần rơi.",
        "direct": "Rót toàn bộ vật liệu khô lớn giữa hai bình mà không tràn khay.",
        "indirect": ["chuẩn bị rót chất lỏng", "ước lượng sức chứa"],
        "setup": "Đặt hai bình giống nhau trên khay; bình trái chứa vật liệu tới một phần ba dung tích.",
        "presentation": [
            "Cầm quai bình bằng tay thuận, tay còn lại đỡ dưới đáy.",
            "Đưa miệng bình chứa sát miệng bình trống rồi nghiêng liên tục, không lắc.",
            "Chờ vật liệu cuối cùng rơi hết trước khi dựng bình và đặt xuống.",
            "Nhặt từng vật rơi trên khay bằng đầu ngón tay rồi đổi vị trí hai bình.",
        ],
        "child_work": [
            "rót hai chiều",
            "tự nhặt phần rơi",
            "dừng khi khay đã phục hồi",
        ],
        "restore": [
            "đổ toàn bộ vật liệu về bình trái",
            "xếp hai quai bình hướng ra ngoài",
        ],
        "isolation": "Hai bình giống nhau và một loại vật liệu có kích thước đồng nhất.",
        "control": "Bình nguồn rỗng; vật liệu rơi được giữ trong khay và nhìn thấy rõ.",
        "duration": (6, 12),
        "repeatability": "Tối đa năm lượt hai chiều khi thao tác vẫn có kiểm soát.",
        "supervision": "NEARBY",
        "hazards": [
            "vật liệu nhỏ gây hóc",
            "hạt thực phẩm gây dị ứng hoặc thu hút côn trùng",
        ],
        "stop": [
            "trẻ cho vật liệu vào miệng",
            "bình nứt",
            "vật liệu rơi ra sàn ngoài khay",
        ],
        "material": (
            "hai bình inox nhẹ có quai, khay viền cao và 20 viên gỗ đường kính 25 mm",
            "hai cốc nhựa có quai, khay nhựa và 20 nắp chai nhựa nguyên vẹn đường kính trên 30 mm",
            "vật liệu đồng cỡ, sạch, không sắc và đủ lớn để không gây hóc",
            ["gạo", "đậu khô", "hạt cườm", "hạt có dị ứng", "bình thủy tinh"],
        ),
        "secondary": ["OBJ_INDEPENDENCE_SELF_CARE"],
        "prereq": [],
        "successors": ["ACT-0033"],
    },
    "ACT-0030": {
        "age": (42, 71),
        "readiness": [
            (
                "READY_PINCH_AND_ALIGN_BUTTON",
                "dùng ngón cái-ngón trỏ giữ nút lớn và đưa hai mép vải lại gần",
            )
        ],
        "purpose": "Tự chăm sóc thông qua thao tác mở và cài nút có trình tự.",
        "direct": "Mở rồi cài sáu nút lớn từ trên xuống.",
        "indirect": ["phối hợp hai tay", "chuẩn bị tự mặc quần áo"],
        "setup": "Trải khung nằm ngang, hàng nút ở giữa và tất cả nút đang cài.",
        "presentation": [
            "Giữ mép vải trái bằng tay không thuận và lật nhẹ để thấy khe nút trên cùng.",
            "Đẩy cạnh nút qua khe, kéo nút ra hoàn toàn rồi chuyển xuống nút kế tiếp.",
            "Sau khi mở hết, vuốt phẳng hai mép vải và ghép mép từ nút trên cùng.",
            "Đưa cạnh nút qua khe, kéo thẳng rồi kiểm tra hai mép không bị xoắn.",
        ],
        "child_work": ["mở từng nút", "cài lại theo thứ tự", "tự kiểm tra mép vải"],
        "restore": ["cài đủ sáu nút", "đặt khung ngay ngắn lên giá"],
        "isolation": "Một loại nút lớn, cùng kích thước; không trộn khóa kéo hoặc dây buộc.",
        "control": "Hai mép vải thẳng và mỗi nút nằm đúng một khe tương ứng.",
        "duration": (8, 15),
        "repeatability": "Một chu kỳ mở-cài; lặp khi trẻ chủ động chọn lại.",
        "supervision": "NEARBY",
        "hazards": ["nút lỏng có thể rời", "kim ghim hoặc cạnh khung hỏng"],
        "stop": ["nút lung lay", "đường may bung", "trẻ kéo mạnh làm kẹt ngón"],
        "material": (
            "khung cài sáu nút nhựa đường kính 25-30 mm được may chắc",
            "áo khoác trẻ em sạch có 4-6 nút lớn và được trải phẳng trên bàn",
            "kiểm tra lực kéo từng nút trước hoạt động; không có kim ghim hoặc chỉ dài",
            ["nút nhỏ", "áo đang mặc trên người", "khuy bị nứt", "kim băng"],
        ),
        "secondary": ["OBJ_MOVEMENT_COORDINATION"],
        "prereq": [],
        "successors": [],
    },
    "ACT-0033": {
        "age": (48, 71),
        "readiness": [
            (
                "READY_CARRIES_PLACE_SETTING",
                "mang từng vật nhẹ bằng hai tay và ghép vật với đường viền hình",
            )
        ],
        "purpose": "Chuẩn bị bàn ăn cho một người theo sơ đồ trật tự.",
        "direct": "Đặt khăn, đĩa, cốc và thìa đúng vị trí trên tấm lót.",
        "indirect": ["định hướng trái-phải", "chăm sóc cộng đồng"],
        "setup": "Đặt tấm lót có đường viền và khay vật dụng không vỡ ở bàn bên cạnh.",
        "presentation": [
            "Mang tấm lót bằng hai tay và căn mép dưới song song mép bàn.",
            "Đặt đĩa vào vòng tròn giữa, khăn ở bên trái và cốc ở góc trên phải.",
            "Cầm thìa ở cán, đặt bên phải đĩa theo đường viền mà không chạm phần xúc.",
            "Đi một vòng nhìn từng đường viền; tự di chuyển vật chưa khớp.",
        ],
        "child_work": ["mang từng vật", "ghép với sơ đồ", "kiểm tra và chỉnh vị trí"],
        "restore": ["mang từng vật về khay", "cuộn tấm lót và lau bàn nếu cần"],
        "isolation": "Một bộ cho một người và một tấm lót có bốn vị trí.",
        "control": "Mỗi vật che đúng đường viền tương ứng và không chồng lên vật khác.",
        "duration": (7, 12),
        "repeatability": "Một lần chuẩn bị và một lần phục hồi; có thể dùng trước bữa ăn thật.",
        "supervision": "NEARBY",
        "hazards": ["vật dụng dễ vỡ", "dao hoặc dụng cụ sắc"],
        "stop": [
            "vật bị nứt/vỡ",
            "trẻ cầm dụng cụ bằng phần nguy hiểm",
            "khu vực di chuyển bị cản",
        ],
        "material": (
            "tấm lót có đường viền, đĩa melamine, cốc inox, thìa đầu tròn và khăn vải",
            "tờ bìa ép plastic tự vẽ sơ đồ, đĩa/cốc nhựa thực phẩm, thìa silicone và khăn cotton",
            "mọi vật nhẹ, không vỡ, không cạnh sắc và sạch để dùng với thực phẩm",
            ["dao", "nĩa nhọn", "đồ thủy tinh", "đồ trang trí nhỏ"],
        ),
        "secondary": ["OBJ_PRACTICAL_LIFE_SEQUENCE"],
        "prereq": ["ACT-0026"],
        "successors": [],
    },
    "ACT-0039": {
        "age": (48, 71),
        "readiness": [
            (
                "READY_MATCHES_IDENTICAL_COLOR",
                "ghép đúng ít nhất ba cặp màu giống nhau khi không có chữ gợi ý",
            )
        ],
        "purpose": "Phân biệt và sắp thứ tự sắc độ trong một họ màu.",
        "direct": "Xếp bảy sắc độ từ đậm đến nhạt bằng so sánh từng cặp.",
        "indirect": [
            "từ vựng so sánh",
            "chuẩn bị quan sát màu trong nghệ thuật và tự nhiên",
        ],
        "setup": "Trải thảm trung tính dưới ánh sáng trắng; chọn một họ màu gồm bảy thẻ không có chữ ở mặt trước.",
        "presentation": [
            "Đặt thẻ đậm nhất và nhạt nhất cách nhau để tạo hai mốc.",
            "Từ các thẻ còn lại, so từng thẻ với mốc đậm và chọn thẻ gần nhất.",
            "Tiếp tục đặt thẻ kế bên, giữ khoảng cách đều và không gọi tên màu khi đang so.",
            "Nhìn dãy từ trái sang phải; đổi chỗ hai thẻ nếu bước chuyển sắc bị đứt.",
        ],
        "child_work": [
            "so sánh từng cặp",
            "xếp dãy",
            "tự phát hiện bước màu không đều",
        ],
        "restore": ["xếp thẻ theo mã nhỏ ở mặt sau", "cất cả họ màu vào hộp"],
        "isolation": "Chỉ một họ màu; thẻ cùng kích thước và độ bóng.",
        "control": "Mã kín ở mặt sau tạo thứ tự 1-7 sau khi trẻ hoàn tất bằng quan sát.",
        "duration": (8, 15),
        "repeatability": "Một đến ba họ màu mỗi lần tùy mức tập trung.",
        "supervision": "NEARBY",
        "hazards": ["thẻ bong lớp phủ hoặc cạnh sắc", "ánh sáng màu làm sai quan sát"],
        "stop": [
            "thẻ rách tạo cạnh sắc",
            "trẻ ném/giẫm thẻ",
            "ánh sáng quá tối hoặc đổi màu",
        ],
        "material": (
            "bảy bảng màu cùng một họ, bề mặt mờ, kích thước 5 x 8 cm và thảm xám",
            "bảy thẻ bìa tự in từ một dải màu chuẩn, ép plastic mờ và đánh mã kín ở mặt sau",
            "mọi thẻ cùng chất liệu/kích thước; khác biệt duy nhất là độ sáng màu",
            [
                "mẫu có chữ ở mặt trước",
                "thẻ khác kích thước",
                "màu huỳnh quang",
                "thẻ bóng phản sáng",
            ],
        ),
        "secondary": ["OBJ_ORDER_GRACE_COURTESY"],
        "prereq": [],
        "successors": ["ACT-0046"],
    },
    "ACT-0046": {
        "age": (48, 71),
        "readiness": [
            (
                "READY_TRIPOD_OR_FUNCTIONAL_GRIP",
                "giữ bút bằng cách cầm chức năng và tô vùng rộng mà không bẻ đầu bút",
            )
        ],
        "purpose": "Chuẩn bị nét viết qua việc vẽ đường trong giới hạn hình học.",
        "direct": "Tạo và tô một hình bằng khung kim loại với các nét song song có kiểm soát.",
        "indirect": ["kiểm soát bút", "nhận biết hình", "chuẩn bị viết"],
        "setup": "Đặt khung, miếng hình, hai bút chì màu và giấy vuông trên bàn phù hợp chiều cao.",
        "presentation": [
            "Giữ khung bằng tay không thuận, đặt bút sát mép trong và đi một vòng liên tục.",
            "Thay khung bằng miếng hình, căn vào đường vừa vẽ rồi dùng màu thứ hai đi quanh mép ngoài.",
            "Chọn một hướng và tô bằng các nét song song từ mép này sang mép kia.",
            "Dừng tại đường biên, xoay giấy nếu cần thay vì vặn cổ tay quá mức.",
        ],
        "child_work": ["đồ khung", "căn miếng hình", "tô bằng nét có hướng"],
        "restore": [
            "đặt bút vào cốc đầu hướng lên",
            "xếp khung và miếng hình đúng cặp",
        ],
        "isolation": "Một hình và hai màu; mục tiêu là kiểm soát đường chứ không đánh giá tranh đẹp.",
        "control": "Hai đường viền cho thấy độ lệch; nét tô vượt biên nhìn thấy được.",
        "duration": (10, 20),
        "repeatability": "Một đến hai hình mỗi lần; dừng khi tay mỏi.",
        "supervision": "NEARBY",
        "hazards": ["đầu bút nhọn", "miếng kim loại cong hoặc có ba via"],
        "stop": [
            "trẻ hướng đầu bút vào mặt",
            "khung có cạnh sắc",
            "trẻ báo đau hoặc mỏi tay",
        ],
        "material": (
            "một cặp khung kim loại Montessori nguyên vẹn, giấy 14 x 14 cm và hai bút chì màu đầu tù",
            "khuôn hình nhựa cứng không cạnh sắc, giấy vuông và hai bút sáp tam giác",
            "khuôn không trượt, không ba via; bút không độc và phù hợp tay trẻ",
            ["dao rọc khuôn", "kim loại gỉ/cong", "bút chì nhọn", "khuôn quá nhỏ"],
        ),
        "secondary": ["OBJ_SENSORIAL_DISCRIMINATION"],
        "prereq": [],
        "successors": [],
    },
    "ACT-0055": {
        "age": (72, 95),
        "readiness": [
            (
                "READY_HANDLES_PLANT_SAMPLE",
                "dùng kính lúp và đặt mẫu xuống mà không bóp hoặc bứt thêm",
            )
        ],
        "purpose": "Quan sát cấu trúc thực vật và ghi nhận bằng từ/nghiệm chứng trực tiếp.",
        "direct": "Xác định rễ, thân, lá và hoa/quả khi có trên một mẫu cây an toàn.",
        "indirect": ["phân loại sinh học", "vẽ quan sát có nhãn"],
        "setup": "Người lớn xác định mẫu không độc/không xử lý hóa chất; đặt mẫu, kính lúp và thẻ nhãn trên khay.",
        "presentation": [
            "Quan sát toàn cây trước, mô tả vị trí trên-dưới mà chưa đặt nhãn.",
            "Dùng kính lúp nhìn một bộ phận, nêu đặc điểm nhìn thấy thay vì đoán chức năng.",
            "Đặt thẻ rễ, thân, lá và hoa/quả cạnh bộ phận tương ứng khi bộ phận đó hiện diện.",
            "Vẽ đường nét chính của mẫu và nối nhãn tới đúng vị trí quan sát.",
        ],
        "child_work": [
            "quan sát toàn thể và chi tiết",
            "đặt nhãn",
            "vẽ/ghi đặc điểm thấy được",
        ],
        "restore": [
            "trả mẫu sống về chậu hoặc bỏ mẫu cắt vào khay hữu cơ",
            "lau kính lúp và xếp thẻ",
        ],
        "isolation": "Một mẫu cây mỗi lần; chỉ nhãn những bộ phận thực sự hiện diện.",
        "control": "Thẻ nhãn có ảnh nhỏ ở mặt sau để đối chiếu vị trí sau quan sát.",
        "duration": (15, 25),
        "repeatability": "So sánh tối đa hai mẫu trong một buổi và ghi khác biệt riêng.",
        "supervision": "NEARBY",
        "hazards": ["cây độc/gai/nhựa kích ứng", "dị ứng phấn hoa", "đất hoặc mẫu bẩn"],
        "stop": [
            "không xác định được loài",
            "kích ứng da/hô hấp",
            "phát hiện thuốc trừ sâu hoặc nấm mốc",
        ],
        "material": (
            "một cây rau thơm ăn được còn nguyên rễ, kính lúp nhựa và bộ thẻ rễ-thân-lá-hoa",
            "mẫu hành lá có rễ trong cốc nước sạch, kính lúp cầm tay và nhãn viết trên bìa",
            "mẫu được người lớn xác nhận không độc, không thuốc trừ sâu và không nấm mốc",
            ["cây dại không rõ loài", "cây có gai", "nấm", "mẫu phun hóa chất"],
        ),
        "secondary": ["OBJ_COSMIC_INTERCONNECTION"],
        "prereq": [],
        "successors": ["ACT-0087"],
    },
    "ACT-0058": {
        "age": (78, 107),
        "readiness": [
            (
                "READY_RECORDS_CHANGES_OVER_TIME",
                "ghi lại ít nhất hai quan sát theo thời điểm và phân biệt quan sát với dự đoán",
            )
        ],
        "purpose": "Mô hình hóa bay hơi, ngưng tụ và nước rơi trong một hệ kín an toàn.",
        "direct": "Quan sát và ghi ba trạng thái trong mô hình vòng tuần hoàn nước đơn giản.",
        "indirect": ["tư duy hệ thống", "ghi dữ liệu theo thời gian"],
        "setup": "Cho 100 ml nước ấm dưới 45°C vào hộp trong, đậy nắp trong và đặt túi đá lên nắp; người lớn xử lý nước.",
        "presentation": [
            "Đánh dấu mực nước ban đầu và ghi nhiệt độ/thời gian bắt đầu.",
            "Quan sát mặt trong nắp sau mỗi hai phút, vẽ vị trí giọt thay vì mở nắp.",
            "Theo dõi giọt lớn dần rồi rơi trở lại; gắn từ bay hơi, ngưng tụ, rơi vào bằng chứng nhìn thấy.",
            "So sánh mực nước đầu-cuối và ghi giới hạn của mô hình so với tự nhiên.",
        ],
        "child_work": [
            "đo và đánh dấu",
            "quan sát theo mốc thời gian",
            "liên hệ thuật ngữ với bằng chứng",
        ],
        "restore": [
            "đổ nước khi đã nguội",
            "lau khô hộp và mặt bàn, cất phiếu quan sát",
        ],
        "isolation": "Một hộp kín; thay đổi nhiệt độ giữa nước phía dưới và đá phía trên.",
        "control": "Giọt nước hiện ở mặt trong nắp và mốc thời gian cho phép kiểm tra chuỗi quan sát.",
        "duration": (20, 30),
        "repeatability": "Lặp vào ngày khác với nước nhiệt độ phòng để so sánh, không tăng nhiệt vượt giới hạn.",
        "supervision": "DIRECT",
        "hazards": ["nước nóng", "nước đổ gần thiết bị điện", "hộp nứt"],
        "stop": ["nước trên 45°C", "hộp biến dạng/nứt", "nước tràn khỏi khay"],
        "material": (
            "hộp nhựa trong chịu ấm có nắp trong, 100 ml nước dưới 45°C, túi đá kín và nhiệt kế",
            "bát inox trong khay, đĩa kim loại làm nắp, túi zip hai lớp chứa đá và nhiệt kế bếp",
            "người lớn cấp nước và kiểm tra nhiệt; mô hình đặt xa ổ điện trên khay chống tràn",
            [
                "nước sôi",
                "lọ thủy tinh mỏng",
                "đá đặt trực tiếp không túi",
                "thiết bị gia nhiệt tại bàn",
            ],
        ),
        "secondary": ["OBJ_COSMIC_INTERCONNECTION"],
        "prereq": [],
        "successors": ["ACT-0091"],
    },
    "ACT-0061": {
        "age": (78, 107),
        "readiness": [
            (
                "READY_PLACE_VALUE_TO_THOUSANDS",
                "biểu diễn và đọc số đến hàng nghìn bằng vật liệu giá trị hàng",
            )
        ],
        "purpose": "Biểu diễn phép nhân nhiều chữ số như các lần cộng và đổi hàng cụ thể.",
        "direct": "Giải một phép nhân bằng bộ tem và ghi từng lần đổi hàng.",
        "indirect": ["thuật toán nhân viết", "kiểm tra ước lượng"],
        "setup": "Chọn thẻ bài toán một chữ số nhân với số đến bốn chữ số; xếp tem theo cột đơn vị-chục-trăm-nghìn.",
        "presentation": [
            "Đọc thừa số và đặt số lần lặp bằng thẻ nhỏ bên cạnh bảng.",
            "Lấy tem cho lần thứ nhất theo từng hàng, rồi lặp lại đúng số lần.",
            "Gom từ hàng đơn vị; cứ mười tem đổi thành một tem ở hàng kế tiếp và ghi mỗi lần đổi.",
            "Đọc kết quả từ hàng cao xuống, ghi phép tính và so với ước lượng ban đầu.",
        ],
        "child_work": ["lặp nhóm tem", "đổi hàng", "ghi và kiểm tra kết quả"],
        "restore": [
            "phân tem về từng ngăn màu",
            "trả thẻ bài toán và xóa bảng ghi tạm",
        ],
        "isolation": "Một bài toán và một bộ màu giá trị hàng; không dạy thuật toán tắt đồng thời.",
        "control": "Số tem sau đổi khớp kết quả in ở mặt sau thẻ bài toán.",
        "duration": (20, 35),
        "repeatability": "Một đến ba bài tăng dần; dừng trước khi thao tác đổi hàng mất chính xác.",
        "supervision": "NEARBY",
        "hazards": [
            "miếng tem nhỏ bị thất lạc hoặc cho vào miệng",
            "quá tải bài toán gây mất kiểm soát",
        ],
        "stop": [
            "trẻ cho tem vào miệng",
            "thiếu miếng làm sai bộ",
            "trẻ liên tục đổi hàng không theo nhóm mười",
        ],
        "material": (
            "bộ stamp game đầy đủ có khay ngăn, thẻ phép nhân tự kiểm tra và giấy ô vuông",
            "bộ thẻ giá trị hàng tự in kích thước tối thiểu 25 mm, bốn khay màu và thẻ đáp án kín",
            "mỗi hạng tem đủ số lượng, màu nhất quán và được kiểm đếm trước/sau",
            [
                "hạt nhỏ rời",
                "thẻ dưới 20 mm",
                "bộ thiếu giá trị hàng",
                "máy tính thay vật liệu",
            ],
        ),
        "secondary": ["OBJ_NUMBER_QUANTITY_PLACE_VALUE"],
        "prereq": [],
        "successors": [],
    },
    "ACT-0067": {
        "age": (78, 107),
        "readiness": [
            (
                "READY_IDENTIFIES_NOUN_VERB",
                "xác định danh từ và động từ trong câu ngắn bằng câu hỏi ai/cái gì và làm gì",
            )
        ],
        "purpose": "Phân tích chức năng từ trong câu bằng ký hiệu trực quan.",
        "direct": "Gắn ký hiệu đúng cho danh từ, mạo từ, tính từ, động từ và trạng từ trong câu mẫu.",
        "indirect": ["cấu trúc câu", "chỉnh sửa văn bản"],
        "setup": "Chọn ba câu 5-8 từ đã kiểm tra từ vựng; đặt bộ ký hiệu và bảng chú giải úp xuống.",
        "presentation": [
            "Đọc cả câu thành tiếng và tìm từ chỉ người/vật trước để đặt tam giác đen danh từ.",
            "Tìm từ chỉ hành động, thử thực hiện hành động và đặt hình cầu đỏ động từ.",
            "Dùng câu hỏi từ nào mô tả danh từ/hành động để đặt ký hiệu tính từ và trạng từ.",
            "Lật bảng chú giải, kiểm tra từng ký hiệu và ghi lại một câu đã phân tích.",
        ],
        "child_work": [
            "đọc câu",
            "đặt ký hiệu theo chức năng",
            "kiểm tra và giải thích lựa chọn",
        ],
        "restore": ["phân ký hiệu theo ngăn", "kẹp câu đã làm và trả thẻ chưa làm"],
        "isolation": "Mỗi câu chỉ chứa loại từ đã được giới thiệu; không chấm ý nghĩa sáng tạo của câu.",
        "control": "Mã ký hiệu ở mặt sau câu cho phép đối chiếu sau khi trẻ giải thích.",
        "duration": (15, 25),
        "repeatability": "Ba câu mỗi lượt; tăng độ dài ở lần làm việc sau.",
        "supervision": "NEARBY",
        "hazards": ["ký hiệu nhỏ bị thất lạc", "nội dung câu không phù hợp độ tuổi"],
        "stop": [
            "thiếu ký hiệu",
            "câu chứa nội dung nhạy cảm",
            "trẻ chuyển sang đoán theo màu mà không đọc",
        ],
        "material": (
            "bộ ký hiệu ngữ pháp Montessori kích thước lớn, ba thẻ câu và bảng đáp án kín",
            "ký hiệu cắt từ bìa màu kích thước trên 30 mm, câu tự viết rõ chữ và phong bì đáp án",
            "màu/hình nhất quán; câu không chứa dữ liệu cá nhân hoặc nội dung gây sợ hãi",
            ["hình quá nhỏ", "câu lấy từ hồ sơ trẻ", "đáp án lộ ở mặt trước"],
        ),
        "secondary": ["OBJ_COMMUNICATION_ARGUMENTATION"],
        "prereq": [],
        "successors": ["ACT-0097"],
    },
    "ACT-0074": {
        "age": (84, 107),
        "readiness": [
            (
                "READY_ESTIMATES_SHORT_TASK",
                "ước lượng và hoàn thành một việc 10-20 phút với lời nhắc tối thiểu",
            )
        ],
        "purpose": "Lập kế hoạch cân bằng giữa việc cần làm, lựa chọn và thời gian nghỉ.",
        "direct": "Xếp tối đa năm nhiệm vụ vào tuần và kiểm tra tiến độ hằng ngày.",
        "indirect": ["tự điều chỉnh", "trách nhiệm cộng đồng"],
        "setup": "Chuẩn bị lịch tuần không có dữ liệu nhạy cảm, thẻ nhiệm vụ cụ thể và đồng hồ hẹn giờ không kết nối mạng.",
        "presentation": [
            "Đọc từng thẻ, xác định hạn và ước lượng một khoảng thời gian thay vì ghi giờ chính xác giả tạo.",
            "Đặt việc bắt buộc trước, sau đó thêm một việc tự chọn và khoảng trống nghỉ.",
            "Chọn một việc cho hôm nay, đặt hẹn giờ và bắt đầu mà không mở thêm nhiệm vụ.",
            "Cuối lượt, đánh dấu hoàn thành/đang làm/chuyển lịch và ghi một lý do thực tế.",
        ],
        "child_work": ["ước lượng", "xếp lịch", "thực hiện một việc", "phản tư ngắn"],
        "restore": [
            "cất thẻ hoàn thành riêng",
            "đặt lịch tuần vào bìa cá nhân không ghi tên đầy đủ",
        ],
        "isolation": "Tối đa năm nhiệm vụ; tập trung vào lập kế hoạch chứ không đánh giá năng suất trẻ.",
        "control": "Tổng thời lượng trong ngày không vượt khung giờ có sẵn và mỗi việc có trạng thái rõ.",
        "duration": (15, 25),
        "repeatability": "Xem lại 5 phút mỗi ngày; lập lịch mới mỗi tuần.",
        "supervision": "NEARBY",
        "hazards": [
            "lịch chứa thông tin cá nhân",
            "khối lượng việc gây áp lực",
            "đồng hồ/ứng dụng thu thập dữ liệu",
        ],
        "stop": [
            "trẻ biểu hiện quá tải",
            "lịch ghi tên/địa chỉ/số liên hệ",
            "người lớn biến kế hoạch thành hình phạt",
        ],
        "material": (
            "bảng tuần tái sử dụng, tối đa năm thẻ nhiệm vụ và đồng hồ hẹn giờ cơ học",
            "tờ lịch giấy không ghi tên đầy đủ, giấy ghi chú màu và đồng hồ bếp ngoại tuyến",
            "chỉ ghi nhiệm vụ học/sinh hoạt không nhạy cảm; thời lượng có khoảng nghỉ",
            [
                "lịch công khai có tên trẻ",
                "ứng dụng bắt đăng nhập",
                "xếp lịch kín không có nghỉ",
            ],
        ),
        "secondary": ["OBJ_PROJECT_SERVICE_LEADERSHIP"],
        "prereq": [],
        "successors": ["ACT-0099"],
    },
    "ACT-0085": {
        "age": (114, 155),
        "readiness": [
            (
                "READY_TABLE_AND_BAR_GRAPH",
                "đọc bảng tần số và tạo biểu đồ cột có nhãn trục",
            )
        ],
        "purpose": "Thiết kế khảo sát không nhạy cảm và mô tả dữ liệu bằng bằng chứng.",
        "direct": "Thu thập một biến phân loại, lập bảng tần số và viết ba nhận xét giới hạn.",
        "indirect": ["tư duy thống kê", "đạo đức dữ liệu cơ bản"],
        "setup": "Chọn câu hỏi không định danh, tối đa năm lựa chọn và bộ dữ liệu fixture hoặc phiếu ẩn danh.",
        "presentation": [
            "Kiểm tra câu hỏi chỉ hỏi một ý và không thu tên, sức khỏe, gia đình, vị trí hoặc tài khoản.",
            "Ghi từng câu trả lời bằng vạch kiểm rồi cộng tần số, kiểm tra tổng bằng số phiếu.",
            "Vẽ biểu đồ với tiêu đề, nhãn trục và cùng một đơn vị cho mỗi cột.",
            "Viết nhận xét về mẫu dữ liệu, nêu cỡ mẫu và điều không thể kết luận.",
        ],
        "child_work": ["kiểm tra câu hỏi", "lập bảng", "vẽ biểu đồ", "mô tả giới hạn"],
        "restore": [
            "hủy phiếu nháp không cần giữ",
            "lưu bảng tổng hợp không định danh",
        ],
        "isolation": "Một câu hỏi và một biến; không dùng dữ liệu cá nhân thật.",
        "control": "Tổng tần số bằng số phiếu và chiều cao cột khớp bảng.",
        "duration": (30, 50),
        "repeatability": "Một khảo sát mỗi chu kỳ; lặp với câu hỏi khác sau khi phản tư giới hạn.",
        "supervision": "NEARBY",
        "hazards": [
            "thu thập dữ liệu cá nhân/nhạy cảm",
            "kết luận vượt dữ liệu",
            "chia sẻ phiếu có nhận dạng",
        ],
        "stop": [
            "câu hỏi liên quan sức khỏe/gia đình/vị trí",
            "phiếu có tên hoặc tài khoản",
            "kết quả được dùng để xếp hạng cá nhân",
        ],
        "material": (
            "bộ 20 phiếu fixture ẩn danh, mẫu bảng tần số, giấy biểu đồ và máy tính cơ bản ngoại tuyến",
            "20 thẻ dữ liệu tổng hợp do người lớn chuẩn bị, giấy ô vuông và bảng phép tính viết tay",
            "dữ liệu hoàn toàn synthetic/ẩn danh; máy tính không đồng bộ tài khoản",
            [
                "Google Form có tài khoản",
                "danh sách tên",
                "dữ liệu sức khỏe",
                "định vị",
            ],
        ),
        "secondary": ["OBJ_COMMUNICATION_ARGUMENTATION"],
        "prereq": [],
        "successors": ["ACT-0099"],
    },
    "ACT-0087": {
        "age": (114, 155),
        "readiness": [
            (
                "READY_COMPARE_OBSERVABLE_TRAITS",
                "mô tả ít nhất ba đặc điểm nhìn thấy mà không dùng phán đoán chủ quan",
            )
        ],
        "purpose": "Tạo khóa lưỡng phân bằng các đặc điểm quan sát được và kiểm thử lại.",
        "direct": "Phân loại 8-12 mẫu/thẻ bằng chuỗi câu hỏi hai lựa chọn.",
        "indirect": ["lập luận điều kiện", "ngôn ngữ khoa học chính xác"],
        "setup": "Dùng bộ thẻ mẫu synthetic hoặc mẫu vật an toàn; đánh mã thay vì tên đáp án ở mặt trước.",
        "presentation": [
            "Liệt kê đặc điểm có thể kiểm tra trực tiếp như số chân, dạng lá hoặc có/không có cánh.",
            "Chọn một đặc điểm chia toàn bộ mẫu thành hai nhóm không chồng lặp.",
            "Lặp câu hỏi cho từng nhánh tới khi mỗi đầu cuối chỉ còn một mẫu.",
            "Đưa một thẻ cho người khác đi từ đầu khóa; sửa câu hỏi nơi kết quả bị mơ hồ.",
        ],
        "child_work": ["quan sát đặc điểm", "tạo nhánh", "kiểm thử chéo", "sửa khóa"],
        "restore": ["xếp thẻ theo mã", "lưu khóa cùng phiên bản bộ mẫu"],
        "isolation": "Chỉ dùng đặc điểm có/không hoặc hai trạng thái rõ; không phân loại người.",
        "control": "Mỗi thẻ phải đi tới đúng một đầu cuối và mã cuối khớp mặt sau.",
        "duration": (30, 50),
        "repeatability": "Kiểm thử bằng ít nhất hai thứ tự thẻ khác nhau.",
        "supervision": "NEARBY",
        "hazards": [
            "mẫu sinh học độc/sắc",
            "phân loại con người bằng đặc điểm nhạy cảm",
            "đặc điểm suy đoán thay vì quan sát",
        ],
        "stop": [
            "mẫu không xác định an toàn",
            "khóa áp dụng cho người",
            "một thẻ có nhiều đầu cuối mà không ghi bất định",
        ],
        "material": (
            "12 thẻ ảnh lá/côn trùng synthetic có mã đáp án và mẫu khóa lưỡng phân",
            "8-12 đồ vật gia dụng an toàn khác nhau rõ ràng và giấy vẽ sơ đồ nhánh",
            "mẫu sạch, không sắc/độc; chỉ phân loại vật hoặc sinh vật trên thẻ",
            [
                "mẫu nấm/cây dại thật",
                "côn trùng sống",
                "ảnh người",
                "thuộc tính sức khỏe/chủng tộc",
            ],
        ),
        "secondary": ["OBJ_HUMANITIES_RESEARCH"],
        "prereq": ["ACT-0055"],
        "successors": [],
    },
    "ACT-0091": {
        "age": (108, 143),
        "readiness": [
            (
                "READY_MODELS_LIGHT_AND_SHADOW",
                "giải thích bóng xuất hiện khi vật cản đường truyền ánh sáng",
            )
        ],
        "purpose": "Dùng mô hình để giải thích phần Mặt Trăng được chiếu sáng mà người quan sát thấy.",
        "direct": "Mô hình hóa và ghi tám vị trí pha Mặt Trăng với nguồn sáng cố định.",
        "indirect": ["tư duy không gian", "phân biệt mô hình với thực tế"],
        "setup": "Phòng có thể giảm sáng nhưng vẫn đi lại an toàn; đèn cố định ở giữa, quả cầu trên que và vòng vị trí trên sàn.",
        "presentation": [
            "Xác định đèn là Mặt Trời, đầu người quan sát là Trái Đất và quả cầu là Mặt Trăng.",
            "Giữ quả cầu ngang mắt, quay người theo tám mốc trong khi đèn không di chuyển.",
            "Ở mỗi mốc, tô phần sáng nhìn thấy trên phiếu và ghi hướng quay.",
            "So sánh tám hình, chỉ ra mô hình không thể hiện đúng tỉ lệ/khoảng cách.",
        ],
        "child_work": [
            "di chuyển theo mốc",
            "quan sát phần sáng",
            "ghi pha",
            "nêu giới hạn mô hình",
        ],
        "restore": [
            "bật sáng phòng trước khi thu vòng mốc",
            "tắt/rút đèn sau khi nguội và cất quả cầu",
        ],
        "isolation": "Một nguồn sáng cố định và một quả cầu; không thêm chuyển động quỹ đạo khác.",
        "control": "Phiếu tám vị trí có sơ đồ kiểm tra và phần sáng phải luôn hướng về đèn.",
        "duration": (25, 40),
        "repeatability": "Lặp với người quan sát khác hoặc quay video mô hình không có trẻ để so sánh vị trí.",
        "supervision": "DIRECT",
        "hazards": [
            "bóng đèn nóng",
            "dây điện gây vấp",
            "phòng quá tối",
            "chiếu sáng vào mắt",
        ],
        "stop": [
            "đèn nóng khi chạm",
            "dây đi qua lối bước",
            "người học chóng mặt",
            "đèn không ổn định",
        ],
        "material": (
            "đèn LED ánh sáng khuếch tán, quả cầu xốp 8-10 cm trên que tù, tám mốc sàn và phiếu pha",
            "đèn pin LED cố định trong hộp, bóng bàn gắn trên bút đầu tù, băng giấy đánh tám vị trí và giấy ghi",
            "chỉ dùng LED mát; dây cố định ngoài lối đi; phòng đủ sáng để thấy sàn",
            [
                "nến",
                "bóng sợi đốt nóng",
                "tia laser",
                "que nhọn",
                "phòng tối hoàn toàn",
            ],
        ),
        "secondary": ["OBJ_SCIENTIFIC_INQUIRY"],
        "prereq": ["ACT-0058"],
        "successors": [],
    },
    "ACT-0097": {
        "age": (114, 155),
        "readiness": [
            (
                "READY_DISTINGUISHES_CLAIM_EVIDENCE",
                "phân biệt một ý kiến với dữ kiện có nguồn trong đoạn ngắn",
            )
        ],
        "purpose": "Xây dựng lập luận giới hạn bằng luận điểm, bằng chứng và giải thích liên kết.",
        "direct": "Viết một đoạn lập luận dùng ít nhất hai bằng chứng được trích nguồn.",
        "indirect": ["đánh giá nguồn", "phản hồi quan điểm khác"],
        "setup": "Chuẩn bị câu hỏi không nhạy cảm, gói 3-4 nguồn ngắn có tác giả/ngày và mẫu claim-evidence-reasoning.",
        "presentation": [
            "Viết một luận điểm có thể tranh luận và giới hạn trong câu hỏi đã cho.",
            "Đọc nguồn, đánh dấu dữ kiện hỗ trợ/phản bác và ghi mã nguồn thay vì chép dài.",
            "Chọn hai bằng chứng khác nhau, giải thích vì sao mỗi bằng chứng liên quan đến luận điểm.",
            "Nêu một phản biện hợp lý, trả lời có giới hạn và thêm danh sách nguồn.",
        ],
        "child_work": [
            "viết luận điểm",
            "chọn bằng chứng",
            "giải thích liên kết",
            "xem xét phản biện",
        ],
        "restore": [
            "trả gói nguồn theo thứ tự",
            "lưu bài cùng phiếu nguồn và xóa ghi chú có dữ liệu không cần thiết",
        ],
        "isolation": "Một câu hỏi và gói nguồn đóng; đánh giá cấu trúc bằng chứng chứ không ép quan điểm.",
        "control": "Mỗi bằng chứng có mã nguồn và mỗi đoạn giải thích trả lời trực tiếp 'vì sao hỗ trợ'.",
        "duration": (35, 60),
        "repeatability": "Sửa một vòng sau phản hồi tập trung vào bằng chứng, không viết lại thay trẻ.",
        "supervision": "NEARBY",
        "hazards": [
            "nguồn không phù hợp độ tuổi",
            "sao chép không ghi nguồn",
            "chủ đề nhạy cảm gây áp lực",
        ],
        "stop": [
            "nguồn chứa nội dung gây hại",
            "bài yêu cầu tiết lộ trải nghiệm cá nhân",
            "không xác định được tác giả/nguồn",
        ],
        "material": (
            "gói bốn nguồn in đã kiểm duyệt, mẫu claim-evidence-reasoning và thẻ mã nguồn",
            "ba bài đọc thư viện công cộng được người lớn in, giấy ba cột và danh mục nguồn mẫu",
            "nguồn có tác giả/ngày, phù hợp độ tuổi, không yêu cầu đăng nhập hoặc dữ liệu cá nhân",
            [
                "mạng xã hội không kiểm chứng",
                "nguồn paywall cần tài khoản",
                "chủ đề sức khỏe cá nhân",
                "chép nguyên văn không dẫn nguồn",
            ],
        ),
        "secondary": ["OBJ_HUMANITIES_RESEARCH"],
        "prereq": ["ACT-0067"],
        "successors": ["ACT-0099"],
    },
    "ACT-0099": {
        "age": (120, 155),
        "readiness": [
            (
                "READY_MANAGES_RESEARCH_MILESTONE",
                "hoàn thành một nhiệm vụ nghiên cứu 20-30 phút và ghi nguồn đã dùng",
            )
        ],
        "purpose": "Quản lý một câu hỏi nghiên cứu qua mốc, nguồn và sản phẩm có thể kiểm chứng.",
        "direct": "Lập và thực hiện kế hoạch nghiên cứu nhỏ gồm câu hỏi, ba mốc, nguồn và sản phẩm cuối.",
        "indirect": ["tự quản lý dự án", "tổng hợp và truyền đạt"],
        "setup": "Chọn câu hỏi không yêu cầu dữ liệu cá nhân; chuẩn bị planner, source log, rubric và giới hạn thời gian/phạm vi.",
        "presentation": [
            "Chuyển chủ đề rộng thành một câu hỏi có thể trả lời trong thời gian và nguồn sẵn có.",
            "Chia thành ba mốc: tìm/đánh giá nguồn, ghi/tổ chức bằng chứng, tạo/kiểm tra sản phẩm.",
            "Với mỗi nguồn, ghi tác giả, ngày, nơi xuất bản, ý chính và lý do sử dụng hoặc loại bỏ.",
            "Tại mỗi mốc, so với rubric, ghi việc tiếp theo và thu hẹp phạm vi nếu bằng chứng không đủ.",
        ],
        "child_work": [
            "đặt câu hỏi",
            "quản lý ba mốc",
            "ghi nguồn",
            "tạo và tự kiểm sản phẩm",
        ],
        "restore": [
            "xếp planner/source log/sản phẩm vào một bìa mã hóa",
            "xóa bản tải tạm và trả tài liệu",
        ],
        "isolation": "Một câu hỏi và ba mốc; không đánh giá trẻ bằng tốc độ hoặc độ bóng bẩy sản phẩm.",
        "control": "Rubric kiểm tra câu hỏi, bằng chứng, nguồn và mốc; source log phải khớp tài liệu được dùng.",
        "duration": (40, 60),
        "repeatability": "Nhiều phiên trong 1-2 tuần; mỗi phiên kết thúc bằng trạng thái/mốc rõ ràng.",
        "supervision": "NEARBY",
        "hazards": [
            "thu thập dữ liệu cá nhân",
            "nguồn trực tuyến không phù hợp",
            "phạm vi quá lớn gây quá tải",
            "vi phạm bản quyền",
        ],
        "stop": [
            "dự án yêu cầu liên hệ người lạ",
            "nguồn yêu cầu tải file không tin cậy",
            "trẻ phải tiết lộ thông tin cá nhân",
            "không còn nguồn phù hợp độ tuổi",
        ],
        "material": (
            "planner ba mốc, source log, gói nguồn thư viện đã duyệt và vật liệu trình bày ngoại tuyến",
            "bìa hồ sơ giấy, bảng tiến độ tự vẽ, sách/tài liệu in do người lớn chọn và giấy/bút trình bày",
            "dùng mã dự án thay tên đầy đủ; nguồn phù hợp độ tuổi; lưu bản quyền/trích dẫn",
            [
                "tài khoản mạng xã hội",
                "liên hệ người lạ",
                "nguồn tải không rõ",
                "dữ liệu định danh trẻ",
            ],
        ),
        "secondary": ["OBJ_COMMUNICATION_ARGUMENTATION", "OBJ_HUMANITIES_RESEARCH"],
        "prereq": ["ACT-0074", "ACT-0085", "ACT-0097"],
        "successors": [],
    },
}


def build_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://sketch2life.local/schemas/montessori/golden-activity.v2.schema.json",
        "title": "Sketch2Life Golden Montessori Activity v2",
        "type": "object",
        "required": [
            "id",
            "version",
            "base_ref",
            "title",
            "age_band",
            "age_months",
            "area",
            "purpose_vi",
            "direct_aim_vi",
            "indirect_aims_vi",
            "objective_mapping",
            "readiness_criteria",
            "prerequisite_activity_ids",
            "progression_successor_ids",
            "prepared_environment_vi",
            "material_group_ids",
            "presentation_steps_vi",
            "child_work_cycle_vi",
            "restoration_steps_vi",
            "isolation_of_difficulty_vi",
            "control_of_error_vi",
            "duration_minutes",
            "repeatability_vi",
            "safety",
            "policy_constraints",
            "catalog_status",
            "variants",
            "completion_observations_vi",
            "review",
            "source_refs",
            "provenance",
        ],
        "properties": {
            "id": {"type": "string", "pattern": "^ACT-[0-9]{4}$"},
            "version": {"const": 2},
            "base_ref": {
                "type": "object",
                "required": ["activity_id", "version", "record_sha256"],
                "additionalProperties": False,
            },
            "title": {"type": "object", "required": ["vi-VN"]},
            "age_band": {"enum": ["0-3", "3-6", "6-9", "9-12"]},
            "age_months": {"type": "object", "required": ["min", "max", "guidance_vi"]},
            "area": {"type": "string", "minLength": 1},
            "purpose_vi": {"type": "string", "minLength": 10},
            "direct_aim_vi": {"type": "string", "minLength": 10},
            "indirect_aims_vi": {"type": "array", "minItems": 1, "uniqueItems": True},
            "objective_mapping": {
                "type": "object",
                "required": ["primary", "secondary"],
                "additionalProperties": False,
            },
            "readiness_criteria": {"type": "array", "minItems": 1},
            "prerequisite_activity_ids": {"type": "array", "uniqueItems": True},
            "progression_successor_ids": {"type": "array", "uniqueItems": True},
            "prepared_environment_vi": {"type": "string", "minLength": 20},
            "material_group_ids": {"type": "array", "minItems": 1, "uniqueItems": True},
            "presentation_steps_vi": {"type": "array", "minItems": 4},
            "child_work_cycle_vi": {"type": "array", "minItems": 3},
            "restoration_steps_vi": {"type": "array", "minItems": 2},
            "isolation_of_difficulty_vi": {"type": "string", "minLength": 15},
            "control_of_error_vi": {"type": "string", "minLength": 15},
            "duration_minutes": {"type": "object", "required": ["min", "max"]},
            "repeatability_vi": {"type": "string", "minLength": 15},
            "safety": {
                "type": "object",
                "required": ["minimum_supervision", "hazards_vi", "stop_conditions_vi"],
            },
            "policy_constraints": {"type": "array", "uniqueItems": True},
            "catalog_status": {"const": "ACTIVE_FIXTURE"},
            "variants": {"type": "array", "minItems": 3, "maxItems": 3},
            "completion_observations_vi": {"type": "array", "minItems": 2},
            "review": {
                "type": "object",
                "required": [
                    "status",
                    "reviewer_role",
                    "reviewed_at",
                    "production_eligible",
                ],
                "properties": {
                    "status": {
                        "enum": [
                            "PENDING_OWNER_REVIEW",
                            "PROVISIONAL_OWNER_REVIEWED",
                        ]
                    },
                    "reviewer_role": {"type": ["string", "null"]},
                    "reviewed_at": {"type": ["string", "null"]},
                    "production_eligible": {"const": False},
                },
                "additionalProperties": False,
            },
            "source_refs": {"type": "array", "minItems": 1, "uniqueItems": True},
            "provenance": {
                "type": "object",
                "required": ["authored_by", "authored_at", "source_type"],
            },
        },
        "additionalProperties": False,
    }


def main() -> None:
    for filename, expected in BASE_FILE_HASHES.items():
        actual = sha256_file(BASE_DIR / filename)
        if actual != expected:
            raise ValueError(f"FEAT-002 baseline hash mismatch: {filename}")

    base_doc = json.loads((BASE_DIR / "activities.v1.json").read_text(encoding="utf-8"))
    objectives_doc = json.loads(
        (BASE_DIR / "learning-objectives.v1.json").read_text(encoding="utf-8")
    )
    base_by_id = {item["id"]: item for item in base_doc["activities"]}
    objective_ids = {item["id"] for item in objectives_doc["objectives"]}
    if set(SPECS) - set(base_by_id):
        raise ValueError("golden selection references missing base activities")
    review_doc = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    review_by_id = {item["activity_id"]: item for item in review_doc["decisions"]}
    if set(review_by_id) != set(SPECS) or len(review_doc["decisions"]) != len(SPECS):
        raise ValueError(
            "owner review ledger must contain exactly the golden selection"
        )
    if any(
        item["activity_version"] != 2 or item["decision"] != "ACCEPT"
        for item in review_doc["decisions"]
    ):
        raise ValueError("all golden decisions must be ACCEPT for this reviewed build")
    if review_doc["production_eligible"] is not False:
        raise ValueError("owner review cannot authorize production eligibility")
    review_status = "PROVISIONAL_OWNER_REVIEWED"
    reviewer_role = review_doc["reviewer_role"]
    reviewed_at = review_doc["reviewed_at"]

    records: list[dict[str, Any]] = []
    materials: list[dict[str, Any]] = []
    selections: list[dict[str, Any]] = []
    progression: list[dict[str, str]] = []

    for activity_id, spec in SPECS.items():
        base = base_by_id[activity_id]
        numeric = activity_id.removeprefix("ACT-")
        group_id = f"GMG-{numeric}-01"
        primary_id = f"GMAT-{numeric}-PRIMARY"
        substitute_id = f"GMAT-{numeric}-SUBSTITUTE"
        primary, substitute, suitability, prohibited = spec["material"]
        materials.extend(
            [
                {
                    "id": primary_id,
                    "activity_id": activity_id,
                    "kind": "PRIMARY",
                    "label_vi": primary,
                    "suitability_vi": suitability,
                    "prohibited_vi": prohibited,
                    "review_status": review_status,
                    "production_eligible": False,
                },
                {
                    "id": substitute_id,
                    "activity_id": activity_id,
                    "kind": "HOUSEHOLD_SUBSTITUTE",
                    "label_vi": substitute,
                    "suitability_vi": suitability,
                    "prohibited_vi": prohibited,
                    "review_status": review_status,
                    "production_eligible": False,
                },
            ]
        )
        all_objectives = [base["objective_ids"][0], *spec["secondary"]]
        if not set(all_objectives) <= objective_ids:
            raise ValueError(f"unknown objective mapping for {activity_id}")
        base_hash = sha256_value(base)
        selections.append(
            {
                "activity_id": activity_id,
                "base_version": 1,
                "base_record_sha256": base_hash,
                "candidate_version": 2,
                "age_band": base["age_band"],
            }
        )
        for successor in spec["successors"]:
            progression.append(
                {
                    "from_activity_id": activity_id,
                    "to_activity_id": successor,
                    "relationship": "PREPARES_FOR",
                }
            )
        min_age, max_age = spec["age"]
        record = {
            "id": activity_id,
            "version": 2,
            "base_ref": {
                "activity_id": activity_id,
                "version": 1,
                "record_sha256": base_hash,
            },
            "title": base["title"],
            "age_band": base["age_band"],
            "age_months": {
                "min": min_age,
                "max": max_age,
                "guidance_vi": "Khoảng tuổi là hướng dẫn provisional; readiness và safety cụ thể vẫn quyết định eligibility.",
            },
            "area": base["area"],
            "purpose_vi": spec["purpose"],
            "direct_aim_vi": spec["direct"],
            "indirect_aims_vi": spec["indirect"],
            "objective_mapping": {
                "primary": {"id": all_objectives[0], "version": 1},
                "secondary": [
                    {"id": objective_id, "version": 1}
                    for objective_id in all_objectives[1:]
                ],
            },
            "readiness_criteria": [
                {"id": readiness_id, "observable_vi": observable}
                for readiness_id, observable in spec["readiness"]
            ],
            "prerequisite_activity_ids": spec["prereq"],
            "progression_successor_ids": spec["successors"],
            "prepared_environment_vi": spec["setup"],
            "material_group_ids": [group_id],
            "presentation_steps_vi": spec["presentation"],
            "child_work_cycle_vi": spec["child_work"],
            "restoration_steps_vi": spec["restore"],
            "isolation_of_difficulty_vi": spec["isolation"],
            "control_of_error_vi": spec["control"],
            "duration_minutes": {
                "min": spec["duration"][0],
                "max": spec["duration"][1],
            },
            "repeatability_vi": spec["repeatability"],
            "safety": {
                "minimum_supervision": spec["supervision"],
                "hazards_vi": spec["hazards"],
                "stop_conditions_vi": spec["stop"],
                "prohibited_substitutions_vi": prohibited,
            },
            "policy_constraints": ["CAREGIVER_PRESENT"]
            if base["age_band"] == "0-3"
            else [],
            "catalog_status": "ACTIVE_FIXTURE",
            "variants": [
                {
                    "id": f"VAR-{numeric}-SUPPORT",
                    "kind": "SUPPORT",
                    "activity_id": activity_id,
                    "activity_version": 2,
                    "objective_ids": all_objectives,
                    "guidance_vi": "Giảm số lượt hoặc chia nhỏ phần trình bày; giữ nguyên readiness, material và safety gates.",
                },
                {
                    "id": f"VAR-{numeric}-STANDARD",
                    "kind": "STANDARD",
                    "activity_id": activity_id,
                    "activity_version": 2,
                    "objective_ids": all_objectives,
                    "guidance_vi": "Thực hiện đầy đủ chuỗi golden activity như mô tả.",
                },
                {
                    "id": f"VAR-{numeric}-EXTENSION",
                    "kind": "EXTENSION",
                    "activity_id": activity_id,
                    "activity_version": 2,
                    "objective_ids": all_objectives,
                    "guidance_vi": "Tăng độ phức tạp quan sát hoặc số lượt trong giới hạn; không thay đổi identity hay hard rules.",
                },
            ],
            "completion_observations_vi": [
                "Ghi trẻ bắt đầu/tiếp tục/kết thúc chuỗi nào mà không chấm điểm tính cách hoặc năng lực.",
                "Ghi loại hỗ trợ và điều kiện vật liệu/safety thực tế, không suy diễn nguyên nhân tâm lý.",
            ],
            "review": {
                "status": review_status,
                "reviewer_role": reviewer_role,
                "reviewed_at": reviewed_at,
                "production_eligible": False,
            },
            "source_refs": base["source_refs"],
            "provenance": {
                "authored_by": "FEAT-013",
                "authored_at": "2026-08-25",
                "source_type": "golden_candidate_overlay",
            },
        }
        records.append(record)

    manifest = {
        "schema_version": 1,
        "parent_feature": "FEAT-002",
        "parent_commit": "2d61528",
        "base_file_hashes": BASE_FILE_HASHES,
        "selection_count": len(selections),
        "selections": selections,
    }
    material_doc = {
        "schema_version": 1,
        "groups": [
            {
                "id": f"GMG-{item['id'].removeprefix('ACT-')}-01",
                "activity_id": item["id"],
                "required": True,
                "any_of": [
                    f"GMAT-{item['id'].removeprefix('ACT-')}-PRIMARY",
                    f"GMAT-{item['id'].removeprefix('ACT-')}-SUBSTITUTE",
                ],
            }
            for item in records
        ],
        "options": materials,
    }
    provenance = {
        "schema_version": 1,
        "feature": "FEAT-013",
        "generated_at": "2026-08-25",
        "baseline_file_hashes": BASE_FILE_HASHES,
        "review_status": review_status,
        "owner_reviewed_at": reviewed_at,
        "reviewed_activity_count": len(records),
        "review_decision_ledger": "features/FEAT-013-montessori-golden-hardening/approvals/OWNER_CONTENT_REVIEW.v1.json",
        "production_eligible": False,
        "network_required": False,
        "limitations": [
            "Project-owner review is provisional and does not replace qualified Montessori review.",
            "Qualified Montessori review is required before production.",
            "No real child data or classroom outcome evidence was used.",
        ],
    }
    write_json(OUT_DIR / "selection-manifest.v1.json", manifest)
    write_json(
        OUT_DIR / "activities.v2.json", {"schema_version": 2, "activities": records}
    )
    write_json(OUT_DIR / "material-registry.v1.json", material_doc)
    write_json(
        OUT_DIR / "progression-edges.v1.json",
        {"schema_version": 1, "edges": progression},
    )
    write_json(OUT_DIR / "provenance.v1.json", provenance)
    write_json(SCHEMA_DIR / "golden-activity.v2.schema.json", build_schema())

    print("GOLDEN_CATALOG_BUILT")
    print(f"activities={len(records)}")
    for band in ("0-3", "3-6", "6-9", "9-12"):
        print(f"band_{band}={sum(item['age_band'] == band for item in records)}")
    print(f"materials={len(materials)}")
    print(f"progression_edges={len(progression)}")
    print(f"review_status={review_status} production_eligible=false")
    print("baseline_unchanged=true network_required=false")


if __name__ == "__main__":
    main()
