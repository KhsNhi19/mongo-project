# Yelp Data Explorer - Ứng dụng Web Phân tích Dữ liệu

Dự án này là một ứng dụng web full-stack (Flask + JavaScript) cho phép khám phá và phân tích bộ dữ liệu của Yelp một cách trực quan. Toàn bộ môi trường, từ database MongoDB đến backend Python, đều được đóng gói bằng Docker để đảm bảo việc cài đặt và chạy ứng dụng trở nên đơn giản và nhất quán.

## ✨ Các tính năng chính

- **Tìm kiếm Doanh nghiệp:** Lọc các doanh nghiệp theo danh mục với hệ thống phân trang (pagination) hiệu quả.
- **Xem chi tiết:** Xem thông tin đầy đủ của từng doanh nghiệp, bao gồm địa chỉ, hình ảnh, review, tips và vị trí trên bản đồ.
- **Phân tích Không gian:** Tương tác trực tiếp trên bản đồ để tìm kiếm các địa điểm trong bán kính 5km.
- **Tìm kiếm toàn văn bản (Full-text Search):** Tìm kiếm từ khóa bất kỳ bên trong nội dung của hàng triệu review.
- **Trực quan hóa Dữ liệu:** Xem thống kê lượt check-in theo ngày trong tuần qua biểu đồ.

## 🛠️ Công nghệ sử dụng

- **Backend:** Flask, PyMongo
- **Frontend:** HTML, CSS, JavaScript (Vanilla), Leaflet.js (Bản đồ), Chart.js (Biểu đồ)
- **Database:** MongoDB
- **DevOps:** Docker, Docker Compose

## 🚀 Cài đặt & Khởi chạy

Hãy làm theo các bước sau để chạy toàn bộ ứng dụng trên máy của bạn.

### **Yêu cầu cần có**

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

### **1. Sao chép Kho chứa (Clone)**

```bash
git clone [https://github.com/KhsNhi19/mongo-project.git](https://github.com/KhsNhi19/mongo-project.git)

cd mongo-project
```

> **Giải thích:** Lệnh `git clone [URL]` sẽ tạo ra một thư mục mới có tên là `mongo-project` (lấy từ cuối URL). Lệnh `cd mongo-project` là để đi vào bên trong thư mục đó.

### **2. Chuẩn bị Dữ liệu**

> **Lưu ý:** Ứng dụng này yêu cầu một file sao lưu database đã được tiền xử lý (`yelp_db_preprocessed.gz`).
>
> **Tải về tại:** [**Google Drive Link**](https://drive.google.com/file/d/1yqM1Da6neEysPGIJ3DViHAAEXfvZSXE3/view?usp=sharing)
>
> Sau khi tải về, hãy đặt file `yelp_db_preprocessed.gz` này vào trong thư mục `mongo-project` bạn vừa clone về.

### **3. Khởi chạy Toàn bộ Ứng dụng**

Lệnh này sẽ build image cho backend Flask và khởi động tất cả các container cần thiết (Flask, MongoDB, Mongo Express) ở chế độ nền.

```bash
docker-compose up --build -d
```

### **4. Nạp Dữ liệu vào Database**

Chờ khoảng 15-20 giây để MongoDB khởi động hoàn toàn, sau đó chạy các lệnh sau để nạp dữ liệu.

```bash
docker cp ./yelp_db_preprocessed.gz mongodb_project:/tmp/backup.gz

docker exec mongodb_project mongorestore \
  --username mongo_demo \
  --password admin_123 \
  --authenticationDatabase admin \
  --db yelp_db \
  --archive=/tmp/backup.gz --gzip --drop
```

Sau khoảng vài phút, dữ liệu sẽ được nạp xong và ứng dụng đã sẵn sàng.

## 📖 Hướng dẫn sử dụng

#### **Ứng dụng Web chính**

- **URL:** `http://localhost:5000`

#### **Giao diện quản trị Database (Mongo Express)**

- **URL:** `http://localhost:8081`
- **Username:** `mongo_demo_web`
- **Password:** `web_123`

---

### Quản lý Môi trường Docker

| Lệnh                             | Mô tả                                                          |
| -------------------------------- | -------------------------------------------------------------- |
| `docker-compose stop`            | Dừng các container đang chạy mà không xóa chúng.               |
| `docker-compose down`            | Dừng và xóa các container, mạng đã định nghĩa.                 |
| `docker-compose down -v`         | **(Nguy hiểm)** Xóa container và **toàn bộ dữ liệu** database. |
| `docker-compose logs -f backend` | Xem log thời gian thực từ ứng dụng Flask.                      |

### 📝 Lưu ý cho Hợp tác Đa nền tảng (Mac & Windows)

Khi làm việc nhóm giữa các hệ điều hành khác nhau, có thể xảy ra vấn đề về định dạng dấu xuống dòng (Line Endings).

- **Người dùng Mac/Linux:** Không cần làm gì.
- **Người dùng Windows:** Sau khi `git clone`, nên chạy lệnh sau một lần để Git tự động xử lý vấn đề này:
  ```bash
  git config --global core.autocrlf true
  ```

<br>

<details>
<summary>▶ Nhấn vào đây để xem nội dung file docker-compose.yml</summary>

```yml
services:
  mongodb:
    image: mongo:6.0
    container_name: mongodb_project
    restart: always
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: mongo_demo
      MONGO_INITDB_ROOT_PASSWORD: admin_123
    volumes:
      - mongo-data:/data/db

  mongo-express:
    image: mongo-express:latest
    container_name: mongo_express_project
    restart: always
    ports:
      - "8081:8081"
    environment:
      ME_CONFIG_MONGODB_SERVER: mongodb
      ME_CONFIG_MONGODB_ADMINUSERNAME: mongo_demo
      ME_CONFIG_MONGODB_ADMINPASSWORD: admin_123
      ME_CONFIG_BASICAUTH_USERNAME: mongo_demo_web
      ME_CONFIG_BASICAUTH_PASSWORD: web_123
    depends_on:
      - mongodb

  backend:
    build: ./backend
    container_name: flask_app_project
    restart: always
    ports:
      - "5000:5000"
    environment:
      FLASK_APP: app.py
      FLASK_DEBUG: 1
    volumes:
      - ./backend:/app
    depends_on:
      - mongodb

volumes:
  mongo-data:
    driver: local
```

</details>
