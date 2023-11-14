<template>
  <div class="nav-global">
    <div class="nav-global-container">
      <nav>
        <a href="https://developer.blender.org/" class="nav-global-logo">
          <!-- Your SVG code for the logo -->
        </a>

        <button
          class="nav-global-logo js-nav-global-dropdown-toggle"
          @click="toggleDropdown('nav-global-nav-links')"
        >
          <!-- Your SVG code for the dropdown toggle -->
        </button>

        <ul class="nav-global-nav-links nav-global-dropdown" :class="{ 'is-visible': isDropdownVisible }">
          <li>
            <a href="/" class="nav-global-link-active">Home</a>
          </li>
          <li>
            <a href="https://projects.blender.org/infrastructure/web-assets">Repository</a>
          </li>
        </ul>

        <ul class="nav-global-links-right">
          <li>
            <div class="nav-global-apps-dropdown-container">
              <button
                class="js-nav-global-dropdown-toggle"
                data-dropdown-id="nav-global-apps-menu"
                @click="toggleDropdown('nav-global-apps-menu')"
              >
                <!-- Your SVG code for the apps dropdown toggle -->
              </button>

              <!-- Include here '_navbar_global_dropdown.html' -->
            </div>
          </li>
        </ul>
      </nav>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      isDropdownVisible: false,
      dropdownToggles: document.getElementsByClassName("js-nav-global-dropdown-toggle"),
      btnActiveClass: 'nav-global-btn-active',
      isVisibleClass: 'is-visible'
    };
  },
  methods: {
    toggleDropdown(dropdownId) {
      const el = document.getElementById(dropdownId);

      if (el) {
        if (el.classList.contains(this.isVisibleClass)) {
          this.hideAllDropdowns();
        } else {
          this.showDropdown(el);
        }
      }
    },
    hideAllDropdowns() {
      const dropdownMenus = document.getElementsByClassName("js-nav-global-dropdown");

      if (dropdownMenus) {
        for (let i = 0; i < dropdownMenus.length; i++) {
          dropdownMenus[i].classList.remove(this.isVisibleClass);
        }
      }

      this.removeActiveStyling();
    },
    showDropdown(el) {
      this.hideAllDropdowns();
      el.classList.add(this.isVisibleClass);
      this.addActiveStyling();
    },
    removeActiveStyling() {
      for (let i = 0; i < this.dropdownToggles.length; i++) {
        this.dropdownToggles[i].classList.remove(this.btnActiveClass);
      }
    },
    addActiveStyling() {
      for (let i = 0; i < this.dropdownToggles.length; i++) {
        this.dropdownToggles[i].classList.add(this.btnActiveClass);
      }
    }
  },
  mounted() {
    for (let i = 0; i < this.dropdownToggles.length; i++) {
      this.dropdownToggles[i].addEventListener("click", (e) => {
        e.stopPropagation();
        const dropdownId = this.dropdownToggles[i].getAttribute('data-dropdown-id');
        const el = document.getElementById(dropdownId);
        if (el) {
          if (el.classList.contains(this.isVisibleClass)) {
            this.hideAllDropdowns();
          } else {
            this.showDropdown(el);
          }
        }
      });
    }

    document.body.addEventListener("click", (e) => {
      if (!e.target.classList.contains("js-nav-global-dropdown")) {
        this.hideAllDropdowns();
      }
    });

    window.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        this.hideAllDropdowns();
      }
    });
  }
};
</script>

<style>
/* This style block should contain a copy of _navigation_global.scss.
 * Custom styling for this website should be inside a <style> block right after. */
</style>
