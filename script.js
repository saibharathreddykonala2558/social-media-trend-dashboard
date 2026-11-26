const API_URL = "http://127.0.0.1:5000";

const authSection = document.getElementById("auth-section");
const dashboardSection = document.getElementById("dashboard-section");
const historySection = document.getElementById("history-section");

const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const searchForm = document.getElementById("search-form");

const authMessage = document.getElementById("auth-message");
const searchMessage = document.getElementById("search-message");

const resultsSection = document.getElementById("results-section");
const historyList = document.getElementById("history-list");

const dailyChart = document.getElementById("daily-chart");
const platformChart = document.getElementById("platform-chart");

const downloadButton = document.getElementById("download-button");

let currentSearchId = null;

function showMessage(element, text, type) {
    element.textContent = text;
    element.className = `message ${type}`;
}

function showSection(section) {
    authSection.classList.add("hidden");
    dashboardSection.classList.add("hidden");
    historySection.classList.add("hidden");
    section.classList.remove("hidden");
}

function setActiveNav(activeId) {
    document.querySelectorAll(".nav-link").forEach(link => {
        link.classList.remove("active");
    });

    document.getElementById(activeId).classList.add("active");
}

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_URL}${path}`, {
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        },
        ...options
    });

    const data = await response.json();
    return { response, data };
}

document.getElementById("login-tab").addEventListener("click", () => {
    document.getElementById("login-tab").classList.add("active");
    document.getElementById("register-tab").classList.remove("active");
    loginForm.classList.remove("hidden");
    registerForm.classList.add("hidden");
    showMessage(authMessage, "", "");
});

document.getElementById("register-tab").addEventListener("click", () => {
    document.getElementById("register-tab").classList.add("active");
    document.getElementById("login-tab").classList.remove("active");
    registerForm.classList.remove("hidden");
    loginForm.classList.add("hidden");
    showMessage(authMessage, "", "");
});

registerForm.addEventListener("submit", async event => {
    event.preventDefault();

    const payload = {
        username: document.getElementById("register-username").value,
        email: document.getElementById("register-email").value,
        phone: document.getElementById("register-phone").value,
        password: document.getElementById("register-password").value
    };

    const { response, data } = await apiRequest("/api/register", {
        method: "POST",
        body: JSON.stringify(payload)
    });

    if (response.ok) {
        showMessage(authMessage, data.message, "success");
        await loadDashboard();
    } else {
        showMessage(authMessage, data.error, "error");
    }
});

loginForm.addEventListener("submit", async event => {
    event.preventDefault();

    const payload = {
        identifier: document.getElementById("login-identifier").value,
        password: document.getElementById("login-password").value
    };

    const { response, data } = await apiRequest("/api/login", {
        method: "POST",
        body: JSON.stringify(payload)
    });

    if (response.ok) {
        showMessage(authMessage, data.message, "success");
        await loadDashboard();
    } else {
        showMessage(authMessage, data.error, "error");
    }
});

document.getElementById("logout-button").addEventListener("click", async () => {
    await apiRequest("/api/logout", { method: "POST" });
    location.reload();
});

document.getElementById("dashboard-link").addEventListener("click", async () => {
    setActiveNav("dashboard-link");
    showSection(dashboardSection);
    await checkLogin();
});

document.getElementById("history-link").addEventListener("click", async () => {
    setActiveNav("history-link");
    showSection(historySection);
    await loadHistory();
});

async function checkLogin() {
    const { response, data } = await apiRequest("/api/me");

    if (response.ok) {
        authSection.classList.add("hidden");
        dashboardSection.classList.remove("hidden");
        setSearchDateToToday();
    } else {
        showSection(authSection);
    }
}

async function loadDashboard() {
    await checkLogin();
}

function setSearchDateToToday() {
    const today = new Date().toISOString().split("T")[0];
    document.getElementById("search-date").value = today;
}

searchForm.addEventListener("submit", async event => {
    event.preventDefault();

    const payload = {
        keyword: document.getElementById("keyword").value,
        platform: document.getElementById("platform").value,
        search_date: document.getElementById("search-date").value
    };

    showMessage(searchMessage, "Fetching live data, please wait...", "");
    resultsSection.classList.add("hidden");

    const { response, data } = await apiRequest("/api/search", {
        method: "POST",
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        showMessage(searchMessage, data.error, "error");
        return;
    }

    showMessage(searchMessage, data.message, "success");
    currentSearchId = data.search_id;

    displayResults(data.analysis, data.results);
    resultsSection.classList.remove("hidden");

    if (data.csv_file) {
        downloadButton.classList.remove("hidden");
    } else {
        downloadButton.classList.add("hidden");
    }
});

function displayResults(analysis, results) {
    const summary = analysis.summary;

    document.getElementById("total-posts").textContent = summary.total_posts;
    document.getElementById("total-likes").textContent = summary.total_likes;
    document.getElementById("total-comments").textContent = summary.total_comments;
    document.getElementById("total-engagement").textContent = summary.total_engagement;

    const dailyDates = analysis.daily_trends.map(item => item.created_at);
    const dailyEngagement = analysis.daily_trends.map(item => item.total_engagement);

    Plotly.newPlot(dailyChart, [{
        x: dailyDates,
        y: dailyEngagement,
        type: "scatter",
        mode: "lines+markers",
        line: {
            color: "#d4af37",
            width: 3
        },
        marker: {
            color: "#f5d67b"
        }
    }], {
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: {
            color: "#d8d8de"
        },
        margin: {
            t: 30,
            r: 30,
            b: 50,
            l: 60
        }
    });

    const platformNames = analysis.platform_trends.map(item => item.platform);
    const platformEngagement = analysis.platform_trends.map(item => item.total_engagement);

    Plotly.newPlot(platformChart, [{
        x: platformNames,
        y: platformEngagement,
        type: "bar",
        marker: {
            color: "#d4af37"
        }
    }], {
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: {
            color: "#d8d8de"
        },
        margin: {
            t: 30,
            r: 30,
            b: 50,
            l: 60
        }
    });

    const keywordList = document.getElementById("keyword-list");
    keywordList.innerHTML = "";

    analysis.top_keywords.forEach(item => {
        const tag = document.createElement("span");
        tag.className = "tag";
        tag.textContent = `${item.keyword} (${item.count})`;
        keywordList.appendChild(tag);
    });

    const hashtagList = document.getElementById("hashtag-list");
    hashtagList.innerHTML = "";

    analysis.top_hashtags.forEach(item => {
        const tag = document.createElement("span");
        tag.className = "tag";
        tag.textContent = `${item.hashtag} (${item.count})`;
        hashtagList.appendChild(tag);
    });

    const postList = document.getElementById("top-posts");
    postList.innerHTML = "";

    analysis.top_posts.forEach(post => {
        const postItem = document.createElement("div");
        postItem.className = "post-item";

        postItem.innerHTML = `
            <div class="post-title">${post.title || "Untitled"}</div>
            <div class="post-meta">
                ${post.platform} • ${post.author || "Unknown"} •
                Likes: ${post.likes} • Comments: ${post.comments} •
                Engagement: ${post.engagement}
            </div>
            <a class="post-link" href="${post.url}" target="_blank">Open original post</a>
        `;

        postList.appendChild(postItem);
    });
}

downloadButton.addEventListener("click", () => {
    if (currentSearchId) {
        window.open(`${API_URL}/api/download/${currentSearchId}`, "_blank");
    }
});

async function loadHistory() {
    const { response, data } = await apiRequest("/api/history");

    historyList.innerHTML = "";

    if (!response.ok) {
        historyList.innerHTML = `<p class="subtitle">${data.error}</p>`;
        return;
    }

    if (data.searches.length === 0) {
        historyList.innerHTML = `<p class="subtitle">No previous searches yet.</p>`;
        return;
    }

    data.searches.forEach(search => {
        const button = document.createElement("button");
        button.className = "history-item";

        button.innerHTML = `
            <div class="history-title">${search.keyword}</div>
            <div class="history-meta">
                ${search.platform} • ${search.search_date} •
                ${search.total_posts} posts • ${search.total_engagement} engagement
            </div>
        `;

        button.addEventListener("click", async () => {
            await openPreviousSearch(search.id);
        });

        historyList.appendChild(button);
    });
}

async function openPreviousSearch(searchId) {
    const { response, data } = await apiRequest(`/api/history/${searchId}`);

    if (!response.ok) {
        showMessage(searchMessage, data.error, "error");
        return;
    }

    setActiveNav("dashboard-link");
    showSection(dashboardSection);

    currentSearchId = searchId;

    document.getElementById("keyword").value = data.search.keyword;
    document.getElementById("search-date").value = data.search.search_date;

    displayResults(data.analysis, data.results);
    resultsSection.classList.remove("hidden");

    if (data.results.length > 0) {
        downloadButton.classList.remove("hidden");
    } else {
        downloadButton.classList.add("hidden");
    }
}

checkLogin();