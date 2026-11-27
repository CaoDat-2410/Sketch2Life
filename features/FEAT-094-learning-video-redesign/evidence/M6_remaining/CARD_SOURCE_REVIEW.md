# 40 thẻ kiến thức: đối chiếu nguồn (FEAT-094, 2026-11-27)

Trạng thái thẻ: vẫn `DRAFT`. Chỉ chủ sở hữu được duyệt (quyết định D3).

**Cách kiểm:** công cụ đọc web của Claude mở bài Wikipedia tiếng Việt và tiếng Anh rồi xếp từng câu vào ba mức. Nhiều
trang dài nên một phần kết luận dựa trên bản tóm tắt do model của công cụ trích ra, không phải đọc nguyên văn toàn
trang. Wikipedia là nguồn phổ thông, không phải nguồn chuyên môn đã thẩm định. Hãy mở trang trước khi duyệt.

| Mức | Số câu |
|---|---|
| Có trang hỗ trợ | 141 |
| Chỉ hỗ trợ một phần | 81 |
| Không thấy trong phần đã đọc (chưa chắc sai) | 19 |
| Tổng | 241 |

Cách duyệt một thẻ sau khi đã sửa hoặc bỏ câu chưa chắc (nguồn đã nằm sẵn trong thẻ; chạy lệnh nghĩa là bạn đã mở và
chấp nhận các trang đó):

```powershell
python tools/knowledge_cards.py approve vi.transport.train --reviewer "<tên>"
```

Thẻ dễ duyệt trước (mọi câu có trang hỗ trợ): bướm, voi, bạch tuộc, sao biển, tàu hỏa.

## vi.animals.butterfly

Nguồn: [Bướm](https://vi.wikipedia.org/wiki/B%C6%B0%E1%BB%9Bm); [Butterfly](https://en.wikipedia.org/wiki/Butterfly)

Mọi câu đều có trang hỗ trợ.

## vi.animals.cat

Nguồn: [Mèo](https://vi.wikipedia.org/wiki/M%C3%A8o); [Cat](https://en.wikipedia.org/wiki/Cat)

- **chỉ một phần** `what`: Mèo là vật nuôi nhỏ, đi bằng bốn chân.
- **chỉ một phần** `part-4`: Cái đuôi giúp mèo giữ thăng bằng khi leo trèo.

Lưu ý: Bốn chân không được nói rõ; đuôi giữ thăng bằng, trang không nhắc leo trèo.

## vi.animals.deer

Nguồn: [Họ Hươu nai](https://vi.wikipedia.org/wiki/H%C6%B0%C6%A1u); [Deer](https://en.wikipedia.org/wiki/Deer)

- **chỉ một phần** `part-1`: Chân dài và thon giúp hươu chạy rất nhanh.
- **không thấy** `part-3`: Tai hươu xoay được để nghe ngóng xung quanh.
- **không thấy** `part-4`: Mắt ở hai bên đầu giúp hươu nhìn rộng.
- **chỉ một phần** `use`: Hươu ăn lá non và là một phần của khu rừng.

Lưu ý: Trang gọi là gạc, không phải sừng.

## vi.animals.dog

Nguồn: [Chó](https://vi.wikipedia.org/wiki/Ch%C3%B3); [Dog](https://en.wikipedia.org/wiki/Dog)

- **không thấy** `part-3`: Chó thường vẫy đuôi khi gặp người quen.
- **chỉ một phần** `part-4`: Bốn chân khỏe giúp chó chạy nhanh.

## vi.animals.elephant

Nguồn: [Voi](https://vi.wikipedia.org/wiki/Voi); [Elephant](https://en.wikipedia.org/wiki/Elephant)

Mọi câu đều có trang hỗ trợ.

Lưu ý: Voi châu Á cái thường ngà rất nhỏ hoặc không có.

## vi.animals.fish

Nguồn: [Cá](https://vi.wikipedia.org/wiki/C%C3%A1); [Fish](https://en.wikipedia.org/wiki/Fish)

- **chỉ một phần** `part-4`: Lớp vảy mỏng bảo vệ thân cá.
- **chỉ một phần** `use`: Cá góp phần làm sông hồ thêm sự sống.

## vi.animals.horse

Nguồn: [Horse](https://en.wikipedia.org/wiki/Horse)

- **chỉ một phần** `part-1`: Móng cứng đỡ chân ngựa khi chạy.
- **chỉ một phần** `part-2`: Bờm là hàng lông dài trên cổ ngựa.
- **không thấy** `part-3`: Ngựa vẫy đuôi dài để xua ruồi muỗi.
- **chỉ một phần** `use`: Ngựa giúp người chở hàng và kéo xe.

Lưu ý: Bài tiếng Việt không hỗ trợ câu nào.

## vi.animals.rabbit

Nguồn: [Thỏ](https://vi.wikipedia.org/wiki/Th%E1%BB%8F); [Rabbit](https://en.wikipedia.org/wiki/Rabbit)

- **chỉ một phần** `part-4`: Đuôi thỏ ngắn và tròn như cục bông.

## vi.animals.turtle

Nguồn: [Turtle](https://en.wikipedia.org/wiki/Turtle)

- **chỉ một phần** `part-3`: Chân rùa ngắn nên rùa bò chậm trên cạn.
- **chỉ một phần** `use`: Rùa ăn rong, cỏ hoặc con vật nhỏ trong thiên nhiên.

Lưu ý: Trang nói chậm do mai nặng, không phải do chân ngắn.

## vi.birds.chicken

Nguồn: [Gà](https://vi.wikipedia.org/wiki/G%C3%A0); [Chicken](https://en.wikipedia.org/wiki/Chicken)

- **chỉ một phần** `part-1`: Gà dùng mỏ nhọn để mổ hạt.
- **chỉ một phần** `part-2`: Chân có móng giúp gà bới đất tìm mồi.
- **chỉ một phần** `part-4`: Gà mẹ xòe cánh ủ ấm cho gà con.
- **chỉ một phần** `use`: Gà đẻ trứng cho người và bắt sâu trong vườn.

## vi.birds.dove

Nguồn: [Họ Bồ câu](https://vi.wikipedia.org/wiki/B%E1%BB%93_c%C3%A2u); [Columbidae](https://en.wikipedia.org/wiki/Columbidae)

- **chỉ một phần** `part-1`: Cánh khỏe giúp bồ câu bay đường dài.
- **chỉ một phần** `part-2`: Bồ câu dùng mỏ nhỏ nhặt hạt.
- **không thấy** `use`: Bồ câu giỏi tìm đường về tổ từ rất xa.

## vi.birds.duck

Nguồn: [Vịt](https://vi.wikipedia.org/wiki/V%E1%BB%8Bt); [Duck](https://en.wikipedia.org/wiki/Duck)

- **chỉ một phần** `what`: Vịt là loài chim bơi rất giỏi.
- **chỉ một phần** `part-1`: Chân có màng giúp vịt đạp nước.
- **không thấy** `part-3`: Lông vịt trơn nên khó thấm nước.
- **chỉ một phần** `part-4`: Nhiều loài vịt trời bay được rất xa.

## vi.birds.owl

Nguồn: [Bộ Cú](https://vi.wikipedia.org/wiki/C%C3%BA_m%C3%A8o); [Owl](https://en.wikipedia.org/wiki/Owl)

- **chỉ một phần** `use`: Cú mèo bắt chuột, giúp bảo vệ mùa màng.

## vi.birds.parrot

Nguồn: [Bộ Vẹt](https://vi.wikipedia.org/wiki/V%E1%BA%B9t); [Parrot](https://en.wikipedia.org/wiki/Parrot)

- **chỉ một phần** `part-3`: Đôi cánh giúp vẹt bay giữa các tán cây.
- **chỉ một phần** `use`: Vẹt ăn quả, hạt và giúp phát tán hạt giống.

Lưu ý: MÂU THUẪN: trang nói vẹt phá hạt chứ không phát tán hạt. Nên sửa câu use.

## vi.birds.peacock

Nguồn: [Công (chim)](https://vi.wikipedia.org/wiki/C%C3%B4ng_(chim)); [Peafowl](https://en.wikipedia.org/wiki/Peafowl)

- **chỉ một phần** `part-2`: Đôi chân khỏe giúp công đi và chạy trên đất.
- **chỉ một phần** `part-4`: Trên đầu công có chùm lông nhỏ như vương miện.

Lưu ý: Trang tả mào dài hẹp, không nói như vương miện.

## vi.birds.sparrow

Nguồn: [Sẻ nhà](https://vi.wikipedia.org/wiki/S%E1%BA%BB_nh%C3%A0); [Bộ Sẻ](https://vi.wikipedia.org/wiki/Chim_s%E1%BA%BB); [House sparrow](https://en.wikipedia.org/wiki/House_sparrow)

- **chỉ một phần** `part-1`: Mỏ ngắn và chắc giúp chim sẻ nhặt hạt.
- **chỉ một phần** `part-2`: Đôi cánh giúp chim sẻ bay từ cành này sang cành khác.
- **chỉ một phần** `part-3`: Ngón chân bám chặt giúp chim đậu trên cành.
- **không thấy** `part-4`: Bộ lông giúp chim giữ ấm cơ thể.
- **chỉ một phần** `use`: Chim sẻ ăn hạt và bắt sâu trong vườn.

## vi.birds.swan

Nguồn: [Thiên nga](https://vi.wikipedia.org/wiki/Thi%C3%AAn_nga); [Swan](https://en.wikipedia.org/wiki/Swan)

- **chỉ một phần** `what`: Thiên nga là loài chim lớn bơi trên hồ.
- **chỉ một phần** `part-1`: Chiếc cổ dài giúp thiên nga tìm cây dưới nước.
- **không thấy** `part-2`: Chân có màng giúp thiên nga bơi nhẹ nhàng.
- **chỉ một phần** `part-3`: Đôi cánh rộng giúp thiên nga bay xa.
- **không thấy** `part-4`: Lông dày giúp thiên nga giữ ấm trên nước.
- **chỉ một phần** `use`: Thiên nga ăn cây thủy sinh và làm hồ thêm đẹp.

## vi.insects.ant

Nguồn: [Kiến](https://vi.wikipedia.org/wiki/Ki%E1%BA%BFn); [Ant](https://en.wikipedia.org/wiki/Ant)

- **chỉ một phần** `what`: Kiến là côn trùng nhỏ sống thành đàn đông.
- **chỉ một phần** `part-1`: Kiến chạm râu để trao đổi tin cho nhau.
- **chỉ một phần** `part-2`: Sáu chân giúp kiến đi nhanh và leo cao.
- **không thấy** `use`: Kiến dọn vụn thức ăn và làm đất tơi xốp.

## vi.insects.bee

Nguồn: [Ong](https://vi.wikipedia.org/wiki/Ong); [Bee](https://en.wikipedia.org/wiki/Bee)

- **chỉ một phần** `what`: Ong là côn trùng chăm chỉ sống thành đàn.
- **chỉ một phần** `part-3`: Ong mang phấn hoa trên hai chân sau.
- **chỉ một phần** `part-4`: Ong có ngòi để tự vệ nên ta nhìn từ xa.

Lưu ý: Chỉ nhiều loài mang phấn ở chân sau.

## vi.insects.caterpillar

Nguồn: [Sâu bướm](https://vi.wikipedia.org/wiki/S%C3%A2u_b%C6%B0%E1%BB%9Bm); [Ong](https://vi.wikipedia.org/wiki/Ong); [Caterpillar](https://en.wikipedia.org/wiki/Caterpillar)

- **chỉ một phần** `what`: Sâu bướm là bạn bướm khi còn nhỏ.
- **chỉ một phần** `part-1`: Sâu bướm gặm lá suốt ngày để lớn nhanh.
- **chỉ một phần** `part-2`: Nhiều chân ngắn giúp sâu bám chắc vào cành.
- **chỉ một phần** `use`: Sâu bướm lớn lên thành bướm giúp hoa thụ phấn.

Lưu ý: Sâu bướm là ấu trùng của cả bướm đêm; nhiều loài phá cây trồng.

## vi.insects.dragonfly

Nguồn: [Chuồn chuồn](https://vi.wikipedia.org/wiki/Chu%E1%BB%93n_chu%E1%BB%93n); [Odonata](https://en.wikipedia.org/wiki/Odonata)

- **chỉ một phần** `part-1`: Bốn cánh mỏng giúp chuồn chuồn bay và đứng yên trên không.
- **chỉ một phần** `part-2`: Đôi mắt to giúp chuồn chuồn nhìn gần như khắp phía.
- **chỉ một phần** `part-3`: Thân sau dài giúp chuồn chuồn giữ thăng bằng.

## vi.insects.ladybug

Nguồn: [Họ Bọ rùa](https://vi.wikipedia.org/wiki/B%E1%BB%8D_r%C3%B9a); [Coccinellidae](https://en.wikipedia.org/wiki/Coccinellidae)

- **không thấy** `part-3`: Bọ rùa có sáu chân để bò trên lá.
- **không thấy** `part-4`: Đôi râu giúp bọ rùa tìm đường và tìm mồi.

## vi.nature.flower

Nguồn: [Hoa](https://vi.wikipedia.org/wiki/Hoa); [Flower](https://en.wikipedia.org/wiki/Flower)

- **chỉ một phần** `what`: Hoa là phần của cây có nhiều cánh xinh.
- **chỉ một phần** `part-1`: Cánh hoa nhiều màu mời ong bướm ghé thăm.
- **không thấy** `part-4`: Lá xanh đón nắng để làm thức ăn cho cây.

Lưu ý: Không phải hoa nào cũng nhiều cánh.

## vi.nature.snail

Nguồn: [Ốc sên](https://vi.wikipedia.org/wiki/%E1%BB%90c_s%C3%AAn); [Snail](https://en.wikipedia.org/wiki/Snail)

- **chỉ một phần** `what`: Ốc sên là con vật thân mềm mang vỏ trên lưng.
- **chỉ một phần** `part-1`: Ốc sên rúc vào vỏ khi gặp nguy hiểm.
- **không thấy** `part-2`: Trên đầu ốc sên có râu, mắt nằm ở đầu râu.
- **chỉ một phần** `part-3`: Ốc sên trườn bằng một chiếc chân rộng dưới thân.
- **chỉ một phần** `part-4`: Chất nhớt giúp ốc sên trườn êm trên đường gồ ghề.
- **chỉ một phần** `use`: Ốc sên ăn lá mục và góp phần làm đất tốt.

## vi.nature.tree

Nguồn: [Cây](https://vi.wikipedia.org/wiki/C%C3%A2y); [Tree](https://en.wikipedia.org/wiki/Tree)

- **chỉ một phần** `part-4`: Cành cây vươn ra để lá đón được nhiều nắng.

## vi.ocean.crab

Nguồn: [Phân thứ bộ Cua](https://vi.wikipedia.org/wiki/Cua); [Crab](https://en.wikipedia.org/wiki/Crab)

- **chỉ một phần** `part-1`: Cua dùng hai càng để gắp thức ăn và tự vệ.
- **chỉ một phần** `part-2`: Nhiều chân giúp cua bò ngang trên cát.
- **không thấy** `part-3`: Mắt cua nằm trên cuống để nhìn xung quanh.
- **chỉ một phần** `part-4`: Khi lớn lên, cua lột vỏ cũ để thay vỏ mới.
- **chỉ một phần** `use`: Cua dọn thức ăn thừa, giúp bãi biển sạch hơn.

## vi.ocean.dolphin

Nguồn: [Cá heo](https://vi.wikipedia.org/wiki/C%C3%A1_heo); [Dolphin](https://en.wikipedia.org/wiki/Dolphin)

- **chỉ một phần** `part-2`: Chiếc đuôi khỏe đẩy cá heo bật khỏi mặt nước.
- **chỉ một phần** `use`: Cá heo sống theo đàn và giúp nhau kiếm ăn.

Lưu ý: Quẫy đuôi dựng người khỏi nước là hành vi hiếm.

## vi.ocean.octopus

Nguồn: [Bạch tuộc](https://vi.wikipedia.org/wiki/B%E1%BA%A1ch_tu%E1%BB%99c); [Octopus](https://en.wikipedia.org/wiki/Octopus)

Mọi câu đều có trang hỗ trợ.

## vi.ocean.seahorse

Nguồn: [Cá ngựa](https://vi.wikipedia.org/wiki/C%C3%A1_ng%E1%BB%B1a); [Seahorse](https://en.wikipedia.org/wiki/Seahorse)

- **chỉ một phần** `part-4`: Cá ngựa bố mang trứng trong chiếc túi ở bụng.
- **chỉ một phần** `use`: Cá ngựa sống nhờ rong biển và rạn san hô.

Lưu ý: Túi ấp nằm ở mặt trước phần đuôi, không phải ở bụng.

## vi.ocean.starfish

Nguồn: [Sao biển](https://vi.wikipedia.org/wiki/Sao_bi%E1%BB%83n); [Starfish](https://en.wikipedia.org/wiki/Starfish)

Mọi câu đều có trang hỗ trợ.

Lưu ý: part-4: bài tiếng Việt chỉ nói một số loài; bài tiếng Anh hỗ trợ.

## vi.ocean.whale

Nguồn: [Cá voi](https://vi.wikipedia.org/wiki/C%C3%A1_voi); [Whale](https://en.wikipedia.org/wiki/Whale)

- **chỉ một phần** `use`: Cá voi là một phần quan trọng của đại dương.

## vi.transport.airplane

Nguồn: [Máy bay](https://vi.wikipedia.org/wiki/M%C3%A1y_bay); [Airplane](https://en.wikipedia.org/wiki/Airplane)

- **chỉ một phần** `part-4`: Bánh xe giúp máy bay lăn khi cất cánh, hạ cánh.
- **chỉ một phần** `use`: Máy bay đưa người và hàng đi xa thật nhanh.

## vi.transport.ambulance

Nguồn: [Xe cứu thương](https://vi.wikipedia.org/wiki/Xe_c%E1%BB%A9u_th%C6%B0%C6%A1ng); [Ambulance](https://en.wikipedia.org/wiki/Ambulance)

- **chỉ một phần** `part-1`: Còi hú báo mọi người nhường đường.
- **chỉ một phần** `part-2`: Đèn nhấp nháy giúp mọi người nhìn thấy xe từ xa.
- **chỉ một phần** `part-3`: Cáng giúp đưa người bệnh lên xe nhẹ nhàng.

## vi.transport.bicycle

Nguồn: [Xe đạp](https://vi.wikipedia.org/wiki/Xe_%C4%91%E1%BA%A1p); [Bicycle](https://en.wikipedia.org/wiki/Bicycle)

- **chỉ một phần** `part-5`: Bóp phanh giúp xe chạy chậm rồi dừng lại.
- **chỉ một phần** `use`: Người ta đi xe đạp tới trường hoặc đi dạo.

## vi.transport.boat

Nguồn: [Thuyền](https://vi.wikipedia.org/wiki/Thuy%E1%BB%81n); [Boat](https://en.wikipedia.org/wiki/Boat)

- **không thấy** `part-4`: Bánh lái giúp thuyền đổi hướng.

## vi.transport.bus

Nguồn: [Xe buýt](https://vi.wikipedia.org/wiki/Xe_bu%C3%BDt); [Bus](https://en.wikipedia.org/wiki/Bus)

- **chỉ một phần** `part-2`: Cửa sổ giúp người ngồi ngắm đường phố.
- **chỉ một phần** `part-3`: Bánh xe lớn đỡ chiếc xe chở nhiều người.
- **chỉ một phần** `part-4`: Số tuyến trên xe cho biết xe đi đường nào.

## vi.transport.car

Nguồn: [Xe hơi](https://vi.wikipedia.org/wiki/%C3%94_t%C3%B4); [Car](https://en.wikipedia.org/wiki/Car)

- **chỉ một phần** `part-3`: Người lái xoay vô lăng để xe đổi hướng.
- **chỉ một phần** `use`: Ô tô chở người và đồ đi xa.

## vi.transport.scooter

Nguồn: [Xe máy](https://vi.wikipedia.org/wiki/Xe_m%C3%A1y); [Motorcycle](https://en.wikipedia.org/wiki/Motorcycle)

- **không thấy** `part-2`: Đèn xe giúp nhìn rõ đường khi trời tối.
- **không thấy** `part-3`: Gương giúp người lái nhìn phía sau.
- **không thấy** `part-4`: Còi xe kêu để báo cho người khác biết.
- **chỉ một phần** `use`: Người lớn đi xe máy và ai cũng đội mũ bảo hiểm.

Lưu ý: Câu use có lời khuyên đội mũ, trang chỉ nói luật nhiều nước bắt buộc.

## vi.transport.train

Nguồn: [Tàu hỏa](https://vi.wikipedia.org/wiki/T%C3%A0u_h%E1%BB%8Fa); [Train](https://en.wikipedia.org/wiki/Train)

Mọi câu đều có trang hỗ trợ.

## vi.transport.truck

Nguồn: [Xe tải](https://vi.wikipedia.org/wiki/Xe_t%E1%BA%A3i); [Truck](https://en.wikipedia.org/wiki/Truck)

- **chỉ một phần** `part-1`: Thùng xe phía sau đựng được rất nhiều hàng.
- **chỉ một phần** `part-2`: Nhiều bánh xe to giúp đỡ hàng nặng.
- **chỉ một phần** `part-4`: Gương lớn giúp bác tài nhìn hai bên xe.
