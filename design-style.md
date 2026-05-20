# HR-Chatbot Frontend Design Style

## Tong Quan

Giao dien cho HR-Chatbot theo phong cach minimalism: toi gian, hien dai, sach se va de doc. Cam giac san pham can than thien, gan gui nhung van chuyen nghiep, phu hop voi cong cu noi bo cho nhan vien cong ty.

Ngon ngu hien thi mac dinh: tieng Viet.

## Mau Sac

- Mau chu dao: xanh duong va trang.
- Light mode:
  - Nen trang hoac xanh rat nhat: `#F5F8FF`, `#FFFFFF`.
  - Mau chinh: xanh duong `#2563EB` hoac `#4F63F6`.
  - Text chinh: `#111827`.
  - Text phu: `#fc8803`.
  - Vien/duong ke: `#E5E7EB`.
- Dark mode:
  - Nen chinh: `#0F172A`.
  - Nen sidebar/chat surface: `#111827`, `#1F2937`.
  - Mau chinh: xanh duong sang `#60A5FA`.
  - Text chinh: `#F9FAFB`.
  - Text phu: `#51f5c4`.
  - Vien/duong ke: `#334155`.

Trang can co nut chuyen doi Light/Dark mode va luu lua chon vao `localStorage`.

## Layout

Layout tham chieu theo anh mau:

- Toan bo ung dung nam trong mot khung chat lon, can giua man hinh tren nen xanh nhat.
- Khung ung dung chinh can co bo goc lon vua phai, khoang `24px-32px` tren desktop, de tao cam giac mem mai va hien dai.
- Tranh layout co nhieu duong vien thang, day, sac canh hoac chia cot qua cung nhu dashboard cu.
- Uu tien tach cac vung bang spacing, background layer va shadow nhe thay vi dung nhieu border/divider.
- Ben trai la sidebar co chieu rong co dinh tren desktop.
- Ben phai la khung chat chinh chiem phan lon dien tich.
- Tren mobile, sidebar co the thu gon/an sau nut menu.

Sidebar gom:

- Ten san pham: `HR-Chatbot`.
- Nut `Cuoc tro chuyen moi`.
- Danh sach cac cuoc tro chuyen gan day hoac placeholder neu chua co history.
- Nut cai dat/chuyen theme o phan duoi.

Khung chat chinh gom:

- Vung hien thi hoi thoai.
- Tin nhan user va assistant phan biet ro rang.
- O nhap tin nhan o duoi cung, dang thanh input noi, co nut gui dang icon.
- Khi assistant dang tra loi, hien thi trang thai streaming nhe nha, khong gay roi.

## Thanh Phan UI

- Tong the giao dien can mem mai, hien dai; tranh cac duong vien thang, day hoac sac canh lam UI bi cu.
- Khung ung dung chinh bo goc `24px-32px` tren desktop va `18px-24px` tren tablet/mobile.
- Sidebar, chat surface va input nen co cam giac noi nhe bang shadow mem, background layer va spacing thoang.
- Light mode shadow goi y: `0 24px 80px rgba(37, 99, 235, 0.12)`.
- Dark mode shadow goi y: `0 24px 80px rgba(0, 0, 0, 0.35)`.
- Sidebar item va nut phu bo goc `12px-16px`, hover bang nen xanh rat nhat thay vi vien dam.
- Input chat dung dang pill/rounded bar, bo goc `20px-28px`, noi nhe khoi nen.
- Border/divider chi dung khi can, mau phai rat nhe de khong tao cam giac cung.
- Nut chinh dung mau xanh duong, text trang.
- Nut phu dung nen trong suot hoac xam rat nhat.
- Icon nen dung lucide icons neu frontend co cai dat hoac CDN phu hop.
- Font uu tien system font: `Inter`, `Segoe UI`, `Arial`, sans-serif.

## Chat Message

- Message user canh phai hoac co nen xanh duong rat nhat.
- Message assistant canh trai, de doc tren nen trong suot/trang.
- Markdown phai render dep cho:
  - bullet list
  - numbered list
  - bold text
  - table
  - inline code
- Khoang cach giua cac message rong vua du, tranh cam giac chat bi chen chuc.

## Citations

Citations can duoc hien thi ro o cuoi message assistant:

- Dung label tieng Viet: `Nguon tham khao`.
- Hien thi citation bang chip/card nho, nen xanh rat nhat trong light mode va nen toi hon trong dark mode.
- Citation khong duoc noi bat hon noi dung cau tra loi, nhung phai de nhin de nguoi dung co the kiem chung.

## Giong Dieu

Tat ca text trong UI dung tieng Viet, than thien va ro rang:

- `Cuoc tro chuyen moi`
- `Nhap cau hoi ve chinh sach nhan su...`
- `Dang tra loi...`
- `Dung lai`
- `Thu lai`
- `Khong the ket noi den may chu`

Khong dung ngon ngu qua vui nhon, emoji day dac, hoac noi dung mang tinh marketing. San pham la cong cu noi bo, nen uu tien ro rang, tin cay va de su dung.

## Responsive

- Desktop: sidebar trai + chat chinh.
- Tablet/mobile: sidebar co the an/hien bang nut menu.
- Input chat luon nam o cuoi man hinh.
- Noi dung chat auto-scroll khi co streaming chunk moi.
