
# AnonChat Bot 🤖💬

Bot chat ẩn danh giúp kết nối ngẫu nhiên 2 người dùng với nhau qua Telegram.

## Cài đặt local:
```bash
pip install -r requirements.txt
python main.py
```

## Deploy trên Render:
- Tạo file `render.yaml` theo cấu hình dưới.
- Push repo lên GitHub.
- Kết nối repo với Render.
- Chọn Python environment.

## Cấu hình Render (render.yaml):
```yaml
services:
  - type: web
    name: anonchat-bot
    env: python
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python main.py"
```

## Liên hệ:
Tác giả: Minh Hiếu
- Telegram: t.me/mmhieusocute
- Facebook: fb.me/lunax1603
