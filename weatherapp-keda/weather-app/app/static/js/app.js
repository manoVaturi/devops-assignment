(() => {
  const cityInput = document.getElementById("cityInput");
  const suggestionList = document.getElementById("suggestionList");
  const searchForm = document.getElementById("searchForm");
  const locateBtn = document.getElementById("locateBtn");
  const statusBar = document.getElementById("statusBar");
  const resultContainer = document.getElementById("resultContainer");
  const weatherTemplate = document.getElementById("weatherTemplate");
  const skeletonTemplate = document.getElementById("skeletonTemplate");

  let suggestionDebounce;

  cityInput.addEventListener("input", (event) => {
    cityInput.classList.remove("is-invalid");
    const query = event.target.value.trim();
    clearTimeout(suggestionDebounce);

    if (query.length < 2) {
      suggestionList.replaceChildren();
      return;
    }

    suggestionDebounce = setTimeout(() => fetchSuggestions(query), 300);
  });

  async function fetchSuggestions(query) {
    try {
      const response = await fetch(`/api/cities?q=${encodeURIComponent(query)}`);
      if (!response.ok) return;
      const cities = await response.json();
      suggestionList.replaceChildren(
        ...cities.map((city) => {
          const option = document.createElement("option");
          option.value = city;
          return option;
        }),
      );
    } catch (error) {
      console.error("Error fetching city suggestions:", error);
    }
  }

  searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const value = cityInput.value.trim();

    if (!value || !value.includes(",")) {
      cityInput.classList.add("is-invalid");
      return;
    }

    requestWeather({ city: value });
  });

  locateBtn.addEventListener("click", () => useCurrentLocation(true));
  document.addEventListener("DOMContentLoaded", () => useCurrentLocation(false));

  function useCurrentLocation(isExplicit) {
    if (!navigator.geolocation) {
      if (isExplicit) setStatus("Geolocation isn't supported by this browser.", true);
      return;
    }

    locateBtn.classList.add("is-loading");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        locateBtn.classList.remove("is-loading");
        requestWeather({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      },
      (error) => {
        locateBtn.classList.remove("is-loading");
        if (isExplicit) {
          setStatus("Couldn't access your location. Please search instead.", true);
        } else {
          console.warn("Geolocation skipped:", error.message);
        }
      },
      { timeout: 8000 },
    );
  }

  async function requestWeather(payload) {
    showSkeleton();
    setStatus("Fetching forecast…");

    try {
      const response = await fetch("/api/weather", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json();

      if (!response.ok) {
        renderError(body.error || "Something went wrong.");
        return;
      }

      renderWeather(body.city, body.forecast);
      setStatus("");
    } catch (error) {
      console.error("Weather request failed:", error);
      renderError("Could not reach the weather service. Please try again shortly.");
    }
  }

  function showSkeleton() {
    resultContainer.replaceChildren(skeletonTemplate.content.cloneNode(true));
  }

  function setStatus(message, isError = false) {
    statusBar.textContent = message;
    statusBar.classList.toggle("text-danger", isError);
    statusBar.classList.toggle("text-muted", !isError);
  }

  function renderError(message) {
    resultContainer.replaceChildren();
    setStatus(message, true);
  }

  function renderWeather(city, forecast) {
    const node = weatherTemplate.content.cloneNode(true);
    node.querySelector(".weather-result").classList.add("fade-in");
    node.querySelector(".js-city-name").textContent = `${city.name}, ${city.country}`;

    const today = forecast[0] || {};
    const icon = node.querySelector(".js-today-icon");
    if (today.icon) {
      icon.src = today.icon;
      icon.classList.remove("d-none");
    }
    node.querySelector(".js-today-max").textContent = `${today.max_c ?? "--"}°`;
    node.querySelector(".js-today-min").textContent = `/ ${today.min_c ?? "--"}°`;
    node.querySelector(".js-today-humidity").textContent = `Humidity: ${today.humidity ?? "--"}%`;

    const upcoming = node.querySelector(".js-upcoming");
    forecast.slice(1).forEach((day) => upcoming.appendChild(buildDayCard(day)));

    resultContainer.replaceChildren(node);
  }

  function buildDayCard(day) {
    const col = document.createElement("div");
    col.className = "col";

    const card = document.createElement("div");
    card.className = "card forecast-day-card h-100 shadow-sm text-center py-3";

    const dayName = document.createElement("div");
    dayName.className = "fs-5 fw-bold";
    dayName.textContent = (day.day || "").slice(0, 3);

    const iconSlot = document.createElement("div");
    iconSlot.className = "my-2";
    if (day.icon) {
      const img = document.createElement("img");
      img.src = day.icon;
      img.width = 50;
      img.alt = "";
      iconSlot.appendChild(img);
    } else {
      iconSlot.innerHTML = '<i class="fa-solid fa-cloud text-muted fs-2"></i>';
    }

    const temps = document.createElement("div");
    const maxTemp = document.createElement("span");
    maxTemp.className = "fw-bold forecast-temp";
    maxTemp.textContent = `${day.max_c ?? "--"}°`;
    const minTemp = document.createElement("span");
    minTemp.className = "text-muted small forecast-temp";
    minTemp.textContent = ` ${day.min_c ?? "--"}°`;
    temps.append(maxTemp, minTemp);

    card.append(dayName, iconSlot, temps);
    col.appendChild(card);
    return col;
  }
})();
