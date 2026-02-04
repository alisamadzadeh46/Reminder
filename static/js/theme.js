(function () {
  const key = "theme";
  const saved = localStorage.getItem(key);

  function apply(theme) {
    document.documentElement.setAttribute("data-bs-theme", theme);
    localStorage.setItem(key, theme);
    const icon = document.getElementById("themeIcon");
    const label = document.getElementById("themeLabel");
    if (icon && label) {
      if (theme === "dark") {
        icon.className = "bi bi-moon-stars-fill";
        label.textContent = "دارک";
      } else {
        icon.className = "bi bi-sun-fill";
        label.textContent = "روشن";
      }
    }
  }

  // initial
  if (saved) {
    apply(saved);
  } else {
    // پیش‌فرض: روشن
    apply("light");
  }

  window.toggleTheme = function () {
    const current = document.documentElement.getAttribute("data-bs-theme") || "light";
    apply(current === "dark" ? "light" : "dark");
  };
})();
