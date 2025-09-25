document.addEventListener("DOMContentLoaded", () => {
  // --- Lấy các phần tử DOM ---
  const views = document.querySelectorAll(".view");
  const navLinks = document.querySelectorAll(".sidebar-nav li");
  const categorySelect = document.getElementById("category-select");
  const searchBtn = document.getElementById("search-btn");
  const resultsContainer = document.getElementById("results-container");
  const paginationContainer = document.getElementById("pagination-container");
  const backBtn = document.getElementById("back-btn");
  const detailsBusinessName = document.getElementById("details-business-name");
  const detailsAddress = document.getElementById("details-address");
  const detailsCity = document.getElementById("details-city");
  const detailsCategories = document.getElementById("details-categories");
  const detailsStars = document.getElementById("details-stars");
  const detailsReviewCount = document.getElementById("details-review-count");
  const detailsMapContainer = document.getElementById("details-map");
  const detailsPhotos = document.getElementById("details-photos");
  const detailsReviews = document.getElementById("details-reviews");
  const detailsTips = document.getElementById("details-tips");
  const reviewSearchInput = document.getElementById("review-search-input");
  const reviewSearchBtn = document.getElementById("review-search-btn");
  const reviewResultsContainer = document.getElementById(
    "review-results-container"
  );
  const findNearbyBtn = document.getElementById("find-nearby-btn");
  const nearbyMapContainer = document.getElementById("nearby-map");
  const nearbyResultsContainer = document.getElementById(
    "nearby-results-container"
  );

  // --- Biến toàn cục ---
  let detailsMap, nearbyMap, checkinsChart;
  let currentPage = 1;
  let currentCategory = "Restaurants";
  let isNearbyMapInitialized = false;

  // --- QUẢN LÝ CÁC MÀN HÌNH (VIEW) ---
  function showView(viewId) {
    views.forEach((view) => view.classList.add("hidden"));
    document.getElementById(viewId).classList.remove("hidden");
    navLinks.forEach((link) => {
      link.classList.remove("active");
      if (link.dataset.view === viewId) {
        link.classList.add("active");
      }
    });
    if (viewId === "view-nearby" && !isNearbyMapInitialized) {
      initializeNearbyMap();
    }
  }

  // --- HÀM GỌI API CHUNG ---
  async function fetchAPI(url) {
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Lỗi HTTP: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error(`Lỗi khi gọi API ${url}:`, error);
      throw error;
    }
  }

  // --- CHỨC NĂNG 1: TÌM BUSINESS THEO CATEGORY ---
  async function populateCategories() {
    try {
      const data = await fetchAPI("/api/categories");
      categorySelect.innerHTML = data
        .map(
          (item) => `<option value="${item.category}">${item.category}</option>`
        )
        .join("");
      currentCategory = categorySelect.value;
      searchBusinesses(1);
    } catch (error) {
      categorySelect.innerHTML = "<option>Lỗi tải category</option>";
    }
  }

  async function searchBusinesses(page = 1) {
    currentPage = page;
    currentCategory = categorySelect.value;
    resultsContainer.innerHTML = "<h2>Đang tải...</h2>";
    paginationContainer.innerHTML = "";
    try {
      const data = await fetchAPI(
        `/api/businesses?category=${encodeURIComponent(
          currentCategory
        )}&page=${currentPage}`
      );
      renderBusinessResults(data.businesses, resultsContainer);
      renderPagination(data.total, data.page, data.limit);
    } catch (error) {
      resultsContainer.innerHTML = "<h2>Đã có lỗi xảy ra khi tải dữ liệu.</h2>";
    }
  }

  function renderPagination(total, page, limit) {
    const totalPages = Math.ceil(total / limit);
    if (totalPages <= 1) {
      paginationContainer.innerHTML = "";
      return;
    }
    const prevButton = document.createElement("button");
    prevButton.innerHTML = "&laquo; Trước";
    prevButton.disabled = page === 1;
    prevButton.addEventListener("click", () => searchBusinesses(page - 1));
    const pageInfo = document.createElement("span");
    pageInfo.textContent = `Trang ${page} / ${totalPages}`;
    const nextButton = document.createElement("button");
    nextButton.innerHTML = "Sau &raquo;";
    nextButton.disabled = page === totalPages;
    nextButton.addEventListener("click", () => searchBusinesses(page + 1));
    paginationContainer.append(prevButton, pageInfo, nextButton);
  }

  // --- CHỨC NĂNG 2: HIỂN THỊ CHI TIẾT BUSINESS ---
  async function showBusinessDetails(businessId, businessName) {
    showView("view-business-details");
    detailsBusinessName.textContent = businessName;
    detailsPhotos.innerHTML = "<p>Đang tải ảnh...</p>";
    detailsReviews.innerHTML = "<p>Đang tải reviews...</p>";
    detailsTips.innerHTML = "<p>Đang tải tips...</p>";
    try {
      const businessDetails = await fetchAPI(`/api/businesses/${businessId}`);
      renderBusinessInfo(businessDetails);
      const [photos, reviews, tips, checkins] = await Promise.all([
        fetchAPI(`/api/businesses/${businessId}/photos`),
        fetchAPI(`/api/businesses/${businessId}/reviews`),
        fetchAPI(`/api/businesses/${businessId}/tips`),
        fetchAPI(`/api/businesses/${businessId}/checkins`),
      ]);
      renderPhotos(photos);
      renderReviews(reviews);
      renderTips(tips);
      renderCheckins(checkins);
    } catch (error) {
      console.error("Lỗi khi tải chi tiết business:", error);
    }
  }

  function renderBusinessInfo(details) {
    detailsAddress.textContent = details.address;
    detailsCity.textContent = details.city;
    detailsCategories.textContent = details.categories;
    detailsStars.textContent = `${details.stars} ⭐`;
    detailsReviewCount.textContent = details.review_count;
    const coords = [details.latitude, details.longitude];
    if (detailsMap) detailsMap.remove();
    detailsMap = L.map(detailsMapContainer).setView(coords, 15);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(
      detailsMap
    );
    L.marker(coords).addTo(detailsMap).bindPopup(details.name).openPopup();
  }

  function renderPhotos(photos) {
    detailsPhotos.innerHTML = "";
    if (photos.length === 0) {
      detailsPhotos.innerHTML = "<p>Không có ảnh nào.</p>";
      return;
    }
    photos.forEach((photo) => {
      const img = document.createElement("img");
      img.src = `https://s3-media1.fl.yelpcdn.com/bphoto/${photo.photo_id}/o.jpg`;
      img.alt = photo.caption;
      detailsPhotos.appendChild(img);
    });
  }

  function renderReviews(reviews) {
    detailsReviews.innerHTML = "";
    if (reviews.length === 0) {
      detailsReviews.innerHTML = "<p>Chưa có review nào.</p>";
      return;
    }
    reviews.forEach((review) => {
      const card = document.createElement("div");
      card.className = "review-card";
      const reviewDate = new Date(review.date).toLocaleDateString("vi-VN");
      card.innerHTML = `<p><strong>${review.userName}</strong> - <span class="review-meta">${review.stars} ⭐ vào ngày ${reviewDate}</span></p><p>${review.text}</p>`;
      detailsReviews.appendChild(card);
    });
  }

  function renderTips(tips) {
    detailsTips.innerHTML = "";
    if (tips.length === 0) {
      detailsTips.innerHTML = "<p>Không có tip nào.</p>";
      return;
    }
    tips.forEach((tip) => {
      const card = document.createElement("div");
      card.className = "review-card";
      card.innerHTML = `<p>${tip.text}</p><p class="review-meta">❤️ ${tip.compliment_count} lượt thích</p>`;
      detailsTips.appendChild(card);
    });
  }

  function renderCheckins(checkins) {
    if (checkinsChart) {
      checkinsChart.destroy();
    }
    const labels = [
      "Chủ Nhật",
      "Thứ 2",
      "Thứ 3",
      "Thứ 4",
      "Thứ 5",
      "Thứ 6",
      "Thứ 7",
    ];
    const data = Array(7).fill(0);
    checkins.forEach((item) => {
      data[item._id - 1] = item.checkinCount;
    });
    const ctx = document.getElementById("checkins-chart").getContext("2d");
    checkinsChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Số lượt Check-in",
            data: data,
            backgroundColor: "rgba(0, 123, 255, 0.5)",
            borderColor: "rgba(0, 123, 255, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: { scales: { y: { beginAtZero: true } } },
    });
  }

  // --- CHỨC NĂNG 3: TÌM KIẾM TRONG REVIEW ---
  async function searchInReviews() {
    const searchTerm = reviewSearchInput.value.trim();
    if (!searchTerm) return;
    reviewResultsContainer.innerHTML = "<h2>Đang tìm...</h2>";
    try {
      const results = await fetchAPI(
        `/api/reviews/search?q=${encodeURIComponent(searchTerm)}`
      );
      renderReviewSearchResults(results);
    } catch (error) {
      reviewResultsContainer.innerHTML = "<h2>Lỗi tìm kiếm.</h2>";
    }
  }

  function renderReviewSearchResults(results) {
    reviewResultsContainer.innerHTML = "";
    if (results.length === 0) {
      reviewResultsContainer.innerHTML =
        "<h2>Không tìm thấy review nào phù hợp.</h2>";
      return;
    }
    results.forEach((result) => {
      const card = document.createElement("div");
      card.className = "review-card";
      card.style.cursor = "pointer";
      card.innerHTML = `<p><strong>Tìm thấy tại: ${result.businessName}</strong></p><p class="review-meta">${result.reviewStars} ⭐</p><p>"...${result.reviewText}..."</p>`;
      card.addEventListener("click", () =>
        showBusinessDetails(result.businessId, result.businessName)
      );
      reviewResultsContainer.appendChild(card);
    });
  }

  // --- CHỨC NĂNG 4: TÌM GẦN ĐÂY ---
  function initializeNearbyMap() {
    if (isNearbyMapInitialized) return;

    const nearbyMapContainer = document.getElementById("nearby-map");
    const nearbyResultsContainer = document.getElementById(
      "nearby-results-container"
    );

    const PhiladelphiaCoords = [39.9526, -75.1652];

    nearbyMap = L.map(nearbyMapContainer).setView(PhiladelphiaCoords, 12); // Zoom gần hơn một chút
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(nearbyMap);

    nearbyMap.on("click", async function (e) {
      const { lat, lng } = e.latlng;
      nearbyResultsContainer.innerHTML = "<h2>Đang tìm các địa điểm...</h2>";
      try {
        const businesses = await fetchAPI(
          `/api/businesses/nearby?lat=${lat}&lon=${lng}`
        );
        renderBusinessResults(businesses, nearbyResultsContainer); // Dùng lại hàm render đã sửa
      } catch (error) {
        nearbyResultsContainer.innerHTML =
          "<h2>Không tìm thấy địa điểm nào.</h2>";
      }
    });

    isNearbyMapInitialized = true;
  }

  function renderBusinessResults(businesses, container) {
    container.innerHTML = "";
    if (!businesses || businesses.length === 0) {
      container.innerHTML = "<h2>Không tìm thấy kết quả nào.</h2>";
      return;
    }
    businesses.forEach((business) => {
      const card = document.createElement("div");
      card.className = "business-card";

      const businessId = business.business_id;

      let cardContent = `<h3>${business.name}</h3>`;
      if (business.city)
        cardContent += `<p><strong>Thành phố:</strong> ${business.city}</p>`;
      if (business.address)
        cardContent += `<p><strong>Địa chỉ:</strong> ${business.address}</p>`;
      if (business.stars)
        cardContent += `<p><strong>Điểm sao:</strong> ${business.stars} ⭐</p>`;
      if (business.review_count)
        cardContent += `<p><strong>Số review:</strong> ${business.review_count}</p>`;
      if (business.distance_km !== undefined)
        cardContent += `<p><strong>Khoảng cách:</strong> ${business.distance_km} km</p>`;

      card.innerHTML = cardContent;

      if (businessId) {
        card.addEventListener("click", () =>
          showBusinessDetails(businessId, business.name)
        );
      }

      container.appendChild(card);
    });
  }

  // --- GẮN CÁC SỰ KIỆN ---
  searchBtn.addEventListener("click", () => searchBusinesses(1));
  backBtn.addEventListener("click", () => showView("view-search-business"));
  reviewSearchBtn.addEventListener("click", searchInReviews);

  navLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const viewId = link.dataset.view;
      if (viewId) showView(viewId);
    });
  });

  // --- KHỞI CHẠY ỨNG DỤNG ---
  populateCategories();
  showView("view-search-business");
});
