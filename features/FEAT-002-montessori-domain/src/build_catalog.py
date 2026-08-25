from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
CATALOG_DIR = ROOT / "data" / "activity-catalog" / "mvp"
SCHEMA_DIR = ROOT / "packages" / "domain-montessori" / "schemas"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def material_id(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"MAT_{normalized.upper()}"


OBJECTIVES = [
    ("OBJ_MOVEMENT_COORDINATION", "Phối hợp vận động", "movement"),
    ("OBJ_OBJECT_PERMANENCE", "Tính thường tồn của đồ vật", "sensorial"),
    ("OBJ_RECEPTIVE_LANGUAGE", "Ngôn ngữ tiếp nhận và biểu đạt", "language"),
    ("OBJ_INDEPENDENCE_SELF_CARE", "Độc lập trong tự chăm sóc", "practical_life"),
    ("OBJ_ORDER_GRACE_COURTESY", "Trật tự, lịch sự và cộng đồng", "practical_life"),
    (
        "OBJ_PRACTICAL_LIFE_SEQUENCE",
        "Chuỗi thao tác thực hành cuộc sống",
        "practical_life",
    ),
    ("OBJ_SENSORIAL_DISCRIMINATION", "Phân biệt và phân loại giác quan", "sensorial"),
    ("OBJ_EARLY_WRITING", "Chuẩn bị và phát triển viết", "language"),
    ("OBJ_EARLY_READING", "Âm vị, ghép từ và đọc ban đầu", "language"),
    (
        "OBJ_NUMBER_QUANTITY_PLACE_VALUE",
        "Số lượng, chữ số và giá trị hàng",
        "mathematics",
    ),
    (
        "OBJ_COSMIC_INTERCONNECTION",
        "Nhận biết tính liên kết trong vũ trụ",
        "cosmic_education",
    ),
    ("OBJ_SCIENTIFIC_OBSERVATION", "Quan sát và mô tả khoa học", "science"),
    (
        "OBJ_MATHEMATICAL_REASONING",
        "Lập luận toán học bằng vật liệu cụ thể",
        "mathematics",
    ),
    ("OBJ_LANGUAGE_ANALYSIS", "Phân tích và sử dụng ngôn ngữ", "language"),
    ("OBJ_SOCIAL_RESPONSIBILITY", "Trách nhiệm cá nhân và cộng đồng", "social_studies"),
    ("OBJ_ADVANCED_MATHEMATICS", "Toán học nâng cao và ứng dụng", "mathematics"),
    ("OBJ_SCIENTIFIC_INQUIRY", "Đặt câu hỏi và điều tra khoa học", "science"),
    (
        "OBJ_HUMANITIES_RESEARCH",
        "Nghiên cứu lịch sử, địa lý và xã hội",
        "cultural_studies",
    ),
    (
        "OBJ_COMMUNICATION_ARGUMENTATION",
        "Giao tiếp, bằng chứng và lập luận",
        "language",
    ),
    (
        "OBJ_PROJECT_SERVICE_LEADERSHIP",
        "Lập kế hoạch dự án và phục vụ cộng đồng",
        "social_studies",
    ),
]


ACTIVITIES: dict[str, list[tuple[str, str, str, str, str, tuple[str, ...]]]] = {
    "0-3": [
        (
            "visual_tracking_mobile",
            "Theo dõi vật chuyển động chậm",
            "movement",
            "OBJ_MOVEMENT_COORDINATION",
            "quan sát một vật tương phản được người lớn di chuyển chậm trong tầm nhìn",
            ("high-contrast mobile",),
        ),
        (
            "grasping_ring",
            "Cầm và chuyển vòng lớn",
            "movement",
            "OBJ_MOVEMENT_COORDINATION",
            "cầm, đổi tay và đặt một vòng lớn an toàn",
            ("large grasping ring", "low tray"),
        ),
        (
            "kicking_soft_ball",
            "Đá bóng mềm có dây neo",
            "movement",
            "OBJ_MOVEMENT_COORDINATION",
            "duỗi chân chạm một quả bóng mềm được neo an toàn",
            ("soft tethered ball", "floor mat"),
        ),
        (
            "object_permanence_scarf",
            "Tìm đồ vật dưới khăn",
            "sensorial",
            "OBJ_OBJECT_PERMANENCE",
            "tìm một đồ vật quen thuộc được che một phần rồi che hoàn toàn",
            ("light scarf", "large familiar object"),
        ),
        (
            "object_permanence_box",
            "Hộp thả bóng có khay",
            "sensorial",
            "OBJ_OBJECT_PERMANENCE",
            "thả bóng lớn vào hộp và quan sát bóng xuất hiện lại",
            ("object permanence box", "large ball"),
        ),
        (
            "safe_treasure_basket",
            "Khám phá giỏ đồ vật an toàn",
            "sensorial",
            "OBJ_OBJECT_PERMANENCE",
            "khám phá có giám sát các đồ vật lớn với chất liệu khác nhau",
            ("low basket", "large safe household objects"),
        ),
        (
            "texture_pairing",
            "Ghép cặp chất liệu",
            "sensorial",
            "OBJ_OBJECT_PERMANENCE",
            "sờ và ghép hai cặp vải có bề mặt khác nhau",
            ("large texture squares", "low tray"),
        ),
        (
            "sealed_sound_shakers",
            "Ghép cặp hộp âm thanh kín",
            "sensorial",
            "OBJ_RECEPTIVE_LANGUAGE",
            "lắc và ghép các hộp kín tạo âm thanh giống nhau",
            ("sealed sound shakers", "floor mat"),
        ),
        (
            "family_photo_naming",
            "Gọi tên người trong ảnh gia đình",
            "language",
            "OBJ_RECEPTIVE_LANGUAGE",
            "chỉ và gọi tên người quen trong ảnh do gia đình cung cấp",
            ("family photo cards",),
        ),
        (
            "body_part_naming",
            "Gọi tên bộ phận cơ thể",
            "language",
            "OBJ_RECEPTIVE_LANGUAGE",
            "chạm hoặc chỉ bộ phận cơ thể khi người lớn gọi tên",
            ("unbreakable mirror",),
        ),
        (
            "animal_object_naming",
            "Gọi tên mô hình động vật lớn",
            "language",
            "OBJ_RECEPTIVE_LANGUAGE",
            "ghép lời nói với mô hình động vật kích thước an toàn",
            ("large animal models", "basket"),
        ),
        (
            "object_picture_matching",
            "Ghép đồ vật với hình ảnh",
            "language",
            "OBJ_RECEPTIVE_LANGUAGE",
            "ghép ba đồ vật quen thuộc với thẻ ảnh tương ứng",
            ("large familiar objects", "picture cards"),
        ),
        (
            "posting_large_discs",
            "Thả đĩa lớn qua khe",
            "movement",
            "OBJ_MOVEMENT_COORDINATION",
            "cầm và thả các đĩa lớn qua khe vào hộp",
            ("large posting discs", "posting box"),
        ),
        (
            "nesting_cups",
            "Xếp cốc lồng nhau",
            "sensorial",
            "OBJ_MOVEMENT_COORDINATION",
            "thử lồng các cốc theo kích thước",
            ("nesting cups", "floor mat"),
        ),
        (
            "stacking_large_rings",
            "Xếp vòng lớn",
            "movement",
            "OBJ_MOVEMENT_COORDINATION",
            "xếp các vòng lớn lên trục theo khả năng",
            ("large stacking rings", "stable post"),
        ),
        (
            "transfer_large_objects",
            "Chuyển đồ vật lớn giữa hai bát",
            "practical_life",
            "OBJ_INDEPENDENCE_SELF_CARE",
            "dùng tay chuyển các vật lớn từ bát này sang bát khác",
            ("two bowls", "large transfer objects"),
        ),
        (
            "spoon_large_objects",
            "Dùng thìa chuyển vật lớn",
            "practical_life",
            "OBJ_INDEPENDENCE_SELF_CARE",
            "dùng thìa lớn chuyển vật không nuốt được giữa hai bát",
            ("large spoon", "two bowls", "large transfer objects"),
        ),
        (
            "pour_small_water",
            "Rót lượng nước nhỏ",
            "practical_life",
            "OBJ_INDEPENDENCE_SELF_CARE",
            "rót một lượng nước nhỏ giữa hai ca nhẹ với người lớn bên cạnh",
            ("two small pitchers", "water", "absorbent cloth"),
        ),
        (
            "handwashing_sequence",
            "Chuỗi rửa tay",
            "practical_life",
            "OBJ_INDEPENDENCE_SELF_CARE",
            "thực hiện từng bước làm ướt, xoa xà phòng, rửa và lau tay",
            ("low basin", "soap", "towel"),
        ),
        (
            "wipe_small_spill",
            "Lau vết nước nhỏ",
            "practical_life",
            "OBJ_INDEPENDENCE_SELF_CARE",
            "lấy khăn, lau vết nước và đặt khăn vào nơi quy định",
            ("small cloth", "low basket"),
        ),
        (
            "pull_on_socks",
            "Tập mang tất",
            "practical_life",
            "OBJ_INDEPENDENCE_SELF_CARE",
            "ngồi ổn định và kéo tất qua bàn chân với trợ giúp khi cần",
            ("loose socks", "low seat"),
        ),
        (
            "banana_slicing",
            "Cắt chuối bằng dụng cụ an toàn",
            "practical_life",
            "OBJ_INDEPENDENCE_SELF_CARE",
            "dùng dụng cụ cắt không sắc để chia chuối dưới giám sát trực tiếp",
            ("banana", "child-safe slicer", "plate"),
        ),
        (
            "water_small_plant",
            "Tưới cây nhỏ",
            "practical_life",
            "OBJ_ORDER_GRACE_COURTESY",
            "mang ca nhỏ, tưới lượng nước đã định và cất dụng cụ",
            ("small watering can", "plant", "cloth"),
        ),
        (
            "carry_low_tray",
            "Mang khay thấp bằng hai tay",
            "practical_life",
            "OBJ_ORDER_GRACE_COURTESY",
            "dùng hai tay mang khay nhẹ giữa hai vị trí gần",
            ("lightweight tray", "floor marker"),
        ),
        (
            "greeting_and_turn_taking",
            "Chào hỏi và chờ lượt",
            "practical_life",
            "OBJ_ORDER_GRACE_COURTESY",
            "thực hành chào, trao một vật lớn và chờ lượt cùng người lớn",
            ("large shared object", "floor mat"),
        ),
    ],
    "3-6": [
        (
            "dry_pouring",
            "Rót hạt khô",
            "practical_life",
            "OBJ_PRACTICAL_LIFE_SEQUENCE",
            "rót vật liệu khô giữa hai bình và xử lý phần rơi",
            ("two pitchers", "large dry counters", "tray"),
        ),
        (
            "water_pouring",
            "Rót nước có vạch giới hạn",
            "practical_life",
            "OBJ_PRACTICAL_LIFE_SEQUENCE",
            "rót nước đến vạch và lau khô khay",
            ("two pitchers", "water", "tray", "cloth"),
        ),
        (
            "spooning_grains",
            "Chuyển hạt bằng thìa",
            "practical_life",
            "OBJ_PRACTICAL_LIFE_SEQUENCE",
            "dùng thìa chuyển vật liệu giữa hai bát theo chiều thống nhất",
            ("spoon", "two bowls", "dry grains"),
        ),
        (
            "tong_transfer",
            "Chuyển vật bằng kẹp",
            "practical_life",
            "OBJ_PRACTICAL_LIFE_SEQUENCE",
            "dùng kẹp chuyển vật theo từng chiếc",
            ("child tongs", "two bowls", "transfer objects"),
        ),
        (
            "button_frame",
            "Khung cài nút",
            "practical_life",
            "OBJ_INDEPENDENCE_SELF_CARE",
            "mở và cài nút theo trình tự từ trên xuống",
            ("button dressing frame",),
        ),
        (
            "zipper_frame",
            "Khung kéo khóa",
            "practical_life",
            "OBJ_INDEPENDENCE_SELF_CARE",
            "tách, nối và kéo khóa với chuyển động có kiểm soát",
            ("zipper dressing frame",),
        ),
        (
            "handwashing_full",
            "Rửa tay theo chuỗi đầy đủ",
            "practical_life",
            "OBJ_PRACTICAL_LIFE_SEQUENCE",
            "chuẩn bị, rửa, lau tay và phục hồi khu vực",
            ("basin", "soap", "water jug", "towel"),
        ),
        (
            "table_setting",
            "Sắp bàn cho một người",
            "practical_life",
            "OBJ_ORDER_GRACE_COURTESY",
            "đặt khăn, đĩa, cốc và dụng cụ theo sơ đồ",
            ("place setting set", "placement mat"),
        ),
        (
            "flower_arranging",
            "Cắm hoa đơn giản",
            "practical_life",
            "OBJ_ORDER_GRACE_COURTESY",
            "chọn, đo, cắt bằng kéo an toàn và cắm hoa",
            ("small vase", "flowers", "child scissors", "water"),
        ),
        (
            "sweeping_marked_area",
            "Quét khu vực có đánh dấu",
            "practical_life",
            "OBJ_ORDER_GRACE_COURTESY",
            "gom vật liệu vào điểm đánh dấu rồi dùng hót rác",
            ("child broom", "dustpan", "floor marker"),
        ),
        (
            "pink_tower",
            "Tháp hồng",
            "sensorial",
            "OBJ_SENSORIAL_DISCRIMINATION",
            "phân cấp khối lập phương theo kích thước",
            ("pink tower", "floor mat"),
        ),
        (
            "brown_stair",
            "Cầu thang nâu",
            "sensorial",
            "OBJ_SENSORIAL_DISCRIMINATION",
            "phân cấp lăng trụ theo độ dày",
            ("brown stair", "floor mat"),
        ),
        (
            "red_rods",
            "Gậy đỏ",
            "sensorial",
            "OBJ_SENSORIAL_DISCRIMINATION",
            "phân cấp gậy theo chiều dài",
            ("red rods", "floor mat"),
        ),
        (
            "color_tablets_grading",
            "Phân cấp bảng màu",
            "sensorial",
            "OBJ_SENSORIAL_DISCRIMINATION",
            "ghép và phân cấp sắc độ từ đậm đến nhạt",
            ("color tablets", "work mat"),
        ),
        (
            "sound_cylinders",
            "Ghép ống âm thanh",
            "sensorial",
            "OBJ_SENSORIAL_DISCRIMINATION",
            "ghép cặp âm thanh và phân cấp độ lớn",
            ("sound cylinders", "work mat"),
        ),
        (
            "rough_smooth_boards",
            "Bảng nhám và mịn",
            "sensorial",
            "OBJ_SENSORIAL_DISCRIMINATION",
            "dùng đầu ngón tay phân biệt và gọi tên nhám/mịn",
            ("rough smooth boards",),
        ),
        (
            "geometric_solids",
            "Khối hình học",
            "sensorial",
            "OBJ_SENSORIAL_DISCRIMINATION",
            "khám phá, gọi tên và ghép khối với hình chiếu",
            ("geometric solids", "base cards"),
        ),
        (
            "sandpaper_letters",
            "Chữ cái nhám",
            "language",
            "OBJ_EARLY_WRITING",
            "tô theo nét chữ và phát âm âm vị tương ứng",
            ("sandpaper letters", "work mat"),
        ),
        (
            "movable_alphabet",
            "Bảng chữ cái rời",
            "language",
            "OBJ_EARLY_WRITING",
            "phân tích âm và ghép từ bằng chữ cái rời",
            ("movable alphabet", "picture cards"),
        ),
        (
            "phonetic_object_box",
            "Hộp đồ vật đọc âm vị",
            "language",
            "OBJ_EARLY_READING",
            "đọc nhãn âm vị và ghép với đồ vật",
            ("phonetic object box", "word labels"),
        ),
        (
            "metal_insets",
            "Khung kim loại luyện nét",
            "language",
            "OBJ_EARLY_WRITING",
            "đồ và tô các hình để luyện kiểm soát bút",
            ("metal insets", "paper", "colored pencils"),
        ),
        (
            "number_rods",
            "Gậy số",
            "mathematics",
            "OBJ_NUMBER_QUANTITY_PLACE_VALUE",
            "ghép chiều dài với tên số và số lượng",
            ("number rods", "number cards"),
        ),
        (
            "sandpaper_numerals",
            "Chữ số nhám",
            "mathematics",
            "OBJ_NUMBER_QUANTITY_PLACE_VALUE",
            "tô chữ số và gọi tên ký hiệu",
            ("sandpaper numerals",),
        ),
        (
            "spindle_boxes",
            "Hộp que tính",
            "mathematics",
            "OBJ_NUMBER_QUANTITY_PLACE_VALUE",
            "đếm số lượng vào ngăn và biểu diễn số không",
            ("spindle boxes", "spindles"),
        ),
        (
            "golden_bead_place_value",
            "Hệ thập phân hạt vàng",
            "mathematics",
            "OBJ_NUMBER_QUANTITY_PLACE_VALUE",
            "xây số bằng đơn vị, chục, trăm và nghìn",
            ("golden bead material", "number cards"),
        ),
    ],
    "6-9": [
        (
            "story_of_universe",
            "Câu chuyện về vũ trụ",
            "cosmic_education",
            "OBJ_COSMIC_INTERCONNECTION",
            "nghe câu chuyện khởi nguồn và lập bản đồ câu hỏi muốn khám phá",
            ("universe story cards", "question journal"),
        ),
        (
            "solar_system_scale",
            "Mô hình tỉ lệ Hệ Mặt Trời",
            "cosmic_education",
            "OBJ_COSMIC_INTERCONNECTION",
            "so sánh kích thước và khoảng cách bằng mô hình có ghi giới hạn tỉ lệ",
            ("planet cards", "measuring tape", "calculation sheet"),
        ),
        (
            "earth_layers_model",
            "Mô hình các lớp Trái Đất",
            "science",
            "OBJ_SCIENTIFIC_OBSERVATION",
            "xây và ghi nhãn mô hình các lớp Trái Đất",
            ("clay", "earth layer labels", "work board"),
        ),
        (
            "land_water_forms",
            "Địa hình đất và nước",
            "cultural_studies",
            "OBJ_SCIENTIFIC_OBSERVATION",
            "mô phỏng và ghép tên các cặp địa hình đất/nước",
            ("land water trays", "water", "labels"),
        ),
        (
            "plant_parts_observation",
            "Quan sát các bộ phận của cây",
            "science",
            "OBJ_SCIENTIFIC_OBSERVATION",
            "quan sát mẫu cây và ghi nhãn rễ, thân, lá, hoa",
            ("safe plant specimen", "magnifier", "labels"),
        ),
        (
            "animal_classification",
            "Phân loại động vật",
            "science",
            "OBJ_SCIENTIFIC_OBSERVATION",
            "phân loại thẻ động vật theo tiêu chí có giải thích",
            ("animal cards", "classification chart"),
        ),
        (
            "food_chain_web",
            "Xây lưới thức ăn",
            "science",
            "OBJ_COSMIC_INTERCONNECTION",
            "nối sinh vật thành chuỗi và lưới thức ăn",
            ("organism cards", "string", "work mat"),
        ),
        (
            "water_cycle_model",
            "Mô hình vòng tuần hoàn nước",
            "science",
            "OBJ_SCIENTIFIC_OBSERVATION",
            "quan sát bay hơi/ngưng tụ trong mô hình kín an toàn",
            ("clear container", "water", "cover", "observation sheet"),
        ),
        (
            "states_of_matter",
            "So sánh ba trạng thái vật chất",
            "science",
            "OBJ_SCIENTIFIC_OBSERVATION",
            "quan sát ví dụ rắn, lỏng, khí và ghi thuộc tính",
            ("safe samples", "observation cards"),
        ),
        (
            "simple_machines",
            "Khám phá máy cơ đơn giản",
            "science",
            "OBJ_MATHEMATICAL_REASONING",
            "thử đòn bẩy, mặt phẳng nghiêng và ghi thay đổi lực",
            ("lever set", "inclined plane", "weights"),
        ),
        (
            "stamp_game_multiplication",
            "Nhân với trò chơi tem",
            "mathematics",
            "OBJ_MATHEMATICAL_REASONING",
            "biểu diễn phép nhân nhiều chữ số bằng tem giá trị hàng",
            ("stamp game", "problem cards"),
        ),
        (
            "long_division_material",
            "Chia dài bằng vật liệu",
            "mathematics",
            "OBJ_MATHEMATICAL_REASONING",
            "phân phối số lượng theo hàng và ghi thương",
            ("division material", "problem cards", "recording sheet"),
        ),
        (
            "fraction_equivalence",
            "Phân số tương đương",
            "mathematics",
            "OBJ_MATHEMATICAL_REASONING",
            "xếp chồng mảnh phân số để tìm các biểu diễn tương đương",
            ("fraction circles", "recording sheet"),
        ),
        (
            "decimal_board",
            "Bảng số thập phân",
            "mathematics",
            "OBJ_MATHEMATICAL_REASONING",
            "xây, đọc và so sánh số thập phân bằng vật liệu",
            ("decimal board", "decimal cards"),
        ),
        (
            "angle_measurement",
            "Đo và phân loại góc",
            "mathematics",
            "OBJ_MATHEMATICAL_REASONING",
            "dựng, đo và phân loại góc",
            ("angle sticks", "protractor", "recording sheet"),
        ),
        (
            "area_equivalence",
            "Khám phá diện tích tương đương",
            "mathematics",
            "OBJ_MATHEMATICAL_REASONING",
            "biến đổi hình mà vẫn giữ diện tích và giải thích",
            ("area tiles", "grid paper"),
        ),
        (
            "grammar_symbols",
            "Phân tích từ loại bằng ký hiệu",
            "language",
            "OBJ_LANGUAGE_ANALYSIS",
            "gắn ký hiệu từ loại vào câu và giải thích lựa chọn",
            ("grammar symbols", "sentence cards"),
        ),
        (
            "sentence_analysis",
            "Phân tích thành phần câu",
            "language",
            "OBJ_LANGUAGE_ANALYSIS",
            "xác định chủ thể, hành động và bổ ngữ bằng sơ đồ",
            ("sentence analysis arrows", "sentence cards"),
        ),
        (
            "prefix_suffix_word_study",
            "Khảo sát tiền tố và hậu tố",
            "language",
            "OBJ_LANGUAGE_ANALYSIS",
            "xây họ từ và suy luận nghĩa từ cấu tạo",
            ("word cards", "word study chart"),
        ),
        (
            "short_research_report",
            "Báo cáo nghiên cứu ngắn",
            "language",
            "OBJ_LANGUAGE_ANALYSIS",
            "đặt câu hỏi, ghi nguồn và trình bày báo cáo ngắn",
            ("reference books", "research organizer"),
        ),
        (
            "timeline_of_life",
            "Dòng thời gian sự sống",
            "cosmic_education",
            "OBJ_COSMIC_INTERCONNECTION",
            "sắp xếp mốc phát triển sự sống và đặt câu hỏi liên hệ",
            ("timeline of life", "event cards"),
        ),
        (
            "continent_country_mapping",
            "Bản đồ châu lục và quốc gia",
            "cultural_studies",
            "OBJ_HUMANITIES_RESEARCH",
            "ghép bản đồ, xác định quốc gia và ghi một đặc điểm",
            ("puzzle map", "country labels", "atlas"),
        ),
        (
            "community_worker_interview",
            "Chuẩn bị phỏng vấn người làm việc cộng đồng",
            "social_studies",
            "OBJ_SOCIAL_RESPONSIBILITY",
            "lập câu hỏi lịch sự và kế hoạch phỏng vấn có người lớn",
            ("question planner", "permission checklist"),
        ),
        (
            "weekly_work_plan",
            "Lập kế hoạch công việc tuần",
            "practical_life",
            "OBJ_SOCIAL_RESPONSIBILITY",
            "ước lượng, ưu tiên và tự theo dõi các nhiệm vụ",
            ("weekly planner", "timer"),
        ),
        (
            "peace_circle_conflict",
            "Vòng tròn hòa bình giải quyết xung đột",
            "social_studies",
            "OBJ_SOCIAL_RESPONSIBILITY",
            "thực hành lắng nghe, nói nhu cầu và đề xuất giải pháp",
            ("talking piece", "peace prompt cards"),
        ),
    ],
    "9-12": [
        (
            "powers_exponents",
            "Lũy thừa và mẫu hình",
            "mathematics",
            "OBJ_ADVANCED_MATHEMATICS",
            "xây bảng lũy thừa và giải thích mẫu hình",
            ("bead material", "exponent cards", "recording sheet"),
        ),
        (
            "square_cube_roots",
            "Căn bậc hai và căn bậc ba",
            "mathematics",
            "OBJ_ADVANCED_MATHEMATICS",
            "dùng vật liệu hình học để liên hệ số và căn",
            ("root material", "number cards"),
        ),
        (
            "algebra_balance",
            "Cân bằng phương trình",
            "mathematics",
            "OBJ_ADVANCED_MATHEMATICS",
            "mô hình hóa phép biến đổi tương đương trên cân",
            ("balance model", "algebra tiles"),
        ),
        (
            "ratio_recipe",
            "Tỉ lệ qua công thức",
            "mathematics",
            "OBJ_ADVANCED_MATHEMATICS",
            "điều chỉnh công thức và kiểm tra tỉ lệ",
            ("recipe card", "measuring tools", "calculator"),
        ),
        (
            "percent_budget",
            "Phần trăm trong ngân sách",
            "mathematics",
            "OBJ_ADVANCED_MATHEMATICS",
            "phân bổ ngân sách giả định và kiểm tra tổng phần trăm",
            ("budget cards", "calculator", "recording sheet"),
        ),
        (
            "fraction_decimal_percent",
            "Chuyển đổi phân số, thập phân, phần trăm",
            "mathematics",
            "OBJ_ADVANCED_MATHEMATICS",
            "biểu diễn cùng giá trị theo ba dạng",
            ("fraction cards", "decimal grid", "percent cards"),
        ),
        (
            "geometric_constructions",
            "Dựng hình bằng compa và thước",
            "mathematics",
            "OBJ_ADVANCED_MATHEMATICS",
            "dựng đường trung trực, phân giác và ghi lý do",
            ("compass", "straightedge", "paper"),
        ),
        (
            "pythagorean_exploration",
            "Khám phá định lý Pythagore",
            "mathematics",
            "OBJ_ADVANCED_MATHEMATICS",
            "so sánh diện tích hình vuông trên ba cạnh tam giác vuông",
            ("pythagorean tiles", "grid paper"),
        ),
        (
            "volume_measurement",
            "Đo và tính thể tích",
            "mathematics",
            "OBJ_ADVANCED_MATHEMATICS",
            "đo vật thể, dự đoán và kiểm tra thể tích",
            ("measuring tools", "unit cubes", "recording sheet"),
        ),
        (
            "statistics_survey",
            "Khảo sát và mô tả dữ liệu",
            "mathematics",
            "OBJ_ADVANCED_MATHEMATICS",
            "thiết kế khảo sát không nhạy cảm và biểu diễn dữ liệu",
            ("survey template", "graph paper", "calculator"),
        ),
        (
            "cell_microscopy",
            "Quan sát tế bào bằng kính hiển vi",
            "science",
            "OBJ_SCIENTIFIC_INQUIRY",
            "chuẩn bị tiêu bản an toàn, quan sát và vẽ có nhãn",
            ("microscope", "prepared slides", "observation sheet"),
        ),
        (
            "classification_key",
            "Xây khóa phân loại",
            "science",
            "OBJ_SCIENTIFIC_INQUIRY",
            "tạo khóa lưỡng phân cho bộ mẫu hoặc thẻ",
            ("specimen cards", "classification template"),
        ),
        (
            "ecosystem_field_survey",
            "Khảo sát hệ sinh thái tại chỗ",
            "science",
            "OBJ_SCIENTIFIC_INQUIRY",
            "lập ô quan sát, ghi dữ liệu và không làm hại sinh vật",
            ("field notebook", "quadrat string", "magnifier"),
        ),
        (
            "mixture_separation",
            "Tách hỗn hợp an toàn",
            "science",
            "OBJ_SCIENTIFIC_INQUIRY",
            "chọn lọc, lắng, lọc hoặc bay hơi dưới giám sát",
            ("safe mixtures", "filter setup", "safety glasses"),
        ),
        (
            "energy_transfer",
            "Theo dõi truyền năng lượng",
            "science",
            "OBJ_SCIENTIFIC_INQUIRY",
            "xây mô hình đơn giản và ghi chuỗi truyền năng lượng",
            ("safe energy model", "measurement sheet"),
        ),
        (
            "moon_phase_model",
            "Mô hình pha Mặt Trăng",
            "science",
            "OBJ_COSMIC_INTERCONNECTION",
            "dùng nguồn sáng và mô hình để giải thích các pha",
            ("lamp", "moon sphere", "observation chart"),
        ),
        (
            "deep_time_timeline",
            "Dòng thời gian địa chất",
            "cosmic_education",
            "OBJ_HUMANITIES_RESEARCH",
            "đặt các mốc địa chất trên dòng thời gian tỉ lệ",
            ("deep time timeline", "event cards", "measuring tape"),
        ),
        (
            "ancient_civilization_research",
            "Nghiên cứu nền văn minh cổ",
            "cultural_studies",
            "OBJ_HUMANITIES_RESEARCH",
            "so sánh nguồn và trình bày một câu hỏi nghiên cứu",
            ("reference sources", "source evaluation sheet"),
        ),
        (
            "migration_trade_map",
            "Lập bản đồ di cư và thương mại",
            "cultural_studies",
            "OBJ_HUMANITIES_RESEARCH",
            "biểu diễn tuyến đường và phân tích nguyên nhân/hệ quả",
            ("world map", "route strings", "source cards"),
        ),
        (
            "civic_decision_simulation",
            "Mô phỏng quyết định cộng đồng",
            "social_studies",
            "OBJ_HUMANITIES_RESEARCH",
            "xem xét nhiều góc nhìn, tiêu chí và ghi quyết định",
            ("scenario cards", "decision matrix"),
        ),
        (
            "classroom_enterprise",
            "Mô phỏng doanh nghiệp lớp học",
            "social_studies",
            "OBJ_PROJECT_SERVICE_LEADERSHIP",
            "lập vai trò, chi phí, giá và quy tắc công bằng",
            ("enterprise planner", "play currency", "calculator"),
        ),
        (
            "evidence_based_argument",
            "Viết lập luận dựa trên bằng chứng",
            "language",
            "OBJ_COMMUNICATION_ARGUMENTATION",
            "nêu luận điểm, chọn bằng chứng và phản hồi ý kiến khác",
            ("source packet", "argument organizer"),
        ),
        (
            "literary_comparison",
            "So sánh hai tác phẩm",
            "language",
            "OBJ_COMMUNICATION_ARGUMENTATION",
            "so sánh chủ đề, cấu trúc và dẫn chứng từ văn bản",
            ("two texts", "comparison organizer"),
        ),
        (
            "independent_research_project",
            "Dự án nghiên cứu độc lập",
            "language",
            "OBJ_PROJECT_SERVICE_LEADERSHIP",
            "lập câu hỏi, mốc tiến độ, nguồn và sản phẩm trình bày",
            ("project planner", "source log", "presentation materials"),
        ),
        (
            "community_service_project",
            "Lập kế hoạch dự án phục vụ cộng đồng",
            "social_studies",
            "OBJ_PROJECT_SERVICE_LEADERSHIP",
            "xác định nhu cầu, hỏi ý kiến, lập kế hoạch an toàn và phản tư",
            ("service planner", "stakeholder checklist", "reflection journal"),
        ),
    ],
}


AGE_CONFIG = {
    "0-3": (
        0,
        35,
        "DIRECT",
        ["caregiver_present"],
        ["CAREGIVER_PRESENT"],
        ["ami-0-3", "ami-programme-levels"],
    ),
    "3-6": (
        36,
        71,
        "NEARBY",
        ["follows_one_step_direction"],
        [],
        ["ami-3-6", "ams-early-childhood-curriculum"],
    ),
    "6-9": (
        72,
        107,
        "NEARBY",
        ["reads_simple_instructions"],
        [],
        ["ami-cosmic-education", "ams-elementary-curriculum"],
    ),
    "9-12": (
        108,
        155,
        "NEARBY",
        ["works_with_multi_step_plan"],
        [],
        ["ami-cosmic-education", "ams-elementary-curriculum"],
    ),
}


PREREQUISITE_SLUGS = {
    "object_permanence_box": ["object_permanence_scarf"],
    "spoon_large_objects": ["transfer_large_objects"],
    "banana_slicing": ["carry_low_tray"],
    "golden_bead_place_value": ["number_rods"],
    "long_division_material": ["stamp_game_multiplication"],
    "pythagorean_exploration": ["geometric_constructions"],
    "independent_research_project": ["evidence_based_argument"],
    "community_service_project": ["civic_decision_simulation"],
}


def build() -> None:
    flattened: list[tuple[str, tuple[str, str, str, str, str, tuple[str, ...]]]] = [
        (band, item) for band, items in ACTIVITIES.items() for item in items
    ]
    if len(flattened) != 100 or any(len(items) != 25 for items in ACTIVITIES.values()):
        raise ValueError(
            "Catalog baseline must contain exactly 25 activities per band and 100 total"
        )

    slug_to_id = {
        item[0]: f"ACT-{index:04d}" for index, (_, item) in enumerate(flattened, 1)
    }
    records: list[dict[str, Any]] = []
    for index, (band, item) in enumerate(flattened, 1):
        slug, title_vi, area, objective_id, action_vi, materials = item
        min_months, max_months, supervision, readiness, policies, source_refs = (
            AGE_CONFIG[band]
        )
        record = {
            "id": f"ACT-{index:04d}",
            "version": 1,
            "slug": slug,
            "title": {"vi-VN": title_vi},
            "age_band": band,
            "age_months": {"min": min_months, "max": max_months},
            "area": area,
            "objective_ids": [objective_id],
            "readiness_tags": readiness,
            "prerequisite_activity_ids": [
                slug_to_id[value] for value in PREREQUISITE_SLUGS.get(slug, [])
            ],
            "material_groups": [
                {
                    "id": f"MG-{index:04d}-{position:02d}",
                    "required": True,
                    "any_of": [
                        material_id(material),
                        f"{material_id(material)}_APPROVED_SUBSTITUTE",
                    ],
                    "label_vi": material,
                    "home_substitute_vi": "vật liệu tương đương, an toàn và phù hợp kích thước",
                }
                for position, material in enumerate(materials, 1)
            ],
            "duration_minutes": 10
            if band in {"0-3", "3-6"}
            else 25
            if band == "6-9"
            else 40,
            "steps_vi": [
                "Người lớn chuẩn bị môi trường gọn, đủ vật liệu và loại bỏ yếu tố gây xao nhãng.",
                f"Giới thiệu ngắn gọn cách {action_vi}.",
                "Trẻ thực hiện theo nhịp riêng; người lớn quan sát và chỉ hỗ trợ khi cần.",
                "Trẻ cùng người lớn phục hồi vật liệu và ghi nhận mức độ độc lập.",
            ],
            "safety": {
                "minimum_supervision": supervision,
                "hazards_vi": [
                    "kiểm tra vật liệu nguyên vẹn, không độc hại và phù hợp kích thước trước khi dùng"
                ],
                "stop_conditions_vi": [
                    "trẻ khó chịu hoặc mệt",
                    "vật liệu hỏng hoặc xuất hiện nguy cơ mất an toàn",
                ],
            },
            "policy_constraints": policies,
            "catalog_status": "ACTIVE_FIXTURE",
            "review": {
                "status": "PENDING_OWNER_REVIEW",
                "reviewer_role": None,
                "reviewed_at": None,
                "production_eligible": False,
            },
            "source_refs": source_refs,
            "provenance": {
                "authored_by": "FEAT-002",
                "authored_at": "2026-08-25",
                "source_type": "provisional_fixture_catalog",
            },
        }
        records.append(record)

    objectives = [
        {
            "id": objective_id,
            "version": 1,
            "title": {"vi-VN": title_vi},
            "area": area,
            "status": "DRAFT",
            "production_eligible": False,
        }
        for objective_id, title_vi, area in OBJECTIVES
    ]

    provenance = {
        "catalog_version": 1,
        "generated_at": "2026-08-25",
        "review_policy": {
            "current_status": "PENDING_OWNER_REVIEW",
            "owner_review_result": "PROVISIONAL_OWNER_REVIEWED",
            "production_gate": "QUALIFIED_MONTESSORI_REVIEW_REQUIRED",
        },
        "source_register_ids": sorted(
            {source for record in records for source in record["source_refs"]}
        ),
        "limitations": [
            "The catalog is synthetic/provisional and is not production-approved Montessori content.",
            "Age bands guide review; activity-specific readiness and supervision remain authoritative.",
            "No real child data was used.",
        ],
    }

    activity_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://sketch2life.local/schemas/montessori/activity.v1.schema.json",
        "title": "Sketch2Life Montessori Activity v1",
        "type": "object",
        "required": [
            "id",
            "version",
            "slug",
            "title",
            "age_band",
            "age_months",
            "area",
            "objective_ids",
            "readiness_tags",
            "prerequisite_activity_ids",
            "material_groups",
            "duration_minutes",
            "steps_vi",
            "safety",
            "catalog_status",
            "review",
            "source_refs",
            "provenance",
        ],
        "properties": {
            "id": {"type": "string", "pattern": "^ACT-[0-9]{4}$"},
            "version": {"type": "integer", "minimum": 1},
            "slug": {"type": "string", "pattern": "^[a-z0-9_]+$"},
            "title": {"type": "object", "required": ["vi-VN"]},
            "age_band": {"enum": ["0-3", "3-6", "6-9", "9-12"]},
            "age_months": {"type": "object", "required": ["min", "max"]},
            "area": {"type": "string"},
            "objective_ids": {"type": "array", "minItems": 1, "uniqueItems": True},
            "readiness_tags": {"type": "array", "uniqueItems": True},
            "prerequisite_activity_ids": {"type": "array", "uniqueItems": True},
            "material_groups": {"type": "array", "minItems": 1},
            "duration_minutes": {"type": "integer", "minimum": 1, "maximum": 120},
            "steps_vi": {"type": "array", "minItems": 3},
            "safety": {
                "type": "object",
                "required": ["minimum_supervision", "hazards_vi", "stop_conditions_vi"],
            },
            "catalog_status": {"enum": ["ACTIVE_FIXTURE", "INACTIVE"]},
            "review": {"type": "object", "required": ["status", "production_eligible"]},
            "source_refs": {"type": "array", "minItems": 1, "uniqueItems": True},
            "provenance": {
                "type": "object",
                "required": ["authored_by", "authored_at", "source_type"],
            },
        },
        "additionalProperties": False,
    }

    objective_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://sketch2life.local/schemas/montessori/learning-objective.v1.schema.json",
        "title": "Sketch2Life Learning Objective v1",
        "type": "object",
        "required": ["id", "version", "title", "area", "status", "production_eligible"],
        "properties": {
            "id": {"type": "string", "pattern": "^OBJ_[A-Z0-9_]+$"},
            "version": {"type": "integer", "minimum": 1},
            "title": {"type": "object", "required": ["vi-VN"]},
            "area": {"type": "string"},
            "status": {
                "enum": [
                    "DRAFT",
                    "PROVISIONAL_OWNER_REVIEWED",
                    "QUALIFIED_REVIEWED",
                    "RETIRED",
                ]
            },
            "production_eligible": {"type": "boolean"},
        },
        "additionalProperties": False,
    }

    write_json(
        CATALOG_DIR / "activities.v1.json", {"schema_version": 1, "activities": records}
    )
    write_json(
        CATALOG_DIR / "learning-objectives.v1.json",
        {"schema_version": 1, "objectives": objectives},
    )
    write_json(CATALOG_DIR / "provenance.v1.json", provenance)
    write_json(SCHEMA_DIR / "activity.v1.schema.json", activity_schema)
    write_json(SCHEMA_DIR / "learning-objective.v1.schema.json", objective_schema)

    print("CATALOG_BUILT")
    print(f"activities={len(records)}")
    print(f"objectives={len(objectives)}")
    for band in AGE_CONFIG:
        print(f"band_{band}={sum(record['age_band'] == band for record in records)}")


if __name__ == "__main__":
    build()
