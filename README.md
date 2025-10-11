# Yelp Data Explorer - Ứng dụng Web Phân tích Dữ liệu

## Mô tả ngắn

Dự án này là một ứng dụng web full-stack (Flask + JavaScript) được xây dựng nhằm mục đích khám phá và thể hiện các khả năng nâng cao của MongoDB. Ứng dụng cho phép người dùng tương tác với bộ dữ liệu lớn của Yelp thông qua một giao diện web trực quan, thực hiện các truy vấn phức tạp như tìm kiếm không gian, tìm kiếm toàn văn bản, và phân tích hiệu năng của các mô hình dữ liệu khác nhau. Toàn bộ hệ thống được đóng gói bằng Docker và giám sát bằng Prometheus & Grafana, mô phỏng một quy trình làm việc chuyên nghiệp.

## Các tính năng chính

- **Tìm kiếm Doanh nghiệp:** Lọc các doanh nghiệp theo danh mục với hệ thống phân trang (pagination).
- **Xem chi tiết:** Xem thông tin đầy đủ của từng doanh nghiệp, bao gồm hình ảnh, review, tips, biểu đồ check-in và vị trí trên bản đồ.
- **Phân tích Không gian:** Tương tác trực tiếp trên bản đồ để tìm kiếm các địa điểm trong bán kính 5km.
- **Tìm kiếm Toàn văn bản (Full-text Search):** Tìm kiếm từ khóa bất kỳ bên trong nội dung của hàng triệu review.
- **Phân tích Hiệu năng Data Model:** So sánh trực quan tốc độ truy vấn giữa mô hình dữ liệu Tham chiếu (Referencing) và Lồng ghép (Embedding).

## Công nghệ sử dụng

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript (Vanilla), Leaflet.js (Bản đồ), Chart.js (Biểu đồ)
- **Database:** MongoDB (với Replica Set)
- **DevOps:** Docker, Docker Compose
- **Giám sát & Phân tích Hiệu năng:** Prometheus, Grafana, k6

## Cấu trúc Dự án

```
mongo_yelp/
├── backend/
│   ├── static/
│   ├── templates/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── k6/
│   └── test.js
│
├── .gitignore
├── docker-compose.yml
├── mongo.key
├── prometheus.yml
├── README.md
└── yelp_db_preprocessed.gz  (Tải riêng)
```

## Cài đặt & Khởi chạy

### Yêu cầu cần có

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

### 1. Sao chép Kho chứa (Clone)

```bash
git clone [https://github.com/KhsNhi19/mongo-demo-project.git](https://github.com/KhsNhi19/mongo-demo-project.git)
cd mongo-demo-project
```

### 2. Chuẩn bị Dữ liệu

> **Lưu ý:** Ứng dụng này yêu cầu một file sao lưu database đã được tiền xử lý (`yelp_db_preprocessed.gz`).
>
> Data gốc: [Yelp_Dataset] (https://business.yelp.com/data/resources/open-dataset/)
>
> **Tải về tại:** [**Google Drive Link**](https://drive.google.com/file/d/1sIInaTIC0LpG8ZJQWOtMaxkQe-BKJrjr/view?usp=sharing)
>
> Sau khi tải về, hãy đặt file `yelp_db_preprocessed.gz` này vào trong thư mục `mongo-demo-project` bạn vừa clone về.

### 3. Khởi tạo các file cần thiết

Dự án yêu cầu một file `mongo.key` để bảo mật Replica Set. Hãy chạy lệnh sau trong terminal:

```bash
openssl rand -base64 756 > mongo.key
chmod 400 mongo.key
```

## Hướng dẫn sử dụng

### 1. Khởi chạy Toàn bộ Ứng dụng

Lệnh này sẽ build image cho backend Flask và khởi động tất cả các container cần thiết (Flask, MongoDB, Mongo Express, Prometheus, Grafana) ở chế độ nền.

```bash
docker-compose up --build -d
```

### 2. Nạp Dữ liệu và Khởi tạo Replica Set

1.  **Chờ khoảng 30 giây** để cụm MongoDB khởi động hoàn toàn.

2.  **Khởi tạo Replica Set** (chỉ chạy một lần duy nhất cho môi trường mới):

    ```bash
    docker exec -it mongo1_project mongosh --username mongo_demo --password admin_123 --authenticationDatabase admin --eval 'rs.initiate({ _id: "rs0", members: [ { _id: 0, host: "mongo1:27017" }, { _id: 1, host: "mongo2:27017" }, { _id: 2, host: "mongo3:27017" } ] })'
    ```

3.  **Khôi phục Database** từ file backup (chọn node Primary, thường là `mongo1` hoặc `mongo2`):
    `bash
docker cp ./yelp_db_preprocessed.gz mongo1_project:/tmp/backup.gz
docker exec mongo1_project mongorestore --username mongo_demo --password admin_123 --authenticationDatabase admin --db yelp_db --archive=/tmp/backup.gz --gzip --drop
`
    Sau vài phút, ứng dụng đã sẵn sàng để sử dụng.

### 3. Truy cập các Dịch vụ

- **Ứng dụng Web:** `http://localhost:5000`
- **Dashboard Giám sát (Grafana):** `http://localhost:3000`
- **Hệ thống giám sát (Prometheus):** `http://localhost:9090`

#### Quản trị Database (Mongo Express)

- **URL:** `http://localhost:8081`
- **Username:** `mongo_demo_web`
- **Password:** `web_123`

## Lưu ý cho Hợp tác Đa nền tảng (Mac & Windows)

Khi làm việc nhóm giữa các hệ điều hành khác nhau, có thể xảy ra vấn đề về định dạng dấu xuống dòng.

- **Người dùng Mac/Linux:** Không cần làm gì.
- **Người dùng Windows:** Sau khi `git clone`, nên chạy lệnh sau một lần để Git tự động xử lý vấn đề này:
  ```bash
  git config --global core.autocrlf true
  ```

## Giấy phép (License)

Dự án này được cấp phép theo Giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.

## Tác giả & Liên hệ

tranthikhanhnhi919@gmail.com
nguyendongphuongvn@gmail.com
vongocghahan218@gmail.com
