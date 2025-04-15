/**
 * Weather Forecast Functionality
 * This script handles fetching and displaying weather forecasts for lawn service bookings
 */

class WeatherForecast {
  constructor() {
    // Map weather conditions to FontAwesome icons (not Bootstrap)
    this.weatherIcons = {
      sunny: "fa-sun",
      "partly-cloudy": "fa-cloud-sun",
      cloudy: "fa-cloud",
      "light-rain": "fa-cloud-rain",
      rainy: "fa-cloud-showers-heavy",
      stormy: "fa-cloud-bolt",
      snowy: "fa-snowflake",
      windy: "fa-wind",
      hot: "fa-temperature-high",
      cold: "fa-temperature-low",
      night: "fa-moon",
      "partly-cloudy-night": "fa-cloud-moon",
    }

    // Map Bootstrap icons to FontAwesome icons
    this.biToFaMap = {
      "bi-sun": "fa-sun",
      "bi-cloud-sun": "fa-cloud-sun",
      "bi-cloud": "fa-cloud",
      "bi-cloud-drizzle": "fa-cloud-rain",
      "bi-cloud-rain": "fa-cloud-showers-heavy",
      "bi-cloud-lightning": "fa-bolt",
      "bi-cloud-lightning-rain": "fa-cloud-bolt",
      "bi-snow": "fa-snowflake",
      "bi-cloud-snow": "fa-snowflake",
      "bi-wind": "fa-wind",
      "bi-thermometer-high": "fa-temperature-high",
      "bi-thermometer-low": "fa-temperature-low",
      "bi-moon": "fa-moon",
      "bi-cloud-moon": "fa-cloud-moon",
      "bi-cloud-question": "fa-question",
    }
  }

  /**
   * Fetch weather forecast for a specific date and city
   * @param {string} date - Date in YYYY-MM-DD format
   * @param {string} city - City name for the forecast
   * @returns {Promise} - Promise that resolves with weather data
   */
  async fetchForecast(date, city = "") {
    try {
      // Validate city input
      if (!city || city.trim() === "") {
        console.warn("City name is empty, using default city")
        city = "Johannesburg" // Default to Johannesburg if no city provided
      }

      console.log(`Fetching weather forecast for ${city} on ${date}`)

      const response = await fetch("/api/weather_forecast", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          date: date,
          city: city.trim(), // Trim whitespace from city name
        }),
      })

      if (!response.ok) {
        throw new Error(`Weather service error: ${response.status}`)
      }

      const data = await response.json()
      console.log(`Weather data received for ${city}:`, data)
      return data
    } catch (error) {
      console.error(`Error fetching weather forecast for ${city}:`, error)
      return {
        success: false,
        error: error.message,
      }
    }
  }

  /**
   * Convert Bootstrap icon class to FontAwesome icon class
   * @param {string} bootstrapIcon - Bootstrap icon class (e.g., "bi-sun")
   * @returns {string} - FontAwesome icon class (e.g., "fa-sun")
   */
  convertToFontAwesome(bootstrapIcon) {
    // If it's already a FontAwesome icon, return it
    if (bootstrapIcon.startsWith("fa-")) {
      return bootstrapIcon
    }

    // Remove the "bi-" prefix if present
    const iconName = bootstrapIcon.replace("bi-", "")

    // Check if we have a direct mapping
    if (this.biToFaMap[bootstrapIcon]) {
      return this.biToFaMap[bootstrapIcon]
    }

    // Try to find a matching icon in our weather icons
    if (this.weatherIcons[iconName]) {
      return this.weatherIcons[iconName]
    }

    // Default to cloud if no match found
    return "fa-cloud"
  }

  /**
   * Display weather forecast in the UI
   * @param {Object} weatherData - Weather forecast data
   * @param {HTMLElement} container - Container element to display the forecast
   */
  displayForecast(weatherData, container) {
    if (!weatherData.success) {
      container.innerHTML = `
      <div class="alert alert-warning">
        <i class="fas fa-exclamation-triangle me-2"></i>
        Weather forecast unavailable at this time.
      </div>
    `
      return
    }

    const forecast = weatherData.forecast
    const city = weatherData.city || "your location"

    // Convert Bootstrap icon to FontAwesome
    let iconClass = "fa-cloud" // Default icon

    if (forecast.icon_class) {
      // Convert from Bootstrap to FontAwesome
      iconClass = this.convertToFontAwesome(forecast.icon_class)
    } else if (forecast.icon) {
      // Try to map from icon name
      iconClass = this.weatherIcons[forecast.icon] || "fa-cloud"
    }

    // Create weather display with FontAwesome icon
    const weatherHTML = `
   <div class="d-flex align-items-center">
     <div class="me-3 fs-1 text-primary">
       <i class="fas ${iconClass}"></i>
     </div>
     <div>
       <div class="d-flex align-items-center mb-1">
         <span class="fs-4 fw-bold me-2">${forecast.avg_temp}°C</span>
         <span class="text-muted">${forecast.condition}</span>
       </div>
       <div class="d-flex align-items-center small text-muted">
         <i class="fas fa-map-marker-alt me-1"></i>
         <span>${city}</span>
       </div>
       <div class="d-flex align-items-center small text-muted">
         <i class="fas fa-droplet me-1"></i>
         <span>${forecast.precipitation_probability}% chance of precipitation</span>
       </div>
       <div class="d-flex align-items-center small text-muted mt-1">
         <i class="fas fa-wind me-1"></i>
         <span>${forecast.wind_speed || 10} km/h</span>
       </div>
     </div>
   </div>
 `

    container.innerHTML = weatherHTML

    // Add warning for high precipitation
    if (forecast.precipitation_probability > 30) {
      const warningEl = document.createElement("div")
      warningEl.className = "alert alert-info mt-3 mb-0 small"
      warningEl.innerHTML = `
     <i class="fas fa-umbrella me-1"></i>
     There's a chance of rain on this date. We may need to reschedule if conditions are too wet for optimal lawn care.
   `
      container.appendChild(warningEl)
    }

    // Add recommendations if available
    if (forecast.recommendations && forecast.recommendations.details && forecast.recommendations.details.length > 0) {
      const recommendationsEl = document.createElement("div")
      recommendationsEl.className = "mt-3 small"

      let recommendationsHTML = `<p class="mb-2 fw-bold"><i class="fas fa-info-circle me-1"></i> ${forecast.recommendations.message}</p><ul class="mb-0 ps-3">`

      forecast.recommendations.details.forEach((detail) => {
        recommendationsHTML += `<li>${detail}</li>`
      })

      recommendationsHTML += `</ul>`
      recommendationsEl.innerHTML = recommendationsHTML
      container.appendChild(recommendationsEl)
    }

    // Add note if using simulated data
    if (weatherData.source === "simulated" && weatherData.note) {
      const noteEl = document.createElement("div")
      noteEl.className = "alert alert-warning mt-3 mb-0 small"
      noteEl.innerHTML = `<i class="fas fa-info-circle me-1"></i> ${weatherData.note}`
      container.appendChild(noteEl)
    }
  }

  /**
   * Get weather advice based on forecast
   * @param {Object} forecast - Weather forecast data
   * @returns {string} - Advice text
   */
  getWeatherAdvice(forecast) {
    if (forecast.precipitation_probability > 60) {
      return "High chance of rain. Consider selecting another date for best results."
    } else if (forecast.precipitation_probability > 30) {
      return "Moderate chance of rain. We'll monitor conditions and contact you if rescheduling is needed."
    } else if (forecast.avg_temp > 30) {
      return "Very warm day. We'll mow at a slightly higher height to protect your lawn from heat stress."
    } else if (forecast.wind_speed > 20) {
      return "Windy conditions may affect debris cleanup. We'll take extra care with this aspect of service."
    } else {
      return "Weather conditions look good for lawn care service."
    }
  }
}

// Export for use in other scripts
window.WeatherForecast = WeatherForecast

