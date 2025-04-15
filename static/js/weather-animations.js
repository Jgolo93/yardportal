/**
 * Weather Animation Handler
 * This script creates and manages weather animations based on the current weather condition
 */

class WeatherAnimations {
  constructor() {
    // Map weather conditions to animation types
    this.weatherAnimationMap = {
      sun: "weather-sun",
      "cloud-sun": "weather-partly-cloudy",
      cloud: "weather-cloud",
      "cloud-drizzle": "weather-rain",
      "cloud-rain": "weather-rain",
      "cloud-lightning": "weather-storm",
      "cloud-lightning-rain": "weather-storm",
      snow: "weather-snow",
      "cloud-snow": "weather-snow",
      wind: "weather-windy",
      "thermometer-high": "weather-sun",
      "thermometer-low": "weather-snow",
      moon: "weather-clear-night",
      "cloud-moon": "weather-partly-cloudy",
    }

    // Map for FontAwesome icons (updated from Bootstrap to FontAwesome)
    this.faIconMap = {
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
    }
  }

  /**
   * Initialize weather animations on the page
   * @param {string} containerSelector - CSS selector for the weather container
   * @param {string} iconClass - Icon class for the weather condition (can be Bootstrap or FontAwesome)
   */
  initAnimation(containerSelector, iconClass) {
    const container = document.querySelector(containerSelector)
    if (!container) return

    // Clear any existing animation
    container.innerHTML = ""

    // Extract the weather type from the icon class
    let weatherType = ""

    // Handle both Bootstrap and FontAwesome icons
    if (iconClass.startsWith("bi-")) {
      weatherType = iconClass.replace("bi-", "")
    } else if (iconClass.startsWith("fa-")) {
      weatherType = iconClass.replace("fa-", "")
      // Map some FA-specific icons back to our animation types
      if (weatherType === "cloud-showers-heavy") weatherType = "cloud-rain"
      if (weatherType === "cloud-bolt") weatherType = "cloud-lightning-rain"
      if (weatherType === "bolt") weatherType = "cloud-lightning"
    } else {
      // If no prefix, assume it's the weather type directly
      weatherType = iconClass
    }

    // Get the animation class for this weather type
    const animationClass = this.weatherAnimationMap[weatherType] || "weather-cloud"
    container.className = "weather-animation-container " + animationClass

    // Convert Bootstrap icon class to Font Awesome if needed
    let faIcon = iconClass
    if (iconClass.startsWith("bi-")) {
      faIcon = this.faIconMap[iconClass] || "fa-cloud"
    } else if (!iconClass.startsWith("fa-")) {
      faIcon = "fa-" + weatherType
    }

    // Create animation elements based on weather type
    switch (animationClass) {
      case "weather-sun":
        this.createSunAnimation(container, faIcon)
        break
      case "weather-cloud":
        this.createCloudAnimation(container, faIcon)
        break
      case "weather-rain":
        this.createRainAnimation(container, faIcon)
        break
      case "weather-partly-cloudy":
        this.createPartlyCloudyAnimation(container, faIcon)
        break
      case "weather-storm":
        this.createStormAnimation(container, faIcon)
        break
      case "weather-snow":
        this.createSnowAnimation(container, faIcon)
        break
      case "weather-windy":
        this.createWindyAnimation(container, faIcon)
        break
      default:
        this.createCloudAnimation(container, faIcon)
    }
  }

  /**
   * Create sun animation with rays
   */
  createSunAnimation(container, iconClass) {
    // Add the sun icon
    const icon = document.createElement("i")
    icon.className = `fas ${iconClass} weather-icon`
    container.appendChild(icon)

    // Add sun rays
    for (let i = 0; i < 8; i++) {
      const ray = document.createElement("div")
      ray.className = "sun-ray"
      container.appendChild(ray)
    }
  }

  /**
   * Create cloud animation with floating clouds
   */
  createCloudAnimation(container, iconClass) {
    // Add the cloud icon
    const icon = document.createElement("i")
    icon.className = `fas ${iconClass} weather-icon`
    container.appendChild(icon)

    // Add animated clouds
    const cloud1 = document.createElement("div")
    cloud1.className = "cloud cloud-1"
    container.appendChild(cloud1)

    const cloud2 = document.createElement("div")
    cloud2.className = "cloud cloud-2"
    container.appendChild(cloud2)
  }

  /**
   * Create rain animation with falling raindrops
   */
  createRainAnimation(container, iconClass) {
    // Add the rain icon
    const icon = document.createElement("i")
    icon.className = `fas ${iconClass} weather-icon`
    container.appendChild(icon)

    // Add raindrops
    for (let i = 0; i < 7; i++) {
      const raindrop = document.createElement("div")
      raindrop.className = "raindrop"
      container.appendChild(raindrop)
    }
  }

  /**
   * Create partly cloudy animation with sun and clouds
   */
  createPartlyCloudyAnimation(container, iconClass) {
    // Add the partly cloudy icon
    const icon = document.createElement("i")
    icon.className = `fas ${iconClass} weather-icon`
    container.appendChild(icon)

    // Add sun
    const sun = document.createElement("div")
    sun.className = "sun-partial"
    container.appendChild(sun)

    // Add clouds
    const cloud1 = document.createElement("div")
    cloud1.className = "cloud cloud-1"
    container.appendChild(cloud1)
  }

  /**
   * Create storm animation with lightning
   */
  createStormAnimation(container, iconClass) {
    // Add the storm icon
    const icon = document.createElement("i")
    icon.className = `fas ${iconClass} weather-icon`
    container.appendChild(icon)

    // Add lightning
    const lightning = document.createElement("div")
    lightning.className = "lightning"
    container.appendChild(lightning)

    // Add some raindrops too
    for (let i = 0; i < 5; i++) {
      const raindrop = document.createElement("div")
      raindrop.className = "raindrop"
      container.appendChild(raindrop)
    }
  }

  /**
   * Create snow animation with falling snowflakes
   */
  createSnowAnimation(container, iconClass) {
    // Add the snow icon
    const icon = document.createElement("i")
    icon.className = `fas ${iconClass} weather-icon`
    container.appendChild(icon)

    // Add snowflakes
    for (let i = 0; i < 7; i++) {
      const snowflake = document.createElement("div")
      snowflake.className = "snowflake"
      snowflake.innerHTML = "❄"
      container.appendChild(snowflake)
    }
  }

  /**
   * Create windy animation with moving lines
   */
  createWindyAnimation(container, iconClass) {
    // Add the wind icon
    const icon = document.createElement("i")
    icon.className = `fas ${iconClass} weather-icon`
    container.appendChild(icon)

    // Add wind lines
    for (let i = 0; i < 4; i++) {
      const windLine = document.createElement("div")
      windLine.className = "wind-line"
      container.appendChild(windLine)
    }
  }
}

// Create a global instance for use in templates
window.weatherAnimations = new WeatherAnimations()

