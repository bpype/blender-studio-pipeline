<template>
  <div class="nav-global">
    <div class="nav-global-container">
      <nav>
        <a href="/" class="nav-global-logo">
          <svg fill-rule="nonzero" viewBox="0 0 200 162.05">
            <path d="M61.1 104.56c.05 2.6.88 7.66 2.12 11.61a61.27 61.27 0 0 0 13.24 22.92 68.39 68.39 0 0 0 23.17 16.64 74.46 74.46 0 0 0 30.42 6.32 74.52 74.52 0 0 0 30.4-6.42 68.87 68.87 0 0 0 23.15-16.7 61.79 61.79 0 0 0 13.23-22.97 58.06 58.06 0 0 0 2.07-25.55 59.18 59.18 0 0 0-8.44-23.1 64.45 64.45 0 0 0-15.4-16.98h.02L112.76 2.46l-.16-.12c-4.09-3.14-10.96-3.13-15.46.02-4.55 3.18-5.07 8.44-1.02 11.75l-.02.02 26 21.14-79.23.08h-.1c-6.55.01-12.85 4.3-14.1 9.74-1.27 5.53 3.17 10.11 9.98 10.14v.02l40.15-.07-71.66 55-.27.2c-6.76 5.18-8.94 13.78-4.69 19.23 4.32 5.54 13.51 5.55 20.34.03l39.1-32s-.56 4.32-.52 6.91zm100.49 14.47c-8.06 8.2-19.34 12.86-31.54 12.89-12.23.02-23.5-4.6-31.57-12.79-3.93-4-6.83-8.59-8.61-13.48a35.57 35.57 0 0 1 2.34-29.25 39.1 39.1 0 0 1 9.58-11.4 44.68 44.68 0 0 1 28.24-9.85 44.59 44.59 0 0 1 28.24 9.77 38.94 38.94 0 0 1 9.58 11.36 35.58 35.58 0 0 1 4.33 14.18 35.1 35.1 0 0 1-1.98 15.05 37.7 37.7 0 0 1-8.61 13.52zm-57.6-27.91a23.55 23.55 0 0 1 8.55-16.68 28.45 28.45 0 0 1 18.39-6.57 28.5 28.5 0 0 1 18.38 6.57 23.57 23.57 0 0 1 8.55 16.67c.37 6.83-2.37 13.19-7.2 17.9a28.18 28.18 0 0 1-19.73 7.79c-7.83 0-14.84-3-19.75-7.8a23.13 23.13 0 0 1-7.19-17.88z"></path>
            </svg><strong>Blender Studio</strong>
        </a>

        <button
          class="nav-global-logo js-nav-global-dropdown-toggle"
          @click="toggleDropdown('nav-global-nav-links')"
        >
          <!-- Your SVG code for the dropdown toggle -->
        </button>

        <ul class="nav-global-nav-links nav-global-dropdown" :class="{ 'is-visible': isDropdownVisible }">
          <!-- TODO: use constant studioURL for links -->
          <li>
            <a href="https://studio.blender.org/films">Films</a>
          </li>
          <li>
            <a href="https://studio.blender.org/training">Training</a>
          </li>
          <li>
            <a href="https://studio.blender.org/characters">Characters</a>
          </li>
          <li>
            <a href="/" class="nav-global-link-active">Pipeline</a>
          </li>
          <li>
            <a href="https://studio.blender.org/blog">Blog</a>
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
                <svg class="nav-global-icon" height="100px" width="100px" viewBox="0 0 1000 1000">
                  <path d="m 150.5,899 a 50,50 0 0 1 -49,-50 V 749 a 50,50 0 0 1 49,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m 299,0 a 50,50 0 0 1 -50,-50 V 749 a 50,50 0 0 1 50,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m 299,0 a 50,50 0 0 1 -50,-50 V 749 a 50,50 0 0 1 50,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m -598,-299 a 50,50 0 0 1 -49,-50 V 450 a 50,50 0 0 1 49,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m 299,0 a 50,50 0 0 1 -50,-50 V 450 a 50,50 0 0 1 50,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m 299,0 a 50,50 0 0 1 -50,-50 V 450 a 50,50 0 0 1 50,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m -598,-299 a 50,50 0 0 1 -49,-50 V 151 a 50,50 0 0 1 49,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m 299,0 a 50,50 0 0 1 -50,-50 V 151 a 50,50 0 0 1 50,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z m 299,0 a 50,50 0 0 1 -50,-50 V 151 a 50,50 0 0 1 50,-50 h 100 a 50,50 0 0 1 50,50 v 100 a 50,50 0 0 1 -50,50 z"></path>
                </svg>
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

    // Cleanup VPNav Vitepress attributes to make links work
    var VPNav = document.querySelector('.VPNav');
    VPNav.removeAttribute('data-v-14f22a90');
    VPNav.removeAttribute('data-v-702a693e');
  }
};
</script>

<style>
/* This style block should contain a copy of _navigation_global.scss.
 * Custom styling for this website should be inside a <style> block right after. */
</style>
