# Dockerfile

# Sử dụng một image Python chính thức
FROM python:3.12-slim

# Thiết lập thư mục làm việc bên trong container
WORKDIR /app

# Copy file requirements vào trước để tận dụng cache của Docker
COPY requirements.txt .

# Cài đặt các thư viện cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code của bạn vào thư mục làm việc
COPY . .

# Chạy ứng dụng khi container khởi động
CMD ["flask", "run", "--host=0.0.0.0"]